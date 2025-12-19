# Deployment

This comprehensive guide explains how to deploy SlowQL in enterprise environments across all supported platforms, including detailed instructions for different Linux distributions, container setups, and enterprise deployment scenarios.

---

## 🧱 Local Installation

### Quick Install (Recommended)

```bash
# Install with pipx (isolated environment)
pipx install slowql

# Or with pip in current environment
pip install slowql

# For development/enterprise use
pip install slowql[dev]
```

### Python Version Management

#### Ubuntu/Debian Systems

```bash
# Install Python 3.12
sudo apt update
sudo apt install python3.12 python3.12-pip python3.12-venv

# Set as default
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1
sudo update-alternatives --install /usr/bin/pip pip /usr/bin/pip3.12 1

# Install SlowQL
python -m pip install --user slowql
```

#### CentOS/RHEL/Fedora Systems

```bash
# CentOS/RHEL 8+ or Fedora
sudo dnf install python3.12 python3.12-pip
# or for older versions
sudo yum install python3 python3-pip

# Install SlowQL
pip3 install slowql
```

#### Arch Linux

```bash
# Install Python and pip
sudo pacman -S python python-pip

# Install SlowQL
pip install slowql
```

### Verification

```bash
# Check installation
slowql --version

# Test analysis
slowql --input-file examples/sample.sql --export json
```

---

## 🐳 Container Deployment

### Docker Deployment

#### Standard Docker Usage

```bash
# Pull and run with volume mounting
docker run --rm -v "$PWD":/work makroumi/slowql slowql --input-file /work/queries.sql

# Interactive mode
docker run --rm -it makroumi/slowql slowql --mode auto

# Non-interactive for CI/CD
docker run --rm -v "$PWD":/work makroumi/slowql slowql --non-interactive --input-file /work/sql/ --export json
```

#### Docker Compose Setup

```yaml
# docker-compose.yml for enterprise deployment
version: '3.8'
services:
  slowql-analyzer:
    image: makroumi/slowql:latest
    volumes:
      - ./sql-files:/app/sql:ro
      - ./reports:/app/reports
      - ./config:/app/config:ro
    working_dir: /app
    environment:
      - SLOWQL_CONFIG=/app/config/.slowql.toml
    command: >
      sh -c "
        slowql --input-file sql/ 
        --export html csv json 
        --out reports/ 
        --config config/.slowql.toml
      "
    profiles:
      - analysis

  slowql-ci:
    image: makroumi/slowql:latest
    volumes:
      - .:/workspace:ro
    working_dir: /workspace
    command: >
      sh -c "
        slowql --non-interactive 
        --input-file sql/ 
        --export json 
        --out reports/
      "
    profiles:
      - ci
```

#### Multi-Stage Docker Build

```dockerfile
# Dockerfile for custom enterprise deployment
FROM python:3.12-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Production stage
FROM python:3.12-slim

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Add to PATH
ENV PATH=/root/.local/bin:$PATH

# Create working directories
RUN mkdir -p /app/sql /app/reports /app/config

# Copy application
COPY --chmod=755 slowql/ /usr/local/bin/

# Set working directory
WORKDIR /app

# Default command
CMD ["slowql", "--help"]

# Example usage
# docker build -t enterprise-slowql .
# docker run --rm -v $(pwd):/app enterprise-slowql slowql --input-file sql/
```

### Podman Deployment

#### Standard Podman Usage

```bash
# Run with Podman (Docker-compatible)
podman run --rm -v "$PWD":/work -w /work docker.io/makroumi/slowql slowql --input-file queries.sql

# Create development pod
podman pod create --name slowql-dev --share net
podman run --pod slowql-dev -v "$PWD":/work -w /work docker.io/makroumi/slowql slowql --mode auto

# Multi-container pod with volumes
podman pod create --name slowql-enterprise \
  --share net \
  -p 8080:8080

podman run --pod slowql-enterprise \
  -v ./sql:/app/sql:ro \
  -v ./reports:/app/reports \
  docker.io/makroumi/slowql \
  slowql --input-file /app/sql/ --export html --out /app/reports/
```

