#!/bin/bash
# Master Pipeline Runner Script
#
# Usage:
#   ./run_master_pipeline.sh                    # Run full pipeline with validation
#   ./run_master_pipeline.sh --validate-only    # Run only validation
#   ./run_master_pipeline.sh --skip-validation  # Run pipelines without validation
#   ./run_master_pipeline.sh --quick            # Quick validation (sample players)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "src/master_pipeline/run_validator.py" ]; then
    print_error "Please run this script from the red_ocean workspace root directory"
    exit 1
fi

# Parse arguments
VALIDATE_ONLY=false
SKIP_VALIDATION=false
QUICK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        --skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        --quick)
            QUICK=true
            shift
            ;;
        --help)
            echo "Master Pipeline Runner"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --validate-only    Run only validation, skip data pipelines"
            echo "  --skip-validation  Skip validation steps, run only pipelines"
            echo "  --quick            Quick validation (sample players only)"
            echo "  --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Run full pipeline with validation"
            echo "  $0 --validate-only    # Run only validation"
            echo "  $0 --skip-validation  # Run pipelines without validation"
            echo "  $0 --quick            # Quick validation"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build command
CMD="python3 src/master_pipeline/run_validator.py"

if [ "$VALIDATE_ONLY" = true ]; then
    CMD="$CMD --validate-only"
    print_status "Running in validate-only mode"
fi

if [ "$SKIP_VALIDATION" = true ]; then
    CMD="$CMD --skip-validation"
    print_status "Running with validation disabled"
fi

if [ "$QUICK" = true ]; then
    CMD="$CMD --quick"
    print_status "Running with quick validation"
fi

# Print startup information
print_status "Starting Master Pipeline Runner"
print_status "Command: $CMD"
print_status "Working directory: $(pwd)"
print_status "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"

# Create output directory if it doesn't exist
mkdir -p /mnt/storage_fast/workspaces/red_ocean/_data/reports/validator

# Run the pipeline
print_status "Executing pipeline..."
echo ""

if $CMD; then
    print_success "Pipeline completed successfully!"
    echo ""
    print_status "Reports saved to: /mnt/storage_fast/workspaces/red_ocean/_data/reports/validator/"
    print_status "Check the latest timestamped directory for detailed results"
    exit 0
else
    print_error "Pipeline failed!"
    echo ""
    print_warning "Check the error output above for details"
    print_status "Reports may still be available in: /mnt/storage_fast/workspaces/red_ocean/_data/reports/validator/"
    exit 1
fi
