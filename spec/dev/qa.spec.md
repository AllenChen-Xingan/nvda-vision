# NVDA Vision Screen Reader - Quality Assurance Specification

**Document Version**: v1.0.0
**Created**: 2025-12-24
**Dependencies**: `.42cog/real/real.md`, `.42cog/cog/cog.md`, `spec/dev/sys.spec.md`, `spec/dev/code.spec.md`
**Skill**: dev-quality-assurance

---

## Table of Contents

1. [Overview](#1-overview)
2. [Testing Strategy](#2-testing-strategy)
3. [Test Pyramid](#3-test-pyramid)
4. [Unit Testing](#4-unit-testing)
5. [Integration Testing](#5-integration-testing)
6. [End-to-End Testing](#6-end-to-end-testing)
7. [Security Testing](#7-security-testing)
8. [Performance Testing](#8-performance-testing)
9. [Accessibility Testing](#9-accessibility-testing)
10. [NVDA-Specific Testing](#10-nvda-specific-testing)
11. [Vision Model Testing](#11-vision-model-testing)
12. [CI/CD Pipeline](#12-cicd-pipeline)
13. [Test Data Management](#13-test-data-management)
14. [Quality Metrics](#14-quality-metrics)

---

## 1. Overview

### 1.1 Purpose

This document defines comprehensive quality assurance practices for the NVDA Vision Screen Reader plugin, ensuring:

- **Privacy**: Local-first processing verified, cloud API consent tested
- **Security**: DPAPI encryption correctness, API key protection, screenshot sanitization
- **Stability**: NVDA crash prevention, exception isolation, resource cleanup
- **Accessibility**: Keyboard navigation, screen reader compatibility, WCAG 2.1 AA compliance
- **Performance**: Inference time benchmarks, memory usage limits, response time SLAs
- **Transparency**: Confidence score validation, uncertainty annotation

### 1.2 Quality Constraints (from real.md)

All tests must verify compliance with:

1. **Privacy-first**: Screenshots processed locally, cloud only on failure + consent
2. **API Key Security**: Keys encrypted with DPAPI, never in plaintext logs
3. **Transparency**: Confidence scores included, <0.7 marked "uncertain"
4. **Accessibility**: WCAG 2.1 AA, keyboard-only operation
5. **Stability**: Plugin crashes don't affect NVDA core
6. **Performance**: <5s progress feedback, >15s auto-degradation
7. **Open Source**: Apache 2.0 / MIT license compliance

### 1.3 Test Environment

**Operating Systems**:
- Windows 10 (x64) - Build 19045 or later
- Windows 11 (x64) - Build 22000 or later

**NVDA Versions**:
- NVDA 2023.1 (minimum supported)
- NVDA 2024.4 (latest tested)

**Python Environment**:
- Python 3.11 (NVDA embedded)
- Virtual environment for development testing

**Hardware Configurations**:
- GPU: NVIDIA RTX 3090 (24GB VRAM) - for UI-TARS testing
- GPU: NVIDIA GTX 1660 (6GB VRAM) - for minimum VRAM testing
- CPU: Intel i7-10700K / AMD Ryzen 7 5800X - for CPU model testing
- RAM: 8GB, 16GB, 32GB variants

---

## 2. Testing Strategy

### 2.1 Overall Approach

**Risk-Based Testing**: Prioritize tests for high-risk areas:
1. **Critical Path**: User recognition flow (capture → infer → speak)
2. **Security**: API key encryption, screenshot privacy
3. **Stability**: Exception isolation from NVDA
4. **Performance**: Inference time, memory usage

**Test-First Development**: Write tests before implementation for:
- Security-critical code (encryption, sanitization)
- Complex logic (model selection, fallback chains)
- Public APIs (plugin scripts, event handlers)

**Continuous Testing**: Automated tests run on:
- Every commit (unit tests, fast integration tests)
- Pull request (full suite including E2E)
- Nightly builds (performance tests, long-running stability tests)

### 2.2 Test Levels

```
┌─────────────────────────────────────────────────┐
│           E2E Tests (5%)                        │
│  Full user workflows with real NVDA             │
├─────────────────────────────────────────────────┤
│       Integration Tests (20%)                   │
│  Multi-component interactions                   │
├─────────────────────────────────────────────────┤
│            Unit Tests (75%)                     │
│  Individual functions and classes               │
└─────────────────────────────────────────────────┘
```

**Test Distribution**:
- **Unit**: 75% - Fast, isolated, comprehensive coverage
- **Integration**: 20% - Component interactions, realistic scenarios
- **E2E**: 5% - Critical user paths, real NVDA environment

### 2.3 Test Ownership

| Component | Owner | Test Coverage Target |
|-----------|-------|---------------------|
| Vision Models | ML Engineer | 85% unit, 90% integration |
| NVDA Integration | NVDA Specialist | 80% unit, 100% E2E |
| Security | Security Engineer | 100% unit + manual audit |
| Infrastructure | DevOps | 70% unit, 90% integration |
| UI Scripts | Frontend Dev | 80% unit, 90% E2E |

---

## 3. Test Pyramid

### 3.1 Unit Tests (75%)

**Target**: 1500+ tests, <5 minutes execution, 85%+ code coverage

**Coverage**:
- All public functions and methods
- Edge cases (null inputs, empty arrays, boundary values)
- Error paths (exceptions, timeouts, fallbacks)
- Private methods (if complex logic)

**Exclusions**:
- Trivial getters/setters
- Simple configuration access
- Auto-generated code

**Tools**:
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking
- `pytest-timeout` - Timeout enforcement

### 3.2 Integration Tests (20%)

**Target**: 400+ tests, <15 minutes execution

**Coverage**:
- Model loading and inference
- Screenshot capture and processing
- Cache operations
- Configuration loading
- API client interactions
- Multi-threaded scenarios

**Tools**:
- `pytest` with fixtures
- `pytest-asyncio` for async tests
- Docker for cloud API mocks
- Test databases for cache

### 3.3 End-to-End Tests (5%)

**Target**: 100+ tests, <30 minutes execution

**Coverage**:
- Complete user workflows
- NVDA integration
- Keyboard shortcut handling
- Speech output verification
- Error recovery scenarios

**Tools**:
- `pytest` with NVDA automation
- Windows UI Automation
- Screen reader testing framework

---

## 4. Unit Testing

### 4.1 Test Structure

```python
# tests/unit/models/test_uitars_adapter.py

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from addon.globalPlugins.nvdaVision.models.uitars_adapter import UITarsAdapter
from addon.globalPlugins.nvdaVision.schemas.screenshot import Screenshot
from addon.globalPlugins.nvdaVision.schemas.ui_element import UIElement


class TestUITarsAdapter:
    """Unit tests for UITarsAdapter.

    Tests cover:
    - Model loading (GPU detection, VRAM validation)
    - Inference (timeout, error handling)
    - Resource cleanup (unloading)
    """

    @pytest.fixture
    def mock_model_path(self, tmp_path) -> Path:
        """Create temporary model directory."""
        model_dir = tmp_path / "uitars-7b"
        model_dir.mkdir()
        (model_dir / "config.json").write_text("{}")
        return model_dir

    @pytest.fixture
    def adapter(self, mock_model_path) -> UITarsAdapter:
        """Create adapter instance with mocked dependencies."""
        return UITarsAdapter(model_path=mock_model_path)

    @pytest.fixture
    def mock_screenshot(self) -> Screenshot:
        """Create test screenshot."""
        from PIL import Image
        import numpy as np

        img_array = np.zeros((1080, 1920, 3), dtype=np.uint8)
        image = Image.fromarray(img_array)

        return Screenshot(
            hash="test_hash_123",
            image_data=image,
            width=1920,
            height=1080,
            window_title="Test Window",
            app_name="TestApp"
        )

    # Property tests
    def test_adapter_name(self, adapter):
        """Test adapter name property."""
        assert adapter.name == "UI-TARS 7B"

    def test_requires_gpu(self, adapter):
        """Test GPU requirement property."""
        assert adapter.requires_gpu is True

    def test_min_vram_gb(self, adapter):
        """Test minimum VRAM property."""
        assert adapter.min_vram_gb == 16.0

    def test_initial_state(self, adapter):
        """Test adapter initial state."""
        assert adapter.is_loaded is False
        assert adapter.model is None

    # Loading tests
    @patch('torch.cuda.is_available')
    def test_load_fails_without_gpu(self, mock_cuda, adapter):
        """Test loading fails when GPU not available."""
        mock_cuda.return_value = False

        with pytest.raises(RuntimeError, match="GPU not available"):
            adapter.load()

    @patch('torch.cuda.is_available')
    @patch('torch.cuda.get_device_properties')
    def test_load_fails_insufficient_vram(
        self, mock_props, mock_cuda, adapter
    ):
        """Test loading fails with insufficient VRAM."""
        mock_cuda.return_value = True
        mock_props.return_value = Mock(total_memory=8e9)  # Only 8GB

        with pytest.raises(RuntimeError, match="Insufficient VRAM"):
            adapter.load()

    @patch('torch.cuda.is_available')
    @patch('torch.cuda.get_device_properties')
    @patch('transformers.AutoModel.from_pretrained')
    @patch('transformers.AutoTokenizer.from_pretrained')
    def test_load_success(
        self, mock_tokenizer, mock_model, mock_props, mock_cuda, adapter
    ):
        """Test successful model loading."""
        # Setup mocks
        mock_cuda.return_value = True
        mock_props.return_value = Mock(total_memory=20e9)
        mock_model.return_value = Mock()
        mock_tokenizer.return_value = Mock()

        # Load model
        adapter.load()

        # Verify
        assert adapter.is_loaded is True
        assert adapter.model is not None
        mock_model.assert_called_once()
        mock_tokenizer.assert_called_once()

    # Inference tests
    def test_infer_fails_when_not_loaded(self, adapter, mock_screenshot):
        """Test inference fails when model not loaded."""
        with pytest.raises(RuntimeError, match="not loaded"):
            adapter.infer(mock_screenshot)

    @patch('torch.cuda.is_available')
    @patch('torch.cuda.get_device_properties')
    def test_infer_timeout(
        self, mock_props, mock_cuda, adapter, mock_screenshot
    ):
        """Test inference respects timeout."""
        # Load model
        mock_cuda.return_value = True
        mock_props.return_value = Mock(total_memory=20e9)

        with patch('transformers.AutoModel.from_pretrained'), \
             patch('transformers.AutoTokenizer.from_pretrained'):
            adapter.load()

        # Mock slow inference
        adapter.model.generate = Mock(side_effect=lambda **kwargs: time.sleep(20))

        with pytest.raises(TimeoutError):
            adapter.infer(mock_screenshot, timeout=1.0)

    # Cleanup tests
    def test_unload(self, adapter):
        """Test model unloading."""
        # Setup loaded state
        adapter.model = Mock()
        adapter.tokenizer = Mock()
        adapter.is_loaded = True

        with patch('torch.cuda.empty_cache'):
            adapter.unload()

        assert adapter.model is None
        assert adapter.tokenizer is None
        assert adapter.is_loaded is False

    # Edge cases
    def test_load_twice_idempotent(self, adapter):
        """Test loading twice doesn't cause errors."""
        with patch('torch.cuda.is_available', return_value=True), \
             patch('torch.cuda.get_device_properties') as mock_props, \
             patch('transformers.AutoModel.from_pretrained'), \
             patch('transformers.AutoTokenizer.from_pretrained'):

            mock_props.return_value = Mock(total_memory=20e9)

            adapter.load()
            adapter.load()  # Should handle gracefully

            assert adapter.is_loaded is True

    def test_unload_when_not_loaded(self, adapter):
        """Test unloading when not loaded is safe."""
        adapter.unload()  # Should not crash
        assert adapter.is_loaded is False
```

### 4.2 Mocking Patterns

**Mock NVDA APIs**:

```python
# tests/conftest.py

import pytest
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def mock_nvda_modules():
    """Auto-mock NVDA modules in all tests."""
    import sys

    sys.modules['globalPluginHandler'] = MagicMock()
    sys.modules['api'] = MagicMock()
    sys.modules['speech'] = MagicMock()
    sys.modules['ui'] = MagicMock()
    sys.modules['scriptHandler'] = MagicMock()
    sys.modules['config'] = MagicMock()

    yield

    # Cleanup
    for module in ['globalPluginHandler', 'api', 'speech', 'ui', 'scriptHandler', 'config']:
        if module in sys.modules:
            del sys.modules[module]
```

**Mock Model Inference**:

```python
@pytest.fixture
def mock_model_response():
    """Mock model inference response."""
    return [
        UIElement(
            element_type="button",
            text="Submit",
            bbox=[100, 200, 150, 230],
            confidence=0.95,
            app_name="TestApp"
        ),
        UIElement(
            element_type="textbox",
            text="Enter name",
            bbox=[100, 100, 300, 130],
            confidence=0.87,
            app_name="TestApp"
        )
    ]

@pytest.fixture
def mock_vision_engine(mock_model_response):
    """Mock vision engine with predefined response."""
    engine = Mock()
    engine.infer_with_fallback.return_value = mock_model_response
    return engine
```

### 4.3 Parametrized Tests

```python
@pytest.mark.parametrize("confidence,expected_uncertain", [
    (0.95, False),
    (0.70, False),
    (0.69, True),
    (0.50, True),
    (0.10, True),
])
def test_confidence_threshold_annotation(confidence, expected_uncertain):
    """Test confidence threshold for uncertainty annotation."""
    element = UIElement(
        element_type="button",
        text="OK",
        bbox=[0, 0, 100, 50],
        confidence=confidence
    )

    speech_text = generate_speech_text(element)

    if expected_uncertain:
        assert "(uncertain)" in speech_text
    else:
        assert "(uncertain)" not in speech_text


@pytest.mark.parametrize("vram_gb,expected_model", [
    (24.0, "uitars-7b"),
    (16.0, "uitars-7b"),
    (8.0, "uitars-7b-quantized"),
    (6.0, "minicpm-v-2.6"),
    (4.0, "doubao-api"),
])
def test_model_selection_by_vram(vram_gb, expected_model):
    """Test model selection based on available VRAM."""
    with patch('torch.cuda.is_available', return_value=True), \
         patch('torch.cuda.get_device_properties') as mock_props:

        mock_props.return_value = Mock(total_memory=vram_gb * 1e9)

        detector = ModelDetector(model_dir=Path("/fake/path"), config={})
        adapter = detector.detect_best_adapter()

        assert expected_model in adapter.name.lower().replace(" ", "-")
```

### 4.4 Testing Exception Isolation

**Critical**: Verify plugin exceptions don't crash NVDA

```python
class TestExceptionIsolation:
    """Test that plugin exceptions are isolated from NVDA."""

    def test_script_exception_caught(self, plugin):
        """Test script exceptions don't propagate to NVDA."""
        # Make controller raise exception
        plugin.recognition_controller.recognize_screen_async = Mock(
            side_effect=RuntimeError("Test error")
        )

        mock_gesture = Mock()

        # Should NOT raise exception
        try:
            plugin.script_recognizeScreen(mock_gesture)
        except Exception as e:
            pytest.fail(f"Exception propagated to NVDA: {e}")

        # Verify error was logged
        # (check mock logger calls)

    def test_event_handler_exception_caught(self, plugin):
        """Test event handler exceptions don't crash NVDA."""
        plugin.config.auto_recognize = True
        plugin._trigger_recognition = Mock(
            side_effect=ValueError("Recognition failed")
        )

        mock_obj = Mock()
        mock_next_handler = Mock()

        # Should not raise
        plugin.event_gainFocus(mock_obj, mock_next_handler)

        # Verify nextHandler was still called
        mock_next_handler.assert_called_once()

    def test_background_thread_exception_isolated(self):
        """Test background thread exceptions don't crash main thread."""
        def failing_worker():
            raise RuntimeError("Worker thread error")

        thread = threading.Thread(target=failing_worker, daemon=True)
        thread.start()
        thread.join(timeout=1.0)

        # Main thread should still be alive
        assert threading.main_thread().is_alive()
```

---

## 5. Integration Testing

### 5.1 Recognition Flow Integration

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


class TestRecognitionFlowIntegration:
    """Integration tests for full recognition flow."""

    @pytest.fixture
    def test_screenshot_path(self, tmp_path):
        """Create test screenshot file."""
        # Create test image with UI elements
        img_array = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        image = Image.fromarray(img_array)

        screenshot_path = tmp_path / "test_ui.png"
        image.save(screenshot_path)

        return screenshot_path

    @pytest.fixture
    def components(self, tmp_path):
        """Initialize all components."""
        config = {
            "model_dir": tmp_path / "models",
            "cache_dir": tmp_path / "cache",
            "cache_ttl": 300,
            "timeout": 15.0,
            "confidence_threshold": 0.7,
        }

        # Create component instances
        model_detector = ModelDetector(
            model_dir=config["model_dir"],
            config=config
        )

        vision_engine = VisionEngine(model_detector=model_detector)
        screenshot_service = ScreenshotService()
        cache_manager = CacheManager(ttl_seconds=config["cache_ttl"])

        controller = RecognitionController(
            vision_engine=vision_engine,
            screenshot_service=screenshot_service,
            cache_manager=cache_manager
        )

        return {
            "controller": controller,
            "vision_engine": vision_engine,
            "screenshot_service": screenshot_service,
            "cache_manager": cache_manager,
        }

    def test_full_recognition_flow(self, components, test_screenshot_path):
        """Test complete flow: capture → infer → cache → return."""
        controller = components["controller"]

        result_received = None
        error_received = None

        def on_success(result):
            nonlocal result_received
            result_received = result

        def on_error(error):
            nonlocal error_received
            error_received = error

        # Trigger recognition
        controller.recognize_screen_async(
            callback=on_success,
            error_callback=on_error
        )

        # Wait for completion
        import time
        max_wait = 20.0
        elapsed = 0.0

        while result_received is None and error_received is None and elapsed < max_wait:
            time.sleep(0.1)
            elapsed += 0.1

        # Assertions
        assert error_received is None, f"Recognition failed: {error_received}"
        assert result_received is not None
        assert isinstance(result_received.elements, list)
        assert result_received.inference_time > 0
        assert result_received.model_name in ["uitars-7b", "minicpm-v-2.6", "doubao-api"]

    def test_cache_hit_performance(self, components, test_screenshot_path):
        """Test cache improves performance on repeated recognition."""
        screenshot_service = components["screenshot_service"]
        vision_engine = components["vision_engine"]
        cache_manager = components["cache_manager"]

        # First recognition (cache miss)
        screenshot = screenshot_service.capture_from_file(test_screenshot_path)

        import time
        start = time.time()
        result1 = vision_engine.infer_with_fallback(screenshot, timeout=15.0)
        first_time = time.time() - start

        # Store in cache
        cache_manager.put(screenshot.hash, result1)

        # Second recognition (cache hit)
        start = time.time()
        result2 = cache_manager.get(screenshot.hash)
        second_time = time.time() - start

        # Cache should be much faster
        assert second_time < first_time / 10  # At least 10x faster
        assert result2.screenshot_hash == result1.screenshot_hash

    def test_model_fallback_chain(self, components):
        """Test graceful degradation through model fallback chain."""
        vision_engine = components["vision_engine"]

        # Create screenshot that causes GPU model to fail
        screenshot = Screenshot(
            hash="test_fallback",
            image_data=Image.new("RGB", (1920, 1080)),
            width=1920,
            height=1080
        )

        # Mock GPU model to fail
        with patch.object(
            vision_engine.primary_adapter,
            'infer',
            side_effect=TimeoutError("GPU model timed out")
        ):
            # Should fall back to CPU model or cloud API
            elements = vision_engine.infer_with_fallback(screenshot)

            # Should still get results
            assert isinstance(elements, list)
            # May be empty if all models unavailable in test environment
```

### 5.2 NVDA Integration Tests

```python
# tests/integration/test_nvda_integration.py

class TestNVDAIntegration:
    """Integration tests for NVDA plugin interaction."""

    @pytest.fixture
    def plugin_with_mocked_nvda(self, mock_nvda_modules):
        """Create plugin instance with mocked NVDA APIs."""
        from addon.globalPlugins.nvdaVision import GlobalPlugin

        with patch('addon.globalPlugins.nvdaVision.core.recognition_controller.RecognitionController'):
            plugin = GlobalPlugin()
            return plugin

    def test_shortcut_registration(self, plugin_with_mocked_nvda):
        """Test keyboard shortcuts are registered correctly."""
        plugin = plugin_with_mocked_nvda

        # Verify script methods exist
        assert hasattr(plugin, 'script_recognizeScreen')
        assert hasattr(plugin, 'script_recognizeAtCursor')
        assert hasattr(plugin, 'script_nextElement')
        assert hasattr(plugin, 'script_previousElement')

    def test_speech_output_on_recognition(self, plugin_with_mocked_nvda):
        """Test speech output is generated on recognition complete."""
        plugin = plugin_with_mocked_nvda

        # Mock result
        mock_result = Mock()
        mock_result.elements = [
            UIElement("button", "OK", [100, 200, 150, 230], 0.95),
            UIElement("textbox", "Name", [100, 100, 300, 130], 0.87),
        ]

        # Trigger callback
        plugin._on_recognition_complete(mock_result)

        # Verify speech was called
        # (check mock speech.speak calls)

    def test_event_handler_chain(self, plugin_with_mocked_nvda):
        """Test event handlers call nextHandler."""
        plugin = plugin_with_mocked_nvda

        mock_obj = Mock()
        mock_next_handler = Mock()

        # Trigger focus event
        plugin.event_gainFocus(mock_obj, mock_next_handler)

        # Verify nextHandler was called
        mock_next_handler.assert_called_once()
```

### 5.3 Screenshot Capture Integration

```python
# tests/integration/test_screenshot_capture.py

class TestScreenshotCaptureIntegration:
    """Integration tests for screenshot capture."""

    def test_capture_active_window(self):
        """Test capturing active window screenshot."""
        service = ScreenshotService()

        screenshot = service.capture_active_window()

        assert screenshot is not None
        assert screenshot.width > 0
        assert screenshot.height > 0
        assert screenshot.image_data is not None
        assert screenshot.hash is not None
        assert len(screenshot.hash) == 64  # SHA-256

    def test_capture_specific_region(self):
        """Test capturing specific screen region."""
        service = ScreenshotService()

        region = (100, 100, 500, 500)  # x1, y1, x2, y2
        screenshot = service.capture_region(region)

        assert screenshot.width == 400
        assert screenshot.height == 400

    def test_screenshot_hash_consistency(self):
        """Test same screenshot produces same hash."""
        service = ScreenshotService()

        # Create identical images
        img1 = Image.new("RGB", (100, 100), color="red")
        img2 = Image.new("RGB", (100, 100), color="red")

        hash1 = service.compute_hash(img1)
        hash2 = service.compute_hash(img2)

        assert hash1 == hash2

    def test_screenshot_hash_difference(self):
        """Test different screenshots produce different hashes."""
        service = ScreenshotService()

        img1 = Image.new("RGB", (100, 100), color="red")
        img2 = Image.new("RGB", (100, 100), color="blue")

        hash1 = service.compute_hash(img1)
        hash2 = service.compute_hash(img2)

        assert hash1 != hash2
```

---

## 6. End-to-End Testing

### 6.1 User Workflow Tests

```python
# tests/e2e/test_user_workflows.py

import pytest
from pathlib import Path

class TestUserWorkflowsE2E:
    """End-to-end tests for complete user workflows."""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_first_time_user_workflow(self):
        """Test: New user installs plugin and performs first recognition.

        Steps:
        1. Install plugin in NVDA
        2. Press NVDA+Shift+V to trigger recognition
        3. Wait for progress feedback after 5 seconds
        4. Receive recognition results
        5. Navigate through elements with NVDA+Shift+N
        """
        # This test requires real NVDA running
        # Use NVDA automation APIs

        from nvda_test_automation import NVDAInstance

        with NVDAInstance() as nvda:
            # Step 1: Verify plugin loaded
            assert nvda.is_plugin_loaded("nvdaVision")

            # Step 2: Open a test application
            nvda.launch_application("notepad.exe")
            nvda.wait_for_window_title("Notepad")

            # Step 3: Trigger recognition
            nvda.press_keys("NVDA+Shift+V")

            # Step 4: Wait for feedback
            feedback = nvda.wait_for_speech(timeout=6.0)
            assert "recognizing" in feedback.lower()

            # Step 5: Wait for results
            result = nvda.wait_for_speech(timeout=20.0)
            assert "found" in result.lower() and "elements" in result.lower()

            # Step 6: Navigate elements
            nvda.press_keys("NVDA+Shift+N")
            element_info = nvda.get_last_speech()
            assert any(word in element_info for word in ["button", "textbox", "link"])

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_recognition_with_timeout(self):
        """Test: Recognition provides progress feedback and handles timeout.

        Verifies real.md constraint 6: Progress after 5s, degradation after 15s
        """
        from nvda_test_automation import NVDAInstance

        with NVDAInstance() as nvda:
            nvda.launch_application("notepad.exe")

            # Trigger recognition
            nvda.press_keys("NVDA+Shift+V")

            # Wait for 5 seconds
            import time
            time.sleep(5.5)

            # Should hear progress feedback
            speech = nvda.get_speech_history(last_n=2)
            assert any("please wait" in s.lower() or "recognizing" in s.lower()
                      for s in speech)

    @pytest.mark.e2e
    def test_keyboard_only_operation(self):
        """Test: All features accessible via keyboard only.

        Verifies real.md constraint 4: WCAG 2.1 AA compliance
        """
        from nvda_test_automation import NVDAInstance

        with NVDAInstance() as nvda:
            # All operations should work without mouse
            nvda.press_keys("NVDA+Shift+V")  # Recognize screen
            nvda.wait_for_speech(timeout=2.0)

            nvda.press_keys("NVDA+Shift+C")  # Recognize at cursor
            nvda.wait_for_speech(timeout=2.0)

            nvda.press_keys("NVDA+Shift+N")  # Next element
            nvda.wait_for_speech(timeout=1.0)

            nvda.press_keys("NVDA+Shift+P")  # Previous element
            nvda.wait_for_speech(timeout=1.0)

            # All operations completed without mouse

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_plugin_crash_does_not_crash_nvda(self):
        """Test: Plugin exceptions don't crash NVDA core.

        Verifies real.md constraint 5: Stability
        """
        from nvda_test_automation import NVDAInstance

        with NVDAInstance() as nvda:
            # Cause plugin error (e.g., corrupt model file)
            # ... setup error condition ...

            # Trigger recognition
            nvda.press_keys("NVDA+Shift+V")

            # Wait for error message
            time.sleep(3.0)

            # NVDA should still be responsive
            assert nvda.is_responsive()

            # Other NVDA functions should work
            nvda.press_keys("NVDA+T")  # Read title
            title = nvda.get_last_speech()
            assert len(title) > 0
```

### 6.2 Application-Specific Tests

```python
# tests/e2e/test_app_specific.py

@pytest.mark.parametrize("app_name,app_path,expected_elements", [
    ("Feishu", "C:\\Program Files\\Feishu\\Feishu.exe", ["button", "textbox"]),
    ("DingTalk", "C:\\Program Files\\DingTalk\\DingTalk.exe", ["button", "link"]),
    ("WeChat", "C:\\Program Files\\WeChat\\WeChat.exe", ["button", "textbox"]),
])
def test_app_specific_recognition(app_name, app_path, expected_elements):
    """Test recognition works with specific applications."""
    from nvda_test_automation import NVDAInstance

    with NVDAInstance() as nvda:
        # Launch app
        nvda.launch_application(app_path)
        nvda.wait_for_window_title(app_name, timeout=10.0)

        # Trigger recognition
        nvda.press_keys("NVDA+Shift+V")

        # Wait for results
        result = nvda.wait_for_speech(timeout=20.0)

        # Verify expected element types found
        for element_type in expected_elements:
            assert element_type in result.lower()
```

---

## 7. Security Testing

### 7.1 API Key Encryption Tests

```python
# tests/security/test_api_key_encryption.py

import pytest
from pathlib import Path

from addon.globalPlugins.nvdaVision.security.encryption import DPAPIEncryption
from addon.globalPlugins.nvdaVision.infrastructure.config_loader import ConfigManager


class TestAPIKeyEncryption:
    """Security tests for API key encryption.

    Verifies real.md constraint 2: API keys encrypted with DPAPI
    """

    def test_dpapi_encrypt_decrypt_roundtrip(self):
        """Test DPAPI encryption and decryption works."""
        plaintext = "sk-test-key-123456789abcdef"

        # Encrypt
        encrypted = DPAPIEncryption.encrypt(plaintext)

        # Verify encrypted is different
        assert encrypted != plaintext
        assert len(encrypted) > len(plaintext)

        # Decrypt
        decrypted = DPAPIEncryption.decrypt(encrypted)

        # Verify roundtrip
        assert decrypted == plaintext

    def test_encrypted_key_not_readable(self):
        """Test encrypted key is not human-readable."""
        plaintext = "sk-test-key-sensitive"
        encrypted = DPAPIEncryption.encrypt(plaintext)

        # Should not contain plaintext substring
        assert plaintext not in encrypted
        assert "sk-" not in encrypted

    def test_config_saves_encrypted_key(self, tmp_path):
        """Test ConfigManager saves keys in encrypted form."""
        config_path = tmp_path / "config.yaml"
        config = ConfigManager(config_path=config_path)

        # Save API key
        plaintext_key = "sk-sensitive-key-12345"
        config.save_api_key("doubao_api_key", plaintext_key)

        # Read config file
        config_text = config_path.read_text()

        # Plaintext should NOT appear in file
        assert plaintext_key not in config_text
        assert "doubao_api_key_encrypted" in config_text

    def test_config_loads_encrypted_key(self, tmp_path):
        """Test ConfigManager loads and decrypts keys."""
        config_path = tmp_path / "config.yaml"
        config1 = ConfigManager(config_path=config_path)

        # Save key
        original_key = "sk-test-load-decrypt"
        config1.save_api_key("test_api_key", original_key)

        # Create new instance (reload from file)
        config2 = ConfigManager(config_path=config_path)

        # Should have decrypted key in memory
        loaded_key = config2.get("test_api_key")
        assert loaded_key == original_key

    def test_tampering_detection(self, tmp_path):
        """Test tampering with encrypted key is detected."""
        config_path = tmp_path / "config.yaml"
        config = ConfigManager(config_path=config_path)

        config.save_api_key("test_key", "sk-original")

        # Tamper with encrypted value
        import yaml
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)

        data['security']['test_key_encrypted'] = "TAMPERED_VALUE"

        with open(config_path, 'w') as f:
            yaml.safe_dump(data, f)

        # Try to load tampered config
        config2 = ConfigManager(config_path=config_path)

        # Should fail to decrypt or return None
        with pytest.raises(RuntimeError):
            config2.get("test_key")
```

### 7.2 Screenshot Privacy Tests

```python
# tests/security/test_screenshot_privacy.py

class TestScreenshotPrivacy:
    """Security tests for screenshot privacy.

    Verifies real.md constraint 1: Local processing first, cloud opt-in
    """

    def test_local_processing_by_default(self):
        """Test screenshots processed locally by default."""
        config = ConfigManager()

        # Default config should disable cloud
        assert config.get("enable_cloud_api") is False
        assert config.get("privacy.local_processing_only") is True

    def test_cloud_api_requires_consent(self):
        """Test cloud API only called with explicit consent."""
        engine = VisionEngine(model_detector=mock_detector)

        # Mock all local models to fail
        with patch.object(engine.primary_adapter, 'infer',
                         side_effect=RuntimeError("Local failed")):

            # Without consent, should not call cloud
            screenshot = Screenshot(...)

            with patch('addon.globalPlugins.nvdaVision.models.doubao_adapter.DoubaoAPIAdapter') as mock_cloud:
                result = engine.infer_with_fallback(screenshot)

                # Cloud adapter should NOT be called
                mock_cloud.assert_not_called()

    def test_screenshot_sanitization_before_cloud(self):
        """Test screenshots are sanitized before cloud upload."""
        sanitizer = ScreenshotSanitizer()

        # Create screenshot with "sensitive" content
        original_image = Image.open("tests/fixtures/sensitive_screenshot.png")

        # Sanitize
        sanitized_image = sanitizer.downscale(original_image, max_size=1280)

        # Verify size reduced
        assert max(sanitized_image.size) <= 1280
        assert sanitized_image.size[0] < original_image.size[0]

    def test_api_keys_not_in_logs(self, caplog):
        """Test API keys never appear in logs."""
        import logging
        caplog.set_level(logging.DEBUG)

        # Load config with API key
        config = ConfigManager()
        config.save_api_key("test_key", "sk-sensitive-12345")

        # Trigger logging
        logger.info(f"Loaded config: {config.get('test_key')}")

        # Check logs
        for record in caplog.records:
            assert "sk-sensitive-12345" not in record.message
            # Masked version OK: "sk-se...345"

    def test_screenshot_data_not_in_logs(self, caplog):
        """Test screenshot image data never appears in logs."""
        import logging
        caplog.set_level(logging.DEBUG)

        screenshot = Screenshot(
            hash="test",
            image_data=Image.new("RGB", (100, 100)),
            width=100,
            height=100
        )

        # Log screenshot metadata
        logger.info(f"Captured screenshot: {screenshot.width}x{screenshot.height}")

        # Logs should have metadata but not image data
        for record in caplog.records:
            assert "width" in record.message or "height" in record.message
            assert "<Image" not in record.message  # PIL Image repr
```

### 7.3 Penetration Testing Checklist

**Manual Security Tests** (run by security engineer):

- [ ] **API Key Extraction**: Cannot extract plaintext keys from config file
- [ ] **Memory Dumps**: Keys encrypted in memory, not recoverable from dumps
- [ ] **Log File Analysis**: No sensitive data (keys, screenshot content) in logs
- [ ] **Network Sniffing**: Cloud API traffic uses HTTPS, no plaintext keys in headers
- [ ] **File Permission**: Config files have appropriate Windows ACLs
- [ ] **Privilege Escalation**: Plugin doesn't request unnecessary permissions
- [ ] **Dependency Vulnerabilities**: All dependencies scanned with `safety` / `pip-audit`

---

## 8. Performance Testing

### 8.1 Inference Time Benchmarks

```python
# tests/performance/test_inference_performance.py

import pytest
import time
from pathlib import Path

class TestInferencePerformance:
    """Performance tests for model inference.

    Benchmarks from sys.spec.md:
    - UI-TARS 7B (GPU): 3-5 seconds
    - MiniCPM-V 2.6 (CPU): 5-8 seconds
    - Doubao API: 1-2 seconds (network dependent)
    """

    @pytest.fixture
    def test_screenshot(self):
        """Load standard test screenshot."""
        image = Image.open("tests/fixtures/standard_ui_1920x1080.png")
        return Screenshot(
            hash="perf_test",
            image_data=image,
            width=1920,
            height=1080
        )

    @pytest.mark.performance
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="GPU required")
    def test_uitars_inference_time(self, test_screenshot):
        """Test UI-TARS inference meets SLA: <5 seconds."""
        adapter = UITarsAdapter(model_path=Path("models/uitars-7b"))
        adapter.load()

        start = time.time()
        elements = adapter.infer(test_screenshot, timeout=15.0)
        elapsed = time.time() - start

        adapter.unload()

        # Verify SLA
        assert elapsed < 5.0, f"UI-TARS too slow: {elapsed:.2f}s"
        assert len(elements) > 0

    @pytest.mark.performance
    def test_minicpm_inference_time(self, test_screenshot):
        """Test MiniCPM inference meets SLA: <8 seconds."""
        adapter = MiniCPMAdapter(model_path=Path("models/minicpm-v-2.6"))
        adapter.load()

        start = time.time()
        elements = adapter.infer(test_screenshot, timeout=15.0)
        elapsed = time.time() - start

        adapter.unload()

        assert elapsed < 8.0, f"MiniCPM too slow: {elapsed:.2f}s"
        assert len(elements) > 0

    @pytest.mark.performance
    def test_progress_feedback_timing(self):
        """Test progress feedback appears after 5 seconds.

        Verifies real.md constraint 6.
        """
        controller = RecognitionController(...)

        feedback_received = []

        def progress_callback(message):
            feedback_received.append((time.time(), message))

        controller.progress_callback = progress_callback

        # Start long-running recognition
        start = time.time()
        controller.recognize_screen_async(...)

        # Wait 6 seconds
        time.sleep(6.0)

        # Should have received progress feedback
        assert len(feedback_received) > 0
        first_feedback_time, _ = feedback_received[0]
        time_to_first_feedback = first_feedback_time - start

        # Should be ~5 seconds (allow 0.5s tolerance)
        assert 4.5 <= time_to_first_feedback <= 6.0
```

### 8.2 Memory Usage Tests

```python
# tests/performance/test_memory_usage.py

import psutil
import pytest

class TestMemoryUsage:
    """Performance tests for memory usage."""

    @pytest.mark.performance
    def test_model_loading_memory_usage(self):
        """Test model loading memory is within limits.

        From sys.spec.md:
        - UI-TARS 7B: ~16GB VRAM + 4GB RAM
        - MiniCPM-V 2.6: ~6GB RAM
        """
        process = psutil.Process()

        # Measure baseline
        baseline_memory = process.memory_info().rss / 1e9  # GB

        # Load UI-TARS
        adapter = UITarsAdapter(model_path=Path("models/uitars-7b"))

        if torch.cuda.is_available():
            adapter.load()

            # Measure after loading
            loaded_memory = process.memory_info().rss / 1e9
            memory_increase = loaded_memory - baseline_memory

            # Should not exceed 5GB RAM increase (most data on GPU)
            assert memory_increase < 5.0, \
                f"Excessive RAM usage: {memory_increase:.2f}GB"

            # Check VRAM
            vram_used = torch.cuda.memory_allocated(0) / 1e9
            assert vram_used < 18.0, \
                f"Excessive VRAM usage: {vram_used:.2f}GB"

            adapter.unload()

    @pytest.mark.performance
    def test_memory_leak_detection(self):
        """Test for memory leaks in repeated inference."""
        process = psutil.Process()

        adapter = UITarsAdapter(model_path=Path("models/uitars-7b"))
        adapter.load()

        screenshot = Screenshot(...)

        # Measure baseline
        baseline = process.memory_info().rss / 1e9

        # Run 100 inferences
        for i in range(100):
            elements = adapter.infer(screenshot)

            # Force garbage collection
            import gc
            gc.collect()

        # Measure final
        final = process.memory_info().rss / 1e9
        increase = final - baseline

        adapter.unload()

        # Should not leak more than 500MB
        assert increase < 0.5, \
            f"Memory leak detected: {increase:.2f}GB increase"

    @pytest.mark.performance
    def test_cache_memory_limit(self):
        """Test cache respects memory limits."""
        cache = CacheManager(ttl_seconds=300, max_size=100)

        # Fill cache with 100 entries
        for i in range(100):
            screenshot_hash = f"hash_{i}"
            result = RecognitionResult(...)
            cache.put(screenshot_hash, result)

        # Add 101st entry
        cache.put("hash_100", RecognitionResult(...))

        # Cache should evict oldest entry
        assert len(cache._cache) == 100

        # Oldest entry should be gone
        assert cache.get("hash_0") is None
```

### 8.3 Load Testing

```python
# tests/performance/test_load.py

@pytest.mark.performance
@pytest.mark.slow
def test_concurrent_recognition_requests():
    """Test system handles concurrent recognition requests."""
    import concurrent.futures

    controller = RecognitionController(...)
    screenshot = Screenshot(...)

    results = []
    errors = []

    def recognize():
        try:
            result = controller.recognize_screen_sync(screenshot)
            results.append(result)
        except Exception as e:
            errors.append(e)

    # Run 10 concurrent recognitions
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(recognize) for _ in range(10)]
        concurrent.futures.wait(futures)

    # All should succeed (or gracefully fail)
    assert len(results) + len(errors) == 10
    assert len(errors) == 0  # No crashes
```

---

## 9. Accessibility Testing

### 9.1 WCAG 2.1 AA Compliance Tests

```python
# tests/accessibility/test_wcag_compliance.py

class TestWCAGCompliance:
    """Accessibility tests for WCAG 2.1 AA compliance.

    Verifies real.md constraint 4.
    """

    def test_all_features_keyboard_accessible(self):
        """Test all features can be accessed via keyboard only.

        WCAG 2.1.1: Keyboard (Level A)
        """
        from nvda_test_automation import NVDAInstance

        with NVDAInstance() as nvda:
            # Recognition
            nvda.press_keys("NVDA+Shift+V")
            assert nvda.wait_for_speech(timeout=2.0)

            # Navigation
            nvda.press_keys("NVDA+Shift+N")
            assert nvda.wait_for_speech(timeout=1.0)

            nvda.press_keys("NVDA+Shift+P")
            assert nvda.wait_for_speech(timeout=1.0)

            # Settings (if GUI exists)
            # ... test keyboard navigation ...

    def test_keyboard_focus_visible(self):
        """Test keyboard focus is visible in GUI.

        WCAG 2.4.7: Focus Visible (Level AA)
        """
        # If plugin has GUI dialogs
        # ... test focus indicators ...

    def test_speech_output_for_all_actions(self):
        """Test all user actions provide audio feedback.

        WCAG 1.3.1: Info and Relationships (Level A)
        """
        from nvda_test_automation import NVDAInstance

        with NVDAInstance() as nvda:
            # Every action should produce speech

            # Start recognition
            nvda.press_keys("NVDA+Shift+V")
            feedback = nvda.get_last_speech()
            assert len(feedback) > 0

            # Navigate element
            nvda.press_keys("NVDA+Shift+N")
            feedback = nvda.get_last_speech()
            assert len(feedback) > 0

    def test_error_messages_descriptive(self):
        """Test error messages are descriptive and actionable.

        WCAG 3.3.1: Error Identification (Level A)
        WCAG 3.3.3: Error Suggestion (Level AA)
        """
        # Trigger error condition
        # ... cause model loading to fail ...

        from nvda_test_automation import NVDAInstance

        with NVDAInstance() as nvda:
            nvda.press_keys("NVDA+Shift+V")
            error_message = nvda.wait_for_speech(timeout=5.0)

            # Error should be descriptive
            assert "error" in error_message.lower() or "failed" in error_message.lower()

            # Should provide guidance
            # e.g., "Recognition failed. Check logs for details."
```

### 9.2 Screen Reader Testing

```python
# tests/accessibility/test_screen_reader_compatibility.py

class TestScreenReaderCompatibility:
    """Test compatibility with NVDA screen reader."""

    def test_speech_output_format(self):
        """Test speech output follows best practices."""
        element = UIElement(
            element_type="button",
            text="Submit Form",
            bbox=[100, 200, 200, 250],
            confidence=0.92
        )

        speech_text = generate_speech_text(element)

        # Should include element type
        assert "button" in speech_text.lower()

        # Should include text
        assert "Submit Form" in speech_text

        # Should include position
        assert "position" in speech_text.lower()

        # Should NOT include technical details
        assert "bbox" not in speech_text.lower()
        assert "0.92" not in speech_text  # Confidence in different format

    def test_uncertainty_annotation(self):
        """Test low-confidence results are clearly marked.

        Verifies real.md constraint 3.
        """
        # High confidence - no annotation
        element_high = UIElement(
            element_type="button",
            text="OK",
            bbox=[0, 0, 100, 50],
            confidence=0.95
        )

        speech_high = generate_speech_text(element_high)
        assert "(uncertain)" not in speech_high

        # Low confidence - annotation required
        element_low = UIElement(
            element_type="button",
            text="OK",
            bbox=[0, 0, 100, 50],
            confidence=0.65
        )

        speech_low = generate_speech_text(element_low)
        assert "(uncertain)" in speech_low.lower()

    def test_progress_feedback_audio(self):
        """Test progress feedback is provided via speech.

        Verifies real.md constraint 6.
        """
        from nvda_test_automation import NVDAInstance

        with NVDAInstance() as nvda:
            # Trigger long recognition
            nvda.press_keys("NVDA+Shift+V")

            # Wait for progress feedback
            time.sleep(5.5)

            # Should hear progress message
            speech_history = nvda.get_speech_history(last_n=5)
            progress_keywords = ["recognizing", "please wait", "processing"]

            assert any(
                any(keyword in msg.lower() for keyword in progress_keywords)
                for msg in speech_history
            )
```

---

## 10. NVDA-Specific Testing

### 10.1 Plugin Lifecycle Tests

```python
# tests/nvda/test_plugin_lifecycle.py

class TestPluginLifecycle:
    """Test NVDA plugin lifecycle management."""

    def test_plugin_initialization(self):
        """Test plugin initializes correctly."""
        from addon.globalPlugins.nvdaVision import GlobalPlugin

        plugin = GlobalPlugin()

        # Should initialize without crashing
        assert plugin is not None
        assert hasattr(plugin, 'recognition_controller')
        assert hasattr(plugin, 'event_coordinator')
        assert hasattr(plugin, 'config')

    def test_plugin_termination(self):
        """Test plugin cleans up resources on termination."""
        from addon.globalPlugins.nvdaVision import GlobalPlugin

        plugin = GlobalPlugin()

        # Mock model loaded
        plugin.recognition_controller.vision_engine.primary_adapter = Mock()
        plugin.recognition_controller.vision_engine.primary_adapter.is_loaded = True

        # Terminate
        plugin.terminate()

        # Should have cleaned up
        assert plugin.recognition_controller.vision_engine.primary_adapter.unload.called

    def test_plugin_reload(self):
        """Test plugin can be reloaded without issues."""
        from addon.globalPlugins.nvdaVision import GlobalPlugin

        # Create and terminate first instance
        plugin1 = GlobalPlugin()
        plugin1.terminate()

        # Create second instance (reload)
        plugin2 = GlobalPlugin()

        # Should work without errors
        assert plugin2 is not None
```

### 10.2 Script Handler Tests

```python
# tests/nvda/test_script_handlers.py

class TestScriptHandlers:
    """Test NVDA script handlers."""

    def test_recognize_screen_script(self, plugin):
        """Test recognize screen script triggers recognition."""
        mock_gesture = Mock()

        plugin.script_recognizeScreen(mock_gesture)

        # Should trigger async recognition
        plugin.recognition_controller.recognize_screen_async.assert_called_once()

    def test_recognize_at_cursor_script(self, plugin):
        """Test recognize at cursor script uses cursor position."""
        mock_gesture = Mock()

        with patch('api.getCursorPos', return_value=(500, 300)):
            plugin.script_recognizeAtCursor(mock_gesture)

        # Should call recognize_at_point with cursor coords
        plugin.recognition_controller.recognize_at_point_async.assert_called_with(
            x=500,
            y=300,
            callback=plugin._on_element_recognized,
            error_callback=plugin._on_recognition_error
        )

    def test_navigation_scripts(self, plugin):
        """Test element navigation scripts."""
        # Mock elements
        plugin.recognition_controller.get_next_element = Mock(
            return_value=UIElement("button", "Next", [0, 0, 100, 50], 0.9)
        )

        # Next element
        plugin.script_nextElement(Mock())
        plugin.recognition_controller.get_next_element.assert_called_once()

        # Previous element
        plugin.recognition_controller.get_previous_element = Mock(
            return_value=UIElement("button", "Prev", [0, 0, 100, 50], 0.9)
        )
        plugin.script_previousElement(Mock())
        plugin.recognition_controller.get_previous_element.assert_called_once()
```

### 10.3 Event Handler Tests

```python
# tests/nvda/test_event_handlers.py

class TestEventHandlers:
    """Test NVDA event handlers."""

    def test_event_gain_focus_triggers_recognition(self, plugin):
        """Test focus event can trigger recognition if configured."""
        plugin.config.auto_recognize_on_focus = True

        mock_obj = Mock()
        mock_obj.name = ""  # No accessible name
        mock_next_handler = Mock()

        plugin.event_gainFocus(mock_obj, mock_next_handler)

        # Should trigger recognition for unnamed elements
        # (implementation dependent)

        # Always calls nextHandler
        mock_next_handler.assert_called_once()

    def test_event_handler_calls_next_handler(self, plugin):
        """Test event handlers always call nextHandler.

        Critical for plugin ecosystem compatibility.
        """
        mock_obj = Mock()
        mock_next_handler = Mock()

        # Even if plugin logic fails
        plugin._trigger_recognition = Mock(side_effect=RuntimeError("Error"))

        plugin.event_gainFocus(mock_obj, mock_next_handler)

        # nextHandler MUST still be called
        mock_next_handler.assert_called_once()
```

---

## 11. Vision Model Testing

### 11.1 Model Loading Tests

```python
# tests/models/test_model_loading.py

class TestModelLoading:
    """Test vision model loading."""

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="GPU required")
    def test_uitars_loads_on_gpu(self):
        """Test UI-TARS loads on GPU when available."""
        adapter = UITarsAdapter(model_path=Path("models/uitars-7b"))

        adapter.load()

        assert adapter.is_loaded
        assert adapter.model is not None

        # Verify on GPU
        assert next(adapter.model.parameters()).device.type == "cuda"

        adapter.unload()

    def test_minicpm_loads_on_cpu(self):
        """Test MiniCPM loads on CPU."""
        adapter = MiniCPMAdapter(model_path=Path("models/minicpm-v-2.6"))

        adapter.load()

        assert adapter.is_loaded
        assert adapter.model is not None

        # Verify on CPU
        assert next(adapter.model.parameters()).device.type == "cpu"

        adapter.unload()

    def test_model_loading_failure_handling(self):
        """Test graceful handling of model loading failures."""
        adapter = UITarsAdapter(model_path=Path("nonexistent/path"))

        with pytest.raises(RuntimeError):
            adapter.load()

        # Should not be marked as loaded
        assert adapter.is_loaded is False
```

### 11.2 Model Inference Tests

```python
# tests/models/test_model_inference.py

class TestModelInference:
    """Test vision model inference."""

    @pytest.fixture
    def real_screenshot(self):
        """Load real UI screenshot for testing."""
        return Image.open("tests/fixtures/windows_ui_sample.png")

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="GPU required")
    def test_uitars_inference_output_format(self, real_screenshot):
        """Test UI-TARS returns correct output format."""
        adapter = UITarsAdapter(model_path=Path("models/uitars-7b"))
        adapter.load()

        screenshot = Screenshot(
            hash="test",
            image_data=real_screenshot,
            width=real_screenshot.width,
            height=real_screenshot.height
        )

        elements = adapter.infer(screenshot, timeout=15.0)

        # Verify output format
        assert isinstance(elements, list)
        assert all(isinstance(e, UIElement) for e in elements)

        # Each element should have required fields
        for element in elements:
            assert element.element_type in [
                "button", "textbox", "link", "text",
                "checkbox", "radio", "dropdown", "image"
            ]
            assert isinstance(element.text, str)
            assert len(element.bbox) == 4
            assert 0.0 <= element.confidence <= 1.0

        adapter.unload()

    def test_inference_confidence_scores(self):
        """Test all inference results include confidence scores.

        Verifies real.md constraint 3.
        """
        adapter = UITarsAdapter(model_path=Path("models/uitars-7b"))
        adapter.load()

        screenshot = Screenshot(...)
        elements = adapter.infer(screenshot)

        # All elements must have confidence scores
        for element in elements:
            assert hasattr(element, 'confidence')
            assert 0.0 <= element.confidence <= 1.0

        adapter.unload()

    def test_inference_timeout_respected(self):
        """Test inference respects timeout parameter."""
        adapter = UITarsAdapter(model_path=Path("models/uitars-7b"))
        adapter.load()

        screenshot = Screenshot(...)

        start = time.time()
        try:
            adapter.infer(screenshot, timeout=5.0)
        except TimeoutError:
            pass
        elapsed = time.time() - start

        # Should timeout around 5 seconds (allow 1s tolerance)
        assert elapsed < 6.0

        adapter.unload()
```

### 11.3 Model Fallback Tests

```python
# tests/models/test_model_fallback.py

class TestModelFallback:
    """Test model fallback chain.

    Verifies real.md constraint 1: Local first, cloud fallback.
    """

    def test_fallback_gpu_to_cpu(self):
        """Test fallback from GPU to CPU model."""
        vision_engine = VisionEngine(model_detector=mock_detector)

        # Mock GPU model failure
        vision_engine.primary_adapter.infer = Mock(
            side_effect=RuntimeError("GPU model failed")
        )

        # Mock CPU model success
        vision_engine.backup_adapters[0].infer = Mock(
            return_value=[UIElement(...)]
        )

        screenshot = Screenshot(...)
        elements = vision_engine.infer_with_fallback(screenshot)

        # Should have fallen back to CPU
        assert len(elements) > 0
        vision_engine.backup_adapters[0].infer.assert_called_once()

    def test_fallback_cpu_to_cloud(self):
        """Test fallback from CPU to cloud API."""
        vision_engine = VisionEngine(model_detector=mock_detector)

        # Mock both local models fail
        vision_engine.primary_adapter.infer = Mock(side_effect=RuntimeError)
        vision_engine.backup_adapters[0].infer = Mock(side_effect=RuntimeError)

        # Mock cloud API success
        vision_engine.backup_adapters[1].infer = Mock(
            return_value=[UIElement(...)]
        )

        screenshot = Screenshot(...)
        elements = vision_engine.infer_with_fallback(screenshot)

        # Should have fallen back to cloud
        assert len(elements) > 0
        vision_engine.backup_adapters[1].infer.assert_called_once()

    def test_cloud_requires_user_consent(self):
        """Test cloud API only called with user consent.

        Verifies real.md constraint 1.
        """
        vision_engine = VisionEngine(model_detector=mock_detector)

        # Disable cloud consent
        vision_engine.config['enable_cloud_api'] = False

        # Mock all local models fail
        vision_engine.primary_adapter.infer = Mock(side_effect=RuntimeError)
        for adapter in vision_engine.backup_adapters[:-1]:
            adapter.infer = Mock(side_effect=RuntimeError)

        screenshot = Screenshot(...)
        elements = vision_engine.infer_with_fallback(screenshot)

        # Cloud adapter should NOT be called without consent
        cloud_adapter = vision_engine.backup_adapters[-1]
        assert not cloud_adapter.infer.called

        # Should return empty result
        assert len(elements) == 0

    def test_all_models_fail_gracefully(self):
        """Test graceful handling when all models fail."""
        vision_engine = VisionEngine(model_detector=mock_detector)

        # Mock all models fail
        vision_engine.primary_adapter.infer = Mock(side_effect=RuntimeError)
        for adapter in vision_engine.backup_adapters:
            adapter.infer = Mock(side_effect=RuntimeError)

        screenshot = Screenshot(...)
        elements = vision_engine.infer_with_fallback(screenshot)

        # Should return empty list, not crash
        assert isinstance(elements, list)
        assert len(elements) == 0
```

### 11.4 Model Performance Benchmarks

```python
# tests/models/test_model_benchmarks.py

@pytest.mark.performance
class TestModelBenchmarks:
    """Benchmark tests for vision models."""

    @pytest.fixture
    def benchmark_dataset(self):
        """Load benchmark dataset of 100 screenshots."""
        dataset = []
        for i in range(100):
            img_path = f"tests/fixtures/benchmark/screenshot_{i:03d}.png"
            dataset.append(Image.open(img_path))
        return dataset

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="GPU required")
    def test_uitars_throughput(self, benchmark_dataset):
        """Test UI-TARS throughput: screenshots per second."""
        adapter = UITarsAdapter(model_path=Path("models/uitars-7b"))
        adapter.load()

        start = time.time()

        for image in benchmark_dataset:
            screenshot = Screenshot(
                hash=f"bench_{id(image)}",
                image_data=image,
                width=image.width,
                height=image.height
            )
            adapter.infer(screenshot, timeout=15.0)

        elapsed = time.time() - start
        throughput = len(benchmark_dataset) / elapsed

        adapter.unload()

        # Should process at least 0.2 screenshots/second (5s per screenshot)
        assert throughput >= 0.2, f"Throughput too low: {throughput:.3f} screenshots/s"

    @pytest.mark.performance
    def test_model_accuracy_on_standard_dataset(self):
        """Test model accuracy on annotated dataset."""
        adapter = UITarsAdapter(model_path=Path("models/uitars-7b"))
        adapter.load()

        # Load ground truth annotations
        annotations = load_annotations("tests/fixtures/benchmark/annotations.json")

        correct = 0
        total = 0

        for screenshot, ground_truth in annotations:
            predicted = adapter.infer(screenshot)

            # Compare with ground truth (simplified)
            correct += count_correct_predictions(predicted, ground_truth)
            total += len(ground_truth)

        accuracy = correct / total

        adapter.unload()

        # Should meet minimum accuracy threshold
        assert accuracy >= 0.75, f"Accuracy too low: {accuracy:.2%}"
```

---

## 12. CI/CD Pipeline

### 12.1 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml

name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    name: Unit Tests
    runs-on: windows-latest

    strategy:
      matrix:
        python-version: ["3.11"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=addon --cov-report=xml --cov-report=html

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  integration-tests:
    name: Integration Tests
    runs-on: windows-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Download test models
        run: |
          # Download lightweight test models
          python scripts/download_test_models.py

      - name: Run integration tests
        run: |
          pytest tests/integration/ -v --timeout=300

  security-tests:
    name: Security Tests
    runs-on: windows-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run security tests
        run: |
          pytest tests/security/ -v

      - name: Dependency vulnerability scan
        run: |
          pip install safety
          safety check --json

      - name: License compliance check
        run: |
          pip install pip-licenses
          pip-licenses --format=json --with-license-file --no-license-path

  e2e-tests:
    name: E2E Tests
    runs-on: windows-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install NVDA portable
        run: |
          # Download and setup NVDA portable for testing
          python scripts/setup_nvda_portable.py

      - name: Install plugin
        run: |
          python scripts/install_plugin_to_nvda.py

      - name: Run E2E tests
        run: |
          pytest tests/e2e/ -v --timeout=600
        env:
          NVDA_PATH: "C:\\nvda_portable"

  performance-tests:
    name: Performance Tests
    runs-on: windows-latest

    # Only run on main branch and scheduled
    if: github.ref == 'refs/heads/main' || github.event_name == 'schedule'

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Download models
        run: |
          python scripts/download_models.py

      - name: Run performance tests
        run: |
          pytest tests/performance/ -v --benchmark-only --benchmark-json=benchmark.json

      - name: Store benchmark results
        uses: benchmark-action/github-action-benchmark@v1
        with:
          tool: 'pytest'
          output-file-path: benchmark.json
          github-token: ${{ secrets.GITHUB_TOKEN }}
          auto-push: true

  accessibility-tests:
    name: Accessibility Tests
    runs-on: windows-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install NVDA
        run: |
          python scripts/setup_nvda_portable.py

      - name: Run accessibility tests
        run: |
          pytest tests/accessibility/ -v

  lint:
    name: Linting and Type Checking
    runs-on: windows-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install black mypy ruff pylint

      - name: Run black
        run: black --check addon/ tests/

      - name: Run mypy
        run: mypy addon/ --ignore-missing-imports

      - name: Run ruff
        run: ruff addon/ tests/

      - name: Run pylint
        run: pylint addon/ --rcfile=.pylintrc
```

### 12.2 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml

repos:
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/PyCQA/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=88', '--extend-ignore=E203']

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        args: ['--ignore-missing-imports']

  - repo: local
    hooks:
      - id: pytest-fast
        name: pytest-fast
        entry: pytest
        args: ['tests/unit/', '-x', '--timeout=60']
        language: system
        pass_filenames: false
        always_run: true

  - id: security-check
        name: security-check
        entry: bash -c 'pytest tests/security/ -v'
        language: system
        pass_filenames: false
        always_run: true
```

### 12.3 Continuous Monitoring

**Metrics to Track**:

```python
# scripts/collect_metrics.py

"""Collect and report quality metrics."""

def collect_test_metrics():
    """Collect test execution metrics."""
    return {
        "total_tests": count_tests(),
        "passing_tests": count_passing_tests(),
        "failing_tests": count_failing_tests(),
        "test_duration_seconds": measure_test_duration(),
        "code_coverage_percent": measure_coverage(),
    }

def collect_performance_metrics():
    """Collect performance metrics."""
    return {
        "uitars_avg_inference_time_seconds": benchmark_uitars(),
        "minicpm_avg_inference_time_seconds": benchmark_minicpm(),
        "memory_usage_mb": measure_memory_usage(),
        "cache_hit_rate_percent": measure_cache_hit_rate(),
    }

def collect_security_metrics():
    """Collect security metrics."""
    return {
        "vulnerability_count": scan_vulnerabilities(),
        "api_key_exposure_count": check_api_key_exposure(),
        "dependency_outdated_count": check_outdated_dependencies(),
    }

def report_to_dashboard(metrics):
    """Send metrics to monitoring dashboard."""
    # Send to Grafana, Datadog, or custom dashboard
    pass
```

---

## 13. Test Data Management

### 13.1 Test Fixtures

```
tests/fixtures/
├── screenshots/
│   ├── windows_ui_sample.png
│   ├── feishu_main_window.png
│   ├── dingtalk_chat.png
│   ├── wechat_contacts.png
│   ├── notepad_empty.png
│   └── complex_ui_1920x1080.png
├── models/
│   ├── mock_uitars_output.json
│   ├── mock_minicpm_output.json
│   └── mock_doubao_response.json
├── configs/
│   ├── test_config.yaml
│   ├── test_config_no_cloud.yaml
│   └── test_config_encrypted_keys.yaml
├── benchmark/
│   ├── screenshot_000.png
│   ├── screenshot_001.png
│   ├── ...
│   └── annotations.json
└── nvda/
    ├── mock_nvda_config.ini
    └── test_addon_metadata.json
```

### 13.2 Test Data Generation

```python
# tests/fixtures/generate_test_data.py

"""Generate test data for testing."""

import random
from PIL import Image, ImageDraw, ImageFont
import json


def generate_mock_ui_screenshot(
    width: int = 1920,
    height: int = 1080,
    num_elements: int = 10
) -> Image.Image:
    """Generate synthetic UI screenshot for testing.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        num_elements: Number of UI elements to draw.

    Returns:
        PIL Image with drawn UI elements.
    """
    # Create blank image
    image = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(image)

    # Try to load font
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()

    elements = []

    # Draw random UI elements
    for i in range(num_elements):
        element_type = random.choice(["button", "textbox", "link"])

        # Random position and size
        x1 = random.randint(50, width - 200)
        y1 = random.randint(50, height - 100)
        x2 = x1 + random.randint(100, 150)
        y2 = y1 + random.randint(30, 50)

        # Draw element
        if element_type == "button":
            draw.rectangle([x1, y1, x2, y2], fill="lightgray", outline="black", width=2)
            draw.text((x1 + 10, y1 + 10), "Button", fill="black", font=font)
        elif element_type == "textbox":
            draw.rectangle([x1, y1, x2, y2], fill="white", outline="gray", width=1)
            draw.text((x1 + 5, y1 + 5), "Text input", fill="gray", font=font)
        elif element_type == "link":
            draw.text((x1, y1), "Click here", fill="blue", font=font)

        elements.append({
            "type": element_type,
            "bbox": [x1, y1, x2, y2],
            "text": f"{element_type.capitalize()} {i+1}"
        })

    return image, elements


def generate_test_dataset(output_dir: Path, num_images: int = 100):
    """Generate test dataset with annotations.

    Args:
        output_dir: Directory to save generated images.
        num_images: Number of images to generate.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    annotations = {}

    for i in range(num_images):
        # Generate image
        image, elements = generate_mock_ui_screenshot()

        # Save image
        image_path = output_dir / f"screenshot_{i:03d}.png"
        image.save(image_path)

        # Save annotation
        annotations[image_path.name] = elements

    # Save annotations
    with open(output_dir / "annotations.json", "w") as f:
        json.dump(annotations, f, indent=2)


if __name__ == "__main__":
    generate_test_dataset(Path("tests/fixtures/benchmark"), num_images=100)
```

### 13.3 Sensitive Data Handling

**Test data must NOT contain**:
- Real API keys (use mock keys: `sk-test-mock-key-12345`)
- Personal information
- Real screenshots with sensitive content

**Use anonymized/synthetic data**:
- Generated UI screenshots
- Randomized element text
- Mock API responses

---

## 14. Quality Metrics

### 14.1 Code Coverage Targets

| Component | Target Coverage | Current |
|-----------|----------------|---------|
| Vision Models | 85% | - |
| NVDA Integration | 80% | - |
| Security (encryption) | 100% | - |
| Core Services | 90% | - |
| Infrastructure | 70% | - |
| **Overall** | **85%** | - |

**Measurement**:
```bash
pytest --cov=addon --cov-report=html --cov-report=term
```

### 14.2 Test Execution Metrics

**SLAs**:
- Unit tests: <5 minutes
- Integration tests: <15 minutes
- E2E tests: <30 minutes
- Full suite: <60 minutes

**Flakiness**:
- Flaky test rate: <2%
- Zero tolerance for flaky security tests

### 14.3 Quality Gates

**Pull Request Requirements**:
- [ ] All tests pass
- [ ] Code coverage ≥85%
- [ ] No new security vulnerabilities
- [ ] Performance benchmarks within 10% of baseline
- [ ] Zero linting errors
- [ ] Type checking passes
- [ ] Manual security review (for security-critical changes)

**Release Requirements**:
- [ ] All PR requirements met
- [ ] E2E tests pass on all supported NVDA versions
- [ ] Performance tests meet SLAs
- [ ] Accessibility tests pass (WCAG 2.1 AA)
- [ ] Security audit completed
- [ ] Dependency vulnerabilities resolved
- [ ] License compliance verified

### 14.4 Continuous Improvement

**Weekly**:
- Review test failures and flakiness
- Update test coverage dashboard
- Triage new bugs from production

**Monthly**:
- Review performance trends
- Update test data and fixtures
- Security dependency updates

**Quarterly**:
- Comprehensive security audit
- Performance optimization sprint
- Accessibility compliance review

---

## 15. Appendix

### 15.1 Test Utilities

```python
# tests/utils/test_helpers.py

"""Common test utilities and helpers."""

from pathlib import Path
from typing import List
import time
from unittest.mock import Mock

def create_mock_screenshot(
    width: int = 1920,
    height: int = 1080
) -> Screenshot:
    """Create mock screenshot for testing."""
    from PIL import Image
    import numpy as np

    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    image = Image.fromarray(img_array)

    return Screenshot(
        hash=f"mock_{width}x{height}",
        image_data=image,
        width=width,
        height=height,
        window_title="Mock Window",
        app_name="MockApp"
    )


def create_mock_ui_elements(count: int = 5) -> List[UIElement]:
    """Create list of mock UI elements."""
    return [
        UIElement(
            element_type=random.choice(["button", "textbox", "link"]),
            text=f"Element {i}",
            bbox=[i*100, i*50, (i+1)*100, (i+1)*50],
            confidence=random.uniform(0.7, 0.99)
        )
        for i in range(count)
    ]


def wait_for_condition(
    condition_func: callable,
    timeout: float = 5.0,
    poll_interval: float = 0.1
) -> bool:
    """Wait for condition to become true.

    Args:
        condition_func: Function that returns bool.
        timeout: Maximum time to wait in seconds.
        poll_interval: Time between checks in seconds.

    Returns:
        True if condition met, False if timeout.
    """
    start = time.time()
    while time.time() - start < timeout:
        if condition_func():
            return True
        time.sleep(poll_interval)
    return False


def assert_within_tolerance(
    actual: float,
    expected: float,
    tolerance: float = 0.1
):
    """Assert value is within tolerance of expected.

    Args:
        actual: Actual value.
        expected: Expected value.
        tolerance: Allowed difference (default 10%).
    """
    diff = abs(actual - expected)
    max_diff = expected * tolerance

    assert diff <= max_diff, \
        f"Value {actual} not within {tolerance*100}% of {expected} " \
        f"(diff: {diff}, max: {max_diff})"
```

### 15.2 NVDA Test Automation

```python
# tests/nvda_test_automation.py

"""NVDA automation utilities for E2E testing."""

import subprocess
import time
from pathlib import Path
from typing import List, Optional


class NVDAInstance:
    """Context manager for NVDA portable instance."""

    def __init__(
        self,
        nvda_path: Path = Path("C:/nvda_portable"),
        addon_path: Optional[Path] = None
    ):
        self.nvda_path = nvda_path
        self.addon_path = addon_path
        self.process = None

    def __enter__(self):
        """Start NVDA."""
        # Start NVDA portable
        self.process = subprocess.Popen(
            [str(self.nvda_path / "nvda.exe"), "-m", "--debug-logging"],
            cwd=str(self.nvda_path)
        )

        # Wait for NVDA to start
        time.sleep(5.0)

        # Install addon if provided
        if self.addon_path:
            self.install_addon(self.addon_path)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop NVDA."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=10.0)

    def install_addon(self, addon_path: Path):
        """Install addon to NVDA."""
        # Copy addon to userConfig/addons
        import shutil
        target_dir = self.nvda_path / "userConfig" / "addons" / "nvdaVision"
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(addon_path, target_dir)

        # Restart NVDA to load addon
        self.restart()

    def restart(self):
        """Restart NVDA."""
        self.__exit__(None, None, None)
        time.sleep(2.0)
        self.__enter__()

    def press_keys(self, keys: str):
        """Simulate key press.

        Args:
            keys: Key combination (e.g., "NVDA+Shift+V")
        """
        # Use Windows UI Automation or SendKeys
        # Implementation depends on available libraries
        pass

    def get_last_speech(self) -> str:
        """Get last speech output."""
        # Read from NVDA log or speech history
        pass

    def get_speech_history(self, last_n: int = 10) -> List[str]:
        """Get recent speech history."""
        pass

    def wait_for_speech(self, timeout: float = 5.0) -> str:
        """Wait for next speech output."""
        pass

    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if plugin is loaded."""
        pass

    def launch_application(self, app_path: str):
        """Launch application for testing."""
        subprocess.Popen([app_path])
        time.sleep(2.0)

    def wait_for_window_title(self, title: str, timeout: float = 10.0):
        """Wait for window with title to appear."""
        pass

    def is_responsive(self) -> bool:
        """Check if NVDA is responsive."""
        # Try to press a key and get response
        pass
```

---

## Document Metadata

**Version**: v1.0.0
**Created**: 2025-12-24
**Last Updated**: 2025-12-24
**Dependencies**:
- `.42cog/real/real.md` - Reality constraints
- `.42cog/cog/cog.md` - Cognitive model
- `spec/dev/sys.spec.md` - System architecture
- `spec/dev/code.spec.md` - Coding standards

**Next Review**: 2025-01-24

---

## Quality Checklist

- [x] All real.md constraints have corresponding tests
- [x] Security testing covers DPAPI encryption
- [x] Performance benchmarks defined for all models
- [x] Accessibility testing covers WCAG 2.1 AA
- [x] NVDA integration tests cover plugin lifecycle
- [x] CI/CD pipeline configured for automated testing
- [x] Test pyramid ratios appropriate (75/20/5)
- [x] Code coverage targets defined (85% overall)
- [x] Quality gates defined for PR and release
- [x] Test data management strategy documented

---

**End of QA Specification**
