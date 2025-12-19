# Basic Usage

This comprehensive example shows how to run SlowQL on SQL files and interpret the results. It's ideal for first-time users, quick local analysis, and understanding the full capabilities of the tool.

---

## 📂 Sample SQL File

Create a file called `sample.sql` with various query types:

```sql
-- Performance issues
SELECT * FROM users WHERE email LIKE '%@gmail.com';
SELECT name, email FROM users;

-- Security issues  
UPDATE users SET password = 'secret123' WHERE id = 1;

-- Data safety issues
DELETE FROM orders;

-- Best practice violations
SELECT * FROM users WHERE active = true;
```

---

## 🚀 Run SlowQL

### Basic Analysis
```bash
slowql --input-file sample.sql
```

**What you'll see:**
- 🔍 **Real-time Analysis**: Issues detected instantly with health score
- 🎯 **Severity Classification**: Critical, High, Medium, Low issues  
- 💡 **Actionable Fixes**: Specific recommendations for each issue
- 📊 **Interactive Tables**: Sortable, filterable results
- 🎭 **Matrix Rain Animation**: Professional intro experience

### Interactive Mode (Premium Experience)
```bash
slowql --mode auto
```

**Navigation:**
- **↑/↓** to move between menu items
- **Enter** to select options
- **q/Esc** to cancel/exit
- **A/E/X** for quick actions (Analyze/Exit)

---

## 📤 Export Results

Generate comprehensive reports in multiple formats:

### JSON Export (Machine-Readable)
```bash
slowql --input-file sample.sql --export json --out results.json
```

**JSON Structure:**
```json
{
  "statistics": {
    "total_issues": 5,
    "by_severity": {
      "CRITICAL": 1,
      "HIGH": 2,
      "MEDIUM": 2
    },
    "health_score": 72
  },
  "issues": [
    {
      "rule_id": "SEC-INJ-001",
      "severity": "CRITICAL",
      "dimension": "security",
      "message": "Potential SQL injection detected",
      "impact": "Data breach risk",
      "fix": "Use parameterized queries",
      "location": "line 3"
    }
  ]
}
```

### HTML Export (Shareable Reports)
```bash
slowql --input-file sample.sql --export html --out report.html
```

**Features:**
- **Single-page report** with dark neon theme
- **Interactive visualizations** and statistics
- **Print-friendly layout** for documentation
- **Professional presentation** for stakeholders

### CSV Export (Spreadsheet Analysis)
```bash
slowql --input-file sample.sql --export csv --out analysis.csv
```

**CSV Columns:**
- severity, rule_id, dimension, message, impact, fix, location

---

## ⚙️ Advanced Options

### Fast Mode (Quick Scans)
```bash
slowql --fast --input-file sample.sql
```

**Use Cases:**
- Time-sensitive code reviews
- Large codebase initial assessment
- CI/CD pipeline optimization

### CI/CD Safe Mode (Automation)
```bash
slowql --non-interactive --input-file sample.sql --export json --out results.json
```

**Features:**
- Clean output without animations
- Machine-readable JSON format
- Suitable for automated pipelines
- Exit codes for quality gates

### Verbose Analysis (Detailed Output)
```bash
slowql --input-file sample.sql --verbose
```

**Includes:**
- Detailed rule execution information
- Performance metrics
- Rule coverage statistics
- Analysis timing data

### Custom Configuration
```bash
slowql --input-file sample.sql --config .slowql.toml --export html csv
```

---

## 📊 Understanding Results

### Issue Severity Levels

| Severity | Description | Action Required | Example |
|----------|-------------|-----------------|---------|
| **CRITICAL** | Security risks, data loss potential | Fix immediately | SQL injection, hardcoded passwords |
| **HIGH** | Performance issues, compliance risks | Fix before production | SELECT *, missing WHERE clauses |
| **MEDIUM** | Best practice violations | Address in next sprint | Non-SARGable queries |
| **LOW** | Minor optimizations | Consider for improvement | Style improvements |

### Health Score Interpretation

- **90-100**: Excellent query design
- **70-89**: Good with minor improvements needed  
- **50-69**: Average, several issues to address
- **30-49**: Poor, significant issues present
- **0-29**: Critical, major redesign needed

### Issue Dimensions

| Dimension | Focus | Examples |
|-----------|-------|----------|
| **Security** | Attack prevention | SQL injection, hardcoded credentials |
| **Performance** | Query optimization | SELECT *, missing indexes |
| **Cost** | Resource usage | Large table scans, cross-region joins |
| **Reliability** | Data safety | Missing WHERE clauses, DROP statements |
| **Quality** | Code maintainability | Consistent naming, modern SQL |
| **Compliance** | Regulatory adherence | PII exposure, audit violations |

---

## 🛠️ Common Use Cases

