"""Vision inference engine with model fallback chain.

This module orchestrates vision model inference with automatic fallback
from GPU → CPU → Cloud API, following privacy-first principles.
"""

from typing import List, Optional
import time

from ..schemas.screenshot import Screenshot
from ..schemas.ui_element import UIElement
from ..models.base_adapter import VisionModelAdapter
from ..infrastructure.logger import logger
from ..constants import InferenceSource


class VisionEngine:
    """Vision inference engine with fallback support.

    Implements fallback chain:
    1. Primary adapter (GPU model if available)
    2. Backup adapters (CPU model)
    3. Cloud API (only with user consent)

    Privacy constraint (real.md): Local processing first, cloud only on failure + consent
    """

    def __init__(
        self,
        primary_adapter: VisionModelAdapter,
        backup_adapters: Optional[List[VisionModelAdapter]] = None,
        cloud_adapter: Optional[VisionModelAdapter] = None,
        enable_cloud: bool = False
    ):
        """Initialize vision engine.

        Args:
            primary_adapter: Primary model adapter (usually GPU model)
            backup_adapters: List of backup adapters (CPU models)
            cloud_adapter: Cloud API adapter (optional)
            enable_cloud: Whether cloud API is enabled (requires consent)
        """
        self.primary_adapter = primary_adapter
        self.backup_adapters = backup_adapters or []
        self.cloud_adapter = cloud_adapter
        self.enable_cloud = enable_cloud

        # Statistics
        self._inference_count = 0
        self._fallback_count = 0
        self._cloud_count = 0

        logger.info(
            f"VisionEngine initialized: "
            f"primary={primary_adapter.name}, "
            f"backups={len(self.backup_adapters)}, "
            f"cloud={'enabled' if enable_cloud and cloud_adapter else 'disabled'}"
        )

    def load_models(self):
        """Load all models into memory.

        Raises:
            RuntimeError: If primary model fails to load
        """
        # Load primary model (required)
        logger.info(f"Loading primary model: {self.primary_adapter.name}")
        try:
            self.primary_adapter.load()
            logger.info(f"Primary model loaded successfully: {self.primary_adapter.name}")
        except Exception as e:
            logger.error(f"Failed to load primary model: {e}")
            raise RuntimeError(f"Primary model loading failed: {e}") from e

        # Load backup models (optional, failures are logged but not fatal)
        for adapter in self.backup_adapters:
            try:
                logger.info(f"Loading backup model: {adapter.name}")
                adapter.load()
                logger.info(f"Backup model loaded: {adapter.name}")
            except Exception as e:
                logger.warning(f"Failed to load backup model {adapter.name}: {e}")

        # Cloud adapter doesn't need loading
        if self.cloud_adapter and self.enable_cloud:
            logger.info(f"Cloud adapter available: {self.cloud_adapter.name}")

    def infer_with_fallback(
        self,
        screenshot: Screenshot,
        timeout: float = 15.0
    ) -> tuple[List[UIElement], InferenceSource]:
        """Run inference with automatic fallback.

        Args:
            screenshot: Screenshot to analyze
            timeout: Timeout for each inference attempt

        Returns:
            Tuple of (list of UIElements, inference source)
            Returns empty list if all models fail
        """
        self._inference_count += 1
        start_time = time.time()

        # Try primary adapter
        try:
            logger.debug(f"Attempting inference with primary: {self.primary_adapter.name}")
            elements = self.primary_adapter.infer(screenshot, timeout=timeout)
            elapsed = time.time() - start_time

            logger.info(
                f"Primary inference successful: {len(elements)} elements "
                f"in {elapsed:.2f}s"
            )
            return elements, InferenceSource.LOCAL_GPU

        except TimeoutError:
            logger.warning(f"Primary adapter timed out after {timeout}s")
            self._fallback_count += 1
            self._notify_user("Primary model timed out, switching to backup...")
        except Exception as e:
            logger.warning(f"Primary adapter failed: {e}")
            self._fallback_count += 1
            self._notify_user("Primary model failed, switching to backup...")

        # Try backup adapters
        for adapter in self.backup_adapters:
            try:
                logger.debug(f"Attempting inference with backup: {adapter.name}")
                elements = adapter.infer(screenshot, timeout=timeout)
                elapsed = time.time() - start_time

                logger.info(
                    f"Backup inference successful ({adapter.name}): "
                    f"{len(elements)} elements in {elapsed:.2f}s"
                )
                return elements, InferenceSource.LOCAL_CPU

            except TimeoutError:
                logger.warning(f"Backup adapter {adapter.name} timed out")
                continue
            except Exception as e:
                logger.warning(f"Backup adapter {adapter.name} failed: {e}")
                continue

        # Try cloud adapter (only if enabled and consented)
        if self.enable_cloud and self.cloud_adapter:
            # Check user consent for cloud API usage (real.md constraint 1)
            if self._check_cloud_consent():
                try:
                    logger.debug(f"Attempting inference with cloud: {self.cloud_adapter.name}")
                    self._cloud_count += 1
                    self._notify_user("Local models failed, using cloud API...")

                    elements = self.cloud_adapter.infer(screenshot, timeout=timeout)
                    elapsed = time.time() - start_time

                    logger.info(
                        f"Cloud inference successful: {len(elements)} elements "
                        f"in {elapsed:.2f}s"
                    )
                    self._notify_user(f"Recognition successful via cloud API")
                    return elements, InferenceSource.CLOUD_API

                except Exception as e:
                    logger.error(f"Cloud adapter failed: {e}")
            else:
                logger.info("User declined cloud API usage")
                self._notify_user("Cloud API declined by user")

        # All adapters failed
        elapsed = time.time() - start_time
        logger.error(
            f"All adapters failed after {elapsed:.2f}s. "
            f"Primary + {len(self.backup_adapters)} backups + "
            f"{'1 cloud' if self.enable_cloud else 'no cloud'}"
        )

        return [], InferenceSource.CACHE  # Return empty result

    def unload_models(self):
        """Unload all models to free resources."""
        logger.info("Unloading all models...")

        # Unload primary
        try:
            self.primary_adapter.unload()
            logger.info(f"Unloaded primary model: {self.primary_adapter.name}")
        except Exception as e:
            logger.exception(f"Failed to unload primary model: {e}")

        # Unload backups
        for adapter in self.backup_adapters:
            try:
                adapter.unload()
                logger.info(f"Unloaded backup model: {adapter.name}")
            except Exception as e:
                logger.exception(f"Failed to unload backup model {adapter.name}: {e}")

        # Cloud adapter doesn't need unloading
        logger.info("All models unloaded")

    def _notify_user(self, message: str):
        """Notify user with voice feedback.

        Args:
            message: Message to announce
        """
        try:
            import wx
            import ui
            wx.CallAfter(ui.message, message)
        except Exception as e:
            logger.warning(f"Failed to notify user: {e}")

    def _check_cloud_consent(self) -> bool:
        """Check if user consents to cloud API usage.

        Returns:
            True if user consents, False otherwise

        Implementation follows real.md constraint 1 (privacy-first)
        """
        # Check if permanent consent is enabled in config
        # This would be set via configuration interface
        # For now, always ask for consent

        try:
            import wx
            dlg = wx.MessageDialog(
                None,
                (
                    "Local models failed to recognize the screen.\n\n"
                    "Allow using cloud API?\n"
                    "(Will upload screenshot to Doubao cloud service)\n\n"
                    "You can permanently enable cloud API in settings."
                ),
                "Use Cloud API?",
                wx.YES_NO | wx.ICON_QUESTION | wx.NO_DEFAULT
            )

            result = dlg.ShowModal()
            dlg.Destroy()

            return result == wx.ID_YES

        except Exception as e:
            logger.exception(f"Failed to show consent dialog: {e}")
            # Default to no consent on error
            return False

    def get_statistics(self) -> dict:
        """Get inference statistics.

        Returns:
            Dictionary with inference metrics
        """
        fallback_rate = (
            (self._fallback_count / self._inference_count * 100)
            if self._inference_count > 0
            else 0
        )
        cloud_rate = (
            (self._cloud_count / self._inference_count * 100)
            if self._inference_count > 0
            else 0
        )

        return {
            "total_inferences": self._inference_count,
            "fallback_count": self._fallback_count,
            "fallback_rate_percent": fallback_rate,
            "cloud_count": self._cloud_count,
            "cloud_rate_percent": cloud_rate,
            "primary_model": self.primary_adapter.name,
            "backup_models": [a.name for a in self.backup_adapters],
            "cloud_enabled": self.enable_cloud and self.cloud_adapter is not None,
        }


__all__ = ["VisionEngine"]
