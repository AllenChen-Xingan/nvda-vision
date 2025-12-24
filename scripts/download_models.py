"""Download and setup vision models for NVDA Vision plugin.

This script downloads the required vision models to the appropriate location.
"""

import os
import sys
from pathlib import Path
import argparse


def get_model_dir():
    """Get the model directory path."""
    return Path.home() / ".nvda_vision" / "models"


def download_uitars():
    """Download UI-TARS 7B model (GPU, 16GB+ VRAM)."""
    print("=" * 60)
    print("Downloading UI-TARS 7B Model")
    print("=" * 60)
    print("\nRequirements:")
    print("  - NVIDIA GPU with 16GB+ VRAM")
    print("  - CUDA 11.8 or later")
    print("  - ~14GB disk space")
    print("\nDownload Instructions:")
    print("1. Visit: https://huggingface.co/microsoft/UI-TARS-7B")
    print("2. Click 'Files and versions'")
    print("3. Download all model files")
    print("4. Place them in:")

    model_path = get_model_dir() / "ui-tars-7b"
    model_path.mkdir(parents=True, exist_ok=True)
    print(f"   {model_path}")

    print("\nNote: Due to the large size, you may want to use git-lfs:")
    print(f"   cd {model_path.parent}")
    print("   git lfs install")
    print("   git clone https://huggingface.co/microsoft/UI-TARS-7B ui-tars-7b")

    return model_path


def download_minicpm():
    """Download MiniCPM-V 2.6 model (CPU, 6GB+ RAM)."""
    print("=" * 60)
    print("Downloading MiniCPM-V 2.6 Model")
    print("=" * 60)
    print("\nRequirements:")
    print("  - 6GB+ available RAM")
    print("  - ~4GB disk space")
    print("\nDownload Instructions:")
    print("1. Visit: https://huggingface.co/openbmb/MiniCPM-V-2_6")
    print("2. Click 'Files and versions'")
    print("3. Download all model files")
    print("4. Place them in:")

    model_path = get_model_dir() / "minicpm-v-2.6"
    model_path.mkdir(parents=True, exist_ok=True)
    print(f"   {model_path}")

    print("\nNote: You can use git-lfs for easier download:")
    print(f"   cd {model_path.parent}")
    print("   git lfs install")
    print("   git clone https://huggingface.co/openbmb/MiniCPM-V-2_6 minicpm-v-2.6")

    return model_path


def configure_cloud_api():
    """Configure Doubao Cloud API."""
    print("=" * 60)
    print("Configure Doubao Cloud API")
    print("=" * 60)
    print("\nRequirements:")
    print("  - Internet connection")
    print("  - Doubao API key")
    print("\nConfiguration Steps:")
    print("1. Get API key from: https://console.volcengine.com/ark")
    print("2. Edit configuration file:")

    config_path = Path.home() / ".nvda_vision" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"   {config_path}")
    print("\n3. Add the following:")
    print("   enable_cloud_api: true")
    print("   doubao_api_key: 'your-api-key-here'")
    print("\n4. Restart NVDA")

    # Create sample config if doesn't exist
    if not config_path.exists():
        sample_config = """# NVDA Vision Configuration

# Model settings
model_dir: null  # null = use default (~/.nvda_vision/models)
confidence_threshold: 0.7

# Cache settings
cache:
  enabled: true
  ttl_minutes: 5
  max_results: 1000

# Privacy settings
privacy:
  local_processing_only: true

# Cloud API (optional - only used as fallback)
enable_cloud_api: false
doubao_api_key: null  # Set your API key here

# Performance
inference_timeout: 15.0
"""
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(sample_config)

        print(f"\nSample configuration created at: {config_path}")

    return config_path


def check_installation():
    """Check which models are installed."""
    print("=" * 60)
    print("Checking Model Installation")
    print("=" * 60)

    model_dir = get_model_dir()

    models = {
        "UI-TARS 7B (GPU)": model_dir / "ui-tars-7b",
        "MiniCPM-V 2.6 (CPU)": model_dir / "minicpm-v-2.6",
    }

    installed = []
    missing = []

    for name, path in models.items():
        if path.exists() and any(path.iterdir()):
            installed.append(name)
            print(f"✓ {name} - Installed")
            print(f"  Location: {path}")
        else:
            missing.append(name)
            print(f"✗ {name} - Not installed")
            print(f"  Expected at: {path}")

    # Check cloud API config
    config_path = Path.home() / ".nvda_vision" / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'enable_cloud_api: true' in content and 'doubao_api_key:' in content:
                print(f"✓ Doubao Cloud API - Configured")
                print(f"  Config: {config_path}")
            else:
                print(f"✗ Doubao Cloud API - Not configured")
    else:
        print(f"✗ Doubao Cloud API - Not configured")

    print("\nSummary:")
    print(f"  Installed models: {len(installed)}")
    print(f"  Missing models: {len(missing)}")

    if missing:
        print("\nTo download missing models, run:")
        for name in missing:
            if "UI-TARS" in name:
                print("  python scripts/download_models.py --uitars")
            elif "MiniCPM" in name:
                print("  python scripts/download_models.py --minicpm")

    return installed, missing


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download and setup vision models for NVDA Vision"
    )
    parser.add_argument(
        "--uitars",
        action="store_true",
        help="Show instructions for downloading UI-TARS 7B (GPU model)"
    )
    parser.add_argument(
        "--minicpm",
        action="store_true",
        help="Show instructions for downloading MiniCPM-V 2.6 (CPU model)"
    )
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Configure Doubao Cloud API"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check which models are installed"
    )

    args = parser.parse_args()

    # If no arguments, show help
    if not any([args.uitars, args.minicpm, args.cloud, args.check]):
        parser.print_help()
        print("\n" + "=" * 60)
        print("Quick Start:")
        print("=" * 60)
        print("\n1. Check current installation:")
        print("   python scripts/download_models.py --check")
        print("\n2. Download a model:")
        print("   python scripts/download_models.py --uitars  (GPU)")
        print("   python scripts/download_models.py --minicpm (CPU)")
        print("\n3. Or configure cloud API:")
        print("   python scripts/download_models.py --cloud")
        return 0

    if args.check:
        check_installation()

    if args.uitars:
        download_uitars()

    if args.minicpm:
        download_minicpm()

    if args.cloud:
        configure_cloud_api()

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Restart NVDA")
    print("2. Press NVDA+Shift+V to test recognition")
    print("3. Check logs at: ~/.nvda_vision/logs/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
