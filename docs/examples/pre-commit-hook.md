# Pre-Commit Hook

This comprehensive example shows how to integrate SlowQL into pre-commit workflows so SQL files are automatically analyzed before every commit. Includes advanced configurations, multiple hook types, and enterprise-grade setup.

---

## 🚀 Complete Pre-Commit Setup

### 1. Install Pre-Commit

```bash
# Install pre-commit globally (recommended)
pip install pre-commit

# Or install per-project
pipenv install --dev pre-commit
# or
poetry install --group dev pre-commit
```

### 2. Create Configuration File

Create `.pre-commit-config.yaml`:

```yaml
# Pre-commit configuration for SlowQL
repos:
  # Local repository with SlowQL hooks
  - repo: local
    hooks:
      # Primary SlowQL analysis hook
      - id: slowql-analysis
        name: SlowQL SQL Analysis
        entry: slowql --non-interactive --export json
        language: system
        files: '\.(sql|ddl|dml)$'
        pass_filenames: false
        stages: [commit]
        args: ['--input-file']
        
      # Security-focused analysis hook
      - id: slowql-security
        name: SlowQL Security Scan
        entry: slowql --non-interactive --analyzer security --export json
        language: system
        files: '\.(sql|ddl|dml)$'
        pass_filenames: false
        stages: [commit]
        args: ['--input-file']
        
      # Performance-focused analysis hook
      - id: slowql-performance
        name: SlowQL Performance Scan
        entry: slowql --non-interactive --analyzer performance --export json
        language: system
        files: '\.(sql|ddl|dml)$'
        pass_filenames: false
        stages: [commit]
        args: ['--input-file']
        
      # Quick analysis for fast feedback
      - id: slowql-fast
        name: SlowQL Fast Check
        entry: slowql --fast --non-interactive
        language: system
        files: '\.(sql|ddl|dml)$'
        pass_filenames: false
        stages: [commit]
        args: ['--input-file']
        
      # Configuration validation hook
      - id: slowql-config-validate
        name: SlowQL Config Validation
        entry: slowql --validate-config
        language: system
        files: '\.slowql\.toml$'
        pass_filenames: true
        stages: [commit]
        
  # Pre-commit built-in hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
        args: [--markdown-linebreak-ext=md]
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      args: ['--maxkb=1000']
      - id: check-case-conflict
      - id: check-merge-conflict
      - id: check-executables-have-shebangs
      - id: check-shebang-scripts-are-executable
      - id: debug-statements
      - id: requirements-txt-fixer

  # Code formatting hooks
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.12
        
  # Python linting
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.270
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

# Global configuration
fail_fast: false  # Continue checking all files even if one fails
minimum_pre_commit_version: '3.0.0'
default_stages: [commit]
```

### 3. Install Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Install hooks for all stages
pre-commit install --hook-type pre-commit
pre-commit install --hook-type pre-push
pre-commit install --hook-type commit-msg

# Install specific hooks
pre-commit install --hook-type pre-commit --hook-id slowql-analysis
pre-commit install --hook-type pre-push --hook-id slowql-security
```

---

## 🔧 Advanced Configurations

### Environment-Specific Configuration

#### `.pre-commit-config.yaml` with Environment Variables
```yaml
repos:
  - repo: local
    hooks:
      - id: slowql-analysis
        name: SlowQL SQL Analysis
        entry: bash -c 'slowql --non-interactive --export json --config ${SLOWQL_CONFIG:-.slowql.toml}'
        language: system
        files: '\.(sql|ddl|dml)$'
        pass_filenames: false
        stages: [commit]
        args: ['--input-file']
        env:
          SLOWQL_CONFIG: '.slowql.toml'
```

#### Conditional Hooks Based on Files Changed
```yaml
repos:
  - repo: local
    hooks:
      - id: slowql-changed-files
        name: SlowQL Analysis (Changed Files Only)
        entry: >
          bash -c '
            if git diff --cached --name-only | grep -q "\.sql$"; then
              echo "SQL files changed - running SlowQL analysis"
              slowql --non-interactive --export json --input-file $(git diff --cached --name-only | grep "\.sql$" | tr "\n" " ")
            else
              echo "No SQL files changed - skipping SlowQL analysis"
            fi
          '
        language: system
        stages: [commit]
```

### Multi-Stage Hooks

#### Pre-Commit Hooks (Local Files Only)
```yaml
- repo: local
  hooks:
    - id: slowql-local
      name: SlowQL Analysis (Local Changes)
      entry: slowql --non-interactive --input-file .
      language: system
      files: '\.(sql|ddl|dml)$'
      stages: [commit]
