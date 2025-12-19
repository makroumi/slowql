# SlowQL Release Guides

This directory contains comprehensive release guides for the SlowQL project, covering all major distribution platforms and deployment methods.

## Overview

SlowQL is a next-generation SQL analyzer that provides security, performance, compliance, and cost optimization analysis. This collection of guides covers the complete release process across multiple platforms:

- **Local Development**: Podman-based local pod creation
- **Container Registries**: DockerHub and GitHub Container Registry (GHCR)
- **Python Package Index**: PyPI for Python package distribution

## Available Guides

### 1. [Podman Local Pod Creation Guide](01-podman-local-pod-creation.md)

**Purpose**: Step-by-step instructions for setting up and running SlowQL locally using Podman.

**Key Topics**:
- Installing Podman on different platforms
- Creating and managing local pods
- Building Docker images locally
- Testing containers in local environment
- Advanced usage with volumes and environment variables
- Troubleshooting common Podman issues

**Best For**: Developers who want to test SlowQL locally before release, or set up local development environments.

---

### 2. [DockerHub Release Process Guide](02-dockerhub-release-process.md)

**Purpose**: Complete guide for releasing SlowQL Docker images to DockerHub container registry.

**Key Topics**:
- DockerHub account setup and repository configuration
- Authentication using CLI tokens and personal access tokens
- Building and tagging images for different architectures
- Pushing images to DockerHub with proper versioning
- Creating GitHub releases and tags
- Automated release scripts and GitHub Actions workflows
- Verification and testing procedures

**Best For**: Developers who want to distribute SlowQL via DockerHub for easy container deployment.

---

### 3. [GHCR Release Process Guide](03-ghcr-release-process.md)

**Purpose**: Comprehensive guide for releasing SlowQL to GitHub Container Registry (GHCR).

**Key Topics**:
- GitHub Personal Access Token setup with package permissions
- Authentication methods for GHCR
- Building images with proper GHCR tagging conventions
- Pushing images and making packages public
- Multi-platform builds and cross-architecture support
- Package visibility management and access control
- Integration with GitHub Actions and automated workflows

**Best For**: Developers who prefer GitHub-native container distribution or want seamless integration with GitHub workflows.

---

### 4. [PyPI Release Process Guide](04-pypi-release-process.md)

**Purpose**: Complete Python package release guide for distributing SlowQL via PyPI.

**Key Topics**:
- PyPI and Test PyPI account setup
- API token creation and secure configuration
- Building Python packages with proper metadata
- Uploading to Test PyPI for validation before production
- Verification steps and cross-platform testing
- Automation scripts and GitHub Actions workflows
- Package security best practices and quality checks

**Best For**: Python developers who want to install SlowQL via pip or distribute it as a Python package.

---

## Quick Start Guide

### For Local Development
1. Start with [Podman Local Pod Creation Guide](01-podman-local-pod-creation.md)
2. Set up local testing environment
3. Use provided troubleshooting section for common issues

### For Container Distribution
1. Choose your preferred registry:
   - **DockerHub**: Follow [DockerHub Release Process Guide](02-dockerhub-release-process.md)
   - **GHCR**: Follow [GHCR Release Process Guide](03-ghcr-release-process.md)
2. Set up authentication and repository access
3. Use automation scripts for consistent releases

### For Python Package Distribution
1. Follow [PyPI Release Process Guide](04-pypi-release-process.md)
2. Start with Test PyPI for validation
3. Use provided scripts for automated releases

---

## Prerequisites Summary

All guides assume you have:
- Git installed and access to the SlowQL repository
- Basic command-line knowledge
- Administrative access to your chosen platforms

Platform-specific requirements:
- **Podman**: Docker/Podman installed, Linux/macOS/Windows with WSL2
- **DockerHub**: DockerHub account, Docker CLI
- **GHCR**: GitHub account, Personal Access Token, Docker/Podman
- **PyPI**: Python 3.11+, pip, PyPI account, API token

---

## Release Workflow

### Recommended Release Process

1. **Pre-Release Testing**
   ```bash
   # Local testing with Podman
   ./release-guides/scripts/test-local.sh
   
   # Package validation
   ./release-guides/scripts/validate-package.sh
   ```

2. **Container Release**
   ```bash
   # Build and test container locally
   docker build -t slowql:test .
   docker run --rm slowql:test slowql --help
   
   # Release to chosen registry
   ./release-guides/scripts/release-dockerhub.sh 2.0.0
   # OR
   ./release-guides/scripts/release-ghcr.sh 2.0.0
   ```

3. **Python Package Release**
   ```bash
   # Test on Test PyPI first
   TEST_PYPI=true ./release-guides/scripts/release-pypi.sh 2.0.0
   
   # If tests pass, release to production
   ./release-guides/scripts/release-pypi.sh 2.0.0
   ```

4. **Post-Release Verification**
   ```bash
   # Verify all distribution channels
   ./release-guides/scripts/verify-release.sh 2.0.0
   ```

---

## Automation Scripts

Each guide includes automation scripts to streamline the release process:

- **Release Scripts**: Automated building, tagging, and uploading
- **Test Scripts**: Validation before production releases
- **Cleanup Scripts**: Maintenance and old version management
- **GitHub Actions**: CI/CD integration examples

Usage:
```bash
# Make scripts executable
chmod +x release-guides/scripts/*.sh

# Use release scripts
./release-guides/scripts/release-dockerhub.sh 2.0.0
./release-guides/scripts/release-ghcr.sh 2.0.0
./release-guides/scripts/release-pypi.sh 2.0.0
```

---

## Security Considerations

All guides include security best practices:

- **Token Management**: Secure storage and rotation of API tokens
- **Package Security**: Vulnerability scanning and dependency checking
- **Access Control**: Proper permissions and visibility settings
- **Verification**: Multiple validation steps before production releases

---

## Troubleshooting

Each guide includes comprehensive troubleshooting sections covering:
- Common authentication issues
- Build and upload failures
- Permission and access problems
- Platform-specific issues
- Performance optimization tips

---

## Project Information

- **Project**: SlowQL - Next-generation SQL analyzer
- **Repository**: https://github.com/makroumi/slowql
- **Documentation**: https://slowql.dev/docs
- **Current Version**: 2.0.0
- **Python Support**: 3.11+
- **License**: Apache-2.0

---

## Contributing

These guides are part of the SlowQL project. To contribute:

1. **Improvements**: Suggest enhancements to existing guides
2. **New Platforms**: Add guides for additional distribution platforms
3. **Automation**: Contribute scripts and GitHub Actions workflows
4. **Documentation**: Improve clarity and add examples

### Development Setup
```bash
git clone https://github.com/makroumi/slowql.git
cd slowql/release-guides

# Edit guides with your preferred markdown editor
# Test scripts in a safe environment
# Submit pull requests with improvements
```

---

## Additional Resources

- [SlowQL Main Documentation](https://slowql.dev/docs)
- [GitHub Repository](https://github.com/makroumi/slowql)
- [Issue Tracker](https://github.com/makroumi/slowql/issues)
- [Discussions](https://github.com/makroumi/slowql/discussions)
- [Security Policy](https://github.com/makroumi/slowql/blob/main/SECURITY.md)

---

## Support

For issues with these release guides:
- Check the troubleshooting sections in each guide
- Search existing [GitHub Issues](https://github.com/makroumi/slowql/issues)
- Create a new issue with the "release-guides" label
- Join the [Discussions](https://github.com/makroumi/slowql/discussions) for general questions

---

**Last Updated**: December 2025
**Guide Version**: 1.0.0
**SlowQL Version**: 2.0.0