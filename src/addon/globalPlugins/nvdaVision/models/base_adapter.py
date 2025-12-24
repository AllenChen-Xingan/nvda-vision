"""Base adapter for vision models.

This module defines the abstract base class for all vision model adapters.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from ..schemas.screenshot import Screenshot
from ..schemas.ui_element import UIElement


class VisionModelAdapter(ABC):
    """Abstract base class for vision model adapters.

    Adapters encapsulate different vision models (UI-TARS, MiniCPM-V,
    cloud APIs) behind a unified interface.
    """

    def __init__(self, model_path: Optional[Path] = None):
        """Initialize adapter.

        Args:
            model_path: Path to model files (None for cloud APIs)
        """
        self.model_path = model_path
        self.is_loaded = False
        self.model = None

    @abstractmethod
    def load(self) -> None:
        """Load model into memory.

        Raises:
            RuntimeError: If model loading fails
        """
        pass

    @abstractmethod
    def infer(
        self,
        screenshot: Screenshot,
        timeout: float = 15.0
    ) -> List[UIElement]:
        """Run inference on a screenshot.

        Args:
            screenshot: Screenshot to analyze
            timeout: Max inference time in seconds

        Returns:
            List of detected UI elements with confidence scores

        Raises:
            TimeoutError: If inference exceeds timeout
            RuntimeError: If inference fails
        """
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload model from memory to free resources."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable model name."""
        pass

    @property
    @abstractmethod
    def requires_gpu(self) -> bool:
        """Whether model requires GPU."""
        pass

    @property
    @abstractmethod
    def min_vram_gb(self) -> float:
        """Minimum GPU VRAM in GB (0 if CPU-only)."""
        pass

    @property
    @abstractmethod
    def min_ram_gb(self) -> float:
        """Minimum system RAM in GB."""
        pass


__all__ = ["VisionModelAdapter"]
