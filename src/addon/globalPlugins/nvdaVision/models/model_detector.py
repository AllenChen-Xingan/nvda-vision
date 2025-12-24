"""Model detector for automatically selecting best vision model.

This module detects available hardware and selects the optimal vision model.
"""

from pathlib import Path
from typing import Optional, List
import psutil

from .base_adapter import VisionModelAdapter
from .uitars_adapter import UITarsAdapter
from .minicpm_adapter import MiniCPMAdapter
from .doubao_adapter import DoubaoAPIAdapter
from ..infrastructure.logger import logger


class ModelDetector:
    """Detect hardware and select optimal vision model.

    Selection priority:
    1. UI-TARS 7B (GPU with 16GB+ VRAM)
    2. MiniCPM-V 2.6 (CPU with 6GB+ RAM)
    3. Doubao Cloud API (fallback with consent)
    """

    def __init__(self, model_dir: Path, config: dict):
        """Initialize model detector.

        Args:
            model_dir: Directory containing model files
            config: Configuration dictionary
        """
        self.model_dir = model_dir
        self.config = config

    def detect_best_adapter(self) -> VisionModelAdapter:
        """Detect and return best available vision model adapter.

        Returns:
            Best vision model adapter for current hardware

        Raises:
            RuntimeError: If no suitable model found
        """
        logger.info("Detecting optimal vision model...")

        # Check GPU availability for UI-TARS
        if self._check_gpu_requirements():
            uitars_path = self.model_dir / "ui-tars-7b"
            if uitars_path.exists():
                logger.info("Selected UI-TARS 7B (GPU model)")
                return UITarsAdapter(uitars_path, self.config)
            else:
                logger.warning(f"GPU available but UI-TARS model not found at {uitars_path}")

        # Check CPU/RAM for MiniCPM
        if self._check_cpu_requirements():
            minicpm_path = self.model_dir / "minicpm-v-2.6"
            if minicpm_path.exists():
                logger.info("Selected MiniCPM-V 2.6 (CPU model)")
                return MiniCPMAdapter(minicpm_path, self.config)
            else:
                logger.warning(f"CPU suitable but MiniCPM model not found at {minicpm_path}")

        # Fallback to cloud API if enabled
        if self.config.get("enable_cloud_api", False):
            api_key = self.config.get("doubao_api_key")
            if api_key:
                logger.info("Selected Doubao Cloud API (fallback)")
                return DoubaoAPIAdapter(api_key, config=self.config)
            else:
                logger.warning("Cloud API enabled but no API key configured")

        raise RuntimeError(
            "No suitable vision model found. Please ensure:\n"
            "1. GPU with 16GB+ VRAM for UI-TARS, OR\n"
            "2. CPU with 6GB+ RAM and MiniCPM model installed, OR\n"
            "3. Cloud API enabled with valid API key"
        )

    def detect_all_adapters(self) -> List[VisionModelAdapter]:
        """Detect all available vision model adapters.

        Returns:
            List of all available adapters (primary + backups + cloud)
        """
        adapters = []

        # UI-TARS (GPU)
        if self._check_gpu_requirements():
            uitars_path = self.model_dir / "ui-tars-7b"
            if uitars_path.exists():
                adapters.append(UITarsAdapter(uitars_path, self.config))
                logger.info("Found UI-TARS 7B (GPU)")

        # MiniCPM (CPU)
        if self._check_cpu_requirements():
            minicpm_path = self.model_dir / "minicpm-v-2.6"
            if minicpm_path.exists():
                adapters.append(MiniCPMAdapter(minicpm_path, self.config))
                logger.info("Found MiniCPM-V 2.6 (CPU)")

        # Doubao Cloud API
        if self.config.get("enable_cloud_api", False):
            api_key = self.config.get("doubao_api_key")
            if api_key:
                adapters.append(DoubaoAPIAdapter(api_key, config=self.config))
                logger.info("Found Doubao Cloud API")

        logger.info(f"Total adapters detected: {len(adapters)}")
        return adapters

    def _check_gpu_requirements(self) -> bool:
        """Check if GPU meets UI-TARS requirements.

        Returns:
            True if GPU with 16GB+ VRAM available
        """
        try:
            import torch

            if not torch.cuda.is_available():
                logger.debug("GPU check: CUDA not available")
                return False

            # Check VRAM
            device_props = torch.cuda.get_device_properties(0)
            vram_gb = device_props.total_memory / 1e9

            logger.debug(
                f"GPU check: {device_props.name}, "
                f"VRAM: {vram_gb:.1f}GB"
            )

            if vram_gb < 16.0:
                logger.debug(f"GPU check: Insufficient VRAM ({vram_gb:.1f}GB < 16GB)")
                return False

            logger.info(f"GPU check: PASSED ({device_props.name}, {vram_gb:.1f}GB)")
            return True

        except ImportError:
            logger.debug("GPU check: PyTorch not installed")
            return False
        except Exception as e:
            logger.warning(f"GPU check failed: {e}")
            return False

    def _check_cpu_requirements(self) -> bool:
        """Check if CPU/RAM meets MiniCPM requirements.

        Returns:
            True if 6GB+ RAM available
        """
        try:
            available_ram_gb = psutil.virtual_memory().available / 1e9
            total_ram_gb = psutil.virtual_memory().total / 1e9

            logger.debug(
                f"CPU check: RAM {available_ram_gb:.1f}GB available / "
                f"{total_ram_gb:.1f}GB total"
            )

            if available_ram_gb < 6.0:
                logger.debug(
                    f"CPU check: Insufficient RAM ({available_ram_gb:.1f}GB < 6GB)"
                )
                return False

            logger.info(f"CPU check: PASSED ({available_ram_gb:.1f}GB available)")
            return True

        except Exception as e:
            logger.warning(f"CPU check failed: {e}")
            return False

    def get_hardware_info(self) -> dict:
        """Get detailed hardware information.

        Returns:
            Dictionary with hardware specs
        """
        info = {
            "cpu_cores": psutil.cpu_count(logical=False),
            "cpu_threads": psutil.cpu_count(logical=True),
            "total_ram_gb": psutil.virtual_memory().total / 1e9,
            "available_ram_gb": psutil.virtual_memory().available / 1e9,
            "gpu_available": False,
            "gpu_name": None,
            "gpu_vram_gb": 0.0,
        }

        try:
            import torch

            if torch.cuda.is_available():
                device_props = torch.cuda.get_device_properties(0)
                info["gpu_available"] = True
                info["gpu_name"] = device_props.name
                info["gpu_vram_gb"] = device_props.total_memory / 1e9

        except Exception:
            pass

        return info


__all__ = ["ModelDetector"]
