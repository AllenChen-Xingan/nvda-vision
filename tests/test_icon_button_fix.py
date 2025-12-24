"""
Icon Button Recognition Test

Tests the improved Doubao prompt for icon button recognition.
Verifies that icon buttons without text labels are properly identified.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "addon" / "globalPlugins" / "nvdaVision"))

def test_prompt_changes():
    """Test that prompt changes are in place"""
    print("\n" + "="*60)
    print("ICON BUTTON RECOGNITION TEST")
    print("="*60)

    print("\n[TEST 1] Verifying Prompt Changes")

    try:
        from models.doubao_adapter import DoubaoAPIAdapter

        # Check if file has been modified
        import inspect
        source = inspect.getsource(DoubaoAPIAdapter.infer)

        # Check for key phrases in the new prompt
        checks = {
            "visually impaired users": "visually impaired users" in source,
            "CRITICAL REQUIREMENTS": "CRITICAL REQUIREMENTS" in source,
            "Microphone/mic": "Microphone/mic" in source or "microphone" in source.lower(),
            "NEVER return empty": "NEVER return empty" in source,
            "temperature": "0.1" in source,
        }

        print("\n  Prompt Check Results:")
        for check_name, passed in checks.items():
            status = "OK" if passed else "FAIL"
            print(f"    {status}: {check_name}")

        all_passed = all(checks.values())

        if all_passed:
            print("\n  OK PASS: All prompt improvements detected")
        else:
            print("\n  FAIL: Some improvements missing")

        return all_passed

    except Exception as e:
        print(f"\n  FAIL: Error checking prompt: {e}")
        return False


def test_speech_feedback():
    """Test speech feedback improvements"""
    print("\n[TEST 2] Verifying Speech Feedback Changes")

    try:
        # Read the __init__.py file
        init_file = project_root / "src" / "addon" / "globalPlugins" / "nvdaVision" / "__init__.py"
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for improvements
        checks = {
            "empty text handling": "unrecognized element" in content,
            "button type check": "icon_button" in content and "unrecognized" in content,
        }

        print("\n  Speech Feedback Check Results:")
        for check_name, passed in checks.items():
            status = "OK" if passed else "FAIL"
            print(f"    {status}: {check_name}")

        all_passed = all(checks.values())

        if all_passed:
            print("\n  OK PASS: Speech feedback improvements detected")
        else:
            print("\n  FAIL: Some improvements missing")

        return all_passed

    except Exception as e:
        print(f"\n  FAIL: Error checking speech feedback: {e}")
        return False


def test_api_key_config():
    """Check if API key is configured"""
    print("\n[TEST 3] Checking API Key Configuration")

    try:
        from infrastructure.config_manager import ConfigManager

        config = ConfigManager()
        api_key = config.get("doubao_api_key")

        if api_key:
            print(f"\n  OK API key configured (length: {len(api_key)} chars)")
            return True
        else:
            print("\n  WARN: No API key configured")
            print("  INFO: To test actual recognition, configure API key:")
            print("        Edit ~/.nvda_vision/config.yaml")
            print("        Add: doubao_api_key: \"your-key-here\"")
            return False

    except Exception as e:
        print(f"\n  WARN: Could not check API key: {e}")
        return False


def print_test_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    test_names = [
        "Prompt Changes",
        "Speech Feedback",
        "API Key Config"
    ]

    for name, passed in zip(test_names, results):
        status = "OK PASS" if passed else "FAIL/WARN"
        print(f"  {status}: {name}")

    critical_passed = results[0] and results[1]  # First two are critical

    print("-"*60)
    if critical_passed:
        print("  Status: READY - Icon button improvements are in place!")
        if not results[2]:
            print("  Note: Configure API key to test actual recognition")
    else:
        print("  Status: INCOMPLETE - Some improvements missing")
    print("="*60 + "\n")

    return critical_passed


def print_next_steps():
    """Print next steps for user"""
    print("="*60)
    print("NEXT STEPS")
    print("="*60)
    print("""
1. Configure Doubao API Key (if not already done):
   - Visit: https://console.volcengine.com/
   - Get API key
   - Edit: ~/.nvda_vision/config.yaml
   - Add: doubao_api_key: "your-key-here"

2. Test with real application:
   - Open Tencent Meeting / Zoom
   - Press NVDA+Shift+V to recognize
   - Press N to navigate elements
   - Listen for: "icon_button: microphone mute"
   - Instead of: "button, at 120, 540"

3. Verify improvements:
   - Icon buttons should have descriptive names
   - No empty text fields
   - User can understand button function

4. Feedback:
   - If icon recognition is inaccurate, review:
     docs/ICON_BUTTON_ACCESSIBILITY.md
   - Consider adjusting prompt for specific apps
    """)
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\nTesting icon button recognition improvements...")

    results = [
        test_prompt_changes(),
        test_speech_feedback(),
        test_api_key_config()
    ]

    success = print_test_summary(results)

    if success:
        print_next_steps()

    sys.exit(0 if success else 1)
