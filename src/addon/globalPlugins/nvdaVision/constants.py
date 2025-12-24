"""Constants and enums for NVDA Vision plugin.

This module defines all constants, enums, and default values used throughout
the NVDA Vision Screen Reader plugin.
"""

from enum import Enum, auto
from pathlib import Path

# Version
__version__ = "0.1.0"

# ========== Timing Constants ==========

# Maximum model inference time (real.md constraint 6)
MAX_INFERENCE_TIME = 15.0  # seconds

# Progress feedback delay (real.md constraint 6)
PROGRESS_FEEDBACK_DELAY = 5.0  # seconds

# Progress update interval
PROGRESS_UPDATE_INTERVAL = 3.0  # seconds

# Cache TTL
CACHE_TTL = 300  # seconds (5 minutes)

# Cleanup interval
CLEANUP_INTERVAL = 3600  # seconds (1 hour)


# ========== Recognition Constants ==========

# Minimum confidence threshold (real.md constraint 3)
MIN_CONFIDENCE_THRESHOLD = 0.7

# Low confidence threshold for "uncertain" annotation
LOW_CONFIDENCE_THRESHOLD = 0.7


# ========== Model Constants ==========

# Model names
MODEL_UITARS_7B = "uitars-7b"
MODEL_MINICPM_V_26 = "minicpm-v-2.6"
MODEL_DOUBAO_API = "doubao-vision-pro"

# Model memory requirements (GB)
UITARS_MIN_VRAM = 16.0  # GPU VRAM
MINICPM_MIN_RAM = 6.0   # System RAM

# Inference timeouts per model
MODEL_TIMEOUTS = {
    MODEL_UITARS_7B: 15.0,
    MODEL_MINICPM_V_26: 20.0,
    MODEL_DOUBAO_API: 10.0,
}


# ========== Path Constants ==========

# Default paths (Windows AppData)
DEFAULT_CONFIG_DIR = Path.home() / ".nvda_vision"
DEFAULT_MODEL_DIR = DEFAULT_CONFIG_DIR / "models"
DEFAULT_CACHE_DIR = DEFAULT_CONFIG_DIR / "cache"
DEFAULT_LOG_DIR = DEFAULT_CONFIG_DIR / "logs"


# ========== Cache Constants ==========

# Maximum cached results
MAX_CACHE_RESULTS = 1000

# Maximum cache size in MB
MAX_CACHE_SIZE_MB = 100


# ========== Keyboard Shortcuts ==========

# Default keyboard gestures
GESTURE_RECOGNIZE_SCREEN = "kb:NVDA+shift+v"
GESTURE_RECOGNIZE_AT_CURSOR = "kb:NVDA+shift+c"
GESTURE_NEXT_ELEMENT = "kb:NVDA+shift+n"
GESTURE_PREVIOUS_ELEMENT = "kb:NVDA+shift+p"
GESTURE_ACTIVATE_ELEMENT = "kb:NVDA+shift+enter"
GESTURE_CANCEL = "kb:escape"


# ========== UI Element Types ==========

# Interactive element types
INTERACTIVE_TYPES = {"button", "link", "textbox", "dropdown", "checkbox", "radio"}

# Display element types
DISPLAY_TYPES = {"text", "icon", "image", "label", "tooltip"}

# Container element types
CONTAINER_TYPES = {"dialog", "panel", "menu", "list", "table"}


# ========== Enums ==========

class ModelStatus(Enum):
    """Model loading/inference status."""
    NOT_LOADED = auto()
    LOADING = auto()
    LOADED = auto()
    LOAD_FAILED = auto()
    DEGRADED = auto()


class RecognitionStatus(Enum):
    """Recognition result status."""
    SUCCESS = auto()
    PARTIAL_SUCCESS = auto()  # Low confidence
    FAILURE = auto()
    TIMEOUT = auto()
    CACHE_HIT = auto()


class InferenceSource(Enum):
    """Source of inference result."""
    LOCAL_GPU = auto()
    LOCAL_CPU = auto()
    CLOUD_API = auto()
    CACHE = auto()


