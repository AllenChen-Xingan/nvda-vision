"""MiniCPM-V 2.6 vision model adapter.

This adapter wraps the MiniCPM-V 2.6 model for UI element recognition.
Runs on CPU with 6GB+ RAM.
"""

from pathlib import Path
from typing import List
import time

from .base_adapter import VisionModelAdapter
from ..schemas.screenshot import Screenshot
from ..schemas.ui_element import UIElement
from ..infrastructure.logger import logger


class MiniCPMAdapter(VisionModelAdapter):
    """Adapter for MiniCPM-V 2.6 vision model.

    Requirements:
    - CPU with 6GB+ RAM
    - PyTorch 2.0+ (CPU version)
    """

    def __init__(self, model_path: Path, config: dict = None):
        """Initialize MiniCPM adapter.

        Args:
            model_path: Path to MiniCPM model files
            config: Optional configuration dict
        """
        super().__init__(model_path)
        self.config = config or {}
        self.model = None
        self.tokenizer = None
        self.device = None

    @property
    def name(self) -> str:
        return "MiniCPM-V 2.6"

    @property
    def requires_gpu(self) -> bool:
        return False

    @property
    def min_vram_gb(self) -> float:
        return 0.0  # CPU-only

    @property
    def min_ram_gb(self) -> float:
        return 6.0

    def load(self) -> None:
        """Load MiniCPM model into memory.

        Raises:
            RuntimeError: If insufficient RAM
        """
        if self.is_loaded:
            logger.warning("MiniCPM model already loaded")
            return

        try:
            import torch
            import psutil
            from transformers import AutoModel, AutoTokenizer

            # Check available RAM
            available_ram_gb = psutil.virtual_memory().available / 1e9

            if available_ram_gb < self.min_ram_gb:
                raise RuntimeError(
                    f"Insufficient RAM: {available_ram_gb:.1f}GB available, "
                    f"{self.min_ram_gb}GB required"
                )

            logger.info(
                f"Loading MiniCPM model from {self.model_path} "
                f"(Available RAM: {available_ram_gb:.1f}GB)"
            )

            # Load model on CPU
            self.device = torch.device("cpu")
            self.model = AutoModel.from_pretrained(
                str(self.model_path),
                torch_dtype=torch.float32,
                trust_remote_code=True
            ).to(self.device)
            self.model.eval()

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                trust_remote_code=True
            )

            self.is_loaded = True
            logger.info("MiniCPM model loaded successfully on CPU")

        except Exception as e:
            logger.exception("Failed to load MiniCPM model")
            self.is_loaded = False
            raise RuntimeError(f"MiniCPM model loading failed: {e}") from e

    def infer(
        self,
        screenshot: Screenshot,
        timeout: float = 15.0
    ) -> List[UIElement]:
        """Run MiniCPM inference on screenshot.

        Args:
            screenshot: Screenshot to analyze
            timeout: Maximum inference time in seconds

        Returns:
            List of detected UI elements

        Raises:
            RuntimeError: If model not loaded
            TimeoutError: If inference exceeds timeout
        """
        if not self.is_loaded:
            raise RuntimeError("MiniCPM model not loaded")

        start_time = time.time()

        try:
            import torch

            logger.debug(
                f"Starting MiniCPM inference for {screenshot.hash[:8]} "
                f"({screenshot.width}x{screenshot.height})"
            )

            # Prepare image
            image_tensor = self._prepare_image(screenshot)

            # Prepare prompt
            prompt = (
                "Analyze this UI screenshot and list all interactive elements. "
                "For each element provide: type (button/textbox/link/etc), "
                "visible text, position, and confidence score."
            )

            # Tokenize
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True
            ).to(self.device)

            # Run inference
            with torch.no_grad():
                # Check timeout
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Inference exceeded timeout: {timeout}s")

                # Generate
                outputs = self.model.generate(
                    **inputs,
                    images=image_tensor,
                    max_new_tokens=1024,
                    temperature=0.7,
                    do_sample=False
                )

                # Check timeout
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Inference exceeded timeout: {timeout}s")

            # Decode output
            output_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Parse to UIElements
            elements = self._parse_model_output(output_text, screenshot)

            elapsed = time.time() - start_time
            logger.info(
                f"MiniCPM inference complete: {len(elements)} elements "
                f"in {elapsed:.2f}s"
            )

            return elements

        except TimeoutError:
            elapsed = time.time() - start_time
            logger.warning(f"MiniCPM inference timed out after {elapsed:.2f}s")
            raise

        except Exception as e:
            elapsed = time.time() - start_time
            logger.exception(f"MiniCPM inference failed after {elapsed:.2f}s")
            raise RuntimeError(f"MiniCPM inference failed: {e}") from e

    def _prepare_image(self, screenshot: Screenshot):
        """Prepare image tensor for model input."""
        import torch
        from torchvision import transforms

        # MiniCPM image preprocessing
        transform = transforms.Compose([
            transforms.Resize((224, 224)),  # MiniCPM input size
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

        image_tensor = transform(screenshot.image_data).unsqueeze(0).to(self.device)
        return image_tensor

    def _parse_model_output(
        self,
        output_text: str,
        screenshot: Screenshot
    ) -> List[UIElement]:
        """Parse model output into UIElement objects."""
        elements = []

        try:
            import re
            import json

            # Try JSON parsing first
            json_match = re.search(r'\[.*\]', output_text, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())

                for item in parsed_data:
                    element = UIElement(
                        id=item.get("id", ""),
                        element_type=item.get("type", "unknown"),
                        text=item.get("text", ""),
                        bbox=item.get("bbox", [0, 0, 0, 0]),
                        confidence=item.get("confidence", 0.5),
                        actionable=item.get("actionable", True),
                        attributes=item.get("attributes", {})
                    )
                    elements.append(element)

            logger.debug(f"Parsed {len(elements)} elements from MiniCPM output")

        except Exception as e:
            logger.warning(f"Failed to parse MiniCPM output: {e}")

        return elements

    def unload(self) -> None:
        """Unload model from memory."""
        if not self.is_loaded:
            logger.debug("MiniCPM model not loaded, nothing to unload")
            return

        try:
            import torch
            import gc

            # Delete model and tokenizer
            del self.model
            del self.tokenizer

            self.model = None
            self.tokenizer = None
            self.device = None

            # Force garbage collection
            gc.collect()

            self.is_loaded = False
            logger.info("MiniCPM model unloaded successfully")

        except Exception as e:
            logger.exception("Failed to unload MiniCPM model")
            raise RuntimeError(f"MiniCPM unload failed: {e}") from e


__all__ = ["MiniCPMAdapter"]
