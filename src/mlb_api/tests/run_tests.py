#!/usr/bin/env python3
"""
Simple test runner for MLB API data validation.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from mlb_api.tests.data_validation import DataValidator


def main():
    """Run the data validation tests."""
    print("🧪 MLB API Data Validation Test Runner")
    print("=" * 50)

    validator = DataValidator()
    summary = validator.run_all_tests()

    # Print final status
    if summary['test_summary']['failed_tests'] == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {summary['test_summary']['failed_tests']} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