class ElementType(Enum):
    """UI element types (from cog.md)."""
    # Interactive
    BUTTON = "button"
    LINK = "link"
    TEXTBOX = "textbox"
    DROPDOWN = "dropdown"
    CHECKBOX = "checkbox"
    RADIO = "radio"

    # Display
    TEXT = "text"
    ICON = "icon"
    IMAGE = "image"
    LABEL = "label"
    TOOLTIP = "tooltip"

    # Container
    DIALOG = "dialog"
    PANEL = "panel"
    MENU = "menu"
    LIST = "list"
    TABLE = "table"


class DeviceType(Enum):
    """Device type for model execution."""
    CUDA = "cuda"
    CPU = "cpu"
    API = "api"


# ========== Screenshot Constants ==========

# Maximum screenshot dimension for processing
MAX_SCREENSHOT_DIMENSION = 1920  # pixels

# Screenshot quality for compression
SCREENSHOT_QUALITY = 85  # 1-100

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {".png", ".jpg", ".jpeg", ".bmp"}


# ========== API Constants ==========

# Doubao API endpoint
DOUBAO_API_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/visual"

# API request timeout
API_REQUEST_TIMEOUT = 30.0  # seconds

# Maximum retries for API calls
API_MAX_RETRIES = 3


# ========== Logging Constants ==========

# Log levels
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Default log level
DEFAULT_LOG_LEVEL = "INFO"

# Log file retention
LOG_RETENTION_DAYS = 7

# Log file rotation size
LOG_MAX_SIZE_MB = 10


# ========== Privacy Constants ==========

# Privacy mode (real.md constraint 1)
PRIVACY_LOCAL_ONLY = True

# Cloud API disabled by default
CLOUD_API_DEFAULT_ENABLED = False


# ========== Validation Constants ==========

# Minimum screenshot size
MIN_SCREENSHOT_WIDTH = 100
MIN_SCREENSHOT_HEIGHT = 100

# Maximum UI elements per recognition
MAX_UI_ELEMENTS = 1000

# Valid confidence range
CONFIDENCE_MIN = 0.0
CONFIDENCE_MAX = 1.0


# ========== Error Messages ==========

ERROR_NO_GPU = "GPU not available for model inference"
ERROR_INSUFFICIENT_VRAM = "Insufficient GPU VRAM for model"
ERROR_INSUFFICIENT_RAM = "Insufficient system RAM for model"
ERROR_MODEL_NOT_FOUND = "Model files not found at specified path"
ERROR_MODEL_LOAD_FAILED = "Failed to load model"
ERROR_INFERENCE_TIMEOUT = "Model inference exceeded timeout"
ERROR_INFERENCE_FAILED = "Model inference failed"
ERROR_SCREENSHOT_FAILED = "Failed to capture screenshot"
ERROR_CACHE_FAILED = "Cache operation failed"
ERROR_CONFIG_LOAD_FAILED = "Failed to load configuration"
ERROR_API_KEY_MISSING = "API key not configured"
ERROR_API_REQUEST_FAILED = "API request failed"


# ========== Success Messages ==========

MSG_RECOGNIZING = "Recognizing screen..."
MSG_RECOGNITION_COMPLETE = "Recognition complete"
MSG_CACHE_HIT = "Using cached result"
MSG_NO_ELEMENTS = "No UI elements detected"
MSG_ELEMENT_ACTIVATED = "Element activated"


# ========== WCAG Compliance ==========

# WCAG 2.1 AA compliance (real.md constraint 4)
WCAG_LEVEL = "AA"
WCAG_VERSION = "2.1"


# ========== License ==========

# Open source license (real.md constraint 7)
LICENSE = "Apache 2.0"


# ========== Feature Flags ==========

# Enable/disable features
FEATURE_AUTO_RECOGNIZE_ON_FOCUS = False
FEATURE_RECOGNIZE_ON_HOVER = False
FEATURE_CACHE_COMPRESSION = False
FEATURE_SCREENSHOT_SANITIZATION = True
