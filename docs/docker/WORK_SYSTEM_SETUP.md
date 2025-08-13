# 🐳 Work System Setup Guide - SaberSim HAR Extraction

## Overview
This guide will help you set up and run the SaberSim HAR extraction system on your work system using Docker containers.

## 🚀 Quick Start (5 minutes)

### 1. Install Docker
**Windows:**
```bash
# Download Docker Desktop from:
# https://www.docker.com/products/docker-desktop/
# Install and restart your computer
```

**macOS:**
```bash
# Download Docker Desktop from:
# https://www.docker.com/products/docker-desktop/
# Install and restart your computer
```

**Linux (Ubuntu/Debian):**
```bash
# Update package index
sudo apt-get update

# Install prerequisites
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up stable repository
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Add your user to docker group (optional, for non-sudo usage)
sudo usermod -aG docker $USER
# Log out and back in for this to take effect
```

### 2. Install Docker Compose
**Windows/macOS:** Docker Desktop includes Docker Compose

**Linux:**
```bash
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### 3. Download Project Files
```bash
# Create project directory
mkdir sabersim-extractor
cd sabersim-extractor

# Download these files to your project directory:
# - Dockerfile
# - docker-compose.yml
# - requirements.txt
# - src/ (entire source code directory)
```

### 4. Create Directory Structure
```bash
# Create necessary directories
mkdir har_files    # Put your HAR files here
mkdir _data        # Output will go here
```

### 5. Build and Run
```bash
# Build the container
docker-compose build

# Run extraction (replace with your HAR file path)
docker-compose run sabersim-extractor python src/sabersim/atoms/extractors/extract.py har_files/your_file.har

# Or run interactively for development
docker-compose run sabersim-dev
```

## 📁 Project Structure on Work System

```
sabersim-extractor/
├── Dockerfile                 # Container definition
├── docker-compose.yml         # Container orchestration
├── requirements.txt           # Python dependencies
├── har_files/                # Your HAR files go here
│   ├── app.sabersim.com      # Example HAR file
│   └── other_files.har       # Other HAR files
├── _data/                    # Output directory (auto-created)
└── src/                      # Source code
    └── sabersim/
        └── atoms/
            └── extractors/
                ├── extract.py
                ├── tables.py
                ├── status.py
                └── extractor.py
```

## 🔧 Usage Examples

### Basic Extraction
```bash
# Extract from HAR file
docker-compose run sabersim-extractor \
  python src/sabersim/atoms/extractors/extract.py \
  har_files/app.sabersim.com
```

### Generate Tables
```bash
# Generate summary tables
docker-compose run sabersim-extractor \
  python src/sabersim/atoms/extractors/tables.py \
  _data/sabersim_2025/fanduel/0812_main_slate/atoms_output/atoms
```

### Check Status
```bash
# Check system status
docker-compose run sabersim-extractor \
  python src/sabersim/atoms/extractors/status.py
```

### Interactive Development
```bash
# Get interactive shell for development
docker-compose run sabersim-dev

# Inside container, you can run:
python src/sabersim/atoms/extractors/extract.py har_files/app.sabersim.com
python src/sabersim/atoms/extractors/tables.py _data/sabersim_2025/fanduel/0812_main_slate/atoms_output/atoms
python src/sabersim/atoms/extractors/status.py
```

## 🐛 Troubleshooting

### Docker Not Found
```bash
# Check if Docker is running
docker --version

# Start Docker Desktop (Windows/macOS)
# Or start Docker service (Linux)
sudo systemctl start docker
```

### Permission Denied
```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

### Port Already in Use
```bash
# Check what's using the port
docker ps

# Stop conflicting containers
docker-compose down
```

### Build Errors
```bash
# Clean build cache
docker-compose build --no-cache

# Check Dockerfile syntax
docker build -t test .
```

## 📊 Data Output

After running extraction, your data will be organized like this:
```
_data/
└── sabersim_2025/
    ├── fanduel/
    │   └── 0812_main_slate/
    │       └── atoms_output/
    │           ├── atoms/           # Extracted data
    │           ├── metadata/        # Extraction info
    │           └── tables/          # Summary tables
    └── draftkings/
        └── ...
```

## 🔄 Updating the System

### Update Source Code
```bash
# Pull latest changes
git pull origin main

# Rebuild container
docker-compose build --no-cache
```

### Update Dependencies
```bash
# Edit requirements.txt
# Rebuild container
docker-compose build --no-cache
```

## 🚀 Production Usage

### Run as Service
```bash
# Start in background
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop service
docker-compose down
```

### Scheduled Extraction
```bash
# Create cron job or scheduled task
# Example: Run every hour
0 * * * * cd /path/to/sabersim-extractor && docker-compose run sabersim-extractor python src/sabersim/atoms/extractors/extract.py har_files/latest.har
```

## 📋 Checklist

- [ ] Docker installed and running
- [ ] Docker Compose installed
- [ ] Project files downloaded
- [ ] Directory structure created
- [ ] Container built successfully
- [ ] Test extraction run
- [ ] Output verified in `_data/` directory

## 🆘 Need Help?

### Common Issues:
1. **Docker not starting** - Restart computer after installation
2. **Permission denied** - Add user to docker group (Linux)
3. **Build fails** - Check internet connection and try `--no-cache`
4. **No output** - Verify HAR file path and permissions

### Commands to Check Status:
```bash
# Docker status
docker --version
docker-compose --version

# Container status
docker ps
docker-compose ps

# Build status
docker-compose build

# Run test
docker-compose run sabersim-extractor python --version
```

---

**🎯 You're all set!** The containerized system will work exactly the same as your development environment, but now it's portable and easy to deploy on any system with Docker.

*Last Updated: August 12, 2025*