#### Podman Quadlet (Systemd Integration)

```ini
# slowql-pod.container
[Container]
Image=docker.io/makroumi/slowql:latest
Volume=./sql:/app/sql:ro
Volume=./reports:/app/reports
WorkingDir=/app
Exec=slowql --input-file sql/ --export html csv json --out reports/

[Install]
WantedBy=multi-user.target

# Enable and start
systemctl --user enable slowql-pod.container
systemctl --user start slowql-pod.container
```

---

## ☁️ Cloud Deployment

### Kubernetes Deployment

```yaml
# slowql-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: slowql-analyzer
  namespace: devops-tools
spec:
  replicas: 2
  selector:
    matchLabels:
      app: slowql-analyzer
  template:
    metadata:
      labels:
        app: slowql-analyzer
    spec:
      containers:
      - name: slowql
        image: makroumi/slowql:latest
        volumeMounts:
        - name: sql-storage
          mountPath: /app/sql
        - name: reports-storage
          mountPath: /app/reports
        - name: config-storage
          mountPath: /app/config
        args:
        - "--input-file"
        - "/app/sql/"
        - "--export"
        - "html"
        - "csv"
        - "json"
        - "--out"
        - "/app/reports/"
        env:
        - name: SLOWQL_CONFIG
          value: "/app/config/.slowql.toml"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: sql-storage
        persistentVolumeClaim:
          claimName: sql-files-pvc
      - name: reports-storage
        persistentVolumeClaim:
          claimName: reports-pvc
      - name: config-storage
        configMap:
          name: slowql-config
---
apiVersion: v1
kind: Service
metadata:
  name: slowql-service
  namespace: devops-tools
spec:
  selector:
    app: slowql-analyzer
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

### AWS ECS Deployment

```json
{
  "family": "slowql-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/slowqlTaskRole",
  "containerDefinitions": [
    {
      "name": "slowql-analyzer",
      "image": "makroumi/slowql:latest",
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/slowql-analyzer",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "mountPoints": [
        {
          "sourceVolume": "sql-storage",
          "containerPath": "/app/sql",
          "readOnly": true
        },
        {
          "sourceVolume": "reports-storage",
          "containerPath": "/app/reports"
        }
      ],
      "command": [
        "--input-file",
        "/app/sql/",
        "--export",
        "html",
        "csv",
        "json",
        "--out",
        "/app/reports/"
      ]
    }
  ],
  "volumes": [
    {
      "name": "sql-storage",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-12345678",
        "transitEncryption": "ENABLED"
      }
    },
    {
      "name": "reports-storage",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-87654321",
        "transitEncryption": "ENABLED"
      }
    }
  ]
}
```

---

## ⚙️ CI/CD Integration

### GitHub Actions (Enhanced)

```yaml
# .github/workflows/slowql-analysis.yml
name: SlowQL Analysis
on:
  push:
    paths:
      - '**.sql'
      - '.github/workflows/slowql-analysis.yml'
  pull_request:
    paths:
      - '**.sql'

jobs:
  slowql-analysis:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          
      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          
      - name: Install SlowQL
        run: |
          python -m pip install --upgrade pip
          pip install slowql[dev] readchar
          
      - name: Run SlowQL Analysis
        run: |
          slowql --non-interactive \
            --input-file sql/ \
            --export html csv json \
            --out ./reports/ \
            --verbose
            
      - name: Upload reports
        uses: actions/upload-artifact@v4
        with:
          name: slowql-reports-${{ matrix.python-version }}
          path: reports/
          retention-days: 30
          
      - name: Fail on critical issues
        run: |
          python - <<'PY'
          import json, glob, sys
          
          # Find the most recent report
          report_files = glob.glob('reports/slowql_results_*.json')
          if not report_files:
              print("❌ No report files found!")
              sys.exit(1)
              
          latest_report = max(report_files)
          data = json.load(open(latest_report, encoding='utf-8'))
          
          critical_count = data["statistics"]["by_severity"].get("CRITICAL", 0)
          high_count = data["statistics"]["by_severity"].get("HIGH", 0)
          
          if critical_count > 0:
              print(f"❌ Found {critical_count} CRITICAL SQL issues!")
              sys.exit(1)
          elif high_count > 0:
              print(f"⚠️  Found {high_count} HIGH severity SQL issues")
              sys.exit(1)
          else:
              print("✅ No critical SQL issues found")
          PY
