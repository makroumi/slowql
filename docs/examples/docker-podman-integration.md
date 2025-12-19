# Docker & Podman Integration

This comprehensive guide shows how to integrate SlowQL with Docker and Podman containers across different deployment scenarios, from local development to enterprise production environments.

---

## 🐳 Docker Integration

### Basic Docker Usage

#### Quick Analysis with Docker
```bash
# Analyze a local SQL file using Docker
docker run --rm -v "$PWD":/work makroumi/slowql slowql --input-file /work/queries.sql

# Run in interactive mode
docker run --rm -it makroumi/slowql slowql --mode auto

# Analyze and export results
docker run --rm -v "$PWD":/work makroumi/slowql slowql --input-file /work/queries.sql --export html csv json --out /work/reports/
```

#### Advanced Docker Configuration
```bash
# Run with custom working directory and environment
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace \
  -e SLOWQL_CONFIG=/workspace/.slowql.toml \
  makroumi/slowql \
  slowql --input-file sql/ --export json --out reports/

# Multi-stage analysis with different configurations
docker run --rm \
  -v "$PWD":/data \
  -v "$PWD/.slowql.toml":/config/.slowql.toml:ro \
  makroumi/slowql \
  slowql --input-file /data/queries.sql \
    --config /config/.slowql.toml \
    --export html csv json \
    --out /data/reports/
```

### Docker Compose Setup

#### Basic Development Setup
```yaml
# docker-compose.yml
version: '3.8'
services:
  slowql:
    image: makroumi/slowql:latest
    volumes:
      - ./sql-files:/app/sql:ro
      - ./reports:/app/reports
      - ./.slowql.toml:/app/.slowql.toml:ro
    working_dir: /app
    environment:
      - SLOWQL_CONFIG=/app/.slowql.toml
    command: >
      sh -c "
        slowql --input-file sql/ 
        --export html csv json 
        --out reports/ 
        --config .slowql.toml
      "

volumes:
  reports:
```

#### Multi-Service Development Environment
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  slowql-analyzer:
    image: makroumi/slowql:latest
    volumes:
      - ./sql:/app/sql:ro
      - ./config:/app/config:ro
      - ./reports:/app/reports
    working_dir: /app
    environment:
      - SLOWQL_CONFIG=/app/config/.slowql.toml
    command: slowql --input-file sql/ --export html csv json --out reports/
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

  slowql-watch:
    image: makroumi/slowql:latest
    volumes:
      - ./sql:/app/sql:ro
      - ./reports:/app/reports
    working_dir: /app
    command: >
      sh -c "
        while true; do
          slowql --input-file sql/ --export html --out reports/ --timestamp
          sleep 30
        done
      "
    profiles:
      - watch

  nginx-reports:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./reports:/usr/share/nginx/html:ro
    profiles:
      - webserver
```

#### Production-Ready Setup
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  slowql-scheduler:
    image: makroumi/slowql:latest
    volumes:
      - ./sql-repository:/app/sql:ro
      - ./config:/app/config:ro
      - ./reports:/app/reports
      - ./logs:/app/logs
    working_dir: /app
    environment:
      - SLOWQL_CONFIG=/app/config/.slowql.toml
      - LOG_LEVEL=INFO
    command: >
      sh -c "
        while true; do
          echo 'Running scheduled analysis...'
          slowql --input-file sql/ \
            --export html csv json \
            --out reports/ \
            --config config/.slowql.toml \
            --log-file logs/slowql-$(date +%Y%m%d).log
          sleep 3600  # Run every hour
        done
      "
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  slowql-webhook:
    image: makroumi/slowql:latest
    volumes:
      - ./sql-repository:/app/sql:ro
      - ./config:/app/config:ro
      - ./reports:/app/reports
    working_dir: /app
    environment:
      - SLOWQL_CONFIG=/app/config/.slowql.toml
    command: >
      sh -c "
        # Simulate webhook handler
        while true; do
          if [ -f trigger ]; then
            echo 'Trigger detected, running analysis...'
            slowql --input-file sql/ \
              --export json \
              --out reports/webhook-report-$(date +%Y%m%d-%H%M%S).json \
              --config config/.slowql.toml
            rm trigger
          fi
          sleep 10
        done
      "
    restart: unless-stopped
    profiles:
      - webhook

volumes:
  sql-repository:
    driver: local
  reports:
    driver: local
  config:
    driver: local
  logs:
    driver: local
```

---

## 🔧 Podman Integration

### Basic Podman Usage

