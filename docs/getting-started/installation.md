# Installation

SlowQL can be installed in multiple ways depending on your environment and workflow. This comprehensive guide covers installation across all supported platforms and methods.

---

## 📋 Prerequisites

Before installing SlowQL, ensure you have the following:

- **Python 3.11+** (3.12+ recommended)
- **pip** or **pipx** package manager
- **Operating System**: Linux, macOS, or Windows

### Python Version Check
```bash
# Check your Python version
python --version  # Should be 3.11+

# If using pyenv (recommended for multiple Python versions)
pyenv install 3.12.0
pyenv global 3.12.0
```

---

## 🛠️ Installation Methods

### Method 1: Recommended (pipx)

**Best for isolated environments and avoiding dependency conflicts.**

```bash
# Install with pipx (isolated environment)
pipx install slowql

# Optional: Install readchar for interactive menus
pipx install readchar
```

**Advantages:**
- Isolated from other Python packages
- Automatic virtual environment creation
- Easy uninstallation
- No system-wide dependencies

### Method 2: Standard (pip)

**Best for quick installation in current Python environment.**

```bash
# Install in current Python environment
pip install slowql

# Optional: Install readchar for interactive menus
pip install readchar

# Or install with development dependencies
pip install slowql[dev]
```

### Method 3: Development Version

**For contributors and users who want the latest features.**

```bash
# Clone and install from source
git clone https://github.com/makroumi/slowql.git
cd slowql
pip install -e ".[dev]"
```

---

## 🐳 Container Installation

### Docker (GHCR)

```bash
# Pull latest image
docker pull ghcr.io/makroumi/slowql:latest

# Run with volume mounting
docker run --rm -v "$PWD":/work makroumi/slowql slowql --input-file /work/queries.sql

# Run in interactive mode
docker run --rm -it ghcr.io/makroumi/slowql slowql --help
```

### Docker Hub

```bash
# Alternative registry
docker pull makroumi/slowql:latest
docker run --rm -v "$PWD":/work makroumi/slowql slowql --input-file /work/queries.sql
```

### Podman

```bash
# Run with Podman (Docker-compatible)
podman run --rm -v "$PWD":/work -w /work docker.io/makroumi/slowql slowql --input-file queries.sql

# Create local development pod
podman pod create --name slowql-dev
podman run --pod slowql-dev -v "$PWD":/work -w /work docker.io/makroumi/slowql slowql --help
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  slowql:
    image: docker.io/makroumi/slowql
    volumes:
      - ./sql:/work
    working_dir: /work
    command: slowql --input-file queries.sql --export html csv
```

---

## 🐧 Platform-Specific Installation

### Ubuntu/Debian

```bash
# Install Python 3.12 and pip
sudo apt update
sudo apt install python3.12 python3.12-pip python3.12-venv

# Install SlowQL
pip3.12 install slowql

# Or use pipx (recommended)
pip3.12 install pipx
pipx install slowql
```

### CentOS/RHEL/Fedora

```bash
# Install Python 3.12
sudo dnf install python3.12 python3.12-pip
# or for older versions:
sudo yum install python3 python3-pip

# Install SlowQL
pip3 install slowql

# Or use pipx
pip3 install pipx
pipx install slowql
```

### Arch Linux

```bash
# Install Python and pip
sudo pacman -S python python-pip

# Install SlowQL
pip install slowql

# Or use pipx
pip install pipx
pipx install slowql
```

### macOS

```bash
# Using Homebrew
brew install python

# Install SlowQL
pip install slowql

# Or use pipx
brew install pipx
pipx install slowql
```

### Windows

```powershell
# Using Chocolatey
choco install python

# Or using winget
winget install Python.Python.3.12

# Install SlowQL
pip install slowql

# Or use pipx
pip install pipx
pipx install slowql
```

---

## ✅ Verify Installation

```bash
# Check installation
slowql --version

# View help
slowql --help

# Test with sample analysis
slowql --input-file examples/sample.sql
```

---

## 🔧 Troubleshooting Installation

### Python Version Issues

**Problem**: `Python 3.11+ required`

**Solutions:**
```bash
# Check current version
python --version

# Install newer Python (Ubuntu/Debian)
sudo apt install python3.12
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

# Using pyenv (recommended)
pyenv install 3.12.0
pyenv global 3.12.0
```

### Permission Issues

**Problem**: `Permission denied` or `Access denied`

**Solutions:**
```bash
# Use user installation
pip install --user slowql

# Or use pipx (recommended)
pip install pipx
pipx install slowql

# For system-wide installation
sudo pip install slowql
```

### Import Errors

**Problem**: `ModuleNotFoundError` or import issues

**Solutions:**
```bash
# Reinstall with all dependencies
pip install --force-reinstall slowql

# Install with development dependencies
pip install slowql[dev]

# Check Python path
python -c "import sys; print(sys.path)"
```

### Terminal Navigation Issues

**Problem**: Interactive menus don't work with arrow keys

**Solution:**
```bash
# Install readchar for interactive menus
pipx install readchar
# or
pip install readchar
```

---

## 📦 Package Information

- **PyPI Package**: [slowql](https://pypi.org/project/slowql/)
- **Docker Images**: 
  - [GHCR](https://github.com/makroumi/slowql/pkgs/container/slowql)
  - [Docker Hub](https://hub.docker.com/r/makroumi/slowql)
- **Version**: v1.3.0 (latest stable)
- **Python Support**: 3.11, 3.12, 3.13

---

## 🔗 Related Pages

- [Quick Start](quick-start.md)
- [Configuration](configuration.md)
- [First Analysis](first-analysis.md)
- [CLI Reference](../user-guide/cli-reference.md)
- [Development Setup](../development/setup.md)
