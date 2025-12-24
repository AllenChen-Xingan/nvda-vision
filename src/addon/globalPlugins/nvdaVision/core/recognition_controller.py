"""Recognition controller for orchestrating recognition flow.

This module coordinates the complete recognition pipeline:
screenshot → cache lookup → inference → result processing → speech output
"""

import threading
from typing import Callable, Optional, List
from datetime import datetime
import time

from ..schemas.screenshot import Screenshot
from ..schemas.recognition_result import RecognitionResult, UIElement
from ..services.screenshot_service import ScreenshotService
from ..services.cache_manager import CacheManager
from ..services.vision_engine import VisionEngine
from ..services.result_processor import ResultProcessor
from ..infrastructure.logger import logger
from ..constants import RecognitionStatus, InferenceSource


class RecognitionController:
    """Orchestrate recognition flow with async execution.

    Handles:
    - Asynchronous recognition to avoid blocking NVDA
    - Progress feedback (5s+ operations)
    - Timeout management (15s max)
    - Cache integration
    - Graceful degradation on errors
    """

    def __init__(
        self,
        screenshot_service: ScreenshotService,
        cache_manager: CacheManager,
        vision_engine: VisionEngine,
        result_processor: ResultProcessor,
        config: dict
    ):
        """Initialize recognition controller.

        Args:
            screenshot_service: Service for capturing screenshots
            cache_manager: Cache manager for results
            vision_engine: Vision inference engine
            result_processor: Result post-processor
            config: Configuration dictionary
        """
        self.screenshot_service = screenshot_service
        self.cache_manager = cache_manager
        self.vision_engine = vision_engine
        self.result_processor = result_processor
        self.config = config

        # Current state
        self._current_thread: Optional[threading.Thread] = None
        self._cancel_requested = False
        self._current_result: Optional[RecognitionResult] = None
        self._current_element_index = 0

        logger.info("RecognitionController initialized with full pipeline")

    def recognize_screen_async(
        self,
        callback: Callable[[RecognitionResult], None],
        error_callback: Callable[[Exception], None]
    ):
        """Recognize screen in background thread.

        Args:
            callback: Called with result on success
            error_callback: Called with exception on failure
        """
        # Cancel previous recognition if still running
        if self._current_thread and self._current_thread.is_alive():
            logger.warning("Previous recognition still running, cancelling")
            self._cancel_requested = True
            self._current_thread.join(timeout=1.0)

        self._cancel_requested = False

        # Start new background thread
        self._current_thread = threading.Thread(
            target=self._recognition_worker,
            args=(callback, error_callback),
            daemon=True,
            name="RecognitionWorker"
        )
        self._current_thread.start()

        logger.info("Recognition started in background thread")

    def _recognition_worker(
        self,
        callback: Callable,
        error_callback: Callable
    ):
        """Worker function running in background thread."""
        start_time = time.time()
        progress_notified = False

        try:
            # Step 1: Capture screenshot
            logger.debug("Step 1: Capturing screenshot...")
            screenshot = self.screenshot_service.capture_active_window()

            if self._cancel_requested:
                logger.info("Recognition cancelled after screenshot")
                return

            # Step 2: Check cache
            logger.debug(f"Step 2: Checking cache for {screenshot.hash[:8]}")
            cached_result = self.cache_manager.get(screenshot)

            if cached_result:
                # Cache hit
                logger.info(f"Cache hit: {screenshot.hash[:8]}")
                self._current_result = cached_result
                self._current_element_index = 0
                self._call_on_main_thread(callback, cached_result)
                return

            # Step 3: Cache miss - perform inference
            logger.info("Cache miss - performing inference")

            # Set up progress feedback (after 5 seconds) - real.md constraint 6
            def progress_monitor():
                nonlocal progress_notified
                time.sleep(5.0)
                if not progress_notified and self._current_thread and self._current_thread.is_alive():
                    elapsed = time.time() - start_time
                    logger.info(f"Long-running inference, {elapsed:.1f}s elapsed")

                    # Notify user via voice feedback
                    try:
                        import wx
                        import ui
                        wx.CallAfter(
                            ui.message,
                            f"Recognizing, {int(elapsed)} seconds elapsed..."
                        )
                        progress_notified = True
                    except Exception as e:
                        logger.warning(f"Failed to provide progress feedback: {e}")

            progress_thread = threading.Thread(target=progress_monitor, daemon=True)
            progress_thread.start()

            if self._cancel_requested:
                logger.info("Recognition cancelled before inference")
                return

            # Run inference with fallback
            timeout = self.config.get("inference_timeout", 15.0)
            inference_start = time.time()

            elements, source = self.vision_engine.infer_with_fallback(
                screenshot,
                timeout=timeout
            )

            inference_time = time.time() - inference_start

            if self._cancel_requested:
                logger.info("Recognition cancelled after inference")
                return

            # Step 4: Process results
            logger.debug(f"Step 4: Processing {len(elements)} elements")

            result = self.result_processor.process(
                elements=elements,
                screenshot=screenshot,
                model_name=self.vision_engine.primary_adapter.name,
                inference_time=inference_time,
                source=source
            )

            # Step 5: Cache result (if successful)
            if result.status != RecognitionStatus.FAILURE:
                logger.debug("Step 5: Caching result")
                self.cache_manager.put(screenshot, result)

            # Update state
            self._current_result = result
            self._current_element_index = 0

            elapsed = time.time() - start_time
            logger.info(
                f"Recognition complete: {len(result.elements)} elements "
                f"in {elapsed:.2f}s total"
            )

            # Callback with result
            self._call_on_main_thread(callback, result)

        except Exception as e:
            elapsed = time.time() - start_time
            logger.exception(f"Recognition failed after {elapsed:.2f}s")
            self._call_on_main_thread(error_callback, e)

    def _call_on_main_thread(self, func: Callable, arg):
        """Call function on NVDA main thread.

        Uses wx.CallAfter to safely update UI from background thread.
        """
        try:
            import wx
            wx.CallAfter(func, arg)
        except Exception as e:
            logger.exception("Failed to call function on main thread")
            # Fallback: call directly (less safe but better than nothing)
            try:
                func(arg)
            except Exception:
                logger.exception("Callback failed even on direct call")

    def get_next_element(self) -> Optional[UIElement]:
        """Navigate to next UI element.

        Returns:
            Next UIElement or None if no more elements
        """
        if not self._current_result or not self._current_result.elements:
            return None

        self._current_element_index += 1
        if self._current_element_index >= len(self._current_result.elements):
            self._current_element_index = len(self._current_result.elements) - 1
            return None

        return self._current_result.elements[self._current_element_index]

    def get_previous_element(self) -> Optional[UIElement]:
        """Navigate to previous UI element.

        Returns:
            Previous UIElement or None if at start
        """
        if not self._current_result or not self._current_result.elements:
            return None

        self._current_element_index -= 1
        if self._current_element_index < 0:
            self._current_element_index = 0
            return None

        return self._current_result.elements[self._current_element_index]

    def get_current_element(self) -> Optional[UIElement]:
        """Get currently focused UI element.

        Returns:
            Current UIElement or None if no elements available
        """
        if not self._current_result or not self._current_result.elements:
            return None

        if self._current_element_index < 0 or \
           self._current_element_index >= len(self._current_result.elements):
            return None

        return self._current_result.elements[self._current_element_index]

    def cancel_recognition(self):
        """Request cancellation of current recognition."""
        if self._current_thread and self._current_thread.is_alive():
            logger.info("Requesting recognition cancellation")
            self._cancel_requested = True

    def cleanup(self):
        """Cleanup resources."""
        self.cancel_recognition()
        if self._current_thread:
            self._current_thread.join(timeout=2.0)
        logger.info("RecognitionController cleaned up")


__all__ = ["RecognitionController"]
