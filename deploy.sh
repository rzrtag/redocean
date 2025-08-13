#!/bin/bash

# SaberSim HAR Extraction System - Deployment Script
# This script sets up and runs the containerized system

set -e  # Exit on any error

echo "🚀 SaberSim HAR Extraction System - Deployment Script"
echo "=================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "📖 See WORK_SYSTEM_SETUP.md for installation instructions."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "📖 See WORK_SYSTEM_SETUP.md for installation instructions."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p har_files
mkdir -p _data

# Build the container
echo "🔨 Building Docker container..."
docker-compose build

echo "✅ Container built successfully!"

# Show usage information
echo ""
echo "🎯 System is ready! Here are some common commands:"
echo ""
echo "📊 Extract from HAR file:"
echo "   docker-compose run sabersim-extractor python src/sabersim/atoms/extractors/extract.py har_files/your_file.har"
echo ""
echo "📋 Generate tables:"
echo "   docker-compose run sabersim-extractor python src/sabersim/atoms/extractors/tables.py _data/sabersim_2025/fanduel/0812_main_slate/atoms_output/atoms"
echo ""
echo "📈 Check status:"
echo "   docker-compose run sabersim-extractor python src/sabersim/atoms/extractors/status.py"
echo ""
echo "🐚 Interactive shell:"
echo "   docker-compose run sabersim-dev"
echo ""
echo "📖 For more information, see WORK_SYSTEM_SETUP.md"
echo ""
echo "🎉 Happy extracting!"