```

#### Pre-Push Hooks (Include Remote Changes)
```yaml
- repo: local
  hooks:
    - id: slowql-push
      name: SlowQL Analysis (Include Remote)
      entry: slowql --non-interactive --input-file .
      language: system
      files: '\.(sql|ddl|dml)$'
      stages: [push]
      pass_filenames: false
```

#### Commit Message Hooks
```yaml
- repo: local
  hooks:
    - id: slowql-commit-msg
      name: SlowQL Commit Message Check
      entry: bash -c '
        if git log --oneline -1 | grep -qi "sql\|database\|query"; then
          echo "SQL-related commit detected - consider running full analysis"
        fi
      '
      language: system
      stages: [commit-msg]
```

---

## 🎯 Specialized Hook Configurations

### Security-Focused Hook
```yaml
# Enhanced security hook with detailed reporting
- id: slowql-security-detailed
  name: SlowQL Security Analysis
  entry: >
    bash -c '
      slowql --non-interactive \
        --analyzer security \
        --export json \
        --out ./reports/security-check-$(date +%Y%m%d-%H%M%S).json \
        --verbose
    '
  language: system
  files: '\.(sql|ddl|dml)$'
  pass_filenames: false
  stages: [commit]
  always_run: false
```

### Performance-Focused Hook
```yaml
- id: slowql-performance-check
  name: SlowQL Performance Analysis
  entry: >
    bash -c '
      slowql --non-interactive \
        --analyzer performance \
        --export json \
        --out ./reports/performance-check-$(date +%Y%m%d-%H%M%S).json \
        --verbose
    '
  language: system
  files: '\.(sql|ddl|dml)$'
  pass_filenames: false
  stages: [commit]
```

### Configuration Validation Hook
```yaml
- id: slowql-config-validation
  name: SlowQL Configuration Validation
  entry: >
    bash -c '
      if [ -f ".slowql.toml" ]; then
        slowql --validate-config --config .slowql.toml
      else
        echo "No .slowql.toml found - using default configuration"
      fi
    '
  language: system
  files: '\.slowql\.toml$'
  pass_filenames: true
  stages: [commit]
```

---

## 🏢 Enterprise Configuration

### Organization-Wide Configuration

#### Centralized Configuration Repository
```yaml
# .pre-commit-config.yaml (organization template)
repos:
  - repo: https://github.com/your-org/slowql-precommit-hooks
    rev: v1.3.0
    hooks:
      - id: slowql-enterprise
        name: SlowQL Enterprise Analysis
        entry: slowql --non-interactive --config /etc/slowql/enterprise.toml
        language: system
        files: '\.(sql|ddl|dml)$'
        stages: [commit]
        args: ['--input-file']
        additional_dependencies:
          - slowql[enterprise]
```

#### Template Repository Setup
```bash
# Create template repository
git clone https://github.com/your-org/slowql-precommit-template.git
cd slowql-precommit-template

# Update organization-specific configuration
sed 's/your-org/ACME-CORP/g' .pre-commit-config.yaml > .pre-commit-config.yaml.tmp
mv .pre-commit-config.yaml.tmp .pre-commit-config.yaml

# Commit and push
git add .
git commit -m "Update organization configuration"
git push origin main
```

### Compliance and Audit Hooks

#### Audit Trail Hook
```yaml
- id: slowql-audit-trail
  name: SlowQL Audit Trail
  entry: >
    bash -c '
      AUDIT_FILE="./.slowql/audit-$(date +%Y%m%d).log"
      mkdir -p ./.slowql
      echo "[$(date)] Commit: $(git rev-parse HEAD) - Author: $(git log -1 --pretty=%an) - Files: $(git diff --cached --name-only | grep "\.sql$" | tr "\n" ",")" >> $AUDIT_FILE
    '
  language: system
  files: '\.(sql|ddl|dml)$'
  stages: [commit]
  pass_filenames: false
```

#### Compliance Reporting Hook
```yaml
- id: slowql-compliance-report
  name: SlowQL Compliance Report
  entry: >
    bash -c '
      slowql --non-interactive \
        --analyzer compliance \
        --export json \
        --out ./reports/compliance-$(date +%Y%m%d-%H%M%S).json \
        --config .slowql.compliance.toml
    '
  language: system
  files: '\.(sql|ddl|dml)$'
  stages: [commit]
  pass_filenames: false
