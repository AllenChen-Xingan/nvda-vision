#!/usr/bin/env python
"""
Test Runner for NVDA Vision Screen Reader

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --unit             # Run only unit tests
"""

import sys
import argparse
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src" / "addon" / "globalPlugins"))


def run_integration_tests():
    """Run integration tests"""
    from tests.integration.test_mas1_e2e import run_tests
    return run_tests()


def run_unit_tests():
    """Run unit tests (placeholder)"""
    print("Unit tests not yet implemented")
    return True


def main():
    parser = argparse.ArgumentParser(description="NVDA Vision Test Runner")
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )

    args = parser.parse_args()

    success = True

    if args.integration:
        success = run_integration_tests()
    elif args.unit:
        success = run_unit_tests()
    else:
        # Run all tests
        print("Running all tests...\n")
        success = run_integration_tests() and run_unit_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
