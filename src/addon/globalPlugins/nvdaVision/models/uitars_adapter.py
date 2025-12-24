"""UI-TARS 7B vision model adapter.

This adapter wraps the UI-TARS 7B model for UI element recognition.
Requires GPU with 16GB+ VRAM.
"""

from pathlib import Path
from typing import List
import time

from .base_adapter import VisionModelAdapter
from ..schemas.screenshot import Screenshot
from ..schemas.ui_element import UIElement
from ..infrastructure.logger import logger


class UITarsAdapter(VisionModelAdapter):
    """Adapter for UI-TARS 7B vision model.

    Requirements:
    - GPU with 16GB+ VRAM
    - CUDA 11.8+
    - PyTorch 2.0+
    """

    def __init__(self, model_path: Path, config: dict = None):
        """Initialize UI-TARS adapter.

        Args:
            model_path: Path to UI-TARS model files
            config: Optional configuration dict
        """
        super().__init__(model_path)
        self.config = config or {}
        self.model = None
        self.tokenizer = None
        self.device = None

    @property
    def name(self) -> str:
        return "UI-TARS 7B"

    @property
    def requires_gpu(self) -> bool:
        return True

    @property
    def min_vram_gb(self) -> float:
        return 16.0

    @property
    def min_ram_gb(self) -> float:
        return 4.0

    def load(self) -> None:
        """Load UI-TARS model into GPU memory.

        Raises:
            RuntimeError: If GPU not available or insufficient VRAM
        """
        if self.is_loaded:
            logger.warning("UI-TARS model already loaded")
            return

        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            # Check GPU availability
            if not torch.cuda.is_available():
                raise RuntimeError("GPU not available but required for UI-TARS")

            # Check VRAM
            device_props = torch.cuda.get_device_properties(0)
            vram_gb = device_props.total_memory / 1e9

            if vram_gb < self.min_vram_gb:
                raise RuntimeError(
                    f"Insufficient VRAM: {vram_gb:.1f}GB available, "
                    f"{self.min_vram_gb}GB required"
                )

            logger.info(
                f"Loading UI-TARS model from {self.model_path} "
                f"(GPU: {device_props.name}, VRAM: {vram_gb:.1f}GB)"
            )

            # Load model
            self.device = torch.device("cuda:0")
            self.model = AutoModel.from_pretrained(
                str(self.model_path),
                torch_dtype=torch.float16,
                trust_remote_code=True
            ).to(self.device)
            self.model.eval()

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                trust_remote_code=True
            )

            self.is_loaded = True
            logger.info("UI-TARS model loaded successfully")

        except Exception as e:
            logger.exception("Failed to load UI-TARS model")
            self.is_loaded = False
            raise RuntimeError(f"UI-TARS model loading failed: {e}") from e

    def infer(
        self,
        screenshot: Screenshot,
        timeout: float = 15.0
    ) -> List[UIElement]:
        """Run UI-TARS inference on screenshot.

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
            raise RuntimeError("UI-TARS model not loaded")

        start_time = time.time()

        try:
            import torch

            logger.debug(
                f"Starting UI-TARS inference for {screenshot.hash[:8]} "
                f"({screenshot.width}x{screenshot.height})"
            )

            # Prepare image
            image_tensor = self._prepare_image(screenshot)

            # Prepare prompt for UI element detection
            prompt = (
                "Analyze this UI screenshot and identify all interactive elements. "
                "For each element, provide: type, text, bounding box coordinates, and confidence."
            )

            # Tokenize prompt
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True
            ).to(self.device)

            # Run inference with timeout monitoring
            with torch.no_grad():
                # Check timeout before inference
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Inference exceeded timeout: {timeout}s")

                # Generate predictions
                outputs = self.model.generate(
                    **inputs,
                    images=image_tensor,
                    max_new_tokens=2048,
                    temperature=0.7,
                    do_sample=False
                )

                # Check timeout after inference
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Inference exceeded timeout: {timeout}s")

            # Decode output
            output_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Parse output to UIElement list
            elements = self._parse_model_output(output_text, screenshot)

            elapsed = time.time() - start_time
            logger.info(
                f"UI-TARS inference complete: {len(elements)} elements "
                f"in {elapsed:.2f}s"
            )

            return elements

        except TimeoutError:
            elapsed = time.time() - start_time
            logger.warning(f"UI-TARS inference timed out after {elapsed:.2f}s")
            raise

        except Exception as e:
            elapsed = time.time() - start_time
            logger.exception(f"UI-TARS inference failed after {elapsed:.2f}s")
            raise RuntimeError(f"UI-TARS inference failed: {e}") from e

    def _prepare_image(self, screenshot: Screenshot):
        """Prepare image tensor for model input.

        Args:
            screenshot: Screenshot object

        Returns:
            Image tensor ready for model
        """
        import torch
        from torchvision import transforms

        # Convert PIL Image to tensor
        transform = transforms.Compose([
            transforms.Resize((336, 336)),  # UI-TARS input size
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.48145466, 0.4578275, 0.40821073],
                std=[0.26862954, 0.26130258, 0.27577711]
            )
        ])

        image_tensor = transform(screenshot.image_data).unsqueeze(0).to(self.device)
        return image_tensor

    def _parse_model_output(
        self,
        output_text: str,
        screenshot: Screenshot
    ) -> List[UIElement]:
        """Parse model output text into UIElement objects.

        Args:
            output_text: Raw model output text
            screenshot: Source screenshot

        Returns:
            List of UIElement objects
        """
        elements = []

        try:
            # Parse model output (format depends on UI-TARS output structure)
            # This is a simplified parser - actual implementation depends on model format
            import re
            import json

            # Try to extract JSON structure if present
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

            logger.debug(f"Parsed {len(elements)} elements from model output")

        except Exception as e:
            logger.warning(f"Failed to parse model output: {e}")
            # Return empty list on parse failure

        return elements

    def unload(self) -> None:
        """Unload model from GPU memory."""
        if not self.is_loaded:
            logger.debug("UI-TARS model not loaded, nothing to unload")
            return

        try:
            import torch

            # Delete model and tokenizer
            del self.model
            del self.tokenizer

            self.model = None
            self.tokenizer = None
            self.device = None

            # Clear CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            self.is_loaded = False
            logger.info("UI-TARS model unloaded and CUDA cache cleared")

        except Exception as e:
            logger.exception("Failed to unload UI-TARS model")
            raise RuntimeError(f"UI-TARS unload failed: {e}") from e


__all__ = ["UITarsAdapter"]