```

---

## 📊 Sample SQL Files for Testing

### Test SQL Files
```sql
-- sample.sql (Good examples)
SELECT id, name, email FROM users WHERE active = true;
INSERT INTO orders (user_id, product_id, quantity) VALUES (?, ?, ?);
UPDATE profiles SET last_login = NOW() WHERE id = ?;

-- sample_bad.sql (Issues for testing)
SELECT * FROM users WHERE email LIKE '%@gmail.com';  -- SELECT *
UPDATE users SET password = 'secret123' WHERE id = 1;  -- Hardcoded password
DELETE FROM orders;  -- Missing WHERE clause
```

---

## 🔧 Configuration Files

### `.slowql.toml` for Pre-Commit
```toml
[general]
non_interactive = true
verbose_output = false
cache_enabled = true

[rule_categories]
security = true
performance = true
cost = true
reliability = true
quality = true

[rules.sql_injection]
enabled = true
severity = "critical"
message = "Potential SQL injection detected"
suggestion = "Use parameterized queries"

[rules.select_star]
enabled = true
severity = "medium"
message = "Avoid SELECT * queries"
suggestion = "Specify columns explicitly"

[rules.missing_where]
enabled = true
severity = "high"
message = "UPDATE/DELETE without WHERE clause"
suggestion = "Add WHERE clause to prevent data loss"

[rules.hardcoded_creds]
enabled = true
severity = "critical"
message = "Hardcoded credentials detected"
suggestion = "Use environment variables or secrets management"

[analyzers.security]
enabled_rules = ["sql_injection", "hardcoded_creds", "excessive_privileges"]
severity_threshold = "medium"

[analyzers.performance]
enabled_rules = ["select_star", "non_sargable", "deep_pagination"]
severity_threshold = "medium"

# Pre-commit specific settings
[pre_commit]
fail_on_critical = true
fail_on_high = false
generate_reports = false
report_format = "json"
```

---

## 🛠️ Hook Management Commands

### Installation Commands
```bash
# Install all hooks
pre-commit install

# Install specific hooks
pre-commit install --hook-type pre-commit --hook-id slowql-analysis
pre-commit install --hook-type pre-push --hook-id slowql-security

# Install without auto-running on commit
pre-commit install --hook-type pre-commit --hook-id slowql-analysis --skip
```

### Execution Commands
```bash
# Run hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run slowql-analysis --all-files

# Run hooks on staged files only
pre-commit run

# Run hooks with verbose output
pre-commit run --verbose

# Skip specific hooks
SKIP=slowql-performance git commit -m "Skip performance check"

# Run hooks against specific files
pre-commit run slowql-analysis --files path/to/file.sql

# Update hook versions
pre-commit autoupdate

# Clean up hook cache
pre-commit clean

# Uninstall hooks
pre-commit uninstall
```

### CI/CD Integration
```bash
# Run pre-commit in CI environment
pre-commit run --all-files --show-diff-on-failure

# Run without modifying files
pre-commit run --all-files --no-verify

# Run specific stages
pre-commit run --all-files --hook-stage commit

# Parallel execution
pre-commit run --all-files --jobs 4
```

---

## 🔍 Troubleshooting Pre-Commit

### Common Issues and Solutions

#### Issue: Hook Fails with Import Error
```bash
# Solution: Ensure SlowQL is installed in the environment
pip install slowql[dev]

# Or specify full path to slowql
pre-commit config .pre-commit-config.yaml
```

#### Issue: Hook Times Out on Large Files
```yaml
# Solution: Add timeout configuration
- id: slowql-analysis
  name: SlowQL Analysis
  entry: timeout 300 slowql --non-interactive --input-file .
  language: system
  files: '\.(sql|ddl|dml)$'
  stages: [commit]
  pass_filenames: false
  timeout: 300  # 5 minutes
```

#### Issue: Configuration File Not Found
```yaml
# Solution: Use default config or specify path
- id: slowql-analysis
  name: SlowQL Analysis
  entry: slowql --non-interactive --input-file . --config .slowql.toml
  language: system
  files: '\.(sql|ddl|dml)$'
  stages: [commit]
  pass_filenames: false
```

### Debug Mode
```bash
# Enable debug output
PRE_COMMIT_DEBUG=1 pre-commit run --verbose

# Run single hook with debug
pre-commit run slowql-analysis --verbose --debug

