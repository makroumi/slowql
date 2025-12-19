# Podman Local Pod Creation Guide

This guide provides step-by-step instructions for setting up and running SlowQL locally using Podman.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installing Podman](#installing-podman)
- [Creating a Local Pod](#creating-a-local-pod)
- [Building the Docker Image Locally](#building-the-docker-image-locally)
- [Testing the Container Locally](#testing-the-container-locally)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before starting, ensure you have:
- A Linux, macOS, or Windows system with Podman support
- Sufficient disk space (at least 2GB for images and containers)
- Git (for cloning the repository)
- Basic understanding of containerization concepts

## Installing Podman

### Ubuntu/Debian
```bash
# Update package index
sudo apt update

# Install Podman
sudo apt install podman

# Verify installation
podman --version
```

### Fedora/CentOS/RHEL
```bash
# Install Podman
sudo dnf install podman

# Or for older CentOS/RHEL
sudo yum install podman

# Verify installation
podman --version
```

### macOS
```bash
# Using Homebrew
brew install podman

# Start Podman machine (required for macOS)
podman machine init
podman machine start

# Verify installation
podman --version
```

### Windows (WSL2)
```bash
# In WSL2 terminal
sudo apt update
sudo apt install podman

# Verify installation
podman --version
```

## Creating a Local Pod

### Step 1: Verify Podman Installation
```bash
# Check Podman version and info
podman --version
podman info

# List any existing pods
podman pod ls
```

### Step 2: Create a Pod for SlowQL
```bash
# Create a pod with port mapping (for any web interface if needed)
podman pod create \
  --name slowql-pod \
  -p 8080:8080

# Or create a pod without port mapping (recommended for CLI-only usage)
podman pod create \
  --name slowql-pod
```

### Step 3: Verify Pod Creation
```bash
# List pods
podman pod ls

# Inspect the pod
podman pod inspect slowql-pod
```

## Building the Docker Image Locally

### Step 1: Clone the Repository
```bash
# Clone the SlowQL repository
git clone https://github.com/makroumi/slowql.git
cd slowql

# Verify you're in the correct directory
ls -la | grep -E "(Dockerfile|pyproject.toml|README.md)"
```

### Step 2: Build the Image
```bash
# Build the image using Podman
podman build \
  --tag slowql:latest \
  --build-arg VERSION=2.0.0 \
  .

# Alternative: Build without build args (uses default version)
podman build --tag slowql:latest .
```

### Step 3: Verify the Image
```bash
# List built images
podman images | grep slowql

# Inspect the image
podman inspect slowql:latest
```

## Testing the Container Locally

### Step 1: Create Test Data
```bash
# Create a test SQL file
cat > test_queries.sql << 'EOF'
-- Test SQL queries for SlowQL analysis
SELECT * FROM users WHERE id = 1;

SELECT u.name, p.title 
FROM users u 
JOIN posts p ON u.id = p.user_id 
WHERE u.active = true;

UPDATE users SET last_login = NOW() WHERE id = 1;

DELETE FROM sessions WHERE expired = true;
EOF
```

### Step 2: Run SlowQL Container
```bash
# Run SlowQL in the pod
podman run \
  --pod slowql-pod \
  -v $(pwd):/work \
  -w /work \
  slowql:latest \
  slowql --input-file test_queries.sql

# Or run without pod (standalone container)
podman run \
  -v $(pwd):/work \
  -w /work \
  slowql:latest \
  slowql --input-file test_queries.sql
```

### Step 3: Test Interactive Mode
```bash
# Test interactive mode with terminal
podman run \
  -it \
  --pod slowql-pod \
  -v $(pwd):/work \
  -w /work \
  slowql:latest \
  slowql --mode auto
```

### Step 4: Test Export Functionality
```bash
# Test export to multiple formats
podman run \
  --pod slowql-pod \
  -v $(pwd):/work \
  -w /work \
  slowql:latest \
  slowql --input-file test_queries.sql --export html csv json

# Check generated reports
ls -la reports/
```

## Advanced Usage

### Step 1: Create a Persistent Volume
```bash
# Create a named volume for persistent data
podman volume create slowql-data

# Run container with volume mounted
podman run \
  --pod slowql-pod \
  -v slowql-data:/data \
  -v $(pwd):/work \
  -w /work \
  slowql:latest \
  slowql --input-file test_queries.sql --out /data/reports
```

### Step 2: Set Up Environment Variables
```bash
# Run with custom environment variables
podman run \
  --pod slowql-pod \
  -e SLOWQL_CACHE_DIR=/tmp/cache \
  -e SLOWQL_VERBOSE=true \
  -v $(pwd):/work \
  -w /work \
  slowql:latest \
  slowql --input-file test_queries.sql
```

### Step 3: Run as Non-Root User
```bash
# Create a user namespace for security
podman run \
  --pod slowql-pod \
  --user 1000:1000 \
  -v $(pwd):/work \
  -w /work \
  slowql:latest \
  slowql --input-file test_queries.sql
```

## Verification Steps

### 1. Verify Container Status
```bash
# Check pod status
podman pod ps

# Check container status within pod
podman ps --pod
```

### 2. Verify SlowQL Functionality
```bash
# Test help command
podman run --pod slowql-pod slowql:latest slowql --help

# Test version command
podman run --pod slowql-pod slowql:latest slowql --version

# Test with sample analysis
echo "SELECT * FROM test" | podman run --pod slowql-pod -i slowql:latest slowql
```

### 3. Check Logs and Debugging
```bash
# View container logs
podman logs <container-id>

# Follow logs in real-time
podman logs -f <container-id>

# Execute shell in container for debugging
podman exec -it <container-id> /bin/bash
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Podman Not Found
```bash
# Check if Podman is installed
which podman

# If not found, reinstall using your package manager
# For Ubuntu/Debian:
sudo apt update && sudo apt install podman
```

#### 2. Permission Denied Errors
```bash
# On Linux, you might need to configure subuid/subgid
echo "$USER:100000:65536" | sudo tee -a /etc/subuid
echo "$USER:100000:65536" | sudo tee -a /etc/subgid

# Restart Podman service
sudo systemctl restart podman
```

#### 3. Build Failures
```bash
# Clear Podman cache
podman system prune -a

# Try building with --no-cache flag
podman build --no-cache --tag slowql:latest .
```

#### 4. Container Won't Start
```bash
# Check detailed error messages
podman run --pod slowql-pod slowql:latest 2>&1

# Inspect container state
podman inspect <container-id>

# Check system resources
podman system df
```

#### 5. Port Binding Issues
```bash
# Check if ports are already in use
sudo netstat -tulpn | grep 8080

# Use different port mapping
podman pod create --name slowql-pod -p 8081:8080
```

#### 6. Volume Mounting Issues
```bash
# Check SELinux context (Linux)
sudo setsebool -P container_manage_cgroup on

# Use :Z flag for SELinux
podman run -v $(pwd):/work:Z slowql:latest slowql --help
```

### Performance Optimization

#### 1. Use Build Cache
```bash
# Enable build cache
export BUILDAH_FORMAT=docker

# Use cache-from for remote caching
podman build --cache-from=slowql:latest --tag slowql:latest .
```

#### 2. Resource Limits
```bash
# Run with memory limits
podman run --memory=512m --pod slowql-pod slowql:latest slowql --help

# Run with CPU limits
podman run --cpus=1.0 --pod slowql-pod slowql:latest slowql --help
```

### Cleanup

#### Remove Pod and Containers
```bash
# Stop and remove pod (includes all containers)
podman pod rm -f slowql-pod

# Remove built images
podman rmi slowql:latest

# Clean up unused resources
podman system prune -a
```

#### Complete Cleanup
```bash
# Remove all SlowQL-related resources
podman pod ls --no-trunc | grep slowql | awk '{print $1}' | xargs -r podman pod rm -f
podman images | grep slowql | awk '{print $3}' | xargs -r podman rmi
```

## Next Steps

After successfully setting up the local Podman environment:

1. **Integrate with Development Workflow**: Use the container for local testing
2. **Set Up CI/CD**: Use this setup as reference for automated deployments
3. **Create Development Pods**: Set up persistent development environments
4. **Scale Testing**: Test with larger SQL files and datasets

## Additional Resources

- [Podman Documentation](https://docs.podman.io/)
- [Podman Pods Guide](https://docs.podman.io/en/latest/markdown/podman-pod.1.html)
- [Container Security Best Practices](https://access.redhat.com/articles/3763041)

For issues specific to SlowQL, please refer to the [project documentation](https://slowql.dev/docs) or open an issue on [GitHub](https://github.com/makroumi/slowql/issues).