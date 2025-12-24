"""Screenshot data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import hashlib
from PIL import Image


@dataclass
class Screenshot:
    """Represents a screenshot (from cog.md).

    Attributes:
        hash: SHA-256 hash of image data for deduplication
        image_data: PIL Image object containing the screenshot
        width: Image width in pixels
        height: Image height in pixels
        window_title: Title of the window that was captured
        app_name: Name of the application
        captured_at: Timestamp when screenshot was taken
        file_size: Approximate size in KB (for statistics)
    """

    hash: str
    image_data: Image.Image
    width: int
    height: int
    window_title: Optional[str] = None
    app_name: Optional[str] = None
    captured_at: datetime = field(default_factory=datetime.now)
    file_size: Optional[int] = None

    def __post_init__(self):
        """Validate screenshot data."""
        # Validate dimensions
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Invalid dimensions: {self.width}x{self.height}")

        # Validate hash format (SHA-256 = 64 hex characters)
        if not self.hash or len(self.hash) != 64:
            raise ValueError(f"Invalid SHA-256 hash: {self.hash}")

    @classmethod
    def from_image(
        cls,
        image: Image.Image,
        window_title: Optional[str] = None,
        app_name: Optional[str] = None
    ) -> "Screenshot":
        """Create Screenshot from PIL Image.

        Args:
            image: PIL Image object
            window_title: Optional window title
            app_name: Optional application name

        Returns:
            Screenshot instance with computed hash
        """
        # Compute hash of image data
        img_hash = cls.compute_hash(image)

        # Get dimensions
        width, height = image.size

        # Estimate file size (approximate)
        import io
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        file_size_kb = len(buffer.getvalue()) // 1024

        return cls(
            hash=img_hash,
            image_data=image,
            width=width,
            height=height,
            window_title=window_title,
            app_name=app_name,
            file_size=file_size_kb,
        )

    @staticmethod
    def compute_hash(image: Image.Image) -> str:
        """Compute SHA-256 hash of image data.

        Args:
            image: PIL Image object

        Returns:
            64-character hex string (SHA-256 hash)
        """
        import io
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        return hashlib.sha256(image_bytes).hexdigest()

    def to_dict(self) -> dict:
        """Convert to dictionary (without image data for privacy).

        Returns:
            Dictionary with metadata only (no raw pixels)
        """
        return {
            "hash": self.hash,
            "width": self.width,
            "height": self.height,
            "window_title": self.window_title,
            "app_name": self.app_name,
            "captured_at": self.captured_at.isoformat(),
            "file_size_kb": self.file_size,
        }
