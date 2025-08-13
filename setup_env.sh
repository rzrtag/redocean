#!/bin/bash

# Red Ocean Environment Setup Script
# This script sets up the conda environment and activates it

set -e

echo "🚀 Setting up Red Ocean environment..."

# Check if miniconda is installed
if [ ! -d "$HOME/miniconda3" ]; then
    echo "📥 Miniconda not found. Installing..."
    cd /tmp
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -p $HOME/miniconda3
    echo "✅ Miniconda installed!"
fi

# Add miniconda to PATH
export PATH="$HOME/miniconda3/bin:$PATH"

# Source conda
source $HOME/miniconda3/etc/profile.d/conda.sh

# Check if environment exists
if ! conda env list | grep -q "red_ocean"; then
    echo "🐍 Creating red_ocean conda environment..."
    conda create -n red_ocean python=3.11 -y
    echo "✅ Environment created!"
else
    echo "✅ red_ocean environment already exists!"
fi

# Activate environment
echo "🔧 Activating red_ocean environment..."
conda activate red_ocean

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Setup project structure
echo "🏗️  Setting up project structure..."
make setup

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/mnt/storage_fast/workspaces/red_ocean/src"

echo ""
echo "🎉 Red Ocean environment setup complete!"
echo ""
echo "To activate the environment in the future, run:"
echo "  source $HOME/miniconda3/etc/profile.d/conda.sh"
echo "  conda activate red_ocean"
echo "  export PYTHONPATH=\"\${PYTHONPATH}:/mnt/storage_fast/workspaces/red_ocean/src\""
echo ""
echo "Or use the activate script:"
echo "  source activate_env.sh"
echo ""
echo "Available commands:"
echo "  make help          - Show available make targets"
echo "  python -m src.main status  - Check system status"
echo "  make mlb-collect   - Collect MLB data"
echo "  make sabersim      - Run SaberSim analysis"
