# NVDA Vision Screen Reader - Coding Standards Specification

**Document Version**: v1.0.0
**Created**: 2025-12-24
**Dependencies**: `.42cog/real/real.md`, `.42cog/cog/cog.md`, `spec/dev/sys.spec.md`
**Skill**: dev-coding

---

## Table of Contents

1. [Overview](#1-overview)
2. [File Organization](#2-file-organization)
3. [Python Coding Standards](#3-python-coding-standards)
4. [NVDA Plugin Patterns](#4-nvda-plugin-patterns)
5. [Vision Model Integration](#5-vision-model-integration)
6. [Security Coding Practices](#6-security-coding-practices)
7. [Error Handling and Exception Isolation](#7-error-handling-and-exception-isolation)
8. [Threading Patterns](#8-threading-patterns)
9. [Configuration Management](#9-configuration-management)
10. [Logging Standards](#10-logging-standards)
11. [Testing Patterns](#11-testing-patterns)
12. [Code Review Checklist](#12-code-review-checklist)

---

## 1. Overview

### 1.1 Purpose

This document defines coding standards for the NVDA Vision Screen Reader plugin, ensuring:
- **Privacy**: Screenshots processed locally first, cloud API only as fallback
- **Security**: API keys encrypted with DPAPI, no sensitive data in logs
- **Transparency**: All recognition results include confidence scores
- **Stability**: Plugin failures must not crash NVDA core
- **Accessibility**: All features keyboard-accessible, WCAG 2.1 AA compliant
- **Performance**: <5s feedback, >15s auto-degradation
- **Maintainability**: Clean architecture, testable components

### 1.2 Scope

This document covers:
- Python 3.11 best practices for NVDA plugin development
- NVDA-specific patterns (GlobalPlugin, scriptHandler, etc.)
- PyTorch model integration (UI-TARS, MiniCPM-V)
- Windows API usage (pywin32, DPAPI)
- Security, threading, and error handling

### 1.3 Key Principles

1. **Safety First**: Never crash NVDA. Catch all exceptions in plugin code.
2. **Privacy by Default**: Local processing first, explicit user consent for cloud.
3. **Fail Gracefully**: Degrade to backup models/methods when primary fails.
4. **Be Transparent**: Always report confidence scores, processing source (local/cloud).
5. **Respect Users**: Provide progress feedback, allow cancellation, honor timeouts.

---

## 2. File Organization

### 2.1 Directory Structure

```
addon/globalPlugins/nvdaVision/
├── __init__.py                    # GlobalPlugin entry point
├── config.py                      # Configuration management
├── constants.py                   # Constants and enums
│
├── core/                          # Core business logic
│   ├── __init__.py
│   ├── recognition_controller.py  # Recognition flow orchestration
│   ├── event_coordinator.py       # NVDA event handling
│   └── interaction_manager.py     # Mouse/keyboard automation
│
├── services/                      # Domain services
│   ├── __init__.py
│   ├── screenshot_service.py      # Screen capture
│   ├── vision_engine.py           # Model inference orchestration
│   ├── result_processor.py        # Result parsing and formatting
│   └── cache_manager.py           # Result caching
│
├── models/                        # Vision model adapters
│   ├── __init__.py
│   ├── base_adapter.py            # Abstract base adapter
│   ├── model_detector.py          # Hardware detection and model selection
│   ├── uitars_adapter.py          # UI-TARS 7B adapter (GPU)
│   ├── minicpm_adapter.py         # MiniCPM-V 2.6 adapter (CPU)
│   └── doubao_adapter.py          # Doubao cloud API adapter
│
├── infrastructure/                # External dependencies
│   ├── __init__.py
│   ├── win32_capture.py           # Windows screenshot API (pywin32)
│   ├── model_loader.py            # PyTorch model loading
│   ├── config_loader.py           # YAML + encryption
│   ├── logger.py                  # Loguru configuration
│   └── cloud_client.py            # HTTP client for cloud APIs
│
├── security/                      # Security utilities
│   ├── __init__.py
│   ├── encryption.py              # DPAPI encryption for API keys
│   └── screenshot_sanitizer.py   # Privacy-preserving screenshot handling
│
├── ui/                            # User interface (optional)
│   ├── __init__.py
│   ├── settings_dialog.py         # Configuration GUI (wxPython)
│   └── progress_dialog.py         # Progress feedback dialog
│
├── utils/                         # Utilities
│   ├── __init__.py
│   ├── threading_utils.py         # Thread management helpers
│   ├── timeout_utils.py           # Timeout decorators
│   └── speech_utils.py            # NVDA speech helpers
│
└── schemas/                       # Data models
    ├── __init__.py
    ├── ui_element.py              # UIElement dataclass
    ├── recognition_result.py      # RecognitionResult dataclass
    └── screenshot.py              # Screenshot dataclass

tests/                             # Test suite (outside addon)
├── unit/
│   ├── test_vision_engine.py
│   ├── test_cache_manager.py
│   └── ...
├── integration/
│   ├── test_recognition_flow.py
│   └── ...
└── fixtures/
    ├── screenshots/
    └── models/
```

### 2.2 File Naming Conventions

```python
# ✅ GOOD: Snake case for modules
screenshot_service.py
recognition_controller.py
uitars_adapter.py

# ❌ BAD: Other cases
ScreenshotService.py
recognitionController.py
UITarsAdapter.py

# ✅ GOOD: Test files mirror source structure
tests/unit/services/test_screenshot_service.py
tests/unit/models/test_uitars_adapter.py

# ❌ BAD: Generic test names
tests/test_stuff.py
tests/test1.py
```

### 2.3 Import Organization

```python
"""Module docstring explaining purpose."""

# Standard library imports
import hashlib
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any

# Third-party imports
import torch
import numpy as np
from loguru import logger
from pydantic import BaseModel, Field

# NVDA imports
import api
import globalPluginHandler
import speech
import ui
from scriptHandler import script

# Local imports (relative)
from ..schemas.ui_element import UIElement
from ..schemas.recognition_result import RecognitionResult
from ..utils.timeout_utils import with_timeout
from ..infrastructure.logger import setup_logger
```

**Order**: stdlib → third-party → NVDA → local (alphabetical within each group)

---

## 3. Python Coding Standards

### 3.1 PEP 8 Compliance

Follow [PEP 8](https://peps.python.org/pep-0008/) with these specifics:

```python
# Line length: 88 characters (Black formatter default)
# Indentation: 4 spaces (never tabs)
# Quotes: Double quotes for strings, single for short literals

# ✅ GOOD
def recognize_screen(
    screenshot: Screenshot,
    model_name: str = "uitars-7b",
    timeout: float = 15.0,
) -> RecognitionResult:
    """Recognize UI elements in a screenshot."""
    pass

# ❌ BAD
def recognize_screen(screenshot, model_name="uitars-7b", timeout=15.0):  # No types
    pass  # No docstring
```

### 3.2 Type Hints

**Mandatory** for all public functions, methods, and class attributes.

```python
from typing import Optional, List, Dict, Any, Union, Protocol
from pathlib import Path

# ✅ GOOD: Full type annotations
def load_model(
    model_path: Path,
    device: str = "cuda",
    cache_dir: Optional[Path] = None,
) -> torch.nn.Module:
    """Load a PyTorch model from disk.

    Args:
        model_path: Path to model checkpoint file.
        device: Device to load model on ("cuda" or "cpu").
        cache_dir: Optional cache directory for downloaded models.

    Returns:
        Loaded PyTorch model ready for inference.

    Raises:
        FileNotFoundError: If model_path does not exist.
        RuntimeError: If model loading fails.
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    try:
        model = torch.load(model_path, map_location=device)
        return model
    except Exception as e:
        raise RuntimeError(f"Failed to load model: {e}") from e


# ✅ GOOD: Dataclasses with types
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UIElement:
    """Represents a UI element detected in a screenshot."""

    element_type: str  # "button" | "textbox" | "link" | ...
    text: str
    bbox: List[int]  # [x1, y1, x2, y2]
    confidence: float  # 0.0 - 1.0
    app_name: Optional[str] = None
    parent_id: Optional[str] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0-1, got {self.confidence}")


# ✅ GOOD: Protocol for abstract interfaces
from typing import Protocol

class VisionModelAdapter(Protocol):
    """Protocol for vision model adapters."""

    def load(self, model_path: Path) -> None:
        """Load the model into memory."""
        ...

    def infer(self, screenshot: Screenshot) -> List[UIElement]:
        """Run inference on a screenshot."""
        ...

    def unload(self) -> None:
        """Unload the model from memory."""
        ...


# ❌ BAD: No types
def load_model(model_path, device="cuda"):
    return torch.load(model_path)
```

### 3.3 Docstrings

Use **Google-style** docstrings for all public modules, classes, functions.

```python
def recognize_with_cache(
    screenshot: Screenshot,
    cache_manager: CacheManager,
    vision_engine: VisionEngine,
    ttl: int = 300,
) -> RecognitionResult:
    """Recognize UI elements with caching support.

    Checks cache first using screenshot hash. If cache miss or expired,
    performs inference with vision model and stores result in cache.

    Args:
        screenshot: Screenshot object containing image data and metadata.
        cache_manager: Cache manager instance for storing results.
        vision_engine: Vision engine for running inference.
        ttl: Cache time-to-live in seconds (default: 300).

    Returns:
        RecognitionResult containing detected UI elements, confidence scores,
        inference time, and model name.

    Raises:
        RuntimeError: If all models fail (local GPU, CPU, cloud API).
        TimeoutError: If inference exceeds 15 seconds.

    Example:
        >>> screenshot = Screenshot(image=img, width=1920, height=1080)
        >>> result = recognize_with_cache(screenshot, cache, engine)
        >>> print(f"Found {len(result.elements)} elements")
        Found 23 elements

    Notes:
        - Cache key is SHA-256 hash of screenshot image data
        - Confidence < 0.7 triggers "uncertain" annotation
        - Cloud API only called if local models fail (privacy constraint)
    """
    # Implementation...
```

### 3.4 Constants and Enums

```python
# constants.py

from enum import Enum, auto
from pathlib import Path

# ✅ GOOD: Uppercase constants
MAX_INFERENCE_TIME = 15.0  # seconds
MIN_CONFIDENCE_THRESHOLD = 0.7
CACHE_TTL = 300  # seconds
PROGRESS_UPDATE_INTERVAL = 3.0  # seconds

# Model names
MODEL_UITARS_7B = "uitars-7b"
MODEL_MINICPM_V_26 = "minicpm-v-2.6"
MODEL_DOUBAO_API = "doubao-vision-pro"

# Paths
DEFAULT_CONFIG_DIR = Path.home() / ".nvda_vision"
DEFAULT_MODEL_DIR = DEFAULT_CONFIG_DIR / "models"
DEFAULT_CACHE_DIR = DEFAULT_CONFIG_DIR / "cache"

# ✅ GOOD: Enums for finite sets
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


# ❌ BAD: Magic strings scattered in code
if model_type == "uitars":  # What are valid values?
    ...
```

---

## 4. NVDA Plugin Patterns

### 4.1 GlobalPlugin Structure

```python
# __init__.py

import globalPluginHandler
import api
import speech
import ui
from scriptHandler import script
from loguru import logger

from .core.recognition_controller import RecognitionController
from .core.event_coordinator import EventCoordinator
from .config import ConfigManager
from .infrastructure.logger import setup_logger


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    """NVDA Vision Reader global plugin.

    Provides AI-powered screen reader functionality for recognizing
    UI elements using computer vision models.
    """

    def __init__(self):
        """Initialize the plugin and register shortcuts."""
        super().__init__()

        # Setup logging first
        setup_logger()
        logger.info("Initializing NVDA Vision Reader plugin")

        try:
            # Load configuration
            self.config = ConfigManager()

            # Initialize core components
            self.event_coordinator = EventCoordinator()
            self.recognition_controller = RecognitionController(
                config=self.config
            )

            logger.info("Plugin initialized successfully")

        except Exception as e:
            logger.exception("Failed to initialize plugin")
            # Notify user but don't crash NVDA
            ui.message("NVDA Vision Reader failed to initialize")
            raise

    def terminate(self):
        """Clean up resources when plugin is disabled."""
        logger.info("Terminating NVDA Vision Reader plugin")

        try:
            # Unload models to free memory
            if hasattr(self, 'recognition_controller'):
                self.recognition_controller.cleanup()

            logger.info("Plugin terminated successfully")

        except Exception as e:
            logger.exception("Error during plugin termination")

        finally:
            super().terminate()

    @script(
        gesture="kb:NVDA+shift+v",
        description="Recognize UI elements on current screen",
        category="NVDA Vision Reader"
    )
    def script_recognizeScreen(self, gesture):
        """Recognize all UI elements on the current screen.

        Captures screenshot, runs vision model, speaks results.
        """
        try:
            # Don't block NVDA - run in background thread
            self.recognition_controller.recognize_screen_async(
                callback=self._on_recognition_complete,
                error_callback=self._on_recognition_error
            )

            # Immediate feedback
            ui.message("Recognizing screen...")

        except Exception as e:
            logger.exception("Error in script_recognizeScreen")
            ui.message("Recognition failed")

    @script(
        gesture="kb:NVDA+shift+c",
        description="Recognize UI element at cursor",
        category="NVDA Vision Reader"
    )
    def script_recognizeAtCursor(self, gesture):
        """Recognize UI element at mouse cursor position."""
        try:
            cursor_pos = api.getCursorPos()
            self.recognition_controller.recognize_at_point_async(
                x=cursor_pos[0],
                y=cursor_pos[1],
                callback=self._on_element_recognized,
                error_callback=self._on_recognition_error
            )

            ui.message("Recognizing element...")

        except Exception as e:
            logger.exception("Error in script_recognizeAtCursor")
            ui.message("Recognition failed")

    @script(
        gesture="kb:NVDA+shift+n",
        description="Navigate to next UI element",
        category="NVDA Vision Reader"
    )
    def script_nextElement(self, gesture):
        """Navigate to next recognized UI element."""
        try:
            element = self.recognition_controller.get_next_element()
            if element:
                self._speak_element(element)
            else:
                ui.message("No more elements")

        except Exception as e:
            logger.exception("Error in script_nextElement")
            ui.message("Navigation failed")

    @script(
        gesture="kb:NVDA+shift+p",
        description="Navigate to previous UI element",
        category="NVDA Vision Reader"
    )
    def script_previousElement(self, gesture):
        """Navigate to previous recognized UI element."""
        try:
            element = self.recognition_controller.get_previous_element()
            if element:
                self._speak_element(element)
            else:
                ui.message("No previous elements")

        except Exception as e:
            logger.exception("Error in script_previousElement")
            ui.message("Navigation failed")

    def _on_recognition_complete(self, result):
        """Callback when recognition completes successfully."""
        try:
            num_elements = len(result.elements)
            logger.info(f"Recognition complete: {num_elements} elements found")

            # Announce result
            ui.message(
                f"Found {num_elements} elements. "
                f"Use NVDA+Shift+N to navigate."
            )

        except Exception as e:
            logger.exception("Error in recognition callback")

    def _on_element_recognized(self, element):
        """Callback when single element is recognized."""
        try:
            self._speak_element(element)
        except Exception as e:
            logger.exception("Error speaking element")

    def _on_recognition_error(self, error):
        """Callback when recognition fails."""
        logger.error(f"Recognition error: {error}")
        ui.message("Recognition failed. Check logs for details.")

    def _speak_element(self, element):
        """Speak UI element information with NVDA TTS.

        Args:
            element: UIElement instance to announce.
        """
        # Build speech text
        text_parts = []

        # Type and text
        text_parts.append(f"{element.element_type}: {element.text}")

        # Confidence annotation (real.md constraint 3)
        if element.confidence < 0.7:
            text_parts.append("(uncertain)")

        # Position info
        x = (element.bbox[0] + element.bbox[2]) // 2
        y = (element.bbox[1] + element.bbox[3]) // 2
        text_parts.append(f"at position {x}, {y}")

        speech_text = " ".join(text_parts)
        speech.speak(speech_text)
```

### 4.2 ScriptHandler Decorators

```python
from scriptHandler import script

# ✅ GOOD: Full decorator with metadata
@script(
    gesture="kb:NVDA+shift+v",  # Keyboard shortcut
    description="Recognize UI elements on screen",  # Shows in input gestures dialog
    category="NVDA Vision Reader",  # Groups related scripts
)
def script_recognizeScreen(self, gesture):
    """Docstring for developers (not shown to users)."""
    pass


# ✅ GOOD: Multiple gestures for one script
@script(
    gesture="kb(desktop):NVDA+shift+v",  # Desktop layout
    gesture="kb(laptop):NVDA+shift+v",   # Laptop layout
    description="Recognize screen",
    category="NVDA Vision Reader"
)
def script_recognize(self, gesture):
    pass


# ❌ BAD: Missing metadata
@script(gesture="kb:NVDA+shift+v")
def script_recognize(self, gesture):  # No description or category
    pass


# ❌ BAD: Not using decorator
def script_recognize(self, gesture):  # Won't be registered
    pass
```

### 4.3 NVDA Speech Output

```python
import speech
import ui
from loguru import logger

# ✅ GOOD: Use ui.message for simple notifications
ui.message("Recognizing screen...")
ui.message("Found 5 buttons")

# ✅ GOOD: Use speech.speak for detailed information
speech.speak("Button: Submit, position 520, 340, confidence 95%")

# ✅ GOOD: Priority messages (interrupt current speech)
speech.cancelSpeech()
speech.speak("Recognition failed!")

# ✅ GOOD: Announcing with prosody control
from speech import SpeechCommand, PitchCommand
speech.speak([
    "Found element:",
    PitchCommand(multiplier=1.2),  # Higher pitch
    element.text,
    PitchCommand(multiplier=1.0),  # Normal pitch
])

# ✅ GOOD: Queueing multiple messages
for element in elements:
    speech.speak(f"{element.element_type}: {element.text}")
    # Each message queued, not interrupted

# ❌ BAD: Using print() for user feedback
print("Found 5 buttons")  # User won't hear this!

# ❌ BAD: Logging user messages
logger.info("Found 5 buttons")  # Logs are for developers
```

### 4.4 NVDA Event Handling

```python
import eventHandler
import api
from loguru import logger

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    def event_gainFocus(self, obj, nextHandler):
        """Handle focus change events.

        Called when keyboard focus moves to a new object.
        """
        try:
            # Log for debugging
            logger.debug(f"Focus: {obj.name} ({obj.role})")

            # Your custom logic
            if self.config.auto_recognize_on_focus:
                self._maybe_recognize_element(obj)

        except Exception as e:
            logger.exception("Error in event_gainFocus")

        finally:
            # CRITICAL: Always call nextHandler to allow other plugins
            nextHandler()

    def event_mouseMove(self, obj, nextHandler, x, y):
        """Handle mouse movement events."""
        try:
            if self.config.recognize_on_hover:
                self._schedule_recognition_at_point(x, y)

        except Exception as e:
            logger.exception("Error in event_mouseMove")

        finally:
            nextHandler()

    def _maybe_recognize_element(self, obj):
        """Conditionally trigger recognition for an object."""
        # Only recognize if object has no accessible name
        if not obj.name or obj.name.strip() == "":
            logger.info(f"Element has no name, triggering recognition")
            # Trigger async recognition
            # ...

    # ❌ BAD: Not calling nextHandler
    def event_gainFocus_bad(self, obj, nextHandler):
        self._do_stuff(obj)
        # Missing: nextHandler()
        # This breaks other plugins!
```

---

## 5. Vision Model Integration

### 5.1 Model Adapter Pattern

```python
# models/base_adapter.py

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
            model_path: Path to model files (None for cloud APIs).
        """
        self.model_path = model_path
        self.is_loaded = False
        self.model = None

    @abstractmethod
    def load(self) -> None:
        """Load model into memory.

        Raises:
            RuntimeError: If model loading fails.
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
            screenshot: Screenshot to analyze.
            timeout: Max inference time in seconds.

        Returns:
            List of detected UI elements with confidence scores.

        Raises:
            TimeoutError: If inference exceeds timeout.
            RuntimeError: If inference fails.
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


# models/uitars_adapter.py

import torch
from loguru import logger
from typing import List

from .base_adapter import VisionModelAdapter
from ..schemas.screenshot import Screenshot
from ..schemas.ui_element import UIElement
from ..utils.timeout_utils import with_timeout


class UITarsAdapter(VisionModelAdapter):
    """Adapter for UI-TARS 7B model (GPU-accelerated)."""

    @property
    def name(self) -> str:
        return "UI-TARS 7B"

    @property
    def requires_gpu(self) -> bool:
        return True

    @property
    def min_vram_gb(self) -> float:
        return 16.0  # Full precision

    def load(self) -> None:
        """Load UI-TARS model onto GPU.

        Raises:
            RuntimeError: If GPU not available or VRAM insufficient.
        """
        logger.info(f"Loading {self.name} from {self.model_path}")

        # Check GPU availability
        if not torch.cuda.is_available():
            raise RuntimeError("GPU not available for UI-TARS")

        # Check VRAM
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        if vram_gb < self.min_vram_gb:
            raise RuntimeError(
                f"Insufficient VRAM: {vram_gb:.1f}GB < {self.min_vram_gb}GB"
            )

        try:
            # Load model
            from transformers import AutoModel, AutoTokenizer

            self.model = AutoModel.from_pretrained(
                str(self.model_path),
                device_map="auto",
                torch_dtype=torch.float16,  # Use FP16 for speed
                trust_remote_code=True
            )

            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                trust_remote_code=True
            )

            self.model.eval()  # Inference mode
            self.is_loaded = True

            logger.info(f"{self.name} loaded successfully on GPU")

        except Exception as e:
            logger.exception(f"Failed to load {self.name}")
            raise RuntimeError(f"Model loading failed: {e}") from e

    @with_timeout(seconds=15.0)
    def infer(
        self,
        screenshot: Screenshot,
        timeout: float = 15.0
    ) -> List[UIElement]:
        """Run UI-TARS inference on screenshot.

        Args:
            screenshot: Screenshot to analyze.
            timeout: Max inference time (default: 15s).

        Returns:
            List of detected UI elements.

        Raises:
            TimeoutError: If inference exceeds timeout.
            RuntimeError: If model not loaded or inference fails.
        """
        if not self.is_loaded:
            raise RuntimeError(f"{self.name} not loaded")

        logger.debug(f"Running {self.name} inference")

        try:
            # Prepare input
            image = screenshot.image_data  # PIL Image
            prompt = (
                "Detect all UI elements in this screenshot. "
                "For each element, provide: type, text, bounding box."
            )

            # Run inference (this is model-specific)
            with torch.no_grad():  # Disable gradient computation
                inputs = self.model.prepare_inputs(image, prompt)
                outputs = self.model.generate(**inputs, max_length=512)
                result_text = self.tokenizer.decode(
                    outputs[0],
                    skip_special_tokens=True
                )

            # Parse model output into UIElement objects
            elements = self._parse_model_output(result_text, screenshot)

            logger.info(
                f"{self.name} inference complete: "
                f"{len(elements)} elements found"
            )

            return elements

        except TimeoutError:
            logger.warning(f"{self.name} inference timed out")
            raise

        except Exception as e:
            logger.exception(f"{self.name} inference failed")
            raise RuntimeError(f"Inference error: {e}") from e

    def unload(self) -> None:
        """Unload model from GPU memory."""
        if self.model is not None:
            del self.model
            del self.tokenizer
            torch.cuda.empty_cache()
            self.is_loaded = False
            logger.info(f"{self.name} unloaded from GPU")

    def _parse_model_output(
        self,
        output_text: str,
        screenshot: Screenshot
    ) -> List[UIElement]:
        """Parse model output text into UIElement objects.

        Args:
            output_text: Raw text output from model.
            screenshot: Source screenshot for metadata.

        Returns:
            List of UIElement instances.
        """
        # Model-specific parsing logic
        # This is a simplified example
        elements = []

        # Example: Model outputs JSON-like format
        # {"type": "button", "text": "Submit", "bbox": [100, 200, 150, 230], "conf": 0.95}

        import json
        try:
            data = json.loads(output_text)
            for item in data.get("elements", []):
                element = UIElement(
                    element_type=item["type"],
                    text=item["text"],
                    bbox=item["bbox"],
                    confidence=item["conf"],
                    app_name=screenshot.app_name
                )
                elements.append(element)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse model output: {output_text}")

        return elements
```

### 5.2 Model Detection and Selection

```python
# models/model_detector.py

import torch
from loguru import logger
from typing import Optional

from .base_adapter import VisionModelAdapter
from .uitars_adapter import UITarsAdapter
from .minicpm_adapter import MiniCPMAdapter
from .doubao_adapter import DoubaoAPIAdapter


class ModelDetector:
    """Detects hardware capabilities and selects optimal model.

    Priority (from real.md constraint 1):
    1. Local GPU (UI-TARS 7B) - if NVIDIA GPU with 16GB+ VRAM
    2. Local CPU (MiniCPM-V 2.6) - if no GPU but 6GB+ RAM
    3. Cloud API (Doubao) - if local models fail or unavailable
    """

    def __init__(self, model_dir: Path, config: dict):
        """Initialize detector.

        Args:
            model_dir: Directory containing local model files.
            config: Configuration dict with API keys, thresholds, etc.
        """
        self.model_dir = model_dir
        self.config = config
        self._cached_adapter: Optional[VisionModelAdapter] = None

    def detect_best_adapter(self) -> VisionModelAdapter:
        """Detect hardware and return best available model adapter.

        Returns:
            Instantiated adapter ready for loading.

        Note:
            Adapter is NOT loaded by this method. Caller must call load().
        """
        logger.info("Detecting optimal vision model...")

        # Try GPU model first
        if self._can_use_gpu():
            logger.info("GPU detected, using UI-TARS 7B")
            return UITarsAdapter(
                model_path=self.model_dir / "uitars-7b"
            )

        # Try CPU model
        if self._can_use_cpu():
            logger.info("Using CPU model: MiniCPM-V 2.6")
            return MiniCPMAdapter(
                model_path=self.model_dir / "minicpm-v-2.6"
            )

        # Fallback to cloud API
        logger.info("Local models unavailable, using cloud API")
        return DoubaoAPIAdapter(
            api_key=self.config.get("doubao_api_key"),
            endpoint=self.config.get("doubao_endpoint")
        )

    def _can_use_gpu(self) -> bool:
        """Check if GPU model can be used."""
        if not torch.cuda.is_available():
            logger.debug("CUDA not available")
            return False

        # Check VRAM
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        min_vram = 16.0

        if vram_gb < min_vram:
            logger.debug(f"Insufficient VRAM: {vram_gb:.1f}GB < {min_vram}GB")
            return False

        # Check model files exist
        model_path = self.model_dir / "uitars-7b"
        if not model_path.exists():
            logger.debug(f"Model not found: {model_path}")
            return False

        return True

    def _can_use_cpu(self) -> bool:
        """Check if CPU model can be used."""
        import psutil

        # Check RAM
        ram_gb = psutil.virtual_memory().available / 1e9
        min_ram = 6.0

        if ram_gb < min_ram:
            logger.debug(f"Insufficient RAM: {ram_gb:.1f}GB < {min_ram}GB")
            return False

        # Check model files exist
        model_path = self.model_dir / "minicpm-v-2.6"
        if not model_path.exists():
            logger.debug(f"Model not found: {model_path}")
            return False

        return True
```

### 5.3 Model Inference with Timeouts

```python
# utils/timeout_utils.py

import signal
from functools import wraps
from typing import Callable

from loguru import logger


def with_timeout(seconds: float):
    """Decorator to enforce timeout on function execution.

    Args:
        seconds: Timeout duration in seconds.

    Raises:
        TimeoutError: If function exceeds timeout.

    Example:
        @with_timeout(seconds=15.0)
        def slow_inference(image):
            # ... long-running inference
            return result
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Define timeout handler
            def timeout_handler(signum, frame):
                raise TimeoutError(
                    f"{func.__name__} exceeded {seconds}s timeout"
                )

            # Set alarm
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(seconds))

            try:
                result = func(*args, **kwargs)
            finally:
                # Cancel alarm
                signal.alarm(0)

            return result

        return wrapper
    return decorator


# Alternative: Thread-based timeout (Windows-compatible)

import threading
from typing import Any, Optional


class TimeoutThread(threading.Thread):
    """Thread with timeout support for Windows."""

    def __init__(
        self,
        target: Callable,
        args: tuple = (),
        kwargs: dict = None,
        timeout: float = 15.0
    ):
        super().__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs or {}
        self.timeout = timeout
        self.result: Optional[Any] = None
        self.exception: Optional[Exception] = None
        self.daemon = True  # Don't block program exit

    def run(self):
        """Run target function and capture result/exception."""
        try:
            self.result = self.target(*self.args, **self.kwargs)
        except Exception as e:
            self.exception = e

    def get_result(self) -> Any:
        """Wait for result with timeout.

        Returns:
            Result from target function.

        Raises:
            TimeoutError: If thread doesn't finish within timeout.
            Exception: If target function raised an exception.
        """
        self.join(timeout=self.timeout)

        if self.is_alive():
            # Thread still running - timeout
            raise TimeoutError(
                f"Function exceeded {self.timeout}s timeout"
            )

        if self.exception:
            raise self.exception

        return self.result


# Usage:

def run_with_timeout(func: Callable, *args, timeout: float = 15.0, **kwargs):
    """Run function with timeout (Windows-compatible).

    Args:
        func: Function to run.
        *args: Positional arguments for func.
        timeout: Timeout in seconds.
        **kwargs: Keyword arguments for func.

    Returns:
        Result from func.

    Raises:
        TimeoutError: If func exceeds timeout.
    """
    thread = TimeoutThread(target=func, args=args, kwargs=kwargs, timeout=timeout)
    thread.start()
    return thread.get_result()


# Example:

try:
    elements = run_with_timeout(
        model.infer,
        screenshot,
        timeout=15.0
    )
except TimeoutError:
    logger.warning("Inference timed out, degrading to backup model")
    # Try backup model
```

---

## 6. Security Coding Practices

### 6.1 API Key Encryption with DPAPI

```python
# security/encryption.py

import base64
from typing import Optional

import win32crypt
from loguru import logger


class DPAPIEncryption:
    """Windows DPAPI encryption for API keys.

    DPAPI (Data Protection API) encrypts data using user's Windows credentials.
    Encrypted data can only be decrypted by the same user on the same machine.

    Satisfies real.md constraint 2: API keys must be encrypted.
    """

    @staticmethod
    def encrypt(plaintext: str) -> str:
        """Encrypt plaintext using DPAPI.

        Args:
            plaintext: String to encrypt (e.g., API key).

        Returns:
            Base64-encoded encrypted string.

        Example:
            >>> encrypted = DPAPIEncryption.encrypt("my-secret-key")
            >>> print(encrypted)
            AQAAANCMnd8BF...
        """
        try:
            # Convert to bytes
            plaintext_bytes = plaintext.encode('utf-8')

            # Encrypt with DPAPI
            encrypted_bytes = win32crypt.CryptProtectData(
                plaintext_bytes,
                None,  # Optional description
                None,  # Optional entropy
                None,  # Reserved
                None,  # Prompt struct
                0      # Flags
            )

            # Encode as base64 for storage
            encrypted_base64 = base64.b64encode(encrypted_bytes).decode('ascii')

            logger.debug("API key encrypted successfully")
            return encrypted_base64

        except Exception as e:
            logger.exception("Failed to encrypt API key")
            raise RuntimeError(f"Encryption failed: {e}") from e

    @staticmethod
    def decrypt(encrypted_base64: str) -> str:
        """Decrypt DPAPI-encrypted string.

        Args:
            encrypted_base64: Base64-encoded encrypted string.

        Returns:
            Decrypted plaintext string.

        Raises:
            RuntimeError: If decryption fails (wrong user/machine).
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_base64)

            # Decrypt with DPAPI
            plaintext_bytes = win32crypt.CryptUnprotectData(
                encrypted_bytes,
                None,  # Optional entropy
                None,  # Reserved
                None,  # Prompt struct
                0      # Flags
            )[1]  # Returns (description, plaintext)

            plaintext = plaintext_bytes.decode('utf-8')

            logger.debug("API key decrypted successfully")
            return plaintext

        except Exception as e:
            logger.exception("Failed to decrypt API key")
            raise RuntimeError(
                "Decryption failed. Key may have been encrypted by different user."
            ) from e


# config_loader.py

from pathlib import Path
import yaml

from ..security.encryption import DPAPIEncryption


class ConfigManager:
    """Manage configuration with encrypted API keys."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            return self._create_default_config()

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Decrypt API keys
        if 'doubao_api_key_encrypted' in config:
            config['doubao_api_key'] = DPAPIEncryption.decrypt(
                config['doubao_api_key_encrypted']
            )

        return config

    def save_api_key(self, key_name: str, plaintext_key: str):
        """Save API key with encryption.

        Args:
            key_name: Key identifier (e.g., "doubao_api_key").
            plaintext_key: Plaintext API key.
        """
        # Encrypt key
        encrypted_key = DPAPIEncryption.encrypt(plaintext_key)

        # Store encrypted version
        self.config[f"{key_name}_encrypted"] = encrypted_key

        # Remove plaintext from config file
        self.config.pop(key_name, None)

        # Save to disk
        self._save_config()

        logger.info(f"API key '{key_name}' saved securely")

    def _save_config(self):
        """Save configuration to YAML file."""
        # Create copy without decrypted keys
        config_to_save = {
            k: v for k, v in self.config.items()
            if not k.endswith('_api_key') or k.endswith('_encrypted')
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_to_save, f, default_flow_style=False)
```

### 6.2 Screenshot Sanitization

```python
# security/screenshot_sanitizer.py

from PIL import Image, ImageDraw
from typing import List, Tuple

from loguru import logger


class ScreenshotSanitizer:
    """Sanitize screenshots before cloud API upload.

    Provides privacy-preserving transformations:
    - Blur sensitive regions
    - Remove text content
    - Downscale resolution

    Helps satisfy real.md constraint 1: privacy protection.
    """

    @staticmethod
    def blur_regions(
        image: Image.Image,
        regions: List[Tuple[int, int, int, int]]
    ) -> Image.Image:
        """Blur specified regions in image.

        Args:
            image: PIL Image to modify.
            regions: List of (x1, y1, x2, y2) bounding boxes to blur.

        Returns:
            New image with blurred regions.
        """
        from PIL import ImageFilter

        result = image.copy()

        for x1, y1, x2, y2 in regions:
            # Crop region
            region = result.crop((x1, y1, x2, y2))

            # Apply Gaussian blur
            blurred = region.filter(ImageFilter.GaussianBlur(radius=10))

            # Paste back
            result.paste(blurred, (x1, y1))

        return result

    @staticmethod
    def downscale(image: Image.Image, max_size: int = 1280) -> Image.Image:
        """Downscale image to reduce data sent to cloud.

        Args:
            image: PIL Image to resize.
            max_size: Maximum dimension (width or height).

        Returns:
            Resized image.
        """
        width, height = image.size

        if max(width, height) <= max_size:
            return image  # No need to downscale

        # Calculate new size maintaining aspect ratio
        if width > height:
            new_width = max_size
            new_height = int(height * max_size / width)
        else:
            new_height = max_size
            new_width = int(width * max_size / height)

        return image.resize((new_width, new_height), Image.LANCZOS)

    @staticmethod
    def mask_text_regions(
        image: Image.Image,
        text_boxes: List[Tuple[int, int, int, int]]
    ) -> Image.Image:
        """Replace text regions with gray boxes.

        Useful when only UI structure matters, not text content.

        Args:
            image: PIL Image to modify.
            text_boxes: List of (x1, y1, x2, y2) text bounding boxes.

        Returns:
            Image with text masked.
        """
        result = image.copy()
        draw = ImageDraw.Draw(result)

        for x1, y1, x2, y2 in text_boxes:
            # Draw gray rectangle over text
            draw.rectangle([x1, y1, x2, y2], fill=(128, 128, 128))

        return result


# Usage in cloud API adapter:

class DoubaoAPIAdapter(VisionModelAdapter):

    def infer(self, screenshot: Screenshot, timeout: float = 15.0) -> List[UIElement]:
        """Run inference via cloud API with privacy protection."""

        # Ask user permission (real.md constraint 1)
        if not self._user_consented_to_cloud():
            raise RuntimeError("User did not consent to cloud API usage")

        # Sanitize screenshot before upload
        sanitizer = ScreenshotSanitizer()
        sanitized_image = sanitizer.downscale(
            screenshot.image_data,
            max_size=1280
        )

        # Upload and get results
        # ...
```

### 6.3 Secure Logging

```python
# infrastructure/logger.py

import sys
from pathlib import Path
from loguru import logger


def setup_logger(log_dir: Path, level: str = "INFO"):
    """Configure Loguru logger with security considerations.

    Satisfies real.md constraint 2: No sensitive data in logs.

    Args:
        log_dir: Directory for log files.
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
    """
    # Remove default handler
    logger.remove()

    # Console handler (stderr)
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True
    )

    # File handler
    log_file = log_dir / "nvda_vision_{time:YYYY-MM-DD}.log"
    logger.add(
        log_file,
        rotation="1 day",  # New file each day
        retention="7 days",  # Keep logs for 7 days
        compression="zip",  # Compress old logs
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True  # Thread-safe
    )

    logger.info(f"Logger initialized: level={level}, log_dir={log_dir}")


# Secure logging patterns:

# ✅ GOOD: Log without sensitive data
api_key = config.get("doubao_api_key")
logger.info("Loaded cloud API configuration")

# ❌ BAD: Log sensitive data
logger.info(f"API key: {api_key}")  # NEVER DO THIS!

# ✅ GOOD: Log masked version
logger.debug(f"API key: {api_key[:4]}...{api_key[-4:]}")  # sk-ab...xy

# ✅ GOOD: Log screenshot metadata, not content
logger.info(
    f"Captured screenshot: {screenshot.width}x{screenshot.height}, "
    f"app={screenshot.app_name}"
)

# ❌ BAD: Log screenshot data
logger.debug(f"Screenshot data: {screenshot.image_data}")  # Too large + privacy!

# ✅ GOOD: Log exceptions without exposing internals
try:
    result = api_client.recognize(screenshot)
except APIError as e:
    logger.error(f"API request failed: {e.status_code} {e.message}")
    # Don't log request body if it contains screenshot!
```

---

## 7. Error Handling and Exception Isolation

### 7.1 Exception Isolation from NVDA

**Critical requirement** (real.md constraint 5): Plugin exceptions must NOT crash NVDA core.

```python
# ✅ GOOD: Isolate all plugin code with try-except

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    @script(gesture="kb:NVDA+shift+v")
    def script_recognizeScreen(self, gesture):
        """Recognize screen - isolated from NVDA."""
        try:
            # All plugin logic wrapped
            self.recognition_controller.recognize_screen_async()
            ui.message("Recognizing...")

        except Exception as e:
            # Log error but don't propagate
            logger.exception("Recognition failed")
            ui.message("Recognition error. Check logs.")
            # NVDA continues running normally

    def event_gainFocus(self, obj, nextHandler):
        """Focus event - isolated from NVDA."""
        try:
            # Custom logic
            if self.config.auto_recognize:
                self._trigger_recognition(obj)

        except Exception as e:
            logger.exception("Error in focus handler")
            # Don't crash, just skip this event

        finally:
            # ALWAYS call nextHandler
            nextHandler()


# ✅ GOOD: Isolate background threads

import threading
from loguru import logger

def recognize_in_background(screenshot, callback, error_callback):
    """Run recognition in background thread with isolation."""

    def worker():
        try:
            # Long-running inference
            result = vision_engine.infer(screenshot)

            # Call success callback (also isolated)
            try:
                callback(result)
            except Exception as e:
                logger.exception("Error in recognition callback")

        except Exception as e:
            # Call error callback
            logger.exception("Recognition failed in background thread")
            try:
                error_callback(e)
            except Exception:
                logger.exception("Error in error callback")

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()


# ❌ BAD: Letting exceptions propagate

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    @script(gesture="kb:NVDA+shift+v")
    def script_recognizeScreen(self, gesture):
        # No try-except - if this crashes, NVDA crashes!
        self.recognition_controller.recognize_screen()
```

### 7.2 Graceful Degradation

```python
# services/vision_engine.py

from typing import List, Optional
from loguru import logger

from ..models.base_adapter import VisionModelAdapter
from ..models.model_detector import ModelDetector
from ..schemas.screenshot import Screenshot
from ..schemas.ui_element import UIElement


class VisionEngine:
    """Vision inference engine with graceful degradation.

    Tries models in priority order (real.md constraint 1):
    1. Local GPU (UI-TARS 7B)
    2. Local CPU (MiniCPM-V 2.6)
    3. Cloud API (Doubao)

    If all fail, returns empty result instead of crashing.
    """

    def __init__(self, model_detector: ModelDetector):
        self.model_detector = model_detector
        self.primary_adapter: Optional[VisionModelAdapter] = None
        self.backup_adapters: List[VisionModelAdapter] = []

    def initialize(self):
        """Initialize models in priority order."""
        try:
            # Try primary model (GPU if available)
            self.primary_adapter = self.model_detector.detect_best_adapter()
            self.primary_adapter.load()
            logger.info(f"Primary model loaded: {self.primary_adapter.name}")

        except Exception as e:
            logger.exception("Failed to load primary model")
            self.primary_adapter = None

        # Prepare backup adapters
        self._prepare_backups()

    def infer_with_fallback(
        self,
        screenshot: Screenshot,
        timeout: float = 15.0
    ) -> List[UIElement]:
        """Run inference with automatic fallback.

        Args:
            screenshot: Screenshot to analyze.
            timeout: Per-model timeout in seconds.

        Returns:
            List of detected elements (empty if all models fail).
        """
        # Try primary model
        if self.primary_adapter:
            try:
                logger.info(f"Trying primary model: {self.primary_adapter.name}")
                elements = self.primary_adapter.infer(screenshot, timeout)

                if elements:  # Success
                    logger.info(f"Primary model succeeded: {len(elements)} elements")
                    return elements
                else:
                    logger.warning("Primary model returned no elements")

            except TimeoutError:
                logger.warning(f"Primary model timed out after {timeout}s")

            except Exception as e:
                logger.exception(f"Primary model failed: {e}")

        # Try backup models
        for adapter in self.backup_adapters:
            try:
                logger.info(f"Trying backup model: {adapter.name}")

                # Load if not already loaded
                if not adapter.is_loaded:
                    adapter.load()

                elements = adapter.infer(screenshot, timeout)

                if elements:
                    logger.info(f"Backup model succeeded: {len(elements)} elements")
                    return elements

            except Exception as e:
                logger.exception(f"Backup model {adapter.name} failed: {e}")
                continue

        # All models failed
        logger.error("All models failed, returning empty result")
        return []

    def _prepare_backups(self):
        """Prepare backup model adapters."""
        # Import here to avoid circular dependencies
        from ..models.minicpm_adapter import MiniCPMAdapter
        from ..models.doubao_adapter import DoubaoAPIAdapter

        # CPU model backup
        try:
            cpu_adapter = MiniCPMAdapter(model_path=Path("models/minicpm-v-2.6"))
            self.backup_adapters.append(cpu_adapter)
            logger.info("CPU backup model prepared")
        except Exception as e:
            logger.warning(f"Could not prepare CPU backup: {e}")

        # Cloud API backup
        try:
            cloud_adapter = DoubaoAPIAdapter(api_key=self.config["doubao_api_key"])
            self.backup_adapters.append(cloud_adapter)
            logger.info("Cloud API backup prepared")
        except Exception as e:
            logger.warning(f"Could not prepare cloud backup: {e}")


# Usage:

def recognize_screen():
    """Recognize screen with graceful degradation."""
    try:
        screenshot = screenshot_service.capture()
        elements = vision_engine.infer_with_fallback(screenshot)

        if not elements:
            ui.message("No elements detected. Try adjusting settings.")
        else:
            ui.message(f"Found {len(elements)} elements")

    except Exception as e:
        logger.exception("Recognition failed completely")
        ui.message("Recognition failed. Check logs for details.")
```

### 7.3 Context Managers for Resource Cleanup

```python
# ✅ GOOD: Use context managers for cleanup

from contextlib import contextmanager
from typing import Generator

@contextmanager
def temporary_model_load(adapter: VisionModelAdapter) -> Generator[VisionModelAdapter, None, None]:
    """Context manager for temporary model loading.

    Ensures model is unloaded even if inference fails.

    Example:
        with temporary_model_load(uitars_adapter) as model:
            result = model.infer(screenshot)
    """
    try:
        if not adapter.is_loaded:
            adapter.load()

        yield adapter

    finally:
        # Always unload, even on exception
        if adapter.is_loaded:
            adapter.unload()
            logger.debug(f"Model {adapter.name} unloaded")


# Usage:

def run_one_shot_inference(screenshot: Screenshot) -> List[UIElement]:
    """Run inference and immediately unload model."""
    uitars = UITarsAdapter(model_path=Path("models/uitars-7b"))

    with temporary_model_load(uitars) as model:
        elements = model.infer(screenshot)

    # Model automatically unloaded here
    return elements
```

---

## 8. Threading Patterns

### 8.1 Background Thread for Long Operations

**Requirement** (real.md constraint 5): Long-running operations must not block NVDA main thread.

```python
# core/recognition_controller.py

import threading
from typing import Callable, Optional
from loguru import logger

import ui
from ..services.screenshot_service import ScreenshotService
from ..services.vision_engine import VisionEngine
from ..schemas.recognition_result import RecognitionResult


class RecognitionController:
    """Orchestrate recognition flow with async execution."""

    def __init__(self, vision_engine: VisionEngine, screenshot_service: ScreenshotService):
        self.vision_engine = vision_engine
        self.screenshot_service = screenshot_service
        self._current_thread: Optional[threading.Thread] = None
        self._cancel_requested = False

    def recognize_screen_async(
        self,
        callback: Callable[[RecognitionResult], None],
        error_callback: Callable[[Exception], None]
    ):
        """Recognize screen in background thread.

        Args:
            callback: Called with result on success.
            error_callback: Called with exception on failure.
        """
        # Cancel previous recognition if still running
        if self._current_thread and self._current_thread.is_alive():
            logger.warning("Previous recognition still running, cancelling")
            self._cancel_requested = True
            self._current_thread.join(timeout=1.0)

        self._cancel_requested = False

        # Start new background thread
        self._current_thread = threading.Thread(
            target=self._recognition_worker,
            args=(callback, error_callback),
            daemon=True,  # Don't block program exit
            name="RecognitionWorker"
        )
        self._current_thread.start()

        logger.info("Recognition started in background thread")

    def _recognition_worker(
        self,
        callback: Callable,
        error_callback: Callable
    ):
        """Worker function running in background thread."""
        try:
            # Step 1: Capture screenshot (fast)
            logger.debug("Capturing screenshot...")
            screenshot = self.screenshot_service.capture_active_window()

            if self._cancel_requested:
                logger.info("Recognition cancelled after screenshot")
                return

            # Step 2: Run inference (slow - 3-15 seconds)
            logger.debug("Running inference...")

            # Start progress feedback timer
            progress_timer = self._start_progress_timer()

            try:
                elements = self.vision_engine.infer_with_fallback(
                    screenshot,
                    timeout=15.0
                )
            finally:
                # Stop progress timer
                progress_timer.cancel()

            if self._cancel_requested:
                logger.info("Recognition cancelled after inference")
                return

            # Step 3: Process results
            result = RecognitionResult(
                screenshot_hash=screenshot.hash,
                elements=elements,
                # ... other fields
            )

            # Step 4: Call success callback (on main thread ideally)
            logger.info("Recognition complete, calling callback")
            self._call_on_main_thread(callback, result)

        except Exception as e:
            logger.exception("Recognition failed in worker thread")
            self._call_on_main_thread(error_callback, e)

    def _start_progress_timer(self) -> threading.Timer:
        """Start timer for progress feedback.

        Per real.md constraint 6: Report progress after 5 seconds.

        Returns:
            Timer object (can be cancelled).
        """
        def announce_progress():
            """Announce progress to user."""
            if not self._cancel_requested:
                ui.message("Still recognizing, please wait...")

                # Schedule next update in 3 seconds
                next_timer = threading.Timer(3.0, announce_progress)
                next_timer.daemon = True
                next_timer.start()

        # First announcement after 5 seconds
        timer = threading.Timer(5.0, announce_progress)
        timer.daemon = True
        timer.start()

        return timer

    def _call_on_main_thread(self, func: Callable, arg):
        """Call function on NVDA main thread.

        Uses wx.CallAfter to safely update UI from background thread.
        """
        try:
            import wx
            wx.CallAfter(func, arg)
        except Exception as e:
            logger.exception("Failed to call function on main thread")
            # Fallback: call directly (less safe but better than nothing)
            try:
                func(arg)
            except Exception:
                logger.exception("Callback failed even on direct call")

    def cancel_recognition(self):
        """Request cancellation of current recognition."""
        if self._current_thread and self._current_thread.is_alive():
            logger.info("Requesting recognition cancellation")
            self._cancel_requested = True
            ui.message("Cancelling recognition...")
```

### 8.2 Thread-Safe Caching

```python
# services/cache_manager.py

import threading
from typing import Optional, Dict
from datetime import datetime, timedelta
from loguru import logger

from ..schemas.recognition_result import RecognitionResult


class CacheManager:
    """Thread-safe cache for recognition results.

    Implements TTL (time-to-live) expiration and size limits.
    """

    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        """Initialize cache manager.

        Args:
            ttl_seconds: Cache entry time-to-live (default: 5 minutes).
            max_size: Maximum number of cached entries.
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size

        self._cache: Dict[str, tuple[RecognitionResult, datetime]] = {}
        self._lock = threading.RLock()  # Reentrant lock for nested calls

        # Start cleanup thread
        self._start_cleanup_thread()

    def get(self, screenshot_hash: str) -> Optional[RecognitionResult]:
        """Get cached result for screenshot hash.

        Args:
            screenshot_hash: SHA-256 hash of screenshot.

        Returns:
            Cached RecognitionResult if exists and not expired, else None.
        """
        with self._lock:
            if screenshot_hash not in self._cache:
                logger.debug(f"Cache miss: {screenshot_hash[:8]}")
                return None

            result, timestamp = self._cache[screenshot_hash]

            # Check expiration
            age = (datetime.now() - timestamp).total_seconds()
            if age > self.ttl_seconds:
                logger.debug(f"Cache expired: {screenshot_hash[:8]} (age: {age:.1f}s)")
                del self._cache[screenshot_hash]
                return None

            logger.debug(f"Cache hit: {screenshot_hash[:8]} (age: {age:.1f}s)")
            return result

    def put(self, screenshot_hash: str, result: RecognitionResult):
        """Store result in cache.

        Args:
            screenshot_hash: SHA-256 hash of screenshot.
            result: RecognitionResult to cache.
        """
        with self._lock:
            # Enforce size limit (FIFO eviction)
            if len(self._cache) >= self.max_size:
                oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
                logger.debug(f"Cache full, evicted oldest entry: {oldest_key[:8]}")

            # Store with timestamp
            self._cache[screenshot_hash] = (result, datetime.now())
            logger.debug(f"Cached result: {screenshot_hash[:8]}")

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def _cleanup_expired(self):
        """Remove expired entries (called by background thread)."""
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, (result, timestamp) in self._cache.items()
                if (now - timestamp).total_seconds() > self.ttl_seconds
            ]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def _start_cleanup_thread(self):
        """Start background thread for periodic cleanup."""
        def cleanup_worker():
            while True:
                threading.Event().wait(60)  # Run every 60 seconds
                try:
                    self._cleanup_expired()
                except Exception as e:
                    logger.exception("Error in cache cleanup thread")

        thread = threading.Thread(
            target=cleanup_worker,
            daemon=True,  # Don't block program exit
            name="CacheCleanup"
        )
        thread.start()

        logger.info("Cache cleanup thread started")
```

### 8.3 Daemon Threads for Stability

```python
# ✅ GOOD: Use daemon threads for background tasks

import threading

# Daemon thread automatically terminates when main program exits
thread = threading.Thread(
    target=background_worker,
    daemon=True,  # Key: Won't block NVDA shutdown
    name="BackgroundWorker"
)
thread.start()


# ❌ BAD: Non-daemon thread blocks program exit

thread = threading.Thread(target=background_worker)  # daemon=False (default)
thread.start()
# If NVDA tries to exit, it will hang waiting for this thread!


# ✅ GOOD: Proper daemon thread pattern

class BackgroundService:
    """Service running in background daemon thread."""

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start background thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("Service already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._worker,
            daemon=True,
            name="BackgroundService"
        )
        self._thread.start()
        logger.info("Background service started")

    def stop(self, timeout: float = 5.0):
        """Stop background thread gracefully.

        Args:
            timeout: Max seconds to wait for thread to finish.
        """
        if not self._thread or not self._thread.is_alive():
            return

        logger.info("Stopping background service...")
        self._stop_event.set()
        self._thread.join(timeout=timeout)

        if self._thread.is_alive():
            logger.warning("Background service did not stop in time")
        else:
            logger.info("Background service stopped")

    def _worker(self):
        """Worker function running in daemon thread."""
        while not self._stop_event.is_set():
            try:
                # Do work...
                self._do_work()

                # Sleep but check for stop every 0.1s
                if self._stop_event.wait(timeout=0.1):
                    break

            except Exception as e:
                logger.exception("Error in background service")
                # Continue running despite errors

    def _do_work(self):
        """Perform one unit of work."""
        pass
```

---

## 9. Configuration Management

### 9.1 Configuration File Structure

```yaml
# config.yaml

# General settings
version: "1.0.0"
language: "zh-CN"
enable_cloud_api: false  # Default: local-only (real.md constraint 1)

# Model settings
models:
  preference: "auto"  # auto | gpu | cpu | cloud
  timeout_seconds: 15.0
  confidence_threshold: 0.7

  uitars:
    enabled: true
    model_path: "models/uitars-7b"
    device: "cuda"
    dtype: "float16"

  minicpm:
    enabled: true
    model_path: "models/minicpm-v-2.6"
    device: "cpu"

  doubao:
    enabled: false  # Requires user opt-in
    api_endpoint: "https://ark.cn-beijing.volces.com/api/v3/visual"
    # API key stored encrypted (separate field)

# Cache settings
cache:
  enabled: true
  ttl_seconds: 300  # 5 minutes
  max_size: 100

# UI settings
ui:
  announce_confidence: true
  announce_position: true
  auto_recognize_on_focus: false
  progress_feedback_delay: 5.0  # real.md constraint 6

# Keyboard shortcuts (customizable)
shortcuts:
  recognize_screen: "NVDA+shift+v"
  recognize_at_cursor: "NVDA+shift+c"
  next_element: "NVDA+shift+n"
  previous_element: "NVDA+shift+p"

# Privacy settings (real.md constraints)
privacy:
  local_processing_only: true  # No cloud unless explicitly enabled
  blur_sensitive_regions: false
  log_screenshots: false  # Never log screenshot content

# Security
security:
  # Encrypted API keys (added by ConfigManager.save_api_key())
  doubao_api_key_encrypted: ""

# Logging
logging:
  level: "INFO"  # DEBUG | INFO | WARNING | ERROR
  retention_days: 7
  max_file_size_mb: 10
```

### 9.2 Configuration Loader

```python
# infrastructure/config_loader.py

from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from loguru import logger

from ..security.encryption import DPAPIEncryption


class ConfigManager:
    """Manage configuration with validation and encryption."""

    DEFAULT_CONFIG_PATH = Path.home() / ".nvda_vision" / "config.yaml"

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to config file (default: ~/.nvda_vision/config.yaml).
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config: Dict[str, Any] = {}

        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.load()

    def load(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            self.config = self._get_default_config()
            self.save()
            logger.info("Created default configuration")
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            # Decrypt API keys
            self._decrypt_api_keys()

            logger.info(f"Configuration loaded from {self.config_path}")

        except Exception as e:
            logger.exception("Failed to load configuration")
            self.config = self._get_default_config()

    def save(self):
        """Save configuration to YAML file."""
        try:
            # Create copy without decrypted keys
            config_to_save = self._prepare_for_save()

            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(
                    config_to_save,
                    f,
                    default_flow_style=False,
                    allow_unicode=True
                )

            logger.info(f"Configuration saved to {self.config_path}")

        except Exception as e:
            logger.exception("Failed to save configuration")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Supports nested keys with dot notation: "models.uitars.enabled"

        Args:
            key: Configuration key (dot-separated for nested).
            default: Default value if key not found.

        Returns:
            Configuration value or default.

        Example:
            >>> config.get("models.timeout_seconds")
            15.0
            >>> config.get("nonexistent.key", default=42)
            42
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value by key.

        Args:
            key: Configuration key (dot-separated for nested).
            value: Value to set.

        Example:
            >>> config.set("models.timeout_seconds", 20.0)
        """
        keys = key.split('.')
        target = self.config

        # Navigate to parent
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        # Set value
        target[keys[-1]] = value

    def save_api_key(self, key_name: str, plaintext_key: str):
        """Save API key with DPAPI encryption.

        Args:
            key_name: Key identifier (e.g., "doubao_api_key").
            plaintext_key: Plaintext API key.
        """
        # Encrypt key
        encrypted = DPAPIEncryption.encrypt(plaintext_key)

        # Store encrypted version
        self.set(f"security.{key_name}_encrypted", encrypted)

        # Keep decrypted in memory for current session
        self.config[key_name] = plaintext_key

        # Save to file (only encrypted version)
        self.save()

        logger.info(f"API key '{key_name}' saved securely")

    def _decrypt_api_keys(self):
        """Decrypt API keys from config."""
        security = self.config.get("security", {})

        for key, value in security.items():
            if key.endswith("_encrypted"):
                api_key_name = key.replace("_encrypted", "")
                try:
                    decrypted = DPAPIEncryption.decrypt(value)
                    self.config[api_key_name] = decrypted
                    logger.debug(f"Decrypted API key: {api_key_name}")
                except Exception as e:
                    logger.error(f"Failed to decrypt {api_key_name}: {e}")

    def _prepare_for_save(self) -> Dict[str, Any]:
        """Prepare config for saving (remove decrypted keys).

        Returns:
            Config dict safe to save to file.
        """
        config_copy = self.config.copy()

        # Remove decrypted API keys
        for key in list(config_copy.keys()):
            if key.endswith("_api_key") and not key.endswith("_encrypted"):
                del config_copy[key]

        return config_copy

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "version": "1.0.0",
            "language": "zh-CN",
            "enable_cloud_api": False,
            "models": {
                "preference": "auto",
                "timeout_seconds": 15.0,
                "confidence_threshold": 0.7,
            },
            "cache": {
                "enabled": True,
                "ttl_seconds": 300,
                "max_size": 100,
            },
            "ui": {
                "announce_confidence": True,
                "announce_position": True,
                "auto_recognize_on_focus": False,
                "progress_feedback_delay": 5.0,
            },
            "privacy": {
                "local_processing_only": True,
                "blur_sensitive_regions": False,
                "log_screenshots": False,
            },
            "logging": {
                "level": "INFO",
                "retention_days": 7,
                "max_file_size_mb": 10,
            },
        }
```

---

## 10. Logging Standards

### 10.1 Loguru Configuration

```python
# infrastructure/logger.py

import sys
from pathlib import Path
from loguru import logger


def setup_logger(
    log_dir: Path,
    level: str = "INFO",
    retention_days: int = 7,
    max_file_size_mb: int = 10
):
    """Configure Loguru logger for NVDA Vision plugin.

    Args:
        log_dir: Directory for log files.
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
        retention_days: How many days to keep old logs.
        max_file_size_mb: Max size of each log file before rotation.
    """
    # Remove default handler
    logger.remove()

    # Console handler (colored, human-readable)
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    # File handler (structured, machine-readable)
    log_file = log_dir / "nvda_vision_{time:YYYY-MM-DD}.log"
    logger.add(
        log_file,
        rotation=f"{max_file_size_mb} MB",  # Rotate at size limit
        retention=f"{retention_days} days",  # Keep for N days
        compression="zip",  # Compress old logs
        level=level,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message}"
        ),
        enqueue=True,  # Thread-safe
        backtrace=True,
        diagnose=True
    )

    logger.info(
        f"Logger initialized: level={level}, log_dir={log_dir}, "
        f"retention={retention_days}d, max_size={max_file_size_mb}MB"
    )


# Custom filter to remove sensitive data

def sanitize_log_record(record):
    """Filter to remove sensitive data from logs.

    Ensures compliance with real.md constraint 2: no API keys in logs.
    """
    # Check if message contains potential API key patterns
    message = record["message"]

    # Mask patterns like "sk-..." or long base64 strings
    import re

    # Mask API keys (starts with sk-, mk-, ak- etc.)
    message = re.sub(
        r'\b([sma]k-[a-zA-Z0-9]{4})[a-zA-Z0-9]+([a-zA-Z0-9]{4})\b',
        r'\1...\2',
        message
    )

    # Mask long base64 strings (potential encrypted keys)
    message = re.sub(
        r'\b([A-Za-z0-9+/]{8})[A-Za-z0-9+/]{32,}([A-Za-z0-9+/=]{8})\b',
        r'\1...\2',
        message
    )

    record["message"] = message
    return True


# Apply filter
logger.add(sys.stderr, filter=sanitize_log_record)
```

### 10.2 Logging Best Practices

```python
from loguru import logger

# ✅ GOOD: Structured logging with context

logger.info(
    "Model inference complete",
    model=model.name,
    inference_time=elapsed,
    num_elements=len(elements),
    confidence_avg=sum(e.confidence for e in elements) / len(elements)
)

# ✅ GOOD: Log levels used appropriately

logger.debug("Preparing model inputs...")  # Development debugging
logger.info("Recognition started")  # General information
logger.warning("Confidence below threshold")  # Potential issues
logger.error("Model inference failed")  # Errors that can be handled
logger.critical("NVDA API not available")  # Critical failures

# ✅ GOOD: Exception logging with context

try:
    result = model.infer(screenshot)
except TimeoutError as e:
    logger.exception(
        "Model inference timed out",
        model=model.name,
        timeout=timeout,
        screenshot_size=(screenshot.width, screenshot.height)
    )

# ✅ GOOD: Performance logging

from time import time

start_time = time()
result = model.infer(screenshot)
elapsed = time() - start_time

logger.info(f"Inference completed in {elapsed:.2f}s", model=model.name)

if elapsed > 10.0:
    logger.warning(
        "Inference took longer than expected",
        elapsed=elapsed,
        threshold=10.0
    )

# ❌ BAD: Logging sensitive data

api_key = config.get("doubao_api_key")
logger.info(f"Using API key: {api_key}")  # NEVER!

# ❌ BAD: Logging large objects

logger.debug(f"Screenshot data: {screenshot.image_data}")  # Too large!

# ❌ BAD: String formatting in log calls (inefficient)

logger.debug(f"Processing element: {element}")  # Evaluated even if not logged

# ✅ GOOD: Use lazy evaluation

logger.debug("Processing element: {element}", element=element)  # Only if logged
```

### 10.3 Contextual Logging

```python
from loguru import logger
from contextlib import contextmanager

# ✅ GOOD: Use contextvars for request-specific logging

from contextvars import ContextVar

recognition_id: ContextVar[str] = ContextVar("recognition_id", default="unknown")


@contextmanager
def recognition_context(rec_id: str):
    """Context manager for recognition-specific logging."""
    token = recognition_id.set(rec_id)
    try:
        yield
    finally:
        recognition_id.reset(token)


# Custom format to include context
def format_with_context(record):
    """Add context to log record."""
    rec_id = recognition_id.get()
    record["extra"]["recognition_id"] = rec_id
    return True


logger.add(sys.stderr, filter=format_with_context)


# Usage:

import uuid

rec_id = str(uuid.uuid4())[:8]
with recognition_context(rec_id):
    logger.info("Starting recognition")  # Includes recognition_id
    screenshot = capture_screenshot()
    logger.info("Screenshot captured")  # Same recognition_id
    result = infer(screenshot)
    logger.info("Inference complete")  # Same recognition_id
```

---

## 11. Testing Patterns

### 11.1 Unit Test Structure

```python
# tests/unit/models/test_uitars_adapter.py

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from addon.globalPlugins.nvdaVision.models.uitars_adapter import UITarsAdapter
from addon.globalPlugins.nvdaVision.schemas.screenshot import Screenshot
from addon.globalPlugins.nvdaVision.schemas.ui_element import UIElement


class TestUITarsAdapter:
    """Unit tests for UITarsAdapter."""

    @pytest.fixture
    def mock_model_path(self, tmp_path):
        """Create temporary model directory."""
        model_dir = tmp_path / "uitars-7b"
        model_dir.mkdir()
        return model_dir

    @pytest.fixture
    def adapter(self, mock_model_path):
        """Create adapter instance."""
        return UITarsAdapter(model_path=mock_model_path)

    @pytest.fixture
    def mock_screenshot(self):
        """Create mock screenshot."""
        from PIL import Image
        import numpy as np

        # Create dummy image
        img_array = np.zeros((1080, 1920, 3), dtype=np.uint8)
        image = Image.fromarray(img_array)

        return Screenshot(
            hash="test_hash",
            image_data=image,
            width=1920,
            height=1080,
            window_title="Test Window",
            app_name="TestApp"
        )

    def test_adapter_properties(self, adapter):
        """Test adapter properties."""
        assert adapter.name == "UI-TARS 7B"
        assert adapter.requires_gpu is True
        assert adapter.min_vram_gb == 16.0
        assert adapter.is_loaded is False

    @patch('torch.cuda.is_available')
    @patch('torch.cuda.get_device_properties')
    def test_load_success(self, mock_device_props, mock_cuda_available, adapter):
        """Test successful model loading."""
        # Mock GPU available with sufficient VRAM
        mock_cuda_available.return_value = True
        mock_device_props.return_value = Mock(total_memory=20e9)  # 20GB

        with patch('transformers.AutoModel.from_pretrained') as mock_model, \
             patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:

            mock_model.return_value = Mock()
            mock_tokenizer.return_value = Mock()

            # Load model
            adapter.load()

            # Assertions
            assert adapter.is_loaded is True
            mock_model.assert_called_once()
            mock_tokenizer.assert_called_once()

    @patch('torch.cuda.is_available')
    def test_load_no_gpu(self, mock_cuda_available, adapter):
        """Test loading fails when GPU not available."""
        mock_cuda_available.return_value = False

        with pytest.raises(RuntimeError, match="GPU not available"):
            adapter.load()

    @patch('torch.cuda.is_available')
    @patch('torch.cuda.get_device_properties')
    def test_load_insufficient_vram(self, mock_device_props, mock_cuda_available, adapter):
        """Test loading fails with insufficient VRAM."""
        mock_cuda_available.return_value = True
        mock_device_props.return_value = Mock(total_memory=8e9)  # Only 8GB

        with pytest.raises(RuntimeError, match="Insufficient VRAM"):
            adapter.load()

    def test_infer_not_loaded(self, adapter, mock_screenshot):
        """Test inference fails when model not loaded."""
        with pytest.raises(RuntimeError, match="not loaded"):
            adapter.infer(mock_screenshot)

    @patch('torch.cuda.is_available')
    @patch('torch.cuda.get_device_properties')
    def test_infer_success(self, mock_device_props, mock_cuda_available, adapter, mock_screenshot):
        """Test successful inference."""
        # Setup mocks
        mock_cuda_available.return_value = True
        mock_device_props.return_value = Mock(total_memory=20e9)

        with patch('transformers.AutoModel.from_pretrained') as mock_model_class, \
             patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer_class:

            # Mock model
            mock_model = Mock()
            mock_model.prepare_inputs.return_value = {}
            mock_model.generate.return_value = [[1, 2, 3]]
            mock_model_class.return_value = mock_model

            # Mock tokenizer
            mock_tokenizer = Mock()
            mock_tokenizer.decode.return_value = '{"elements": [{"type": "button", "text": "OK", "bbox": [100, 200, 150, 230], "conf": 0.95}]}'
            mock_tokenizer_class.return_value = mock_tokenizer

            # Load and infer
            adapter.load()
            elements = adapter.infer(mock_screenshot, timeout=15.0)

            # Assertions
            assert len(elements) == 1
            assert elements[0].element_type == "button"
            assert elements[0].text == "OK"
            assert elements[0].confidence == 0.95

    def test_unload(self, adapter):
        """Test model unloading."""
        # Mock loaded model
        adapter.model = Mock()
        adapter.tokenizer = Mock()
        adapter.is_loaded = True

        with patch('torch.cuda.empty_cache'):
            adapter.unload()

        assert adapter.model is None
        assert adapter.tokenizer is None
        assert adapter.is_loaded is False
```

### 11.2 Integration Test Patterns

```python
# tests/integration/test_recognition_flow.py

import pytest
from pathlib import Path
from PIL import Image
import numpy as np

from addon.globalPlugins.nvdaVision.core.recognition_controller import RecognitionController
from addon.globalPlugins.nvdaVision.services.vision_engine import VisionEngine
from addon.globalPlugins.nvdaVision.services.screenshot_service import ScreenshotService
from addon.globalPlugins.nvdaVision.services.cache_manager import CacheManager
from addon.globalPlugins.nvdaVision.models.model_detector import ModelDetector


class TestRecognitionFlow:
    """Integration tests for full recognition flow."""

    @pytest.fixture
    def test_config(self, tmp_path):
        """Create test configuration."""
        return {
            "model_dir": tmp_path / "models",
            "cache_dir": tmp_path / "cache",
            "cache_ttl": 300,
            "timeout": 15.0,
            "confidence_threshold": 0.7,
        }

    @pytest.fixture
    def test_screenshot(self, tmp_path):
        """Create test screenshot file."""
        # Create test image
        img_array = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        image = Image.fromarray(img_array)

        # Save to file
        screenshot_path = tmp_path / "test_screenshot.png"
        image.save(screenshot_path)

        return screenshot_path

    def test_full_recognition_flow(self, test_config, test_screenshot):
        """Test complete recognition flow: capture → infer → cache → speak."""
        # Initialize components
        model_detector = ModelDetector(
            model_dir=test_config["model_dir"],
            config=test_config
        )

        vision_engine = VisionEngine(model_detector=model_detector)
        screenshot_service = ScreenshotService()
        cache_manager = CacheManager(
            ttl_seconds=test_config["cache_ttl"]
        )

        controller = RecognitionController(
            vision_engine=vision_engine,
            screenshot_service=screenshot_service,
            cache_manager=cache_manager
        )

        # Test recognition
        result_received = False

        def on_success(result):
            nonlocal result_received
            result_received = True
            assert result is not None
            assert len(result.elements) >= 0  # May be empty if models unavailable

        def on_error(error):
            pytest.fail(f"Recognition failed: {error}")

        # Trigger async recognition
        controller.recognize_screen_async(
            callback=on_success,
            error_callback=on_error
        )

        # Wait for completion (with timeout)
        import time
        max_wait = 20.0
        elapsed = 0.0
        while not result_received and elapsed < max_wait:
            time.sleep(0.1)
            elapsed += 0.1

        assert result_received, "Recognition did not complete in time"

    def test_cache_hit(self, test_config, test_screenshot):
        """Test cache hit on second recognition of same screenshot."""
        # Setup
        cache_manager = CacheManager(ttl_seconds=300)
        screenshot_service = ScreenshotService()

        # Capture screenshot
        screenshot = screenshot_service.capture_from_file(test_screenshot)

        # Create fake result
        from addon.globalPlugins.nvdaVision.schemas.recognition_result import RecognitionResult
        fake_result = RecognitionResult(
            screenshot_hash=screenshot.hash,
            elements=[],
            model_name="test",
            inference_time=1.0,
            status="success"
        )

        # Store in cache
        cache_manager.put(screenshot.hash, fake_result)

        # Retrieve from cache
        cached_result = cache_manager.get(screenshot.hash)

        assert cached_result is not None
        assert cached_result.screenshot_hash == screenshot.hash
```

### 11.3 NVDA Plugin Testing

```python
# tests/nvda/test_global_plugin.py

import pytest
from unittest.mock import Mock, patch, MagicMock

# Note: NVDA modules may not be available in test environment
# Use mocks for NVDA APIs


class TestGlobalPlugin:
    """Tests for NVDA GlobalPlugin integration."""

    @pytest.fixture
    def mock_nvda_modules(self):
        """Mock NVDA modules."""
        with patch.dict('sys.modules', {
            'globalPluginHandler': MagicMock(),
            'api': MagicMock(),
            'speech': MagicMock(),
            'ui': MagicMock(),
            'scriptHandler': MagicMock(),
        }):
            yield

    @pytest.fixture
    def plugin(self, mock_nvda_modules):
        """Create plugin instance with mocked NVDA."""
        from addon.globalPlugins.nvdaVision import GlobalPlugin

        # Mock config and components
        with patch('addon.globalPlugins.nvdaVision.ConfigManager'), \
             patch('addon.globalPlugins.nvdaVision.RecognitionController'), \
             patch('addon.globalPlugins.nvdaVision.EventCoordinator'):

            plugin = GlobalPlugin()
            return plugin

    def test_plugin_initialization(self, plugin):
        """Test plugin initializes without crashing."""
        assert plugin is not None
        assert hasattr(plugin, 'recognition_controller')
        assert hasattr(plugin, 'event_coordinator')

    def test_script_recognize_screen(self, plugin, mock_nvda_modules):
        """Test recognize screen script."""
        # Mock gesture
        mock_gesture = Mock()

        # Mock controller
        plugin.recognition_controller.recognize_screen_async = Mock()

        # Call script
        plugin.script_recognizeScreen(mock_gesture)

        # Verify controller was called
        plugin.recognition_controller.recognize_screen_async.assert_called_once()

    def test_script_exception_isolation(self, plugin, mock_nvda_modules):
        """Test that script exceptions don't propagate."""
        # Make controller raise exception
        plugin.recognition_controller.recognize_screen_async = Mock(
            side_effect=RuntimeError("Test error")
        )

        mock_gesture = Mock()

        # Should not raise exception
        plugin.script_recognizeScreen(mock_gesture)

        # User should be notified via ui.message
        # (Check mock calls if ui is mocked)
```

---

## 12. Code Review Checklist

### 12.1 Pre-Commit Checklist

Before committing code, ensure:

#### General
- [ ] Code follows PEP 8 style guide
- [ ] All functions have type hints
- [ ] All public APIs have docstrings (Google style)
- [ ] No debugging print() statements remain
- [ ] No commented-out code (remove or explain why kept)
- [ ] No TODOs without issue tracker references

#### Privacy & Security (real.md constraints 1, 2)
- [ ] Screenshots processed locally first, cloud as fallback
- [ ] User consent obtained before cloud API calls
- [ ] API keys encrypted with DPAPI
- [ ] No API keys in logs
- [ ] No screenshot data in logs
- [ ] Screenshot sanitization applied before cloud upload

#### Stability (real.md constraint 5)
- [ ] All plugin code wrapped in try-except
- [ ] Background threads are daemon threads
- [ ] Exception handlers don't crash NVDA
- [ ] Resource cleanup in finally blocks or context managers
- [ ] Timeouts set for long operations

#### User Experience (real.md constraints 3, 6)
- [ ] Confidence scores included in all results
- [ ] Low confidence (<0.7) marked as "uncertain"
- [ ] Progress feedback after 5 seconds
- [ ] Auto-degradation or cancellation after 15 seconds
- [ ] All features have keyboard shortcuts
- [ ] All UI elements have NVDA-readable labels

#### NVDA Integration
- [ ] GlobalPlugin methods don't block main thread
- [ ] Event handlers call nextHandler()
- [ ] Scripts use @script decorator with metadata
- [ ] Speech output uses speech.speak() or ui.message()
- [ ] No direct GUI manipulation (use wx.CallAfter if needed)

#### Testing
- [ ] Unit tests written for new functions
- [ ] Integration tests for user-facing features
- [ ] Edge cases tested (empty input, null values, etc.)
- [ ] Exception paths tested
- [ ] Test coverage >80% for new code

### 12.2 Code Review Questions

When reviewing others' code, ask:

#### Architecture
- Does this fit the layered architecture?
- Are dependencies injected, not hardcoded?
- Is the component testable in isolation?
- Does it follow single responsibility principle?

#### Error Handling
- What happens if this function receives invalid input?
- What if the model fails? Is there a fallback?
- Could this exception crash NVDA?
- Are resources cleaned up on error?

#### Performance
- Could this block the main thread?
- Is this operation cached?
- Could this leak memory?
- Is model loaded/unloaded appropriately?

#### Security
- Could this expose API keys?
- Is user data encrypted at rest?
- Is user consent obtained for cloud operations?
- Could logs expose sensitive data?

#### Maintainability
- Is the code self-documenting?
- Are magic numbers replaced with named constants?
- Are there comments explaining "why", not "what"?
- Could a new developer understand this in 5 minutes?

---

## Appendix A: Common Patterns Quick Reference

### A.1 NVDA Plugin Script

```python
@script(
    gesture="kb:NVDA+shift+v",
    description="Recognize screen",
    category="NVDA Vision Reader"
)
def script_recognizeScreen(self, gesture):
    try:
        self.controller.recognize_screen_async(
            callback=self._on_success,
            error_callback=self._on_error
        )
        ui.message("Recognizing...")
    except Exception as e:
        logger.exception("Script failed")
        ui.message("Error")
```

### A.2 Background Thread with Progress

```python
def recognize_async(self, callback, error_callback):
    def worker():
        try:
            # Start progress timer
            timer = threading.Timer(5.0, lambda: ui.message("Please wait..."))
            timer.daemon = True
            timer.start()

            try:
                result = self.engine.infer(screenshot, timeout=15.0)
            finally:
                timer.cancel()

            wx.CallAfter(callback, result)

        except Exception as e:
            logger.exception("Recognition failed")
            wx.CallAfter(error_callback, e)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
```

### A.3 Model Inference with Timeout

```python
from utils.timeout_utils import run_with_timeout

try:
    elements = run_with_timeout(
        model.infer,
        screenshot,
        timeout=15.0
    )
except TimeoutError:
    logger.warning("Inference timed out, trying backup model")
    elements = backup_model.infer(screenshot)
```

### A.4 API Key Encryption

```python
from security.encryption import DPAPIEncryption

# Save encrypted
plaintext_key = "sk-abc123..."
encrypted = DPAPIEncryption.encrypt(plaintext_key)
config.set("security.doubao_api_key_encrypted", encrypted)

# Load decrypted
encrypted = config.get("security.doubao_api_key_encrypted")
plaintext_key = DPAPIEncryption.decrypt(encrypted)
```

### A.5 Thread-Safe Caching

```python
cache = CacheManager(ttl_seconds=300)

# Check cache first
cached = cache.get(screenshot.hash)
if cached:
    return cached

# Miss - compute and cache
result = vision_engine.infer(screenshot)
cache.put(screenshot.hash, result)
return result
```

### A.6 Graceful Degradation

```python
try:
    elements = gpu_model.infer(screenshot)
except (TimeoutError, RuntimeError):
    try:
        elements = cpu_model.infer(screenshot)
    except Exception:
        elements = cloud_api.infer(screenshot)
```

---

## Appendix B: Anti-Patterns to Avoid

### B.1 Don't Block NVDA Main Thread

```python
# ❌ BAD: Blocks NVDA
def script_recognize(self, gesture):
    elements = model.infer(screenshot)  # Blocks for 10s!
    speech.speak(f"Found {len(elements)} elements")

# ✅ GOOD: Async with callback
def script_recognize(self, gesture):
    self.controller.recognize_async(callback=self._on_complete)
    ui.message("Recognizing...")
```

### B.2 Don't Leak Exceptions to NVDA

```python
# ❌ BAD: Exception crashes NVDA
def event_gainFocus(self, obj, nextHandler):
    self._do_stuff(obj)  # Could raise exception
    nextHandler()

# ✅ GOOD: Isolated exception
def event_gainFocus(self, obj, nextHandler):
    try:
        self._do_stuff(obj)
    except Exception as e:
        logger.exception("Error in focus handler")
    finally:
        nextHandler()
```

### B.3 Don't Log Sensitive Data

```python
# ❌ BAD: Exposes API key
logger.info(f"Using API key: {api_key}")

# ✅ GOOD: Masked
logger.info(f"Using API key: {api_key[:4]}...{api_key[-4:]}")

# ❌ BAD: Logs screenshot
logger.debug(f"Screenshot: {screenshot.image_data}")

# ✅ GOOD: Metadata only
logger.debug(f"Screenshot: {screenshot.width}x{screenshot.height}")
```

### B.4 Don't Use Non-Daemon Threads

```python
# ❌ BAD: Blocks NVDA shutdown
thread = threading.Thread(target=worker)
thread.start()

# ✅ GOOD: Daemon thread
thread = threading.Thread(target=worker, daemon=True)
thread.start()
```

### B.5 Don't Forget Resource Cleanup

```python
# ❌ BAD: Model stays in memory
model.load()
result = model.infer(screenshot)
# Model never unloaded!

# ✅ GOOD: Context manager
with temporary_model_load(model):
    result = model.infer(screenshot)
# Model automatically unloaded
```

---

## Version Information

**Document Version**: v1.0.0
**Created**: 2025-12-24
**Last Updated**: 2025-12-24
**Dependencies**: `.42cog/real/real.md`, `.42cog/cog/cog.md`, `spec/dev/sys.spec.md`
**Next Review**: 2025-01-24

---

## Change Log

| Version | Date       | Changes                          | Author |
|---------|------------|----------------------------------|--------|
| 1.0.0   | 2025-12-24 | Initial coding standards created | Claude |

---

**End of Coding Standards Specification**
