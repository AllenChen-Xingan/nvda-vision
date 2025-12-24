"""Recognition result data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import uuid

from .ui_element import UIElement
from ..constants import RecognitionStatus, InferenceSource


@dataclass
class RecognitionResult:
    """Represents a recognition result (from cog.md).

    Attributes:
        id: Unique identifier (UUID v4)
        screenshot_hash: SHA-256 hash of source screenshot
        elements: List of detected UI elements
        model_name: Name of model used for inference
        inference_time: Time taken for inference (seconds)
        status: Recognition status (success/partial/failure/timeout)
        source: Inference source (local_gpu/local_cpu/cloud_api/cache)
        created_at: Timestamp when result was created
        expires_at: Expiration timestamp (created_at + TTL)
        model_version: Optional model version string
    """

    id: str
    screenshot_hash: str
    elements: List[UIElement]
    model_name: str
    inference_time: float
    status: RecognitionStatus
    source: InferenceSource
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    model_version: Optional[str] = None

    def __post_init__(self):
        """Validate result data."""
        # Generate UUID if not provided
        if not self.id:
            self.id = str(uuid.uuid4())

        # Validate inference time
        if self.inference_time < 0:
            raise ValueError(f"Inference time cannot be negative: {self.inference_time}")

        # Compute expiration if not set
        if self.expires_at is None:
            from datetime import timedelta
            from ..constants import CACHE_TTL
            self.expires_at = self.created_at + timedelta(seconds=CACHE_TTL)

    @property
    def element_count(self) -> int:
        """Get number of detected elements."""
        return len(self.elements)

    @property
    def average_confidence(self) -> float:
        """Calculate average confidence across all elements."""
        if not self.elements:
            return 0.0
        return sum(e.confidence for e in self.elements) / len(self.elements)

    @property
    def actionable_elements(self) -> List[UIElement]:
        """Get only actionable (interactive) elements."""
        return [e for e in self.elements if e.actionable]

    @property
    def high_confidence_elements(self) -> List[UIElement]:
        """Get elements with confidence above threshold."""
        from ..constants import MIN_CONFIDENCE_THRESHOLD
        return [e for e in self.elements if e.confidence >= MIN_CONFIDENCE_THRESHOLD]

    @property
    def is_expired(self) -> bool:
        """Check if result has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() >= self.expires_at

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "screenshot_hash": self.screenshot_hash,
            "elements": [e.to_dict() for e in self.elements],
            "model_name": self.model_name,
            "model_version": self.model_version,
            "inference_time": self.inference_time,
            "status": self.status.name,
            "source": self.source.name,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "element_count": self.element_count,
            "average_confidence": self.average_confidence,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecognitionResult":
        """Create RecognitionResult from dictionary."""
        # Parse elements
        elements = [UIElement.from_dict(e) for e in data.get("elements", [])]

        # Parse timestamps
        created_at_str = data.get("created_at")
        created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now()

        expires_at_str = data.get("expires_at")
        expires_at = datetime.fromisoformat(expires_at_str) if expires_at_str else None

        # Parse enums
        status_str = data.get("status", "SUCCESS")
        status = RecognitionStatus[status_str] if hasattr(RecognitionStatus, status_str) else RecognitionStatus.SUCCESS

        source_str = data.get("source", "LOCAL_GPU")
        source = InferenceSource[source_str] if hasattr(InferenceSource, source_str) else InferenceSource.LOCAL_GPU

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            screenshot_hash=data["screenshot_hash"],
            elements=elements,
            model_name=data["model_name"],
            inference_time=data.get("inference_time", 0.0),
            status=status,
            source=source,
            created_at=created_at,
            expires_at=expires_at,
            model_version=data.get("model_version"),
        )
