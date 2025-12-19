# GitLab CI

This comprehensive example shows how to run SlowQL inside GitLab CI pipelines to automatically analyze SQL files on every commit, merge request, or on a schedule. Includes advanced quality gates, multi-stage pipelines, and comprehensive reporting.

---

## 🚀 Complete Pipeline Example

Create `.gitlab-ci.yml`:

```yaml
# Global variables
variables:
  SLOWQL_VERSION: "latest"
  PYTHON_VERSION: "3.12"
  REPORTS_DIR: "reports"
  ARTIFACT_RETENTION: 1_week

# Pipeline stages
stages:
  - analyze
  - security
  - performance
  - report
  - notify

# Template for SlowQL analysis
.slowql_template: &slowql_template
  image: python:${PYTHON_VERSION}
  before_script:
    - python -m pip install --upgrade pip
    - pip install slowql[dev] readchar
    - mkdir -p ${REPORTS_DIR}
  script:
    - |
      slowql --non-interactive \
        --input-file ${SLOWQL_INPUT_PATH:-.} \
        --export html csv json \
        --out ./${REPORTS_DIR}/ \
        --verbose \
        --config .slowql.toml
  artifacts:
    reports:
      junit: ${REPORTS_DIR}/slowql_results_*.json
    paths:
      - ${REPORTS_DIR}/
    expire_in: ${ARTIFACT_RETENTION}
    when: always
  coverage: '/TOTAL.*\s+(\d+%)$/'
  allow_failure: false

# Main SQL analysis job
slowql-analysis:
  <<: *slowql_template
  stage: analyze
  rules:
    - if: $CI_PIPELINE_SOURCE == "push"
      changes:
        - "**/*.sql"
        - ".slowql.toml"
        - ".gitlab-ci.yml"
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == "main"
  script:
    - |
      # Determine analysis scope
      if [ "$CI_COMMIT_BRANCH" == "main" ]; then
        ANALYSIS_PATH="."
        echo "Running full analysis on main branch"
      else
        # Analyze only changed files for feature branches
        ANALYSIS_PATH="."
        echo "Running targeted analysis on branch: $CI_COMMIT_BRANCH"
      fi
      
      slowql --non-interactive \
        --input-file ${ANALYSIS_PATH} \
        --export html csv json \
        --out ./${REPORTS_DIR}/ \
        --verbose \
        --config .slowql.toml || true
        
  artifacts:
    reports:
      junit: ${REPORTS_DIR}/slowql_results_*.json
    paths:
      - ${REPORTS_DIR}/
    expire_in: ${ARTIFACT_RETENTION}
  cache:
    key: "$CI_JOB_NAME-$CI_COMMIT_REF_SLUG"
    paths:
      - .cache/pip/

# Security-focused analysis
slowql-security:
  <<: *slowql_template
  stage: security
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_MERGE_REQUEST_IID
  variables:
    SLOWQL_INPUT_PATH: "."
  script:
    - |
      slowql --non-interactive \
        --input-file . \
        --analyzer security \
        --export json \
        --out ./${REPORTS_DIR}/security-report.json \
        --config .slowql.toml
        
      # Security-specific quality gate
      python3 - <<'PY'
      import json, sys
      
      try:
        with open('./${REPORTS_DIR}/security-report.json', 'r') as f:
          data = json.load(f)
          
        critical_count = data["statistics"]["by_severity"].get("CRITICAL", 0)
        high_count = data["statistics"]["by_severity"].get("HIGH", 0)
        
        print(f"🔒 Security Analysis Results:")
        print(f"   Critical Issues: {critical_count}")
        print(f"   High Severity: {high_count}")
        
        if critical_count > 0:
          print(f"❌ SECURITY FAILURE: {critical_count} critical security issues found!")
          print("🚨 Critical security issues must be addressed immediately")
          sys.exit(1)
        elif high_count > 0:
          print(f"⚠️  Security Warning: {high_count} high severity security issues")
          # Don't fail but warn
        else:
          print("✅ No critical security issues found")
      except FileNotFoundError:
        print("No security report found - no SQL files analyzed")
      except Exception as e:
        print(f"Error reading security report: {e}")
      PY

# Performance analysis
slowql-performance:
  <<: *slowql_template
  stage: performance
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == "main"
  variables:
    SLOWQL_INPUT_PATH: "."
  script:
    - |
      # Current branch analysis
      slowql --non-interactive \
        --input-file . \
        --analyzer performance \
        --export json \
        --out ./${REPORTS_DIR}/performance-current.json \
        --verbose
        
      # Compare with base branch if it's a merge request
      if [ "$CI_MERGE_REQUEST_IID" != "" ] && [ "$CI_MERGE_REQUEST_TARGET_BRANCH_NAME" != "" ]; then
        echo "Comparing with base branch: $CI_MERGE_REQUEST_TARGET_BRANCH_NAME"
        git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
        git checkout $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
        slowql --non-interactive \
          --input-file . \
          --analyzer performance \
          --export json \
          --out ./${REPORTS_DIR}/performance-base.json
        git checkout $CI_COMMIT_SHA
      fi
      
      # Performance comparison
      python3 - <<'PY'
      import json, glob, sys
      
      current_files = glob.glob('./${REPORTS_DIR}/performance-current*.json')
      base_files = glob.glob('./${REPORTS_DIR}/performance-base*.json')
      
      if current_files:
        current_data = json.load(open(current_files[0]))
        current_performance_issues = current_data["statistics"]["by_severity"].get("HIGH", 0)
        print(f"📊 Current Performance Issues: {current_performance_issues}")
        
        if base_files:
          base_data = json.load(open(base_files[0]))
          base_performance_issues = base_data["statistics"]["by_severity"].get("HIGH", 0)
          print(f"📊 Base Performance Issues: {base_performance_issues}")
          
          if current_performance_issues > base_performance_issues:
            print(f"⚠️  Performance Regression: {current_performance_issues - base_performance_issues} additional issues")
          elif current_performance_issues < base_performance_issues:
            print(f"✅ Performance Improvement: {base_performance_issues - current_performance_issues} fewer issues")
          else:
            print("✅ No performance change detected")
      PY

# Comprehensive analysis with quality gates
slowql-quality-gate:
  <<: *slowql_template
  stage: report
  needs: ["slowql-analysis"]
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == "main"
  script:
    - |
      # Quality gate evaluation
      python3 - <<'PY'
      import json, glob, sys, os
      
      # Find the latest comprehensive report
      report_files = glob.glob('./${REPORTS_DIR}/slowql_results_*.json')
      if not report_files:
          print("⚠️  No report files found - this may be expected for repos without SQL files")
          sys.exit(0)
          
      latest_report = max(report_files)
      data = json.load(open(latest_report, encoding='utf-8'))
      
      critical_count = data["statistics"]["by_severity"].get("CRITICAL", 0)
      high_count = data["statistics"]["by_severity"].get("HIGH", 0)
      total_issues = data["statistics"].get("total_issues", 0)
      health_score = data["statistics"].get("health_score", 100)
      
      print(f"📊 Comprehensive Analysis Results:")
      print(f"   Total Issues: {total_issues}")
      print(f"   Critical: {critical_count}")
      print(f"   High: {high_count}")
      print(f"   Health Score: {health_score}/100")
      
      # Quality gate logic
      quality_status = "PASS"
      quality_message = "Quality gate passed"
      
      if critical_count > 0:
          quality_status = "FAIL"
          quality_message = f"{critical_count} critical issues must be fixed"
          print(f"❌ QUALITY GATE FAILED: {quality_message}")
      elif high_count > 5:
          quality_status = "WARN" 
          quality_message = f"{high_count} high severity issues (threshold: 5)"
          print(f"⚠️  Quality Warning: {quality_message}")
      elif health_score < 70:
          quality_status = "WARN"
          quality_message = f"Health score {health_score}/100 below recommended threshold"
          print(f"⚠️  Health Warning: {quality_message}")
      else:
          print("✅ Quality gate passed")
          
      # Create quality gate report
      quality_report = {
          "pipeline_id": os.getenv("CI_PIPELINE_ID"),
          "commit_sha": os.getenv("CI_COMMIT_SHA"),
          "branch": os.getenv("CI_COMMIT_BRANCH"),
          "status": quality_status,
          "message": quality_message,
          "metrics": {
              "critical": critical_count,
              "high": high_count,
              "total_issues": total_issues,
              "health_score": health_score
          }
      }
      
      with open('./${REPORTS_DIR}/quality-gate-report.json', 'w') as f:
          json.dump(quality_report, f, indent=2)
          
      # Exit with appropriate code
      if quality_status == "FAIL":
          sys.exit(1)
      elif quality_status == "WARN":
          # Don't fail but set exit code 2 for warnings
          sys.exit(2)
      PY
      
  artifacts:
    paths:
      - ${REPORTS_DIR}/quality-gate-report.json
    expire_in: ${ARTIFACT_RETENTION}

# Scheduled comprehensive security audit
security-audit:
  <<: *slowql_template
  stage: security
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
  script:
    - |
      echo "Running comprehensive security audit"
      
      # Full security analysis
      slowql --non-interactive \
        --input-file . \
        --analyzer security \
        --export json html \
        --out ./${REPORTS_DIR}/audit-$(date +%Y%m%d)/ \
        --config .slowql.toml
        
      # Generate audit summary
      python3 - <<'PY'
      import json, glob, datetime
      
      audit_files = glob.glob('./${REPORTS_DIR}/audit-*/slowql_results_*.json')
      if audit_files:
        report_data = json.load(open(audit_files[0]))
        
        summary = {
            "audit_date": datetime.datetime.now().isoformat(),
            "total_issues": report_data["statistics"].get("total_issues", 0),
            "critical": report_data["statistics"]["by_severity"].get("CRITICAL", 0),
            "high": report_data["statistics"]["by_severity"].get("HIGH", 0),
            "medium": report_data["statistics"]["by_severity"].get("MEDIUM", 0),
            "low": report_data["statistics"]["by_severity"].get("LOW", 0)
        }
        
        print("🔍 Security Audit Summary:")
        for severity, count in summary.items():
            if severity != "audit_date":
                print(f"   {severity.title()}: {count}")
                
        with open('./${REPORTS_DIR}/security-audit-summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
      PY

# Notification job
notify-results:
  stage: notify
  needs: ["slowql-quality-gate"]
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH == "main"
  script:
    - |
      echo "Pipeline completed with status: $CI_JOB_STATUS"
      
      # Determine notification message
      if [ "$CI_JOB_STATUS" == "failed" ]; then
        MESSAGE="🚨 SlowQL analysis failed - critical issues detected"
      elif [ -f "./${REPORTS_DIR}/quality-gate-report.json" ]; then
        MESSAGE="✅ SlowQL analysis completed - quality gate passed"
      else
        MESSAGE="ℹ️  SlowQL analysis completed"
      fi
      
      echo "$MESSAGE"
      
      # In a real scenario, you would send notifications here
      # e.g., Slack, email, Teams, etc.
      
      # Example webhook notification (uncomment and configure as needed)
      # curl -X POST -H 'Content-type: application/json' \
      #   --data "{\"text\":\"$MESSAGE - Pipeline: $CI_PIPELINE_URL\"}" \
      #   "$SLACK_WEBHOOK_URL"

# Pages deployment for report sharing
pages:
  stage: report
  image: alpine:latest
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  script:
    - apk add --no-cache git
    - cp -r ${REPORTS_DIR} public/
  artifacts:
    paths:
      - public/
    expire_in: 1_week
  only:
    - main
```

