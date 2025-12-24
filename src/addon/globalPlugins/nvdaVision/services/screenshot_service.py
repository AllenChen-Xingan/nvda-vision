"""Screenshot capture service.

This module provides screenshot capture functionality using Windows API.
"""

from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageGrab
import io

from ..schemas.screenshot import Screenshot
from ..infrastructure.logger import logger


class ScreenshotService:
    """Service for capturing screenshots."""

    def __init__(self):
        """Initialize screenshot service."""
        self.last_screenshot: Optional[Screenshot] = None

    def capture_active_window(self) -> Screenshot:
        """Capture screenshot of the active window.

        Returns:
            Screenshot object with image data and metadata

        Raises:
            RuntimeError: If screenshot capture fails
        """
        try:
            import win32gui
            import win32ui
            import win32con

            # Get active window handle
            hwnd = win32gui.GetForegroundWindow()

            # Get window title
            window_title = win32gui.GetWindowText(hwnd)

            # Get window rectangle
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            # Capture window content
            bbox = (left, top, right, bottom)
            image = ImageGrab.grab(bbox)

            # Get application name from window class
            class_name = win32gui.GetClassName(hwnd)
            app_name = self._guess_app_name(window_title, class_name)

            # Create Screenshot object
            screenshot = Screenshot.from_image(
                image=image,
                window_title=window_title,
                app_name=app_name
            )

            self.last_screenshot = screenshot
            logger.info(
                f"Captured screenshot: {width}x{height}, "
                f"app={app_name}, window={window_title[:30]}"
            )

            return screenshot

        except Exception as e:
            logger.exception("Failed to capture active window")
            raise RuntimeError(f"Screenshot capture failed: {e}") from e

    def capture_full_screen(self) -> Screenshot:
        """Capture full screen screenshot.

        Returns:
            Screenshot object with full screen image

        Raises:
            RuntimeError: If screenshot capture fails
        """
        try:
            # Capture full screen
            image = ImageGrab.grab()

            # Create Screenshot object
            screenshot = Screenshot.from_image(
                image=image,
                window_title="Full Screen",
                app_name="Desktop"
            )

            self.last_screenshot = screenshot
            logger.info(f"Captured full screen: {image.size[0]}x{image.size[1]}")

            return screenshot

        except Exception as e:
            logger.exception("Failed to capture full screen")
            raise RuntimeError(f"Screenshot capture failed: {e}") from e

    def capture_region(
        self,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> Screenshot:
        """Capture a specific screen region.

        Args:
            x: Top-left X coordinate
            y: Top-left Y coordinate
            width: Region width
            height: Region height

        Returns:
            Screenshot of the specified region

        Raises:
            RuntimeError: If screenshot capture fails
        """
        try:
            bbox = (x, y, x + width, y + height)
            image = ImageGrab.grab(bbox)

            screenshot = Screenshot.from_image(
                image=image,
                window_title=f"Region ({x}, {y}, {width}, {height})",
                app_name="Region"
            )

            self.last_screenshot = screenshot
            logger.info(f"Captured region: {width}x{height} at ({x}, {y})")

            return screenshot

        except Exception as e:
            logger.exception("Failed to capture region")
            raise RuntimeError(f"Screenshot capture failed: {e}") from e

    def capture_from_file(self, file_path: Path) -> Screenshot:
        """Load screenshot from file.

        Args:
            file_path: Path to image file

        Returns:
            Screenshot object

        Raises:
            FileNotFoundError: If file doesn't exist
            RuntimeError: If file cannot be loaded
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Screenshot file not found: {file_path}")

        try:
            image = Image.open(file_path)

            screenshot = Screenshot.from_image(
                image=image,
                window_title=file_path.stem,
                app_name="File"
            )

            self.last_screenshot = screenshot
            logger.info(f"Loaded screenshot from file: {file_path}")

            return screenshot

        except Exception as e:
            logger.exception(f"Failed to load screenshot from {file_path}")
            raise RuntimeError(f"Screenshot load failed: {e}") from e

    def save_screenshot(
        self,
        screenshot: Screenshot,
        output_path: Path,
        format: str = "PNG"
    ):
        """Save screenshot to file.

        Args:
            screenshot: Screenshot to save
            output_path: Output file path
            format: Image format (PNG, JPEG, etc.)
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            screenshot.image_data.save(output_path, format=format)
            logger.info(f"Saved screenshot to {output_path}")

        except Exception as e:
            logger.exception(f"Failed to save screenshot to {output_path}")
            raise RuntimeError(f"Screenshot save failed: {e}") from e

    def _guess_app_name(self, window_title: str, class_name: str) -> str:
        """Guess application name from window title and class.

        Args:
            window_title: Window title
            class_name: Window class name

        Returns:
            Guessed application name
        """
        # Known applications
        known_apps = {
            "飞书": "Feishu",
            "钉钉": "DingTalk",
            "微信": "WeChat",
            "企业微信": "WeCom",
            "chrome": "Chrome",
            "firefox": "Firefox",
            "edge": "Edge",
        }

        # Check window title
        title_lower = window_title.lower()
        for keyword, app_name in known_apps.items():
            if keyword in title_lower:
                return app_name

        # Check class name
        class_lower = class_name.lower()
        for keyword, app_name in known_apps.items():
            if keyword in class_lower:
                return app_name

        # Default to window title or class name
        return window_title.split(" - ")[-1] if " - " in window_title else class_name


__all__ = ["ScreenshotService"]
