#!/bin/bash

# Red Ocean Environment Activation Script
# Source this script to activate the environment

echo "🔧 Activating Red Ocean environment..."

# Add miniconda to PATH
export PATH="$HOME/miniconda3/bin:$PATH"

# Source conda
source $HOME/miniconda3/etc/profile.d/conda.sh

# Activate environment
conda activate red_ocean

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/mnt/storage_fast/workspaces/red_ocean/src"

echo "✅ Red Ocean environment activated!"
echo "🐍 Python: $(python --version)"
echo "📁 Working directory: $(pwd)"
echo ""
echo "Available commands:"
echo "  make help          - Show available make targets"
echo "  python -m src.main status  - Check system status"
echo "  make mlb-collect   - Collect MLB data"
echo "  make sabersim      - Run SaberSim analysis"
