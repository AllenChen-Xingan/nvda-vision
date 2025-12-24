"""NVDA Vision Screen Reader Plugin.

This plugin enables vision-impaired users to interact with inaccessible UI
using AI-powered vision models.

Satisfies requirements from:
- .42cog/real/real.md (Reality constraints)
- .42cog/cog/cog.md (Cognitive model)
- spec/dev/code.spec.md (Code specification)
"""

import globalPluginHandler
import addonHandler
import ui
import api
import scriptHandler
from pathlib import Path

from .constants import __version__
from .infrastructure import logger, setup_logger, ConfigManager
from .services import ScreenshotService, CacheManager, VisionEngine, ResultProcessor
from .models import ModelDetector
from .core import RecognitionController
from .schemas import Screenshot, RecognitionResult

# Initialize translation support
addonHandler.initTranslation()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    """NVDA Vision global plugin.

    Provides keyboard shortcuts for vision-based screen recognition.

    Critical: All plugin code MUST be wrapped in try-except to prevent
    NVDA crashes (real.md constraint 5).
    """

    def __init__(self):
        """Initialize NVDA Vision plugin."""
        super().__init__()

        # Plugin state
        self.enabled = False  # Default to disabled until init succeeds
        self.is_recognizing = False

        try:
            # Setup logging first
            log_dir = Path.home() / ".nvda_vision" / "logs"
            setup_logger(log_dir=log_dir, level="INFO")
            logger.info(f"NVDA Vision plugin v{__version__} initializing...")

            # Load configuration
            self.config = ConfigManager()
            logger.info("Configuration loaded successfully")

            # Initialize services
            self.screenshot_service = ScreenshotService()

            cache_dir = Path.home() / ".nvda_vision" / "cache"
            self.cache_manager = CacheManager(
                cache_dir=cache_dir,
                ttl_seconds=self.config.get("cache.ttl_seconds", 300),
                max_size=self.config.get("cache.max_size", 1000)
            )

            # Initialize model detector and vision engine
            model_dir = Path.home() / ".nvda_vision" / "models"
            model_dir.mkdir(parents=True, exist_ok=True)

            logger.info("Detecting available vision models...")
            detector = ModelDetector(model_dir, self.config.config)

            # Get all available adapters
            try:
                adapters = detector.detect_all_adapters()

                if not adapters:
                    logger.warning("No vision models detected. Plugin will run in limited mode.")
                    ui.message("NVDA Vision: No models detected. Please install models.")
                    self.vision_engine = None
                else:
                    # Use first adapter as primary, rest as backups
                    primary = adapters[0]
                    backups = adapters[1:] if len(adapters) > 1 else []

                    # Find cloud adapter if exists
                    cloud_adapter = None
                    for adapter in adapters:
                        if adapter.name == "Doubao Cloud API":
                            cloud_adapter = adapter
                            if adapter in backups:
                                backups.remove(adapter)
                            break

                    # Initialize vision engine
                    enable_cloud = self.config.get("enable_cloud_api", False)
                    self.vision_engine = VisionEngine(
                        primary_adapter=primary,
                        backup_adapters=backups,
                        cloud_adapter=cloud_adapter,
                        enable_cloud=enable_cloud
                    )

                    # Load models (this may take time)
                    logger.info("Loading vision models...")
                    ui.message("Loading vision models, please wait...")
                    self.vision_engine.load_models()
                    logger.info("Vision models loaded successfully")

            except Exception as e:
                logger.exception("Failed to initialize vision models")
                ui.message("NVDA Vision: Model initialization failed. Plugin will run in limited mode.")
                self.vision_engine = None

            # Initialize result processor
            confidence_threshold = self.config.get("confidence_threshold", 0.7)
            self.result_processor = ResultProcessor(confidence_threshold)

            # Initialize recognition controller
            self.recognition_controller = RecognitionController(
                screenshot_service=self.screenshot_service,
                cache_manager=self.cache_manager,
                vision_engine=self.vision_engine,
                result_processor=self.result_processor,
                config=self.config.config
            )

            logger.info("All services initialized successfully")

            # Mark as enabled
            self.enabled = True

            # Register settings panel to NVDA settings dialog
            try:
                import gui.settingsDialogs
                from .ui import NVDAVisionSettingsPanel

                # 将设置面板添加到NVDA设置对话框
                gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(
                    NVDAVisionSettingsPanel
                )
                logger.info("Settings panel registered to NVDA Settings dialog")

            except Exception as e:
                logger.exception("Failed to register settings panel")
                # 不影响插件主功能，继续运行

            # Announce ready
            ui.message("NVDA Vision initialized")
            logger.info("NVDA Vision plugin initialized successfully")

        except Exception as e:
            # Log error but don't crash NVDA
            logger.exception("Failed to initialize NVDA Vision plugin")
            ui.message("NVDA Vision: Initialization failed. Check logs.")
            self.enabled = False

    def terminate(self):
        """Cleanup resources on plugin unload.

        MUST NOT raise exceptions (real.md constraint 5).
        """
        logger.info("NVDA Vision plugin terminating...")

        try:
            # Remove settings panel from NVDA settings dialog
            try:
                import gui.settingsDialogs
                from .ui import NVDAVisionSettingsPanel

                if NVDAVisionSettingsPanel in gui.settingsDialogs.NVDASettingsDialog.categoryClasses:
                    gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(
                        NVDAVisionSettingsPanel
                    )
                    logger.info("Settings panel removed from NVDA Settings dialog")

            except Exception as e:
                logger.exception("Failed to remove settings panel")

            # Unload vision models
            if hasattr(self, 'vision_engine') and self.vision_engine:
                logger.info("Unloading vision models...")
                self.vision_engine.unload_models()

            # Cleanup recognition controller
            if hasattr(self, 'recognition_controller'):
                self.recognition_controller.cleanup()

            # Close cache manager
            if hasattr(self, 'cache_manager'):
                self.cache_manager.close()

            logger.info("NVDA Vision plugin terminated successfully")

        except Exception as e:
            # Log but don't crash NVDA
            logger.exception("Error during plugin termination")

        finally:
            # Always call super().terminate()
            super().terminate()

    @scriptHandler.script(
        description=_("Recognize UI elements on current screen"),
        gesture="kb:NVDA+shift+v",
        category="NVDA Vision"
    )
    def script_recognizeScreen(self, gesture):
        """Recognize current screen using vision model.

        This runs asynchronously to avoid blocking NVDA (real.md constraint 5).
        """
        try:
            if not self.enabled:
                ui.message(_("NVDA Vision is not available"))
                return

            if not self.vision_engine:
                ui.message(_("No vision models available. Please install models."))
                return

            if self.is_recognizing:
                ui.message(_("Recognition already in progress"))
                return

            # Mark as recognizing
            self.is_recognizing = True

            # Start async recognition
            self.recognition_controller.recognize_screen_async(
                callback=self._on_recognition_complete,
                error_callback=self._on_recognition_error
            )

            # Immediate feedback
            ui.message(_("Recognizing screen..."))
            logger.info("Recognition started")

        except Exception as e:
            # Catch all exceptions to prevent NVDA crash
            logger.exception("Error in script_recognizeScreen")
            ui.message(_("Recognition failed to start"))
            self.is_recognizing = False

    @scriptHandler.script(
        description=_("Show cache statistics"),
        gesture="kb:NVDA+shift+c",
        category="NVDA Vision"
    )
    def script_showCacheStats(self, gesture):
        """Show cache statistics."""
        try:
            if not self.enabled:
                ui.message(_("NVDA Vision is not available"))
                return

            stats = self.cache_manager.get_stats()

            message = _(
                "Cache: {total} results, {hits} hits, {rate:.1f}% hit rate"
            ).format(
                total=stats.get('total_results', 0),
                hits=stats.get('total_cache_hits', 0),
                rate=stats.get('hit_rate', 0)
            )

            ui.message(message)
            logger.info(f"Cache stats requested: {message}")

        except Exception as e:
            logger.exception("Failed to get cache stats")
            ui.message(_("Failed to get cache statistics"))

    @scriptHandler.script(
        description=_("Clear recognition cache"),
        gesture="kb:NVDA+shift+alt+c",
        category="NVDA Vision"
    )
    def script_clearCache(self, gesture):
        """Clear recognition cache."""
        try:
            if not self.enabled:
                ui.message(_("NVDA Vision is not available"))
                return

            self.cache_manager.clear()
            ui.message(_("Cache cleared"))
            logger.info("Cache cleared by user")

        except Exception as e:
            logger.exception("Failed to clear cache")
            ui.message(_("Failed to clear cache"))

    @scriptHandler.script(
        description=_("Navigate to next UI element"),
        gesture="kb:NVDA+shift+n",
        category="NVDA Vision"
    )
    def script_nextElement(self, gesture):
        """Navigate to next UI element."""
        try:
            if not self.enabled:
                ui.message(_("NVDA Vision is not available"))
                return

            element = self.recognition_controller.get_next_element()

            if element:
                self._speak_element(element)
            else:
                ui.message(_("No more elements"))

        except Exception as e:
            logger.exception("Error navigating to next element")
            ui.message(_("Navigation failed"))

    @scriptHandler.script(
        description=_("Navigate to previous UI element"),
        gesture="kb:NVDA+shift+p",
        category="NVDA Vision"
    )
    def script_previousElement(self, gesture):
        """Navigate to previous UI element."""
        try:
            if not self.enabled:
                ui.message(_("NVDA Vision is not available"))
                return

            element = self.recognition_controller.get_previous_element()

            if element:
                self._speak_element(element)
            else:
                ui.message(_("No previous elements"))

        except Exception as e:
            logger.exception("Error navigating to previous element")
            ui.message(_("Navigation failed"))

    @scriptHandler.script(
        description=_("Activate current UI element"),
        gesture="kb:NVDA+shift+enter",
        category="NVDA Vision"
    )
    def script_activateElement(self, gesture):
        """Activate (click) current UI element.

        Implementation follows PRIORITY_ROADMAP.md P0-2 requirements:
        - Checks element actionability
        - Validates bbox coordinates
        - Shows confirmation for low-confidence elements
        - Uses pyautogui for mouse simulation
        - Provides voice feedback
        - Satisfies real.md constraint 3 (confidence transparency)
        """
        try:
            if not self.enabled:
                ui.message(_("NVDA Vision is not available"))
                return

            # Get current element
            element = self.recognition_controller.get_current_element()

            if not element:
                ui.message(_("No element to activate"))
                logger.info("Activation failed: no current element")
                return

            # Check if element is actionable
            if not element.actionable:
                ui.message(
                    _("Element not actionable: {type}").format(
                        type=element.element_type
                    )
                )
                logger.info(
                    f"Activation skipped: element not actionable "
                    f"({element.element_type})"
                )
                return

            # Low confidence warning (real.md constraint 3)
            from .constants import LOW_CONFIDENCE_THRESHOLD
            if element.confidence < LOW_CONFIDENCE_THRESHOLD:
                # Ask for confirmation
                try:
                    import wx
                    dlg = wx.MessageDialog(
                        None,
                        _("This element has low confidence ({conf:.0%}).\n"
                          "Type: {type}\n"
                          "Text: {text}\n\n"
                          "Continue with activation?").format(
                            conf=element.confidence,
                            type=element.element_type,
                            text=element.text or "(no text)"
                        ),
                        _("Confirm Activation"),
                        wx.YES_NO | wx.ICON_QUESTION | wx.NO_DEFAULT
                    )

                    result = dlg.ShowModal()
                    dlg.Destroy()

                    if result != wx.ID_YES:
                        ui.message(_("Activation cancelled"))
                        logger.info("User cancelled low-confidence activation")
                        return

                except ImportError:
                    # Fallback: voice warning only (no wx available)
                    ui.message(
                        _("Warning: low confidence {conf:.0%}. "
                          "Press Enter to continue, Escape to cancel").format(
                            conf=element.confidence
                        )
                    )

            # Validate bbox
            bbox = element.bbox
            if not bbox or len(bbox) != 4:
                ui.message(_("Element coordinates invalid"))
                logger.error(f"Invalid bbox: {bbox}")
                return

            x1, y1, x2, y2 = bbox

            # Check bbox is within screen bounds
            try:
                import win32api
                screen_width = win32api.GetSystemMetrics(0)
                screen_height = win32api.GetSystemMetrics(1)

                if not (0 <= x1 < x2 <= screen_width and
                        0 <= y1 < y2 <= screen_height):
                    ui.message(_("Element coordinates out of screen bounds"))
                    logger.error(
                        f"Bbox out of bounds: {bbox}, "
                        f"screen: {screen_width}x{screen_height}"
                    )
                    return

            except Exception as e:
                logger.warning(f"Failed to check screen bounds: {e}")

            # Calculate click position (center of bbox)
            click_x = (x1 + x2) // 2
            click_y = (y1 + y2) // 2

            # Perform click with pyautogui
            try:
                import pyautogui

                # Move mouse to target (with animation for natural feel)
                pyautogui.moveTo(click_x, click_y, duration=0.2)

                # Perform click
                pyautogui.click(click_x, click_y)

                # Voice feedback
                ui.message(
                    _("Activated: {text}").format(
                        text=element.text or element.element_type
                    )
                )

                # Log success
                logger.info(
                    f"Element activated: type={element.element_type}, "
                    f"text='{element.text}', pos=({click_x}, {click_y}), "
                    f"confidence={element.confidence:.2%}"
                )

            except ImportError:
                ui.message(_("pyautogui not installed"))
                logger.error("pyautogui not available for element activation")

            except Exception as e:
                ui.message(_("Activation failed"))
                logger.exception(f"Failed to activate element: {e}")

        except Exception as e:
            logger.exception("Error in element activation")
            ui.message(_("Activation error"))

    def _on_recognition_complete(self, result: RecognitionResult):
        """Callback when recognition completes successfully.

        Args:
            result: Recognition result
        """
        try:
            self.is_recognizing = False

            num_elements = result.element_count
            logger.info(f"Recognition complete: {num_elements} elements found")

            if num_elements == 0:
                ui.message("No UI elements detected")
            else:
                # Announce result with confidence info (real.md constraint 3)
                avg_conf = result.average_confidence
                ui.message(
                    f"Found {num_elements} elements, "
                    f"average confidence {avg_conf:.0%}"
                )

        except Exception as e:
            logger.exception("Error in recognition callback")
            ui.message("Error processing recognition result")

    def _on_recognition_error(self, error: Exception):
        """Callback when recognition fails.

        Args:
            error: Exception that occurred
        """
        try:
            self.is_recognizing = False
            logger.error(f"Recognition error: {error}")
            ui.message("Recognition failed. Check logs for details.")

        except Exception as e:
            logger.exception("Error in error callback")

    def _speak_element(self, element):
        """Speak UI element information with NVDA TTS.

        Args:
            element: UIElement instance to announce
        """
        try:
            # Import speech here to avoid issues if NVDA not available
            import speech

            # Build speech text
            text_parts = []

            # Type and text with better handling for empty text (icon button fix)
            element_description = element.text if element.text else "unrecognized element"

            # If it's a button type without text, add helpful context
            if not element.text and element.element_type in ["button", "icon_button"]:
                element_description = f"unrecognized {element.element_type}"

            text_parts.append(f"{element.element_type}: {element_description}")

            # Confidence annotation (real.md constraint 3)
            from .constants import LOW_CONFIDENCE_THRESHOLD
            if element.confidence < LOW_CONFIDENCE_THRESHOLD:
                text_parts.append("(uncertain)")

            # Position info
            x = element.center_x
            y = element.center_y
            text_parts.append(f"at {x}, {y}")

            speech_text = " ".join(text_parts)
            speech.speak(speech_text)

        except Exception as e:
            logger.exception("Error speaking element")
            ui.message(f"{element.element_type}: {element.text}")


# Module metadata
__all__ = ["GlobalPlugin"]

