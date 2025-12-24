"""Doubao (豆包) Cloud API adapter.

This adapter uses Doubao cloud vision API for UI element recognition.
Only used as fallback when local models fail and user has given consent.
"""

from pathlib import Path
from typing import List, Optional
import time
import base64
import io

from .base_adapter import VisionModelAdapter
from ..schemas.screenshot import Screenshot
from ..schemas.ui_element import UIElement
from ..infrastructure.logger import logger


class DoubaoAPIAdapter(VisionModelAdapter):
    """Adapter for Doubao cloud vision API.

    Requirements:
    - Internet connection
    - Valid API key
    - User consent for cloud processing (privacy constraint)
    """

    def __init__(
        self,
        api_key: str,
        api_endpoint: str = "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        config: dict = None
    ):
        """Initialize Doubao API adapter.

        Args:
            api_key: Doubao API key (encrypted)
            api_endpoint: API endpoint URL
            config: Optional configuration dict
        """
        super().__init__(model_path=None)  # No local model path for cloud API
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.config = config or {}
        self._request_count = 0

    @property
    def name(self) -> str:
        return "Doubao Cloud API"

    @property
    def requires_gpu(self) -> bool:
        return False

    @property
    def min_vram_gb(self) -> float:
        return 0.0

    @property
    def min_ram_gb(self) -> float:
        return 0.5  # Minimal memory for API client

    def load(self) -> None:
        """Initialize API client (no model loading needed).

        Raises:
            RuntimeError: If API key is invalid
        """
        if self.is_loaded:
            logger.warning("Doubao API already initialized")
            return

        if not self.api_key or self.api_key == "":
            raise RuntimeError("Doubao API key not configured")

        # Validate API key format (basic check)
        if len(self.api_key) < 20:
            raise RuntimeError("Doubao API key appears invalid (too short)")

        self.is_loaded = True
        logger.info("Doubao API client initialized")

    def infer(
        self,
        screenshot: Screenshot,
        timeout: float = 15.0
    ) -> List[UIElement]:
        """Run inference via Doubao cloud API.

        Args:
            screenshot: Screenshot to analyze
            timeout: Maximum API request time

        Returns:
            List of detected UI elements

        Raises:
            RuntimeError: If API request fails
            TimeoutError: If request exceeds timeout
        """
        if not self.is_loaded:
            raise RuntimeError("Doubao API not initialized")

        start_time = time.time()
        self._request_count += 1

        try:
            import requests

            logger.debug(
                f"Starting Doubao API request for {screenshot.hash[:8]} "
                f"({screenshot.width}x{screenshot.height})"
            )

            # Prepare image (downscale for API)
            image_base64 = self._prepare_image(screenshot)

            # Prepare API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "model": "doubao-vision-pro",  # Doubao vision model
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "You are a UI accessibility assistant for visually impaired users. "
                                    "Analyze this screenshot and identify ALL UI elements with DETAILED descriptions.\n\n"

                                    "CRITICAL REQUIREMENTS:\n"
                                    "1. For EVERY element, provide a meaningful description\n"
                                    "   - Text buttons: use the visible text\n"
                                    "   - Icon buttons: DESCRIBE what the icon represents\n"
                                    "   - Even if there's no text label, YOU MUST infer the purpose\n\n"

                                    "2. Common icon patterns:\n"
                                    "   - Microphone/mic → \"microphone\" or \"mute\"\n"
                                    "   - Camera → \"camera\" or \"video\"\n"
                                    "   - Monitor/screen → \"share screen\"\n"
                                    "   - Speech bubble → \"chat\" or \"messages\"\n"
                                    "   - People icon → \"participants\" or \"members\"\n"
                                    "   - Gear icon → \"settings\"\n"
                                    "   - Three dots → \"more options\" or \"menu\"\n"
                                    "   - Plus (+) → \"add\" or \"new\"\n"
                                    "   - X icon → \"close\" or \"exit\"\n\n"

                                    "OUTPUT FORMAT (JSON array only):\n"
                                    "[\n"
                                    "  {\n"
                                    "    \"type\": \"button|icon_button|textbox|link|text|label|icon\",\n"
                                    "    \"text\": \"descriptive text or icon meaning\",\n"
                                    "    \"bbox\": [x1, y1, x2, y2],\n"
                                    "    \"confidence\": 0.0-1.0,\n"
                                    "    \"actionable\": true|false\n"
                                    "  }\n"
                                    "]\n\n"

                                    "EXAMPLES:\n"
                                    "[{\"type\":\"icon_button\",\"text\":\"microphone mute\",\"bbox\":[100,500,140,540],\"confidence\":0.92,\"actionable\":true},"
                                    "{\"type\":\"icon_button\",\"text\":\"camera video\",\"bbox\":[145,500,185,540],\"confidence\":0.94,\"actionable\":true},"
                                    "{\"type\":\"icon_button\",\"text\":\"share screen\",\"bbox\":[190,500,230,540],\"confidence\":0.90,\"actionable\":true}]\n\n"

                                    "CRITICAL: NEVER return empty \"text\" field. Always describe what you see. "
                                    "Return ONLY the JSON array, no explanations."
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.1,  # Low temperature for stable icon recognition
                "max_tokens": 2048
            }

            # Make API request with timeout
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=payload,
                timeout=timeout
            )

            # Check timeout
            if time.time() - start_time > timeout:
                raise TimeoutError(f"API request exceeded timeout: {timeout}s")

            # Check response
            if response.status_code != 200:
                raise RuntimeError(
                    f"API request failed: {response.status_code} - {response.text}"
                )

            # Parse response
            result = response.json()
            output_text = result["choices"][0]["message"]["content"]

            # Parse to UIElements
            elements = self._parse_api_response(output_text, screenshot)

            elapsed = time.time() - start_time
            logger.info(
                f"Doubao API request complete: {len(elements)} elements "
                f"in {elapsed:.2f}s (request #{self._request_count})"
            )

            return elements

        except TimeoutError:
            elapsed = time.time() - start_time
            logger.warning(f"Doubao API request timed out after {elapsed:.2f}s")
            raise

        except requests.exceptions.RequestException as e:
            elapsed = time.time() - start_time
            logger.error(f"Doubao API network error after {elapsed:.2f}s: {e}")
            raise RuntimeError(f"Doubao API request failed: {e}") from e

        except Exception as e:
            elapsed = time.time() - start_time
            logger.exception(f"Doubao API request failed after {elapsed:.2f}s")
            raise RuntimeError(f"Doubao API error: {e}") from e

    def _prepare_image(self, screenshot: Screenshot) -> str:
        """Prepare image for API upload (downscale and encode).

        Args:
            screenshot: Screenshot to prepare

        Returns:
            Base64-encoded JPEG image
        """
        from PIL import Image

        # Downscale for API (max 1280px)
        image = screenshot.image_data
        max_size = 1280

        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.debug(f"Downscaled image to {new_size} for API")

        # Convert to JPEG and encode
        buffer = io.BytesIO()
        image.convert("RGB").save(buffer, format="JPEG", quality=85)
        image_bytes = buffer.getvalue()

        # Encode to base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        return image_base64

    def _parse_api_response(
        self,
        response_text: str,
        screenshot: Screenshot
    ) -> List[UIElement]:
        """Parse API response into UIElement objects."""
        elements = []

        try:
            import re
            import json

            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())

                for item in parsed_data:
                    element = UIElement(
                        id=item.get("id", ""),
                        element_type=item.get("type", "unknown"),
                        text=item.get("text", ""),
                        bbox=item.get("bbox", [0, 0, 0, 0]),
                        confidence=item.get("confidence", 0.7),
                        actionable=item.get("actionable", True),
                        attributes=item.get("attributes", {})
                    )
                    elements.append(element)

            logger.debug(f"Parsed {len(elements)} elements from API response")

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse API JSON response: {e}")
        except Exception as e:
            logger.warning(f"Failed to parse API response: {e}")

        return elements

    def unload(self) -> None:
        """Cleanup API client (nothing to unload)."""
        self.is_loaded = False
        logger.info(
            f"Doubao API client closed (total requests: {self._request_count})"
        )

    def get_statistics(self) -> dict:
        """Get API usage statistics."""
        return {
            "total_requests": self._request_count,
            "api_endpoint": self.api_endpoint,
            "model": "doubao-vision-pro"
        }


__all__ = ["DoubaoAPIAdapter"]
