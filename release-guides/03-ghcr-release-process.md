# GHCR (GitHub Container Registry) Release Process Guide

This guide provides comprehensive instructions for releasing SlowQL to GitHub Container Registry (GHCR), including token setup, authentication, building, tagging, pushing images, and making packages public.

## Table of Contents
- [Prerequisites](#prerequisites)
- [GitHub Token Setup](#github-token-setup)
- [Authentication with GHCR](#authentication-with-ghcr)
- [Building Images with GHCR Tags](#building-images-with-ghcr-tags)
- [Pushing Images to GHCR](#pushing-images-to-ghcr)
- [Making Packages Public](#making-packages-public)
- [Verification and Testing](#verification-and-testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before starting the GHCR release process, ensure you have:
- Docker or Podman installed and running
- GitHub account with access to the SlowQL repository
- GitHub Personal Access Token with package permissions
- Command-line access to your system
- Basic understanding of GitHub Container Registry concepts

## GitHub Token Setup

### Step 1: Create Personal Access Token

#### Using GitHub CLI (Recommended)
```bash
# Install GitHub CLI if not already installed
# Visit: https://cli.github.com/

# Authenticate with GitHub
gh auth login

# Create a token with package permissions
gh auth token

# Or create a new token with specific scopes
gh auth login --with-token
```

#### Using Web Interface
```bash
# Go to GitHub Settings
# Settings → Developer settings → Personal access tokens → Tokens (classic)
# Click "Generate new token" → "Generate new token (classic)"
# Note: Use "Generate new token (fine-grained)" for more granular control

# Token name: "SlowQL GHCR Access"
# Expiration: 90 days (recommended for security)
# Scopes needed:
#   ✓ repo (Full control of private repositories)
#   ✓ write:packages (Upload packages to GitHub Package Registry)
#   ✓ delete:packages (Delete packages from GitHub Package Registry)
#   ✓ admin:org (if needed for organization packages)
#   ✓ read:org (if needed for organization packages)

# Click "Generate token"
# Copy and save the token securely
```

### Step 2: Configure Token Permissions

#### Required Permissions
```bash
# For GHCR, your token needs:
# - write:packages (Upload packages)
# - delete:packages (Delete packages) 
# - repo (Read access to repository)
# - workflow (if using GitHub Actions)

# Check your token permissions at:
# https://github.com/settings/tokens
```

#### Fine-Grained Token Setup (Alternative)
```bash
# For more granular control, create a fine-grained token:
# Settings → Developer settings → Personal access tokens → Fine-grained tokens
# Click "Generate new token"

# Resource access: "Only select repositories"
# Select: makroumi/slowql
# Permissions:
#   ✓ Packages: Read and Write
#   ✓ Metadata: Read
```

### Step 3: Verify Token Setup
```bash
# Test token with GitHub API
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.github.com/user

# Should return your user information
```

## Authentication with GHCR

### Method 1: Docker Login (Recommended)

#### Step 1: Login to GHCR
```bash
# Login using GitHub username and personal access token
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u makroumi --password-stdin

# Or use GitHub CLI to get token
docker login ghcr.io -u makroumi --password-stdin <<< $(gh auth token)

# Verify login
docker info | grep -A 5 "Registry:"
```

#### Step 2: Configure Docker for GHCR
```bash
# Add GHCR to Docker daemon configuration (optional)
# Edit /etc/docker/daemon.json
sudo tee /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": ["https://ghcr.io"],
  "insecure-registries": ["ghcr.io"]
}
EOF

# Restart Docker daemon
sudo systemctl restart docker
```

### Method 2: Podman Login

#### Step 1: Login with Podman
```bash
# Login to GHCR with Podman
echo "YOUR_GITHUB_TOKEN" | podman login ghcr.io -u makroumi --password-stdin

# Verify login
podman info | grep -A 5 "registries:"
```

#### Step 2: Configure Podman Registries
```bash
# Add GHCR to Podman registries
sudo tee /etc/containers/registries.conf << 'EOF'
[registries.search]
registries = ['ghcr.io', 'docker.io', 'quay.io']

[registries.insecure]
registries = ['ghcr.io']

[registries.block]
registries = []
EOF
```

### Method 3: GitHub Actions Authentication

#### Step 1: Set Up Repository Secrets
```bash
# In your GitHub repository:
# Go to Settings → Secrets and variables → Actions
# Add repository secrets:
# GHCR_USERNAME: makroumi
# GHCR_TOKEN: [your personal access token]
```

#### Step 2: Configure Workflow Permissions
```yaml
# In your .github/workflows/ci.yml, add:
permissions:
  contents: read
  packages: write
```

## Building Images with GHCR Tags

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

### Step 2: Build Image with GHCR Tags
```bash
# Build image with GHCR tags
docker build \
  --tag ghcr.io/makroumi/slowql:latest \
  --tag ghcr.io/makroumi/slowql:$VERSION \
  --tag ghcr.io/makroumi/slowql:v$VERSION \
  --build-arg VERSION=$VERSION \
  .

# Build with additional tags
docker build \
  --tag ghcr.io/makroumi/slowql:dev \
  --tag ghcr.io/makroumi/slowql:$VERSION-dev \
  --build-arg VERSION=$VERSION \
  .
```

### Step 3: Multi-Architecture Build for GHCR
```bash
# Enable buildx for cross-platform builds
docker buildx create --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag ghcr.io/makroumi/slowql:latest \
  --tag ghcr.io/makroumi/slowql:$VERSION \
  --push \
  --build-arg VERSION=$VERSION \
  .

# Or build locally first, then push
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag ghcr.io/makroumi/slowql:latest \
  --tag ghcr.io/makroumi/slowql:$VERSION \
  --load \
  --build-arg VERSION=$VERSION \
  .
```

### Step 4: Test the Built Image
```bash
# Test the image locally before pushing
docker run --rm ghcr.io/makroumi/slowql:latest slowql --help

# Test with sample analysis
echo "SELECT * FROM users WHERE id = 1;" | \
docker run -i ghcr.io/makroumi/slowql:latest slowql

# Test export functionality
docker run --rm \
  -v $(pwd):/work \
  -w /work \
  ghcr.io/makroumi/slowql:latest \
  slowql --input-file test_queries.sql --export html
```

## Pushing Images to GHCR

### Step 1: Push Individual Tags
```bash
# Push latest tag
docker push ghcr.io/makroumi/slowql:latest

# Push versioned tags
docker push ghcr.io/makroumi/slowql:$VERSION
docker push ghcr.io/makroumi/slowql:v$VERSION

# Push development tags
docker push ghcr.io/makroumi/slowql:dev
```

### Step 2: Push All Tags
```bash
# Push all tags for the image
docker push ghcr.io/makroumi/slowql --all-tags

# Or use buildx to build and push in one command
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag ghcr.io/makroumi/slowql:latest \
  --tag ghcr.io/makroumi/slowql:$VERSION \
  --push \
  --build-arg VERSION=$VERSION \
  .
```

### Step 3: Verify Push Success
```bash
# Check if images are available on GHCR
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://ghcr.io/v2/makroumi/slowql/tags/list

# Pull the image to verify
docker pull ghcr.io/makroumi/slowql:latest

# Verify image details
docker images ghcr.io/makroumi/slowql
```

## Making Packages Public

### Step 1: Check Package Visibility
```bash
# List packages in your account
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://ghcr.io/v2/makroumi/slowql/manifests/latest

# Check package details
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.github.com/user/packages?package_type=container
```

### Step 2: Make Package Public via GitHub CLI
```bash
# List container packages
gh api --jq '.[].name' /user/packages?package_type=container

# Make package public
gh api --method PUT \
  -H "Authorization: Bearer YOUR_TOKEN" \
  /user/packages/ghcr.io/makroumi/slowql/visibility \
  -f visibility=public

# Or for organization packages
gh api --method PUT \
  -H "Authorization: Bearer YOUR_TOKEN" \
  /orgs/YOUR_ORG/packages/ghcr.io/makroumi/slowql/visibility \
  -f visibility=public
```

### Step 3: Make Package Public via Web Interface
```bash
# Go to GitHub Packages
# https://github.com/users/makroumi/packages/container/slowql

# Click on the package
# Go to "Package settings" (at the bottom)
# Click "Change visibility"
# Select "Public"
# Click "Save changes"
```

### Step 4: Configure Default Visibility
```bash
# Set repository to publish packages to GitHub Packages
# In your repository settings:
# Settings → Actions → General
# Scroll to "Workflow permissions"
# Select "Read and write permissions"
# Check "Allow GitHub Actions to create and comment on pull requests"
# Check "Allow this workflow to send dispatch events to other workflows"

# Also in repository settings:
# Settings → Packages
# Select "GitHub Package Registry"
# Choose default repository for publishing
```

## Verification and Testing

### Step 1: Automated Testing Script
```bash
cat > test_ghcr_release.sh << 'EOF'
#!/bin/bash
set -e

echo "🔍 Testing SlowQL GHCR release..."

# Test 1: Check package availability
echo "✓ Checking package availability..."
curl -s -H "Authorization: Bearer $GHCR_TOKEN" \
     https://ghcr.io/v2/makroumi/slowql/tags/list | \
     jq -r '.tags[]' | head -5

# Test 2: Pull image
echo "✓ Pulling image..."
docker pull ghcr.io/makroumi/slowql:latest

# Test 3: Check version
echo "✓ Checking version..."
docker run --rm ghcr.io/makroumi/slowql:latest slowql --version

# Test 4: Test basic functionality
echo "✓ Testing basic functionality..."
echo "SELECT * FROM test WHERE id = 1;" | \
docker run -i ghcr.io/makroumi/slowql:latest slowql > /dev/null

# Test 5: Test export
echo "✓ Testing export..."
mkdir -p test_reports
docker run --rm \
  -v $(pwd):/work \
  -w /work \
  ghcr.io/makroumi/slowql:latest \
  slowql --input-file test_queries.sql --export json > /dev/null

echo "✅ All GHCR tests passed!"
EOF

chmod +x test_ghcr_release.sh
```

### Step 2: Cross-Platform Testing
```bash
# Test on different architectures
docker pull ghcr.io/makroumi/slowql:latest
docker run --rm ghcr.io/makroumi/slowql:latest slowql --version

# Test ARM64 if available
docker run --rm --platform linux/arm64 ghcr.io/makroumi/slowql:latest slowql --version
```

### Step 3: Package Integrity Verification
```bash
# Verify package integrity
docker inspect ghcr.io/makroumi/slowql:latest

# Check package metadata
curl -H "Authorization: Bearer $GHCR_TOKEN" \
     https://api.github.com/user/packages/ghcr.io/makroumi/slowql
```

## Automation Scripts

### Step 1: Create GHCR Release Script
```bash
cat > release_ghcr.sh << 'EOF'
#!/bin/bash
set -e

VERSION=${1:-latest}
GHCR_USERNAME=${GHCR_USERNAME:-makroumi}
IMAGE_NAME="ghcr.io/$GHCR_USERNAME/slowql"

echo "🚀 Releasing SlowQL $VERSION to GHCR"

# Get version from command line or pyproject.toml
if [ "$VERSION" = "latest" ]; then
    VERSION=$(grep "version" pyproject.toml | head -1 | sed 's/version = "\(.*\)"/\1/')
fi

echo "📦 Building Docker image for version $VERSION"

# Build image with buildx for multi-platform support
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag $IMAGE_NAME:latest \
  --tag $IMAGE_NAME:$VERSION \
  --tag $IMAGE_NAME:v$VERSION \
  --build-arg VERSION=$VERSION \
  --load \
  .

echo "🔐 Logging in to GHCR"
echo "$GHCR_TOKEN" | docker login ghcr.io -u $GHCR_USERNAME --password-stdin

echo "📤 Pushing to GHCR"
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag $IMAGE_NAME:latest \
  --tag $IMAGE_NAME:$VERSION \
  --tag $IMAGE_NAME:v$VERSION \
  --push \
  --build-arg VERSION=$VERSION \
  .

echo "✅ GHCR release completed successfully!"
echo "🔗 Package available at: https://github.com/users/$GHCR_USERNAME/packages/container/$IMAGE_NAME"
EOF

chmod +x release_ghcr.sh
```

### Step 2: Use Release Script
```bash
# Set environment variable
export GHCR_TOKEN="your_github_token_here"

# Release specific version
./release_ghcr.sh 2.0.0

# Release latest (from pyproject.toml)
./release_ghcr.sh latest
```

### Step 3: GitHub Actions Workflow
```yaml
# .github/workflows/release-ghcr.yml
name: Release to GHCR

on:
  push:
    tags: ['v*']

jobs:
  release-ghcr:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:latest
            ghcr.io/${{ github.repository }}:${{ steps.version.outputs.VERSION }}
            ghcr.io/${{ github.repository }}:v${{ steps.version.outputs.VERSION }}
          build-args: |
            VERSION=${{ steps.version.outputs.VERSION }}
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Authentication Failures
```bash
# Check if token is valid
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.github.com/user

# Re-authenticate
docker logout ghcr.io
echo "YOUR_TOKEN" | docker login ghcr.io -u makroumi --password-stdin

# Verify token permissions
# Ensure token has write:packages permission
```

#### 2. Permission Denied Errors
```bash
# Check repository permissions
# Ensure you have write access to the repository
# Verify token has correct scopes

# For organization packages, check organization settings
# Organization → Settings → Packages
# Ensure packages are allowed and you have permissions
```

#### 3. Package Not Found
```bash
# Verify package URL format
# Should be: ghcr.io/OWNER/REPOSITORY/IMAGE_NAME
# Example: ghcr.io/makroumi/slowql/slowql

# Check if package exists
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://ghcr.io/v2/makroumi/slowql/manifests/latest
```

#### 4. Visibility Issues
```bash
# Check package visibility
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.github.com/user/packages/ghcr.io/makroumi/slowql

# Make package public if needed
gh api --method PUT \
  -H "Authorization: Bearer YOUR_TOKEN" \
  /user/packages/ghcr.io/makroumi/slowql/visibility \
  -f visibility=public
```

#### 5. Build Failures
```bash
# Check Docker build logs
docker build --no-cache --progress=plain .

# Verify Dockerfile syntax
# Check base image availability
# Ensure sufficient disk space
docker system df
```

#### 6. Multi-Platform Build Issues
```bash
# Check buildx availability
docker buildx version

# Create buildx instance
docker buildx create --use

# Check available platforms
docker buildx inspect --bootstrap
```

### Security Best Practices

#### 1. Token Management
```bash
# Use fine-grained tokens when possible
# Set appropriate expiration dates
# Rotate tokens regularly
# Store tokens securely (GitHub Secrets, environment variables)

# Avoid committing tokens to repository
# Use .gitignore for token files
echo ".token" >> .gitignore
```

#### 2. Image Security
```bash
# Scan images for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image ghcr.io/makroumi/slowql:latest

# Use specific tags instead of :latest
# Regularly update base images
# Run containers as non-root user
```

#### 3. Access Control
```bash
# Review package access regularly
# Remove unnecessary collaborators
# Use organization-level package settings
# Monitor package downloads and access
```

## Advanced Features

### Step 1: Package Version Management
```bash
# List package versions
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://ghcr.io/v2/makroumi/slowql/tags/list

# Delete old versions (if needed)
curl -X DELETE \
     -H "Authorization: Bearer YOUR_TOKEN" \
     https://ghcr.io/v2/makroumi/slowql/manifests/old-version-tag
```

### Step 2: Package Documentation
```bash
# Add README to package
# Create README.md file in repository root
# GHCR will automatically use this as package description

# Add package badges to README.md
# Example badges for GHCR
```

### Step 3: Package Analytics
```bash
# Monitor package usage
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://api.github.com/user/packages/ghcr.io/makroumi/slowql

# Track download statistics
# Monitor package health
```

## Next Steps

After successfully releasing to GHCR:

1. **Update Documentation**: Add GHCR badges and usage examples
2. **Set Up Monitoring**: Track package usage and health
3. **Configure Webhooks**: Set up notifications for package events
4. **Plan Multi-Registry Strategy**: Consider DockerHub + GHCR distribution

## Additional Resources

- [GitHub Container Registry Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Docker Buildx Documentation](https://docs.docker.com/buildx/)
- [GitHub Actions for Packages](https://docs.github.com/en/packages/working-with-a-github-packages-registry/automatically-publishing-a-package-to-github-packages)
- [Package Security Best Practices](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry#authenticating-to-the-container-registry)

For issues specific to GHCR releases, please refer to the [project documentation](https://slowql.dev/docs) or open an issue on [GitHub](https://github.com/makroumi/slowql/issues).