### Developer Workflow
```bash
# During development
slowql --input-file current_feature.sql --export html

# Before committing code
slowql --non-interactive --input-file sql/ --export json --out commit-analysis.json

# Code review preparation
slowql --input-file review_queries.sql --export html --out review_report.html
```

### Performance Testing
```bash
# Analyze performance impact
slowql --input-file optimized_query.sql --verbose --export json

# Compare query versions
slowql --compare --input-file baseline.sql optimized.sql

# Benchmark analysis
slowql --input-file benchmark_queries.sql --export csv --out performance_metrics.csv
```

### Security Auditing
```bash
# Focus on security issues
slowql --input-file legacy_queries.sql --config security-config.toml --export json

# Generate compliance report
slowql --input-file audit_queries.sql --export csv --out compliance_report.csv

# Risk assessment
slowql --input-file critical_queries.sql --export html --out risk_assessment.html
```

### Team Collaboration
```bash
# Generate team report
slowql --input-file team_queries.sql --export html --out team_analysis.html

# Aggregate results from multiple files
slowql --input-file sql/ --export json --out aggregated_results.json

# Export for dashboards
slowql --input-file production_queries.sql --export json csv --out dashboard_data/
```

---

## 🎯 Interactive Features

### Compose Mode (SQL Editor)
```bash
slowql --mode compose
```

**Features:**
- **Syntax highlighting** for SQL
- **Real-time validation** as you type
- **Auto-completion** for keywords
- **Format preservation** for complex queries

### Paste Mode (Clipboard Input)
```bash
slowql --mode paste
```

**Process:**
1. Paste SQL from clipboard when prompted
2. Instant analysis of pasted content
3. Results displayed immediately
4. Option to save or analyze more

### File Browser Mode
```bash
slowql --mode file
```

**Capabilities:**
- **Directory navigation** for SQL files
- **Multi-file selection** for batch analysis
- **File type filtering** (.sql, .ddl, etc.)
- **Preview selected files** before analysis

### Compare Mode
```bash
slowql --compare
```

**Workflow:**
1. Select baseline query/file
2. Select comparison query/file  
3. Side-by-side analysis results
4. Highlight differences and improvements

---

## 🔧 Configuration Options

### Custom Rule Configuration
```bash
# Use custom configuration file
slowql --input-file sample.sql --config custom_rules.toml

# Override specific rules
slowql --input-file sample.sql --rule SEC-INJ-001:disable --rule SELECT-STAR:medium
```

### Export Customization
```bash
# Custom output directory
slowql --input-file sample.sql --export html csv --out ./reports/$(date +%Y%m%d)/

# Include additional metadata
slowql --input-file sample.sql --export json --include-metadata --include-timing
```

### Performance Tuning
```bash
# Disable caching for fresh analysis
slowql --input-file sample.sql --no-cache

# Parallel processing for large files
slowql --input-file large_directory/ --parallel --workers 4

# Memory optimization for constrained environments
slowql --input-file sample.sql --low-memory --chunk-size 100
```

---

## ✅ Verify Setup

```bash
# Check installation and version
slowql --version

# View available options
slowql --help

# Test with provided examples
slowql --input-file examples/sample.sql

# Verify all components work
slowql --input-file examples/sample.sql --export html csv json
```

**Expected Output:**
- Version information: `SlowQL v1.3.0`
- Complete help menu with all options
- Analysis of sample file showing detected issues
- Successfully generated export files

---

## 🎓 Learning Path

### Beginner (Start Here)
1. **Install SlowQL** using pip or pipx
2. **Try basic analysis** with provided examples
3. **Export results** in different formats
4. **Understand severity levels** and recommendations

### Intermediate (Expand Skills)
1. **Use interactive mode** for full experience
2. **Configure custom rules** for your needs
3. **Integrate with IDE** for real-time feedback
4. **Set up pre-commit hooks** for automated checks

### Advanced (Professional Use)
1. **Custom rule development** for specific requirements
2. **CI/CD integration** with quality gates
3. **Team dashboards** with aggregated reporting
4. **Enterprise deployment** with container orchestration

---

## 🔗 Related Examples

- [Docker & Podman Integration](docker-podman-integration.md)
- [GitHub Actions](github-actions.md)
- [GitLab CI](gitlab-ci.md) 
- [Jenkins](jenkins.md)
- [Pre-Commit Hook](pre-commit-hook.md)

---

## 💡 Pro Tips

1. **Start Small**: Begin with individual files before analyzing entire directories
2. **Use Exports**: Generate HTML reports for team discussions and documentation
3. **Leverage Interactive Mode**: The full experience provides the most value for learning
4. **Set Up CI Early**: Automated checks prevent issues from reaching production
5. **Customize Rules**: Adjust sensitivity based on your team's coding standards
6. **Monitor Performance**: Use `--verbose` mode to understand analysis performance
7. **Version Control**: Include SlowQL configuration in your repository for consistency