#### Standard Podman Commands
```bash
# Run with Podman (Docker-compatible)
podman run --rm -v "$PWD":/work -w /work docker.io/makroumi/slowql slowql --input-file queries.sql

# Interactive mode with Podman
podman run --rm -it docker.io/makroumi/slowql slowql --mode auto

# Non-interactive for automation
podman run --rm -v "$PWD":/work -w /work docker.io/makroumi/slowql slowql --non-interactive --input-file /work/sql/ --export json
```

#### Podman Pod Development Environment
```bash
# Create a development pod
podman pod create \
  --name slowql-dev \
  --share net \
  -p 8080:8080 \
  -p 3000:3000

# Add SlowQL container to pod
podman run --pod slowql-dev \
  -v "$PWD":/app/sql:ro \
  -v "$PWD"/reports:/app/reports \
  -v "$PWD"/config:/app/config:ro \
  -w /app \
  docker.io/makroumi/slowql \
  slowql --input-file sql/ --export html csv json --out reports/

# Add report server to pod
podman run --pod slowql-dev \
  -v "$PWD"/reports:/usr/share/nginx/html:ro \
  -p 8080:80 \
  nginx:alpine

# Add monitoring container
podman run --pod slowql-dev \
  -v "$PWD"/logs:/var/log \
  -w /var/log \
  docker.io/makroumi/slowql \
  sh -c "tail -f /app/logs/slowql.log | while read line; do echo \"[$(date)] $line\"; done"
```

#### Podman Quadlet Configuration

```ini
# slowql-pod.container
[Container]
Image=docker.io/makroumi/slowql:latest
Volume=./sql:/app/sql:ro
Volume=./reports:/app/reports:rw
Volume=./config:/app/config:ro
WorkingDir=/app
Exec=slowql --input-file sql/ --export html csv json --out reports/
Environment=SLOWQL_CONFIG=/app/config/.slowql.toml
Restart=unless-stopped

[Install]
WantedBy=multi-user.target

# slowql-watcher.container
[Container]
Image=docker.io/makroumi/slowql:latest
Volume=./sql:/app/sql:ro
Volume=./reports:/app/reports:rw
WorkingDir=/app
Exec=sh -c "while true; do slowql --input-file sql/ --export html --out reports/ --timestamp; sleep 60; done"
Restart=unless-stopped

[Install]
WantedBy=multi-user.target

# Enable systemd units
systemctl --user enable slowql-pod.container slowql-watcher.container
systemctl --user start slowql-pod.container slowql-watcher.container
```

### Podman Compose

```yaml
# podman-compose.yml
version: '3.8'
services:
  slowql-analyzer:
    image: docker.io/makroumi/slowql:latest
    volumes:
      - ./sql-files:/app/sql:ro
      - ./config:/app/config:ro
      - ./reports:/app/reports:rw
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
    restart: unless-stopped

  slowql-watch:
    image: docker.io/makroumi/slowql:latest
    volumes:
      - ./sql-files:/app/sql:ro
      - ./reports:/app/reports:rw
    working_dir: /app
    command: >
      sh -c "
        while true; do
          echo 'Running periodic analysis...'
          slowql --input-file sql/ --export html --out reports/ --timestamp
          sleep 300  # Every 5 minutes
        done
      "
    restart: unless-stopped

  nginx-reports:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./reports:/usr/share/nginx/html:ro
    restart: unless-stopped

networks:
  default:
    driver: bridge
```

---

## 🏗️ Advanced Container Patterns

### Multi-Stage Dockerfile for Custom Builds

```dockerfile
# Dockerfile.custom
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create application user
RUN groupadd -r slowql && useradd -r -g slowql slowql

# Create directories
RUN mkdir -p /app/sql /app/reports /app/config && \
    chown -R slowql:slowql /app

# Copy application code
COPY --chown=slowql:slowql slowql/ /usr/local/bin/
RUN chmod +x /usr/local/bin/slowql

# Set working directory
WORKDIR /app

# Switch to non-root user
USER slowql

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD slowql --help || exit 1

# Default command
CMD ["slowql", "--help"]

# Build and run
# docker build -f Dockerfile.custom -t enterprise-slowql .
# docker run --rm -v $(pwd):/app enterprise-slowql slowql --input-file sql/
```

### Kubernetes Integration

