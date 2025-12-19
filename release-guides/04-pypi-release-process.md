# PyPI Release Process Guide

This guide provides comprehensive instructions for releasing SlowQL to PyPI (Python Package Index), including account setup, API token creation, building packages, uploading, and verification steps.

## Table of Contents
- [Prerequisites](#prerequisites)
- [PyPI Account Setup](#pypi-account-setup)
- [API Token Creation](#api-token-creation)
- [Building the Package](#building-the-package)
- [Uploading to PyPI](#uploading-to-pypi)
- [Verification Steps](#verification-steps)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before starting the PyPI release process, ensure you have:
- Python 3.11+ installed
- pip package manager
- A GitHub repository with SlowQL source code
- Administrative access to the SlowQL repository
- Basic understanding of Python packaging concepts

## PyPI Account Setup

### Step 1: Create PyPI Account

#### Create Production PyPI Account
```bash
# Visit https://pypi.org/account/register/
# Fill in the registration form:
# Username: makroumi (or your preferred username)
# Email: contact@makroumi.dev
# Password: [secure password]
# Confirm password

# Verify your email address by clicking the link sent to your email
```

#### Create Test PyPI Account (Recommended for Testing)
```bash
# Visit https://test.pypi.org/account/register/
# Create a separate account for testing
# Username: makroumi-test (or similar)
# Email: contact@makroumi.dev
# Password: [secure password]

# Verify email for test account
```

### Step 2: Set Up Two-Factor Authentication (Recommended)
```bash
# After logging in to PyPI:
# Go to Account Settings → Two factor authentication
# Choose your preferred method:
# - Authenticator app (recommended)
# - Security keys
# - Email codes

# Follow the setup instructions
# Save backup codes in a secure location
```

### Step 3: Complete Profile Information
```bash
# In your PyPI profile:
# Add full name: makroumi
# Add bio: "Maintainer of SlowQL - Next-generation SQL analyzer"
# Add location: [your location]
# Add website: https://github.com/makroumi/slowql
# Add profile picture (optional)
```

## API Token Creation

### Step 1: Create API Token on PyPI

#### For Production PyPI
```bash
# Log in to PyPI (https://pypi.org)
# Go to Account Settings → API tokens
# Click "Add API token"
# Token name: "SlowQL Release Token"
# Scope: "Entire account" or "Project: slowql" (if available)
# Click "Create token"
# Copy and save the token securely (format: pypi-...)
```

#### For Test PyPI
```bash
# Log in to Test PyPI (https://test.pypi.org)
# Go to Account Settings → API tokens
# Click "Add API token"
# Token name: "SlowQL Test Release Token"
# Scope: "Entire account" or "Project: slowql" (if available)
# Click "Create token"
# Copy and save the token securely (format: pypi-...)
```

### Step 2: Configure Token Security
```bash
# Store tokens securely:
# Option 1: Environment variables
export PYPI_TOKEN="pypi-xxxxxxxxxxxxxxxxx"
export TEST_PYPI_TOKEN="pypi-xxxxxxxxxxxxxxxxx"

# Option 2: .pypirc file (recommended)
# Create ~/.pypirc file
cat > ~/.pypirc << 'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-xxxxxxxxxxxxxxxxx

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-xxxxxxxxxxxxxxxxx
EOF

# Set appropriate permissions
chmod 600 ~/.pypirc
```

### Step 3: Test Token Access
```bash
# Test token with Twine
pip install twine

# Test connection to PyPI
twine check dist/*

# Test upload to Test PyPI (dry run)
twine upload --repository testpypi dist/* --dry-run
```

## Building the Package

### Step 1: Prepare Build Environment
```bash
# Clone the repository
git clone https://github.com/makroumi/slowql.git
cd slowql

# Verify you have the latest code
git pull origin main
git checkout main

# Check current version
VERSION=$(grep "version" pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
echo "Current version: $VERSION"
```

### Step 2: Install Build Dependencies
```bash
# Install build tools
pip install --upgrade pip
pip install build twine

# Install project in development mode (optional)
pip install -e ".[dev]"
```

### Step 3: Clean Previous Builds
```bash
# Clean any existing build artifacts
make clean

# Or manually clean
rm -rf build/ dist/ *.egg-info/

# Verify clean state
ls -la | grep -E "(build|dist|\.egg-info)"
```

### Step 4: Build the Package
```bash
# Build source distribution and wheel
python -m build

# Or build specific formats
python -m build --sdist
python -m build --wheel

# Check build output
ls -la dist/

# Should output:
# slowql-2.0.0-py3-none-any.whl (wheel)
# slowql-2.0.0.tar.gz (source distribution)
```

### Step 5: Verify Package Contents
```bash
# Check wheel contents
python -m zipfile -l dist/slowql-*.whl

# Check source distribution contents
python -m tarfile -l dist/slowql-*.tar.gz

# Verify package metadata
python -m pip show slowql
```

## Uploading to PyPI

### Step 1: Test Upload to Test PyPI (Recommended)
```bash
# Upload to Test PyPI first
twine upload --repository testpypi dist/*

# You'll be prompted for username and password
# Username: __token__
# Password: your Test PyPI token

# Verify the upload
# Visit: https://test.pypi.org/project/slowql/
```

### Step 2: Test Installation from Test PyPI
```bash
# Create a fresh virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ slowql

# Test the installation
slowql --version
slowql --help

# Test with sample analysis
echo "SELECT * FROM users" | slowql

# Clean up
deactivate
rm -rf test_env
```

### Step 3: Upload to Production PyPI
```bash
# Upload to production PyPI
twine upload dist/*

# You'll be prompted for username and password
# Username: __token__
# Password: your PyPI token

# Or use specific repository
twine upload --repository pypi dist/*

# Verify the upload
# Visit: https://pypi.org/project/slowql/
```

### Step 4: Create Git Tag for Release
```bash
# Create annotated tag for the release
git tag -a v$VERSION -m "Release version $VERSION"

# Push tag to GitHub
git push origin v$VERSION

# Create GitHub release (optional)
gh release create v$VERSION \
  --title "SlowQL v$VERSION" \
  --notes "Release version $VERSION - see CHANGELOG.md for details" \
  --generate-notes

# List tags to verify
git tag -l
```

## Verification Steps

### Step 1: Verify Package on PyPI
```bash
# Check package page
open https://pypi.org/project/slowql/

# Verify package information:
# - Name: slowql
# - Version: 2.0.0
# - Author: makroumi
# - Description: Next-generation SQL analyzer
# - Keywords: sql, analyzer, linter, security, performance
# - License: Apache-2.0
# - Python versions: >=3.11
```

### Step 2: Test Installation from Production PyPI
```bash
# Create a fresh virtual environment
python -m venv prod_test_env
source prod_test_env/bin/activate  # On Windows: prod_test_env\Scripts\activate

# Install from production PyPI
pip install slowql

# Test the installation
slowql --version
slowql --help

# Test with sample analysis
echo "SELECT * FROM users WHERE id = 1;" | slowql

# Test interactive mode (if readchar is available)
slowql --mode auto

# Test export functionality
echo "SELECT * FROM test" | slowql --export json

# Clean up
deactivate
rm -rf prod_test_env
```

### Step 3: Verify Package Metadata
```bash
# Check installed package metadata
python -c "import slowql; print(slowql.__version__)"
python -c "import slowql; print(slowql.__file__)"

# Check package information
pip show slowql

# Verify entry points
python -c "from slowql.cli.app import main; print('CLI entry point works')"

# Check installed dependencies
pip list | grep -E "(rich|typer|pydantic|sqlglot)"
```

### Step 4: Cross-Platform Testing
```bash
# Test on different Python versions (if available)
# Python 3.11
python3.11 -m venv test_env_311
source test_env_311/bin/activate
pip install slowql
slowql --version
deactivate
rm -rf test_env_311

# Python 3.12
python3.12 -m venv test_env_312
source test_env_312/bin/activate
pip install slowql
slowql --version
deactivate
rm -rf test_env_312

# Python 3.13 (if available)
python3.13 -m venv test_env_313
source test_env_313/bin/activate
pip install slowql
slowql --version
deactivate
rm -rf test_env_313
```

## Automation Scripts

### Step 1: Create Release Script
```bash
cat > release_pypi.sh << 'EOF'
#!/bin/bash
set -e

VERSION=${1:-latest}
TEST_PYPI=${TEST_PYPI:-false}

echo "🚀 Releasing SlowQL $VERSION to PyPI"

# Get version from command line or pyproject.toml
if [ "$VERSION" = "latest" ]; then
    VERSION=$(grep "version" pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
fi

echo "📦 Version: $VERSION"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Build package
echo "🔨 Building package..."
python -m build

# Check package
echo "✅ Checking package..."
twine check dist/*

# Determine repository
if [ "$TEST_PYPI" = "true" ]; then
    REPO="--repository testpypi"
    echo "📤 Uploading to Test PyPI..."
else
    REPO=""
    echo "📤 Uploading to PyPI..."
fi

# Upload package
echo "⬆️ Uploading package..."
twine $REPO dist/*

# Create git tag
if [ "$TEST_PYPI" = "false" ]; then
    echo "🏷️ Creating git tag..."
    git tag -a v$VERSION -m "Release version $VERSION"
    git push origin v$VERSION
fi

echo "✅ PyPI release completed successfully!"
echo "🔗 Package available at: https://pypi.org/project/slowql/"
EOF

chmod +x release_pypi.sh
```

### Step 2: Use Release Script
```bash
# Set PyPI token environment variable
export PYPI_TOKEN="pypi-xxxxxxxxxxxxxxxxx"

# Release to Test PyPI first
TEST_PYPI=true ./release_pypi.sh 2.0.0

# If tests pass, release to production
./release_pypi.sh 2.0.0

# Release latest version (from pyproject.toml)
./release_pypi.sh latest
```

### Step 3: GitHub Actions Workflow
```yaml
# .github/workflows/release-pypi.yml
name: Release to PyPI

on:
  push:
    tags: ['v*']

jobs:
  release-pypi:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip
          python -m pip install build twine

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT

      - name: Build package
        run: |
          SETUPTOOLS_SCM_PRETEND_VERSION_FOR_SLOWQL=${{ steps.version.outputs.VERSION }} \
          python -m build

      - name: Check package
        run: twine check dist/*

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_TOKEN }}
          skip-existing: true
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Package Name Already Exists
```bash
# Check if package name is taken
curl https://pypi.org/pypi/slowql/json

# If name is taken, you have options:
# 1. Choose a different name (e.g., slowql-analyzer)
# 2. Contact the existing maintainer
# 3. Use a scoped package name (if available)

# Update pyproject.toml with new name
sed -i 's/name = "slowql"/name = "slowql-analyzer"/' pyproject.toml
```

#### 2. Version Already Exists
```bash
# Check existing versions
curl https://pypi.org/pypi/slowql/json | jq '.releases | keys'

# Increment version in pyproject.toml
sed -i 's/version = "2.0.0"/version = "2.0.1"/' pyproject.toml

# Or use semantic versioning
# Patch: 2.0.0 -> 2.0.1 (bug fixes)
# Minor: 2.0.0 -> 2.1.0 (new features)
# Major: 2.0.0 -> 3.0.0 (breaking changes)
```

#### 3. Upload Authentication Failures
```bash
# Check token validity
curl -H "Authorization: token YOUR_TOKEN" https://pypi.org/legacy/

# Re-authenticate
twine upload dist/* --username __token__ --password YOUR_TOKEN

# Check token permissions
# Ensure token has scope for the project
# Verify token hasn't expired
```

#### 4. Package Build Failures
```bash
# Check build dependencies
pip install --upgrade pip build setuptools wheel

# Verify pyproject.toml syntax
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"

# Check for missing files
python -m build --sdist --outdir dist/ --no-isolation

# Enable verbose output
python -m build --verbose
```

#### 5. Package Installation Failures
```bash
# Check package integrity
pip install --dry-run slowql

# Verify dependencies
pip install --dry-run --report - slowql

# Check platform compatibility
pip check slowql

# Test with verbose output
pip install -v slowql
```

#### 6. Metadata Issues
```bash
# Validate package metadata
twine check dist/*

# Check for common issues:
# - Missing description
# - Invalid classifiers
# - Missing keywords
# - Incorrect license

# Verify long description
python -c "from slowql import __doc__; print(__doc__)"
```

### Package Quality Checks

#### 1. Code Quality
```bash
# Run linters
ruff check src/ tests/

# Run type checker
mypy src/

# Run tests
pytest tests/ --cov=src/

# Check code formatting
ruff format --check src/ tests/
```

#### 2. Package Validation
```bash
# Check package contents
python -m zipfile -l dist/slowql-*.whl

# Verify entry points
python -c "from pkg_resources import iter_entry_points; print(list(iter_entry_points('console_scripts', 'slowql')))"

# Check dependencies
pip show slowql
```

#### 3. Security Scanning
```bash
# Scan for vulnerabilities
pip install safety
safety check

# Check for known security issues
pip install bandit
bandit -r src/
```

## Post-Release Tasks

### Step 1: Update Documentation
```bash
# Update README.md badges
# Add new PyPI version badge
[![PyPI](https://img.shields.io/pypi/v/slowql?logo=pypi)](https://pypi.org/project/slowql/)

# Update installation instructions
pip install slowql

# Update version-specific examples
```

### Step 2: Create Announcement
```bash
# Create GitHub release notes
# Write blog post (if applicable)
# Update social media
# Notify community channels
```

### Step 3: Monitor Package Health
```bash
# Check download statistics
# Visit: https://pypistats.org/packages/slowql

# Monitor for issues
# Check GitHub issues and discussions
# Monitor PyPI package page for feedback
```

### Step 4: Plan Next Release
```bash
# Collect user feedback
# Plan new features
# Update development roadmap
# Schedule next release cycle
```

## Security Best Practices

### Step 1: Token Security
```bash
# Store tokens securely
# Use environment variables or .pypirc
# Never commit tokens to repository
# Rotate tokens regularly
# Use scoped tokens when possible

# Set up token monitoring
# Review token usage regularly
# Revoke unused tokens
```

### Step 2: Package Security
```bash
# Scan dependencies for vulnerabilities
pip install safety bandit
safety check
bandit -r src/

# Keep dependencies updated
pip list --outdated
pip install --upgrade package_name

# Use dependency pinning in requirements
pip freeze > requirements.txt
```

### Step 3: Release Security
```bash
# Verify build environment
# Use clean, isolated build environment
# Sign releases (if applicable)
# Review code before release
# Use automated testing

# Monitor for compromised packages
# Check PyPI for typosquatting
# Monitor security advisories
```

## Advanced Features

### Step 1: Multiple Package Distribution
```bash
# For monorepo projects
# Split into multiple packages
# Use workspace tools (poetry, hatch)

# Example with hatch
hatch new package1
hatch new package2
```

### Step 2: Beta/Pre-release Testing
```bash
# Create pre-release versions
# Use semantic versioning: 2.0.0b1, 2.0.0rc1
# Test with beta users
# Gather feedback before stable release

# Upload pre-release to Test PyPI
twine upload --repository testpypi dist/slowql-2.0.0b1*
```

### Step 3. Package Analytics
```bash
# Monitor PyPI statistics
# Use PyPI stats API
# Track download trends
# Analyze user behavior

# Set up monitoring
# Monitor for unusual download patterns
# Track package health metrics
```

## Additional Resources

- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI Help Documentation](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Build Package Documentation](https://pypa-build.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)
- [Python Package Security](https://python.org/dev/security/)

For issues specific to PyPI releases, please refer to the [project documentation](https://slowql.dev/docs) or open an issue on [GitHub](https://github.com/makroumi/slowql/issues).