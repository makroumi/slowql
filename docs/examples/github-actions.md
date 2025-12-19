# GitHub Actions

This comprehensive example shows how to run SlowQL inside GitHub Actions workflows to automatically analyze SQL files on every push, pull request, or on a schedule. Includes advanced quality gates, multi-platform testing, and comprehensive reporting.

---

## 🚀 Complete Workflow Example

Create `.github/workflows/slowql-analysis.yml`:

```yaml
name: SlowQL Analysis
on:
  push:
    paths:
      - '**.sql'
      - '.github/workflows/slowql-analysis.yml'
      - '.slowql.toml'
  pull_request:
    paths:
      - '**.sql'
      - '.github/workflows/slowql-analysis.yml'
      - '.slowql.toml'
  schedule:
    # Weekly security audit every Sunday at 2 AM UTC
    - cron: '0 2 * * 0'
  workflow_dispatch:  # Allow manual triggering
    inputs:
      analysis_type:
        description: 'Type of analysis to perform'
        required: true
        default: 'full'
        type: choice
        options:
          - full
          - security-only
          - performance-only

env:
  SLOWQL_VERSION: "latest"
  PYTHON_VERSION: "3.12"

jobs:
  slowql-analysis:
    name: SlowQL Analysis
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: [3.11, 3.12]
        
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for comprehensive analysis
          
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          
      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt', '**/pyproject.toml') }}
          restore-keys: |
            ${{ runner.os }}-pip-
            
      - name: Install SlowQL
        run: |
          python -m pip install --upgrade pip
          pip install slowql[dev] readchar
          
      - name: Create analysis directories
        run: |
          mkdir -p reports
          mkdir -p temp
          
      - name: Run SlowQL Analysis
        run: |
          # Determine analysis type
          ANALYSIS_TYPE="${{ github.event.inputs.analysis_type || 'full' }}"
          
          # Set command based on analysis type
          case "$ANALYSIS_TYPE" in
            "security-only")
              ARGS="--analyzer security"
              ;;
            "performance-only") 
              ARGS="--analyzer performance"
              ;;
            *)
              ARGS=""  # Full analysis
              ;;
          esac
          
          # Run analysis with comprehensive options
          slowql --non-interactive \
            --input-file . \
            $ARGS \
            --export html csv json \
            --out ./reports/ \
            --verbose \
            --config .slowql.toml || true
            
      - name: Upload reports
        uses: actions/upload-artifact@v4
        with:
          name: slowql-reports-${{ matrix.python-version }}
          path: |
            reports/
          retention-days: 30
          if-no-files-found: warn
          
      - name: Quality Gate - Critical Issues
        run: |
          python - <<'PY'
          import json, glob, sys, os
          
          # Find the most recent comprehensive report
          report_files = glob.glob('reports/slowql_results_*.json')
          if not report_files:
              print("⚠️  No report files found - this may be expected for repos without SQL files")
              sys.exit(0)
              
          latest_report = max(report_files)
          data = json.load(open(latest_report, encoding='utf-8'))
          
          critical_count = data["statistics"]["by_severity"].get("CRITICAL", 0)
          high_count = data["statistics"]["by_severity"].get("HIGH", 0)
          total_issues = data["statistics"]["get"]("total_issues", 0)
          health_score = data["statistics"].get("health_score", 100)
          
          print(f"📊 Analysis Results:")
          print(f"   Total Issues: {total_issues}")
          print(f"   Critical: {critical_count}")
          print(f"   High: {high_count}")
          print(f"   Health Score: {health_score}/100")
          
          # Quality gate logic
          if critical_count > 0:
              print(f"❌ FAILED: Found {critical_count} CRITICAL SQL issues!")
              print("🚨 Critical issues must be fixed before merging")
              sys.exit(1)
          elif high_count > 5:
              print(f"⚠️  WARNING: Found {high_count} HIGH severity SQL issues (threshold: 5)")
              print("Consider addressing high severity issues before merging")
              # Don't fail the build, but warn
          elif health_score < 70:
              print(f"⚠️  WARNING: Health score {health_score}/100 is below recommended threshold (70)")
          else:
              print("✅ Quality gate passed")
              
          PY
          
      - name: Comment PR with Results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const path = require('path');
            
            // Find the latest report
            const reportsDir = 'reports';
            let reportContent = '';
            
            try {
              const files = fs.readdirSync(reportsDir);
              const htmlFiles = files.filter(f => f.endsWith('.html'));
              
              if (htmlFiles.length > 0) {
                const latestReport = htmlFiles.sort().pop();
                const reportPath = path.join(reportsDir, latestReport);
                reportContent = fs.readFileSync(reportPath, 'utf8');
                
                // Extract summary from HTML or create a summary
                const summary = `## 🔍 SlowQL Analysis Results
                
                📊 **Latest Analysis:** ${new Date().toLocaleString()}
                📁 **Reports:** Available in the [workflow artifacts](${context.payload.pull_request.html_url}/checks)
                
                ✅ *Full detailed report attached as workflow artifact*`;
                
                await github.rest.issues.createComment({
                  issue_number: context.issue.number,
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  body: summary
                });
              }
            } catch (error) {
              console.log('Could not create PR comment:', error.message);
            }

  slowql-security-audit:
    name: Security Audit
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule' || github.event.inputs.analysis_type == 'security-only'
    
    steps:
      - uses: actions/checkout@v4
        
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          
      - name: Install SlowQL
        run: pip install slowql[dev]
        
      - name: Run Security Analysis
        run: |
          slowql --non-interactive \
            --input-file . \
            --analyzer security \
            --export json \
            --out ./security-report.json \
            --config .slowql.toml
            
      - name: Upload Security Report
        uses: actions/upload-artifact@v4
        with:
          name: slowql-security-audit
          path: security-report.json
          
      - name: Security Alert on Critical Issues
        if: always()
        run: |
          python - <<'PY'
          import json, sys
          
          try:
            with open('security-report.json', 'r') as f:
              data = json.load(f)
              
            critical_count = data["statistics"]["by_severity"].get("CRITICAL", 0)
            
            if critical_count > 0:
              print(f"🚨 SECURITY ALERT: {critical_count} critical security issues found!")
              # In a real scenario, you might send notifications here
              sys.exit(1)
            else:
              print("✅ No critical security issues found")
          except FileNotFoundError:
            print("No security report found - no SQL files analyzed")
          except Exception as e:
            print(f"Error reading security report: {e}")
          PY

  slowql-performance-benchmark:
    name: Performance Benchmark
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          
      - name: Install SlowQL
        run: pip install slowql[dev]
        
      - name: Performance Analysis
        run: |
          # Analyze current changes
          slowql --non-interactive \
            --input-file . \
            --analyzer performance \
            --export json \
            --out ./performance-current.json \
            --verbose
            
          # Compare with base branch if possible
          if [ "${{ github.event.pull_request.base.sha }}" != "" ]; then
            git checkout "${{ github.event.pull_request.base.sha }}"
            slowql --non-interactive \
              --input-file . \
              --analyzer performance \
              --export json \
              --out ./performance-base.json
            git checkout "${{ github.event.head.sha }}"
          fi
          
      - name: Upload Performance Reports
        uses: actions/upload-artifact@v4
        with:
          name: slowql-performance-benchmark
          path: |
            performance-*.json
```

