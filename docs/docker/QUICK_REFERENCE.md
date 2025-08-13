# 🚀 SaberSim Quick Reference

## 🐳 Container Commands

### Build & Setup
```bash
# Build container
docker-compose build

# Setup directories
./deploy.sh
```

### Basic Usage
```bash
# Extract from HAR file
docker-compose run sabersim-extractor \
  python src/sabersim/atoms/extractors/extract.py \
  har_files/app.sabersim.com

# Generate tables
docker-compose run sabersim-extractor \
  python src/sabersim/atoms/extractors/tables.py \
  _data/sabersim_2025/fanduel/0812_main_slate/atoms_output/atoms

# Check status
docker-compose run sabersim-extractor \
  python src/sabersim/atoms/extractors/status.py
```

### Development
```bash
# Interactive shell
docker-compose run sabersim-dev

# Inside container:
python src/sabersim/atoms/extractors/extract.py har_files/app.sabersim.com
```

## 📁 File Structure
```
sabersim-extractor/
├── har_files/          # Put HAR files here
├── _data/              # Output goes here
├── src/                # Source code
├── Dockerfile          # Container definition
├── docker-compose.yml  # Container orchestration
├── requirements.txt    # Python dependencies
├── deploy.sh          # Setup script
└── WORK_SYSTEM_SETUP.md # Complete setup guide
```

## 🔧 Common Paths
- **HAR Files**: `har_files/`
- **Output Data**: `_data/sabersim_2025/<site>/<date>_<slate>/atoms_output/`
- **Source Code**: `src/sabersim/atoms/extractors/`

## 📊 Output Structure
```
_data/sabersim_2025/fanduel/0812_main_slate/atoms_output/
├── atoms/              # Extracted data
├── metadata/           # Extraction info
└── tables/             # Summary tables
```

## 🆘 Troubleshooting
```bash
# Check Docker
docker --version
docker-compose --version

# Check containers
docker ps
docker-compose ps

# Clean build
docker-compose build --no-cache

# View logs
docker-compose logs
```

---
**📖 Full documentation**: `WORK_SYSTEM_SETUP.md`
**🚀 Quick setup**: `./deploy.sh`