# Check hook configuration
pre-commit validate-config
pre-commit validate-manifest
```

---

## 📈 Performance Optimization

### Caching Strategy
```yaml
# Enable caching for better performance
repos:
  - repo: local
    hooks:
      - id: slowql-analysis
        name: SlowQL Analysis
        entry: slowql --non-interactive --input-file .
        language: system
        files: '\.(sql|ddl|dml)$'
        stages: [commit]
        pass_filenames: false
        entry: >
          bash -c '
            if [ -f .slowql_cache.json ]; then
              echo "Using cached results"
              slowql --non-interactive --input-file . --use-cache
            else
              slowql --non-interactive --input-file . --generate-cache
            fi
          '
```

### Parallel Execution
```bash
# Run hooks in parallel for better performance
pre-commit run --all-files --jobs 4

# Configure parallel execution in config
# Add to .pre-commit-config.yaml:
default_language_version:
  python: python3.12
default_stages: [commit]
maximum_keyword_length: 20
```

---

## 🔔 Integration with Development Workflow

### IDE Integration
```bash
# Generate IDE-specific configuration
pre-commit run --hook-stage manual --format visual-studio-code

# Create pre-commit hooks for specific IDEs
# VS Code: Use pre-commit extension
# PyCharm: Configure external tools
```

### Git Hook Scripts
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run pre-commit
exec pre-commit run --hook-stage commit

# Custom additional checks
if ! ./scripts/custom-sql-check.sh; then
    echo "Custom SQL checks failed"
    exit 1
fi
```

### Notification Integration
```yaml
- id: slowql-notification
  name: SlowQL Notification
  entry: >
    bash -c '
      if [ "$PRE_COMMIT_STATUS" = "failed" ]; then
        echo "SlowQL analysis failed - sending notification"
        # Add your notification logic here
        # curl -X POST -H "Content-Type: application/json" \
        #   --data "{\"text\":\"SlowQL analysis failed for commit $COMMIT_SHA\"}" \
        #   "$SLACK_WEBHOOK_URL"
      fi
    '
  language: system
  stages: [commit]
  pass_filenames: false
```

---

## 🧠 Best Practices

### 1. Hook Organization
- **Start simple**: Begin with basic analysis hook
- **Add complexity gradually**: Add security and performance hooks as needed
- **Use fail-fast**: Configure hooks to fail early for critical issues
- **Optimize performance**: Use caching and parallel execution

### 2. Configuration Management
```yaml
# Use environment-specific configurations
- id: slowql-analysis
  name: SlowQL Analysis
  entry: slowql --non-interactive --input-file . --config ${SLOWQL_CONFIG:-.slowql.toml}
  language: system
  files: '\.(sql|ddl|dml)$'
  stages: [commit]
  pass_filenames: false
  env:
    SLOWQL_CONFIG: '.slowql.toml'
```

### 3. Team Adoption
```bash
# Provide setup scripts for team members
#!/bin/bash
# setup-pre-commit.sh

echo "Setting up SlowQL pre-commit hooks..."

# Install dependencies
pip install pre-commit slowql[dev]

# Install hooks
pre-commit install

# Run initial analysis
pre-commit run --all-files

echo "Setup complete!"
```

### 4. Monitoring and Reporting
```yaml
# Add monitoring hooks
- id: slowql-metrics
  name: SlowQL Metrics Collection
  entry: >
    bash -c '
      METRICS_FILE="./.slowql/metrics.json"
      slowql --non-interactive --input-file . --export json --out /tmp/metrics.json || true
      if [ -f /tmp/metrics.json ]; then
        python3 -c "
          import json, sys
          try:
            with open('/tmp/metrics.json') as f:
              data = json.load(f)
            metrics = {
              'timestamp': '$(date -Iseconds)',
              'total_issues': data.get('statistics', {}).get('total_issues', 0),
              'critical': data.get('statistics', {}).get('by_severity', {}).get('CRITICAL', 0)
            }
            with open('$METRICS_FILE', 'w') as out:
              json.dump(metrics, out)
          except Exception as e:
            print(f'Metrics collection failed: {e}')
        "
      fi
    '
  language: system
  files: '\.(sql|ddl|dml)$'
  stages: [commit]
  pass_filenames: false
```

---

## 🔗 Related Examples

- [Basic Usage](basic-usage.md)
- [Docker & Podman Integration](docker-podman-integration.md)
- [GitHub Actions](github-actions.md)
- [GitLab CI](gitlab-ci.md)
- [Jenkins](jenkins.md)

---

## 📚 Additional Resources

- [Pre-commit Documentation](https://pre-commit.com/)
- [Pre-commit Hooks Repository](https://github.com/pre-commit/pre-commit-hooks)
- [Creating Custom Hooks](https://pre-commit.com/#creating-new-hooks)
- [Pre-commit Configuration](https://pre-commit.com/#config)