---

## 📂 Repository Structure

Include the following files in your repository:

### `.slowql.toml` (Configuration)
```toml
[general]
non_interactive = true
verbose_output = false

[rule_categories]
security = true
performance = true
cost = true
reliability = true
quality = true

[rules.sql_injection]
enabled = true
severity = "critical"

[rules.select_star]
enabled = true
severity = "medium"
```

### Sample SQL Files
```sql
-- sample.sql
SELECT * FROM users WHERE email LIKE '%@gmail.com';
UPDATE users SET password = 'secret123' WHERE id = 1;
DELETE FROM orders;
```

---

## 🔧 Workflow Customization

### Environment Variables
```yaml
env:
  SLOWQL_VERSION: "latest"    # or specific version "1.3.0"
  PYTHON_VERSION: "3.12"      # Python version to use
  ANALYSIS_PATH: "sql/"       # Directory containing SQL files
  REPORT_RETENTION: 30        # Days to keep reports
```

### Trigger Conditions
```yaml
on:
  push:
    branches: [ main, develop ]
    paths:
      - 'sql/**'
      - '**/*.sql'
      - '.github/workflows/**'
  pull_request:
    branches: [ main ]
    paths:
      - 'sql/**'
      - '**/*.sql'
```

### Job Dependencies
```yaml
jobs:
  slowql-analysis:
    # ... analysis steps
    
  slowql-notification:
    needs: slowql-analysis
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Notify team
        run: |
          echo "Analysis completed with status: ${{ needs.slowql-analysis.result }}"
```

---

## 📊 Report Integration

### GitHub Pages Integration
```yaml
- name: Deploy to GitHub Pages
  if: github.ref == 'refs/heads/main'
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./reports
```

### Slack Integration
```yaml
- name: Notify Slack
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    text: 'SlowQL analysis failed'
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 🧠 Best Practices

### 1. Workflow Organization
- **Separate concerns**: Use different jobs for different analysis types
- **Fail fast**: Use `fail-fast: false` for comprehensive testing
- **Cache dependencies**: Improve build times with pip caching
- **Artifact retention**: Keep reports for debugging and compliance

### 2. Quality Gates
```python
# Example quality gate logic
def check_quality_gate(report_data):
    critical = report_data["statistics"]["by_severity"].get("CRITICAL", 0)
    high = report_data["statistics"]["by_severity"].get("HIGH", 0)
    health_score = report_data["statistics"].get("health_score", 100)
    
    if critical > 0:
        return "FAIL", f"{critical} critical issues found"
    elif high > 5:
        return "WARN", f"{high} high severity issues (threshold: 5)"
    elif health_score < 70:
        return "WARN", f"Health score {health_score}/100 below threshold"
    else:
        return "PASS", "Quality gate passed"
```

### 3. Security Considerations
- **Secret management**: Use GitHub Secrets for sensitive data
- **Least privilege**: Grant minimal required permissions
- **Code scanning**: Integrate with GitHub Advanced Security
- **Dependency updates**: Keep SlowQL version updated

### 4. Performance Optimization
```yaml
strategy:
  matrix:
    include:
      - python-version: "3.11"
        slowql-version: "1.2.0"
      - python-version: "3.12"  
        slowql-version: "latest"
```

---

## 🔗 Related Examples

- [Basic Usage](basic-usage.md)
- [Docker & Podman Integration](docker-podman-integration.md)
- [GitLab CI](gitlab-ci.md)
- [Jenkins](jenkins.md)
- [Pre-Commit Hook](pre-commit-hook.md)

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/using-workflows)
- [Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [Environment Protection Rules](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