---

## 🔧 Configuration Files

### `.slowql.toml` Configuration
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

[analyzers.security]
enabled_rules = ["sql_injection", "hardcoded_creds", "excessive_privileges"]
severity_threshold = "medium"

[analyzers.performance]
enabled_rules = ["select_star", "non_sargable", "deep_pagination"]
severity_threshold = "medium"
```

### Sample SQL Files
```sql
-- sample.sql
SELECT * FROM users WHERE email LIKE '%@gmail.com';
UPDATE users SET password = 'secret123' WHERE id = 1;
DELETE FROM orders;
SELECT name, email FROM users WHERE active = true;
```

---

## 📊 Advanced Features

### Multi-Project Pipeline
```yaml
# .gitlab-ci.yml in main project
include:
  - local: '.gitlab/ci/slowql-template.yml'

variables:
  SLOWQL_INPUT_PATH: "shared/sql/"

slowql-shared-analysis:
  extends: .slowql_template
  trigger:
    project: group/slowql-shared
    branch: main
    strategy: depend
```

### Dynamic Analysis
```yaml
dynamic-analysis:
  stage: analyze
  script:
    - |
      # Determine analysis scope based on changed files
      if git diff --name-only HEAD~1 | grep -q "\.sql$"; then
        echo "SQL files changed - running full analysis"
        SLOWQL_INPUT_PATH="."
      else
        echo "No SQL files changed - skipping analysis"
        exit 0
      fi
      
      slowql --non-interactive \
        --input-file ${SLOWQL_INPUT_PATH} \
        --export json \
        --out ./reports/
