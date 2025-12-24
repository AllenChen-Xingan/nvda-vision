"""
Simple verification script to check icon button improvements
"""

from pathlib import Path

project_root = Path(__file__).parent.parent

print("\n" + "="*60)
print("ICON BUTTON FIX - VERIFICATION")
print("="*60)

# Check 1: Prompt improvements in doubao_adapter.py
print("\n[CHECK 1] Doubao Prompt Improvements")
doubao_file = project_root / "src" / "addon" / "globalPlugins" / "nvdaVision" / "models" / "doubao_adapter.py"

with open(doubao_file, 'r', encoding='utf-8') as f:
    content = f.read()

checks = {
    "[OK] Accessibility role": "visually impaired users" in content,
    "[OK] Critical requirements": "CRITICAL REQUIREMENTS" in content,
    "[OK] Icon patterns guide": "Microphone" in content or "microphone" in content,
    "[OK] Never empty text": "NEVER return empty" in content,
    "[OK] Low temperature": "0.1" in content and "Low temperature" in content,
}

for name, passed in checks.items():
    status = "PASS" if passed else "FAIL"
    print(f"  {status} {name}")

prompt_ok = all(checks.values())

# Check 2: Speech feedback improvements in __init__.py
print("\n[CHECK 2] Speech Feedback Improvements")
init_file = project_root / "src" / "addon" / "globalPlugins" / "nvdaVision" / "__init__.py"

with open(init_file, 'r', encoding='utf-8') as f:
    content = f.read()

checks2 = {
    "[OK] Empty text handling": "unrecognized element" in content,
    "[OK] Button type check": "icon_button" in content and "unrecognized" in content,
}

for name, passed in checks2.items():
    status = "PASS" if passed else "FAIL"
    print(f"  {status} {name}")

speech_ok = all(checks2.values())

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

if prompt_ok and speech_ok:
    print("  [OK] All improvements successfully applied!")
    print("\n  Changes:")
    print("    1. Enhanced Doubao prompt with icon recognition")
    print("    2. Temperature reduced to 0.1 for stability")
    print("    3. Speech feedback handles empty text")
    print("\n  Next steps:")
    print("    - Configure Doubao API key if not done")
    print("    - Test with Tencent Meeting/Zoom")
    print("    - Verify icon buttons are recognized")
else:
    print("  [FAIL] Some improvements missing")
    if not prompt_ok:
        print("    - Prompt improvements not detected")
    if not speech_ok:
        print("    - Speech feedback improvements not detected")

print("="*60 + "\n")

# Show sample of improved prompt
if prompt_ok:
    print("Sample of new prompt:")
    print("-" * 60)
    # Extract a sample
    start = content.find("You are a UI accessibility")
    if start > 0:
        sample = content[start:start+200]
        print(sample + "...")
    print("-" * 60 + "\n")
