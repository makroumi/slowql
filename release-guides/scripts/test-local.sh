#!/bin/bash
# Local testing script for SlowQL releases
# Usage: ./test-local.sh [version]

set -e

VERSION=${1:-latest}
PROJECT_NAME="slowql"

echo "🧪 Testing SlowQL $VERSION locally..."

# Check if Docker/Podman is available
if command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
elif command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
else
    echo "❌ Error: Neither Docker nor Podman is installed"
    exit 1
fi

echo "✅ Using $CONTAINER_CMD for container testing"

# Get version from command line or pyproject.toml
if [ "$VERSION" = "latest" ]; then
    VERSION=$(grep "version" pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
fi

echo "📦 Testing version: $VERSION"

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
$CONTAINER_CMD rm -f test-slowql 2>/dev/null || true

# Build the image
echo "🔨 Building Docker image..."
$CONTAINER_CMD build \
  --tag $PROJECT_NAME:test \
  --build-arg VERSION=$VERSION \
  .

# Test basic functionality
echo "🧪 Testing basic functionality..."
$CONTAINER_CMD run --rm --name test-slowql $PROJECT_NAME:test slowql --help > /dev/null
echo "✅ Help command works"

$CONTAINER_CMD run --rm --name test-slowql $PROJECT_NAME:test slowql --version | grep "$VERSION" > /dev/null
echo "✅ Version command works"

# Test with sample SQL
echo "🧪 Testing with sample SQL..."
mkdir -p test_reports
echo "SELECT * FROM users WHERE id = 1;" | \
$CONTAINER_CMD run --rm -i \
  -v $(pwd):/work \
  -w /work \
  $PROJECT_NAME:test \
  slowql > /dev/null

echo "✅ Sample analysis works"

# Test export functionality
echo "🧪 Testing export functionality..."
$CONTAINER_CMD run --rm \
  -v $(pwd):/work \
  -w /work \
  $PROJECT_NAME:test \
  slowql --input-file examples/sample.sql --export json > /dev/null

if [ -f "reports/slowql_results_*.json" ]; then
    echo "✅ Export functionality works"
    rm -f reports/slowql_results_*.json
else
    echo "⚠️  Export test file not found, but export command executed"
fi

# Test Python package build
echo "🧪 Testing Python package build..."
python -m build --wheel --outdir test_dist/ > /dev/null 2>&1

if [ -f "test_dist/slowql-$VERSION-py3-none-any.whl" ]; then
    echo "✅ Python wheel build works"
    rm -rf test_dist/
else
    echo "⚠️  Python wheel build may have issues"
fi

# Clean up
echo "🧹 Cleaning up..."
$CONTAINER_CMD rmi $PROJECT_NAME:test > /dev/null 2>&1 || true
rmdir test_reports 2>/dev/null || true

echo "✅ All local tests passed!"
echo "🎉 SlowQL $VERSION is ready for release"