```

### Container-based Analysis
```yaml
container-analysis:
  stage: analyze
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - docker pull makroumi/slowql:latest
  script:
    - |
      docker run --rm \
        -v "$CI_PROJECT_DIR":/workspace \
        -w /workspace \
        makroumi/slowql:latest \
        slowql --non-interactive \
          --input-file . \
          --export json \
          --out ./reports/
  artifacts:
    paths:
      - reports/
```

---

## 🎯 Environment-Specific Configurations

### Staging Environment
```yaml
staging-analysis:
  extends: .slowql_template
  environment:
    name: staging
  variables:
    SLOWQL_CONFIG_PATH: ".slowql.staging.toml"
  only:
    - develop
```

### Production Environment
```yaml
production-analysis:
  extends: .slowql_template
  environment:
    name: production
  variables:
    SLOWQL_CONFIG_PATH: ".slowql.production.toml"
  only:
    - main
  when: manual
```

---

## 🔍 Integration with GitLab Features

### Code Quality Reports
```yaml
code_quality:
  stage: report
  image: python:3.12
  script:
    - pip install slowql
    - slowql --non-interactive --input-file . --export json --out ./codequality/
  artifacts:
    reports:
      codequality: ./codequality/slowql_results_*.json
  allow_failure: true
```

### Security Scanners Integration
```yaml
security-scan:
  stage: security
  image: python:3.12
  script:
    - pip install slowql
    - slowql --non-interactive --input-file . --analyzer security --export json --out ./security/
  artifacts:
    reports:
      security: ./security/slowql_results_*.json
