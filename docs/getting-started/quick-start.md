# Quick Start

This guide provides a fast path to running SlowQL immediately after installation. Follow these steps to analyze queries in under a minute and discover the full power of the tool.

---

## 🚀 Quick Start Checklist

**New to SlowQL? Follow these steps:**

- [ ] **Install SlowQL** (see [Installation](installation.md))
- [ ] **Try the demo** with sample queries
- [ ] **Analyze your SQL files** using the CLI
- [ ] **Set up CI/CD integration** for automated checks
- [ ] **Explore advanced features** (exports, interactive mode)

---

## ⚡ 1. Quick Analysis Demo

Create a test file and analyze it immediately:

```bash
# Create sample SQL file
cat > sample.sql << 'EOF'
SELECT * FROM users WHERE email LIKE '%@gmail.com';
UPDATE users SET password = 'secret123' WHERE id = 1;
SELECT name, email FROM users;
EOF

# Analyze the file
slowql --input-file sample.sql
```

**What you'll see:**
- 🔍 **Real-time Analysis**: Issues detected instantly
- 🎯 **Severity Classification**: Critical, High, Medium, Low issues
- 💡 **Actionable Fixes**: Specific recommendations for each issue
- 📊 **Health Score**: Overall query quality rating (0-100)

---

## 🧠 2. Interactive Mode

Start the interactive terminal interface for a premium experience:

```bash
slowql --mode auto
```

**Navigation:**
- **↑/↓** to move between options
- **Enter** to select
- **q/Esc** to cancel
- **A/E/X** for quick actions (Analyze/Exit)

**Interactive Features:**
- **Compose Mode**: Interactive SQL editor with syntax highlighting
- **Paste Mode**: Direct SQL input from clipboard
- **File Mode**: Browse and select SQL files
- **Compare Mode**: Side-by-side query comparison

---

## 🔍 3. Compare Queries

Analyze and compare two versions of a query:

```bash
slowql --compare
```

**Use Cases:**
- **Performance Regression Testing**: Compare query optimizations
- **Code Review**: Validate query changes before deployment
- **Benchmarking**: Measure impact of query improvements

---

## 📤 4. Export Results

Generate comprehensive reports in multiple formats:

```bash
slowql --input-file sample.sql --export html csv json
```

**Available Formats:**

### JSON Export
```json
{
  "statistics": {
    "total_issues": 3,
    "by_severity": {
      "CRITICAL": 1,
      "HIGH": 1,
      "MEDIUM": 1
    }
  },
  "issues": [
    {
      "rule_id": "SEC-INJ-001",
      "severity": "CRITICAL",
      "message": "Potential SQL injection detected"
    }
  ]
}
```
**Best for:** CI/CD integration, API integration, data analysis

### HTML Export
- **Interactive single-page report** with dark neon theme
- **Shareable web reports** for team presentations
- **Print-friendly layout** for documentation

**Best for:** Leadership reports, team presentations, documentation

### CSV Export
```csv
severity,rule_id,dimension,message,impact,fix,location
CRITICAL,SEC-INJ-001,security,"SQL injection detected","Data breach risk","Use parameterized queries",line 5
```
**Best for:** Spreadsheet analysis, compliance reporting, external tool integration

---

## 🤖 5. CI/CD Integration

For automated pipelines and quality gates:

```bash
slowql --non-interactive --input-file sql/ --export json
```

**CI/CD Features:**
- **Clean Output**: No animations or interactive prompts
- **Machine-Readable**: JSON format for automated processing
- **Quality Gates**: Fail builds on critical issues
- **Artifact Generation**: Upload reports to CI/CD systems

---

## 🏃‍♂️ 6. Fast Mode

For quick scans without deep analysis:

```bash
slowql --fast --input-file sample.sql
```

**Use When:**
- **Time-sensitive reviews** need quick feedback
- **Large codebases** require rapid scanning
- **Initial assessment** before detailed analysis

---

## 🎛️ 7. Advanced Options

### Custom Output Directory
```bash
slowql --input-file sample.sql --export html csv --out ./reports/
```

### Verbose Analysis
```bash
slowql --input-file sample.sql --verbose
```

### Disable Animations
```bash
slowql --no-intro --input-file sample.sql
```

### Multiple Files
```bash
slowql --input-file sql/ --export json
```

---

## 📊 Understanding Results

### Issue Severity Levels

| Severity | Description | Action Required |
|----------|-------------|-----------------|
| **CRITICAL** | Security risks, data loss potential | Fix immediately |
| **HIGH** | Performance issues, compliance risks | Fix before production |
| **MEDIUM** | Best practice violations | Address in next sprint |
| **LOW** | Minor optimizations | Consider for improvement |

### Health Score Interpretation

- **90-100**: Excellent query design
- **70-89**: Good with minor improvements needed
- **50-69**: Average, several issues to address
- **30-49**: Poor, significant issues present
- **0-29**: Critical, major redesign needed

---

## 🛠️ Common Use Cases

### Developer Workflow
```bash
# During development
slowql --input-file current_query.sql --export html

# Before committing
slowql --non-interactive --input-file sql/ --export json
```

### Code Review
```bash
# Compare query versions
slowql --compare

# Generate review report
slowql --input-file feature_query.sql --export html --out review_report.html
```

### Performance Testing
```bash
# Analyze performance impact
slowql --input-file optimized_query.sql --verbose

# Benchmark against baseline
slowql --compare --input-file baseline.sql optimized.sql
```

### Security Audit
```bash
# Focus on security issues
slowql --input-file legacy_queries.sql --export json

# Generate compliance report
slowql --input-file audit_queries.sql --export csv --out compliance_report.csv
```

---

## ✅ Verify Setup

```bash
# Check installation
slowql --version

# Test all features
slowql --help

# Run demo analysis
slowql --input-file examples/sample.sql
```

**Expected Output:**
- Version information displayed
- Help menu with all options
- Demo analysis showing detected issues

---

## 🔧 Next Steps

### Immediate Actions
1. **Analyze your SQL files** with the basic command
2. **Try interactive mode** to explore all features
3. **Set up exports** for your reporting needs
4. **Configure CI/CD** integration

### Advanced Usage
1. **Customize rules** via configuration file
2. **Create custom detectors** for your specific needs
3. **Integrate with your IDE** for real-time analysis
4. **Set up team dashboards** with exported reports

---

## 🔗 Related Pages

- [Installation](installation.md)
- [Configuration](configuration.md)
- [First Analysis](first-analysis.md)
- [CLI Reference](../user-guide/cli-reference.md)
- [Interactive Mode](../user-guide/interactive-mode.md)
- [Export Formats](../user-guide/export-formats.md)
- [CI/CD Integration](../user-guide/ci-cd-integration.md)

---

## 💡 Tips for Success

1. **Start Small**: Begin with individual files before analyzing entire directories
2. **Use Exports**: Generate reports for team discussions and documentation
3. **Leverage Interactive Mode**: The full experience provides the most value
4. **Set Up CI Early**: Automated checks prevent issues from reaching production
5. **Customize Rules**: Adjust sensitivity based on your team's standards
