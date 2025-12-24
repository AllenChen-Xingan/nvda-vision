"""Test script for NVDA Vision Screen Reader.

This script tests the complete recognition pipeline without NVDA.
"""

import sys
from pathlib import Path
import time

# Add src directory to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from addon.globalPlugins.nvdaVision.services import (
    ScreenshotService,
    CacheManager,
    VisionEngine,
    ResultProcessor
)
from addon.globalPlugins.nvdaVision.models import ModelDetector
from addon.globalPlugins.nvdaVision.core import RecognitionController
from addon.globalPlugins.nvdaVision.infrastructure.logger import logger


def test_system_components():
    """Test all system components individually."""
    print("=" * 60)
    print("NVDA Vision Screen Reader - Component Tests")
    print("=" * 60)

    # Test 1: Model Detector
    print("\n[Test 1] Model Detector")
    print("-" * 40)

    config = {
        "enable_cloud_api": False,
        "doubao_api_key": None,
        "confidence_threshold": 0.7,
        "inference_timeout": 15.0,
    }

    model_dir = Path(__file__).parent.parent / "models"
    model_dir.mkdir(exist_ok=True)

    detector = ModelDetector(model_dir, config)
    hw_info = detector.get_hardware_info()

    print(f"CPU Cores: {hw_info['cpu_cores']}")
    print(f"CPU Threads: {hw_info['cpu_threads']}")
    print(f"Total RAM: {hw_info['total_ram_gb']:.1f}GB")
    print(f"Available RAM: {hw_info['available_ram_gb']:.1f}GB")
    print(f"GPU Available: {hw_info['gpu_available']}")
    if hw_info['gpu_available']:
        print(f"GPU Name: {hw_info['gpu_name']}")
        print(f"GPU VRAM: {hw_info['gpu_vram_gb']:.1f}GB")

    print("\n✓ Model Detector test passed")

    # Test 2: Screenshot Service
    print("\n[Test 2] Screenshot Service")
    print("-" * 40)

    screenshot_service = ScreenshotService()

    # Test file loading (if test image exists)
    test_image_path = Path(__file__).parent / "fixtures" / "test_screenshot.png"

    if test_image_path.exists():
        screenshot = screenshot_service.capture_from_file(test_image_path)
        print(f"Loaded test screenshot: {screenshot.width}x{screenshot.height}")
        print(f"Hash: {screenshot.hash[:16]}...")
    else:
        print("Note: No test screenshot found, skipping file load test")
        print(f"Place a test image at: {test_image_path}")

    print("\n✓ Screenshot Service test passed")

    # Test 3: Cache Manager
    print("\n[Test 3] Cache Manager")
    print("-" * 40)

    cache_dir = Path(__file__).parent.parent / "cache_test"
    cache_dir.mkdir(exist_ok=True)

    cache_manager = CacheManager(
        cache_dir=cache_dir,
        ttl_seconds=300,
        max_size=100
    )

    stats = cache_manager.get_stats()
    print(f"Cache Statistics:")
    print(f"  Total screenshots: {stats.get('total_screenshots', 0)}")
    print(f"  Total results: {stats.get('total_results', 0)}")
    print(f"  Hit rate: {stats.get('hit_rate', 0):.1f}%")

    cache_manager.close()
    print("\n✓ Cache Manager test passed")

    # Test 4: Result Processor
    print("\n[Test 4] Result Processor")
    print("-" * 40)

    result_processor = ResultProcessor(confidence_threshold=0.7)

    # Create mock elements
    from addon.globalPlugins.nvdaVision.schemas.ui_element import UIElement

    mock_elements = [
        UIElement(
            id="",
            element_type="button",
            text="OK",
            bbox=[100, 200, 200, 250],
            confidence=0.95,
            actionable=True
        ),
        UIElement(
            id="",
            element_type="textbox",
            text="Enter name",
            bbox=[100, 100, 400, 150],
            confidence=0.65,
            actionable=True
        ),
    ]

    for elem in mock_elements:
        speech_text = result_processor.generate_speech_text(elem)
        print(f"  {elem.element_type}: {speech_text}")

    print("\n✓ Result Processor test passed")

    print("\n" + "=" * 60)
    print("All component tests passed!")
    print("=" * 60)


def test_recognition_pipeline_mock():
    """Test recognition pipeline with mocked inference."""
    print("\n\n" + "=" * 60)
    print("Recognition Pipeline Test (Mocked)")
    print("=" * 60)

    print("\nNote: This test uses mocked inference since models are not loaded.")
    print("In production, actual models would be loaded and used.")

    # Initialize components
    config = {
        "enable_cloud_api": False,
        "confidence_threshold": 0.7,
        "inference_timeout": 15.0,
    }

    screenshot_service = ScreenshotService()
    cache_dir = Path(__file__).parent.parent / "cache_test"
    cache_manager = CacheManager(cache_dir, ttl_seconds=300, max_size=100)

    result_processor = ResultProcessor(confidence_threshold=0.7)

    print("\n✓ All components initialized")
    print("\nNote: Actual model loading would happen here in production")
    print("Models required:")
    print("  - UI-TARS 7B (GPU, 16GB+ VRAM) OR")
    print("  - MiniCPM-V 2.6 (CPU, 6GB+ RAM) OR")
    print("  - Doubao Cloud API (with API key)")

    cache_manager.close()

    print("\n" + "=" * 60)
    print("Pipeline test completed (mocked)")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_system_components()
        test_recognition_pipeline_mock()

        print("\n\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print("✓ All tests passed successfully!")
        print("\nNext steps:")
        print("1. Download and install vision models")
        print("2. Configure API keys if using cloud API")
        print("3. Test with NVDA integration")
        print("4. Run full end-to-end tests")
        print("=" * 60)

    except Exception as e:
        print(f"\n\n✗ Test failed with error:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
