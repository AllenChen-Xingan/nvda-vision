"""Data schemas for NVDA Vision plugin.

This module defines the core data models using dataclasses.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from PIL import Image


@dataclass
class UIElement:
    """Represents a UI element detected in a screenshot (from cog.md).

    Attributes:
        element_type: Type of element (button, textbox, link, etc.)
        text: Text content displayed in the element
        bbox: Bounding box [x1, y1, x2, y2] in screen coordinates
        confidence: Confidence score 0.0-1.0 from recognition model
        app_name: Name of the application containing this element
        parent_id: ID of parent container element (optional)
        actionable: Whether element can be interacted with
        created_at: Timestamp when element was detected
    """

    element_type: str
    text: str
    bbox: List[int]  # [x1, y1, x2, y2]
    confidence: float
    app_name: Optional[str] = None
    parent_id: Optional[str] = None
    actionable: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate element data after initialization."""
        # Validate confidence range
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0-1, got {self.confidence}")

        # Validate bounding box
        if len(self.bbox) != 4:
            raise ValueError(f"Bounding box must have 4 coordinates, got {len(self.bbox)}")

        x1, y1, x2, y2 = self.bbox
        if x2 <= x1 or y2 <= y1:
            raise ValueError(f"Invalid bounding box: {self.bbox}")

    @property
    def center_x(self) -> int:
        """Get center X coordinate."""
        return (self.bbox[0] + self.bbox[2]) // 2

    @property
    def center_y(self) -> int:
        """Get center Y coordinate."""
        return (self.bbox[1] + self.bbox[3]) // 2

    @property
    def width(self) -> int:
        """Get element width."""
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> int:
        """Get element height."""
        return self.bbox[3] - self.bbox[1]

    @property
    def is_uncertain(self) -> bool:
        """Check if confidence is below threshold (real.md constraint 3)."""
        from ..constants import LOW_CONFIDENCE_THRESHOLD
        return self.confidence < LOW_CONFIDENCE_THRESHOLD

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.element_type,
            "text": self.text,
            "bbox": self.bbox,
            "confidence": self.confidence,
            "app_name": self.app_name,
            "parent_id": self.parent_id,
            "actionable": self.actionable,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UIElement":
        """Create UIElement from dictionary."""
        created_at_str = data.get("created_at")
        created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now()

        return cls(
            element_type=data["type"],
            text=data["text"],
            bbox=data["bbox"],
            confidence=data["confidence"],
            app_name=data.get("app_name"),
            parent_id=data.get("parent_id"),
            actionable=data.get("actionable", True),
            created_at=created_at,
        )