```

---

## 🧠 Best Practices

### 1. Pipeline Optimization
```yaml
# Use rules to avoid unnecessary runs
rules:
  - if: $CI_COMMIT_BRANCH != "main"
    when: on_success
  - if: $CI_COMMIT_BRANCH == "main"
    when: always
```

### 2. Caching Strategy
```yaml
cache:
  key: "$CI_JOB_NAME-$CI_COMMIT_REF_SLUG"
  paths:
    - .cache/pip/
    - .venv/
```

### 3. Artifact Management
```yaml
artifacts:
  paths:
    - reports/
  expire_in: 1_week
  when: always
  reports:
    junit: reports/slowql_results_*.json
```

### 4. Error Handling
```yaml
script:
  - slowql --non-interactive --input-file . --export json || true
  - |
    if [ -f "reports/slowql_results_*.json" ]; then
      echo "Analysis completed successfully"
    else
      echo "No SQL files found or analysis failed"
    fi
```

---

## 📱 Notification Integration

### Slack Integration
```yaml
slack-notification:
  stage: notify
  script:
    - |
      MESSAGE="SlowQL Analysis - Pipeline: $CI_PIPELINE_URL - Status: $CI_JOB_STATUS"
      curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$MESSAGE\"}" \
        "$SLACK_WEBHOOK_URL"
  when: always
```

### Email Integration
```yaml
email-notification:
  stage: notify
  image: alpine/socat
  script:
    - |
      echo "SlowQL Analysis completed. View results: $CI_PIPELINE_URL" | \
      mail -s "SlowQL Analysis - $CI_COMMIT_BRANCH" $NOTIFICATION_EMAIL
  when: on_failure
```

---

## 🔗 Related Examples

- [Basic Usage](basic-usage.md)
- [Docker & Podman Integration](docker-podman-integration.md)
- [GitHub Actions](github-actions.md)
- [Jenkins](jenkins.md)
- [Pre-Commit Hook](pre-commit-hook.md)

---

## 📚 Additional Resources

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [GitLab CI/CD Pipeline Configuration Reference](https://docs.gitlab.com/ee/ci/yaml/)
- [GitLab Container Registry](https://docs.gitlab.com/ee/user/packages/container_registry/)
- [GitLab Environments and Deployments](https://docs.gitlab.com/ee/ci/environments/)
