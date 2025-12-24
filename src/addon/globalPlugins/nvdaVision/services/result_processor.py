"""Result processor for post-processing recognition results.

This module handles filtering, sorting, and enhancing recognition results.
"""

from typing import List
from datetime import datetime
import uuid

from ..schemas.ui_element import UIElement
from ..schemas.recognition_result import RecognitionResult
from ..schemas.screenshot import Screenshot
from ..constants import RecognitionStatus, InferenceSource
from ..infrastructure.logger import logger


class ResultProcessor:
    """Process and enhance recognition results.

    Responsibilities:
    - Filter low-confidence elements
    - Sort elements by position
    - Add uncertainty annotations
    - Generate result summary
    """

    def __init__(self, confidence_threshold: float = 0.7):
        """Initialize result processor.

        Args:
            confidence_threshold: Minimum confidence to include element (default: 0.7)
                                Elements below this are marked as "uncertain"
        """
        self.confidence_threshold = confidence_threshold
        logger.info(f"ResultProcessor initialized with threshold={confidence_threshold}")

    def process(
        self,
        elements: List[UIElement],
        screenshot: Screenshot,
        model_name: str,
        inference_time: float,
        source: InferenceSource
    ) -> RecognitionResult:
        """Process recognition results into final form.

        Args:
            elements: Raw UI elements from model
            screenshot: Source screenshot
            model_name: Name of model used
            inference_time: Time taken for inference
            source: Source of inference (GPU/CPU/Cloud)

        Returns:
            Processed RecognitionResult
        """
        logger.debug(f"Processing {len(elements)} raw elements")

        # Filter invalid elements
        valid_elements = self._filter_invalid(elements)

        # Add uncertainty annotations
        annotated_elements = self._annotate_uncertainty(valid_elements)

        # Sort elements by position (top-to-bottom, left-to-right)
        sorted_elements = self._sort_by_position(annotated_elements)

        # Generate unique IDs for elements without IDs
        id_elements = self._assign_ids(sorted_elements)

        # Determine status
        status = self._determine_status(id_elements)

        # Create result
        result = RecognitionResult(
            id=str(uuid.uuid4()),
            screenshot_hash=screenshot.hash,
            elements=id_elements,
            model_name=model_name,
            inference_time=inference_time,
            status=status,
            source=source,
            created_at=datetime.now()
        )

        logger.info(
            f"Processed result: {len(id_elements)} elements, "
            f"status={status.value}, source={source.value}"
        )

        return result

    def _filter_invalid(self, elements: List[UIElement]) -> List[UIElement]:
        """Filter out invalid elements.

        Args:
            elements: Raw elements

        Returns:
            Valid elements only
        """
        valid = []
        removed = 0

        for element in elements:
            # Check for valid bbox
            if not element.bbox or len(element.bbox) != 4:
                removed += 1
                continue

            x1, y1, x2, y2 = element.bbox
            if x1 >= x2 or y1 >= y2:
                removed += 1
                continue

            # Check confidence
            if element.confidence < 0.0 or element.confidence > 1.0:
                removed += 1
                continue

            valid.append(element)

        if removed > 0:
            logger.debug(f"Filtered out {removed} invalid elements")

        return valid

    def _annotate_uncertainty(self, elements: List[UIElement]) -> List[UIElement]:
        """Add uncertainty annotations to low-confidence elements.

        Args:
            elements: Elements to annotate

        Returns:
            Elements with uncertainty annotations
        """
        for element in elements:
            if element.confidence < self.confidence_threshold:
                # Mark as uncertain
                if "annotations" not in element.attributes:
                    element.attributes["annotations"] = []

                element.attributes["annotations"].append("uncertain")
                logger.debug(
                    f"Marked element as uncertain: {element.element_type} "
                    f"'{element.text}' (confidence={element.confidence:.2f})"
                )

        return elements

    def _sort_by_position(self, elements: List[UIElement]) -> List[UIElement]:
        """Sort elements by visual position (reading order).

        Sorts top-to-bottom, left-to-right.

        Args:
            elements: Elements to sort

        Returns:
            Sorted elements
        """
        def sort_key(element: UIElement):
            # Primary: Y position (top)
            # Secondary: X position (left)
            x1, y1, x2, y2 = element.bbox
            return (y1, x1)

        sorted_elements = sorted(elements, key=sort_key)
        logger.debug(f"Sorted {len(sorted_elements)} elements by position")

        return sorted_elements

    def _assign_ids(self, elements: List[UIElement]) -> List[UIElement]:
        """Assign unique IDs to elements without IDs.

        Args:
            elements: Elements possibly missing IDs

        Returns:
            Elements with IDs assigned
        """
        for i, element in enumerate(elements):
            if not element.id or element.id == "":
                element.id = f"element_{i+1:03d}"

        return elements

    def _determine_status(self, elements: List[UIElement]) -> RecognitionStatus:
        """Determine recognition result status.

        Args:
            elements: Processed elements

        Returns:
            Recognition status
        """
        if not elements:
            return RecognitionStatus.FAILURE

        # Check if we have any actionable elements
        actionable_count = sum(1 for e in elements if e.actionable)

        if actionable_count == 0:
            return RecognitionStatus.PARTIAL_SUCCESS

        # Check overall confidence
        avg_confidence = sum(e.confidence for e in elements) / len(elements)

        if avg_confidence < self.confidence_threshold:
            return RecognitionStatus.PARTIAL_SUCCESS

        return RecognitionStatus.SUCCESS

    def generate_speech_text(self, element: UIElement) -> str:
        """Generate speech-friendly text for UI element.

        Args:
            element: UI element

        Returns:
            Text suitable for screen reader speech
        """
        parts = []

        # Element type
        parts.append(element.element_type)

        # Element text
        if element.text:
            parts.append(f"'{element.text}'")

        # Position hint
        x1, y1, x2, y2 = element.bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        parts.append(f"at position {center_x:.0f}, {center_y:.0f}")

        # Uncertainty annotation
        if "uncertain" in element.attributes.get("annotations", []):
            parts.append("(uncertain)")

        # Confidence (for debugging mode)
        if element.confidence < self.confidence_threshold:
            parts.append(f"confidence {element.confidence:.0%}")

        return " ".join(parts)

    def generate_result_summary(self, result: RecognitionResult) -> str:
        """Generate human-readable result summary.

        Args:
            result: Recognition result

        Returns:
            Summary text
        """
        parts = []

        # Element count
        element_count = len(result.elements)
        parts.append(f"Found {element_count} UI elements")

        # Actionable elements
        actionable_count = sum(1 for e in result.elements if e.actionable)
        if actionable_count > 0:
            parts.append(f"({actionable_count} actionable)")

        # Model info
        parts.append(f"using {result.model_name}")

        # Performance
        parts.append(f"in {result.inference_time:.1f} seconds")

        # Source
        source_text = {
            InferenceSource.LOCAL_GPU: "on GPU",
            InferenceSource.LOCAL_CPU: "on CPU",
            InferenceSource.CLOUD_API: "via cloud API",
            InferenceSource.CACHE: "from cache"
        }.get(result.source, "")

        if source_text:
            parts.append(source_text)

        return ". ".join(parts) + "."


__all__ = ["ResultProcessor"]