#### Kubernetes Deployment
```yaml
# slowql-k8s.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: slowql-analyzer
  namespace: devops-tools
  labels:
    app: slowql-analyzer
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: slowql-analyzer
  template:
    metadata:
      labels:
        app: slowql-analyzer
        version: v1
    spec:
      containers:
      - name: slowql
        image: makroumi/slowql:latest
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: sql-storage
          mountPath: /app/sql
          readOnly: true
        - name: reports-storage
          mountPath: /app/reports
        - name: config-storage
          mountPath: /app/config
          readOnly: true
        args:
        - "--input-file"
        - "/app/sql/"
        - "--export"
        - "html"
        - "csv"
        - "json"
        - "--out"
        - "/app/reports/"
        - "--config"
        - "/app/config/.slowql.toml"
        env:
        - name: SLOWQL_CONFIG
          value: "/app/config/.slowql.toml"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - slowql
            - --help
          initialDelaySeconds: 30
          periodSeconds: 60
        readinessProbe:
          exec:
            command:
            - slowql
            - --help
          initialDelaySeconds: 5
          periodSeconds: 30
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
    protocol: TCP
    name: http
  type: ClusterIP
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: slowql-scheduled
  namespace: devops-tools
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: slowql
            image: makroumi/slowql:latest
            volumeMounts:
            - name: sql-storage
              mountPath: /app/sql
              readOnly: true
            - name: reports-storage
              mountPath: /app/reports
            - name: config-storage
              mountPath: /app/config
              readOnly: true
            args:
            - "--input-file"
            - "/app/sql/"
            - "--export"
            - "html"
            - "json"
            - "--out"
            - "/app/reports/"
            - "--config"
            - "/app/config/.slowql.toml"
            env:
            - name: SLOWQL_CONFIG
              value: "/app/config/.slowql.toml"
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
          restartPolicy: OnFailure
```

---

## 📊 Monitoring and Observability

### Container Monitoring

#### Prometheus Metrics (Custom Implementation)
```yaml
# monitoring/docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

volumes:
  prometheus_data:
  grafana_data:
```

#### Logging Configuration
```yaml
# logging/docker-compose.logging.yml
version: '3.8'
services:
  slowql:
    image: makroumi/slowql:latest
    volumes:
      - ./sql:/app/sql:ro
      - ./reports:/app/reports
      - ./config:/app/config:ro
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service=slowql"

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"

  kibana:
    image: docker.elastic.co/kibana/kibana:7.17.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

  filebeat:
    image: docker.elastic.co/beats/filebeat:7.17.0
    user: root
    volumes:
      - ./logs:/logs:ro
      - ./monitoring/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
    command: filebeat -e -strict.perms=false

volumes:
  logs:
```

---

## 🔧 Container Best Practices

### Security Considerations

1. **Use Minimal Base Images**
   ```dockerfile
   FROM python:3.12-slim  # Not python:3.12
   ```

2. **Run as Non-Root User**
   ```dockerfile
   RUN groupadd -r slowql && useradd -r -g slowql slowql
   USER slowql
   ```

3. **Multi-Stage Builds**
   ```dockerfile
   FROM python:3.12-slim as builder
   # Build dependencies here
   FROM python:3.12-slim as production
   # Copy only necessary artifacts
   ```

4. **Health Checks**
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
     CMD slowql --help || exit 1
   ```

### Performance Optimization

1. **Resource Limits**
   ```yaml
   resources:
     requests:
       memory: "256Mi"
       cpu: "250m"
     limits:
       memory: "512Mi"
       cpu: "500m"
   ```

2. **Volume Mounting**
   ```bash
   # Use bind mounts for development, named volumes for production
   docker run -v "$(pwd)":/app:ro  # Read-only for security
   ```

3. **Caching Strategy**
   ```dockerfile
   # Layer caching for dependencies
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   ```

### Development Workflow

1. **Local Development**
   ```bash
   # Mount source code for development
   docker run -it -v "$(pwd)":/app makroumi/slowql bash
   ```

2. **CI/CD Integration**
   ```yaml
   # GitHub Actions example
   - name: Run SlowQL in Docker
     run: |
       docker run --rm \
         -v "${{ github.workspace }}":/workspace \
         -w /workspace \
         makroumi/slowql \
         slowql --non-interactive --input-file sql/ --export json
   ```

3. **Environment Variables**
   ```bash
   # Pass configuration via environment
   docker run --rm \
     -e SLOWQL_CONFIG=/custom/config.toml \
     -e LOG_LEVEL=DEBUG \
     makroumi/slowql slowql --help
   ```

---

## 🔗 Related Examples

- [Basic Usage](basic-usage.md)
- [GitHub Actions](github-actions.md)
- [GitLab CI](gitlab-ci.md)
- [Jenkins](jenkins.md)
- [Pre-Commit Hook](pre-commit-hook.md)

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Podman Documentation](https://docs.podman.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)