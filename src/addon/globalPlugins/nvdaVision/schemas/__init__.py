"""Data schemas for NVDA Vision plugin."""

from .ui_element import UIElement
from .screenshot import Screenshot
from .recognition_result import RecognitionResult

__all__ = [
    "UIElement",
    "Screenshot",
    "RecognitionResult",
]