```

### GitLab CI (Enhanced)

```yaml
# .gitlab-ci.yml
stages:
  - test
  - report

variables:
  SLOWQL_VERSION: "latest"

slowql-analysis:
  stage: test
  image: python:3.12
  before_script:
    - pip install --upgrade pip
    - pip install slowql[dev] readchar
  script:
    - |
      slowql --non-interactive \
        --input-file sql/ \
        --export html csv json \
        --out ./reports/ \
        --verbose
  artifacts:
    reports:
      junit: reports/slowql_results_*.json
    paths:
      - reports/
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "push"
      changes:
        - "**/*.sql"
    - if: $CI_MERGE_REQUEST_IID

slowql-security-scan:
  stage: report
  image: python:3.12
  script:
    - pip install slowql[dev]
    - |
      slowql --non-interactive \
        --input-file sql/ \
        --export json \
        --out ./security-report.json
  artifacts:
    reports:
      security: security-report.json
    paths:
      - security-report.json
  allow_failure: true
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

### Jenkins Pipeline (Enhanced)

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        SLOWQL_VERSION = 'latest'
        PYTHON_VERSION = '3.12'
    }
    
    parameters {
        choice(
            name: 'ANALYSIS_TYPE',
            choices: ['full', 'security-only', 'performance-only'],
            description: 'Type of analysis to perform'
        )
        booleanParam(
            name: 'GENERATE_REPORTS',
            defaultValue: true,
            description: 'Generate HTML/CSV reports'
        )
    }
    
    stages {
        stage('Setup') {
            steps {
                script {
                    sh '''
                        python3 -m pip install --upgrade pip
                        pip3 install slowql[dev] readchar
                    '''
                }
            }
        }
        
        stage('SlowQL Analysis') {
            steps {
                script {
                    def analysisType = params.ANALYSIS_TYPE
                    def reportFlag = params.GENERATE_REPORTS ? '--export html csv json' : '--export json'
                    
                    sh """
                        slowql --non-interactive \\
                            --input-file sql/ \\
                            ${reportFlag} \\
                            --out ./reports/ \\
                            --verbose
                    """
                }
            }
        }
        
        stage('Quality Gate') {
            steps {
                script {
                    sh '''
                        python3 - <<'PY'
                        import json, glob, sys
                        
                        report_files = glob.glob('reports/slowql_results_*.json')
                        if not report_files:
                            print("❌ No report files found!")
                            sys.exit(1)
                        
                        latest_report = max(report_files)
                        data = json.load(open(latest_report, encoding='utf-8'))
                        
                        critical_count = data["statistics"]["by_severity"].get("CRITICAL", 0)
                        high_count = data["statistics"]["by_severity"].get("HIGH", 0)
                        
                        if critical_count > 0:
                            print(f"❌ Found {critical_count} CRITICAL SQL issues!")
                            currentBuild.result = 'FAILURE'
                            sys.exit(1)
                        elif high_count > 5:
                            print(f"⚠️  Found {high_count} HIGH severity SQL issues (threshold: 5)")
                            currentBuild.result = 'UNSTABLE'
                            sys.exit(1)
                        else:
                            print("✅ SQL analysis passed quality gate")
                        PY
                    '''
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'reports/**', fingerprint: true, allowEmptyArchive: true
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: '*.html',
                reportName: 'SlowQL Analysis Report'
            ])
        }
        failure {
            emailext (
                subject: "SlowQL Analysis Failed - ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "SlowQL analysis found critical issues. Check build logs and reports.",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
    }
}
```

### Pre-commit Hook (Enhanced)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: slowql-analysis
        name: SlowQL SQL Analysis
        entry: slowql --non-interactive --export json
        language: system
        files: '\.(sql)$'
        pass_filenames: false
        args: ['--input-file']
        
      - id: slowql-security
        name: SlowQL Security Scan
        entry: slowql --non-interactive --export json
        language: system
        files: '\.(sql)$'
        pass_filenames: false
        args: ['--input-file', '--analyzer', 'security']
        
      - id: slowql-performance
        name: SlowQL Performance Scan
        entry: slowql --non-interactive --export json
        language: system
        files: '\.(sql)$'
        pass_filenames: false
        args: ['--input-file', '--analyzer', 'performance']
```

---

## 📂 Configuration Management

### Enterprise Configuration File

```toml
# .slowql.toml - Enterprise configuration
[general]
# Analysis settings
cache_enabled = true
verbose_output = false
non_interactive = true

# Export settings
default_export_formats = ["json", "html"]
output_directory = "./reports"

# Performance settings
max_file_size_mb = 10
parallel_analysis = true
max_workers = 4

# Rule categories to enable
[rule_categories]
security = true
performance = true
cost = true
reliability = true
quality = true
compliance = true

# Specific rules configuration
[rules.select_star]
enabled = true
severity = "medium"
message = "Avoid SELECT * queries"
suggestion = "Specify columns explicitly for better performance"

[rules.sql_injection]
enabled = true
severity = "critical"
message = "Potential SQL injection detected"
suggestion = "Use parameterized queries"

[rules.missing_where]
enabled = true
severity = "high"
message = "UPDATE/DELETE without WHERE clause"
suggestion = "Add WHERE clause to prevent data loss"

# Analyzers configuration
[analyzers.security]
enabled_rules = ["sql_injection", "hardcoded_creds", "excessive_privileges"]
severity_threshold = "medium"

[analyzers.performance]
enabled_rules = ["select_star", "non_sargable", "deep_pagination"]
severity_threshold = "medium"

# Export formats configuration
[export.json]
include_statistics = true
include_suggestions = true
pretty_print = true

[export.html]
theme = "dark"
include_charts = true
standalone = true

[export.csv]
include_header = true
separator = ","
encoding = "utf-8"
```

### Configuration in Version Control

```bash
# .gitignore for enterprise deployment
reports/
*.log
.slowql_cache/
temp/

# Configuration files to track
# .slowql.toml should be committed for team consistency
# Custom rule configurations
rules/
custom_rules.py
```

---

## 🧠 Enterprise Best Practices

### Security Considerations

1. **Container Security**
   - Use minimal base images (`python:3.12-slim`)
   - Run containers as non-root user
   - Scan images for vulnerabilities
   - Use private registries for sensitive deployments

2. **Network Security**
   - Deploy in isolated network segments
   - Use secrets management for sensitive data
   - Implement proper firewall rules
   - Monitor network traffic

3. **Data Protection**
   - Encrypt data at rest and in transit
   - Implement proper access controls
   - Regular security audits
   - Incident response procedures

### Performance Optimization

1. **Resource Management**
   ```yaml
   resources:
     requests:
       memory: "256Mi"
       cpu: "250m"
     limits:
       memory: "1Gi"
       cpu: "1000m"
   ```

2. **Caching Strategy**
   - Enable SlowQL result caching
   - Use local volume mounts for cache
   - Implement Redis for distributed caching
   - Cache rule configurations

3. **Parallel Processing**
   - Enable multi-worker analysis
   - Use container orchestration for scaling
   - Implement queue-based processing
   - Monitor resource utilization

### Monitoring and Observability

1. **Logging Configuration**
   ```yaml
   logging:
     level: INFO
     format: json
     output: stdout
     include_metadata: true
   ```

2. **Metrics Collection**
   - Analysis duration
   - Issues detected by severity
   - Rule execution times
   - Error rates and types

3. **Alerting Rules**
   - Critical issues threshold
   - Analysis failure alerts
   - Performance degradation
   - Resource utilization warnings

---

## 🔗 Related Pages

- [Overview](overview.md)
- [Team Features](team-features.md)
- [Support](support.md)
- [Installation](../getting-started/installation.md)
- [Configuration](../getting-started/configuration.md)
- [CI/CD Integration](../user-guide/ci-cd-integration.md)
