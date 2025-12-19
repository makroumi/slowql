# Jenkins

This comprehensive example shows how to run SlowQL inside Jenkins pipelines to automatically analyze SQL files during builds. Includes advanced pipeline configurations, quality gates, multi-branch support, and comprehensive reporting.

---

## 🚀 Complete Jenkins Pipeline Example

### `Jenkinsfile` (Declarative Pipeline)

```groovy
pipeline {
    agent any
    
    environment {
        SLOWQL_VERSION = 'latest'
        PYTHON_VERSION = '3.12'
        REPORTS_DIR = 'reports'
        ARTIFACT_RETENTION = 7
    }
    
    parameters {
        choice(
            name: 'ANALYSIS_TYPE',
            choices: ['full', 'security-only', 'performance-only', 'compliance-only'],
            description: 'Type of analysis to perform'
        )
        booleanParam(
            name: 'GENERATE_REPORTS',
            defaultValue: true,
            description: 'Generate HTML/CSV reports for stakeholders'
        )
        booleanParam(
            name: 'QUALITY_GATE_ENABLED',
            defaultValue: true,
            description: 'Enable quality gate checks'
        )
        string(
            name: 'CRITICAL_THRESHOLD',
            defaultValue: '0',
            description: 'Maximum allowed critical issues (0 for strict)'
        )
        string(
            name: 'HIGH_THRESHOLD',
            defaultValue: '5',
            description: 'Maximum allowed high severity issues'
        )
    }
    
    tools {
        python3 'python-3.12'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        preserveStashes(buildCount: 5)
    }
    
    triggers {
        pollSCM('H/15 * * * *')  // Poll every 15 minutes
        cron('0 2 * * 0')        // Weekly Sunday 2 AM
    }
    
    stages {
        stage('Setup') {
            steps {
                script {
                    echo "🔧 Setting up SlowQL analysis environment"
                    
                    // Create virtual environment
                    sh '''
                        python3 -m venv .venv
                        source .venv/bin/activate
                        pip3 install --upgrade pip
                        pip3 install slowql[dev] readchar
                    '''
                    
                    // Create directories
                    sh '''
                        mkdir -p ${REPORTS_DIR}
                        mkdir -p temp
                        mkdir -p logs
                    '''
                    
                    // Display environment info
                    sh '''
                        source .venv/bin/activate
                        python --version
                        pip list | grep slowql
                    '''
                }
            }
        }
        
        stage('Pre-Analysis Validation') {
            steps {
                script {
                    echo "🔍 Validating analysis parameters"
                    
                    // Check if SQL files exist
                    def sqlFiles = findFiles(glob: '**/*.sql')
                    if (sqlFiles.size() == 0) {
                        echo "ℹ️ No SQL files found - skipping analysis"
                        currentBuild.result = 'NOT_BUILT'
                        return
                    }
                    
                    echo "📊 Found ${sqlFiles.size()} SQL files to analyze"
                    
                    // Display selected parameters
                    echo "Analysis Type: ${params.ANALYSIS_TYPE}"
                    echo "Generate Reports: ${params.GENERATE_REPORTS}"
                    echo "Quality Gate: ${params.QUALITY_GATE_ENABLED}"
                }
            }
        }
        
        stage('SlowQL Analysis') {
            steps {
                script {
                    echo "🚀 Running SlowQL analysis"
                    
                    // Determine analysis command based on parameters
                    def analysisType = params.ANALYSIS_TYPE
                    def reportFormats = params.GENERATE_REPORTS ? 'html csv json' : 'json'
                    def extraArgs = ''
                    
                    switch(analysisType) {
                        case 'security-only':
                            extraArgs = '--analyzer security'
                            break
                        case 'performance-only':
                            extraArgs = '--analyzer performance'
                            break
                        case 'compliance-only':
                            extraArgs = '--analyzer compliance'
                            break
                        default:
                            extraArgs = ''  // Full analysis
                    }
                    
                    // Run SlowQL analysis
                    sh """
                        source .venv/bin/activate
                        slowql --non-interactive \\
                            --input-file . \\
                            ${extraArgs} \\
                            --export ${reportFormats} \\
                            --out ./${REPORTS_DIR}/ \\
                            --verbose \\
                            --config .slowql.toml || true
                    """
                    
                    // Verify reports were generated
                    def reportFiles = findFiles(glob: "${REPORTS_DIR}/**/*")
                    echo "Generated ${reportFiles.size()} report files"
                }
            }
        }
        
        stage('Quality Gate') {
            when {
                expression { return params.QUALITY_GATE_ENABLED }
            }
            steps {
                script {
                    echo "🎯 Evaluating quality gate criteria"
                    
                    // Quality gate evaluation script
                    sh '''
                        source .venv/bin/activate
                        python3 - <<'PY'
                        import json, glob, sys, os
                        
                        # Find the most recent comprehensive report
                        report_files = glob.glob("reports/slowql_results_*.json")
                        if not report_files:
                            print("⚠️  No report files found - this may be expected for repos without SQL files")
                            sys.exit(0)
                            
                        latest_report = max(report_files)
                        data = json.load(open(latest_report, encoding="utf-8"))
                        
                        critical_count = data["statistics"]["by_severity"].get("CRITICAL", 0)
                        high_count = data["statistics"]["by_severity"].get("HIGH", 0)
                        total_issues = data["statistics"].get("total_issues", 0)
                        health_score = data["statistics"].get("health_score", 100)
                        
                        # Get thresholds from environment
                        critical_threshold = int(os.getenv("CRITICAL_THRESHOLD", "0"))
                        high_threshold = int(os.getenv("HIGH_THRESHOLD", "5"))
                        
                        print(f"📊 Quality Gate Analysis:")
                        print(f"   Total Issues: {total_issues}")
                        print(f"   Critical: {critical_count} (threshold: {critical_threshold})")
                        print(f"   High: {high_count} (threshold: {high_threshold})")
                        print(f"   Health Score: {health_score}/100")
                        
                        # Quality gate logic
                        quality_status = "PASS"
                        quality_message = "Quality gate passed"
                        
                        if critical_count > critical_threshold:
                            quality_status = "FAIL"
                            quality_message = f"{critical_count} critical issues exceed threshold ({critical_threshold})"
                            print(f"❌ QUALITY GATE FAILED: {quality_message}")
                        elif high_count > high_threshold:
                            quality_status = "WARN" 
                            quality_message = f"{high_count} high severity issues exceed threshold ({high_threshold})"
                            print(f"⚠️  Quality Warning: {quality_message}")
                        elif health_score < 70:
                            quality_status = "WARN"
                            quality_message = f"Health score {health_score}/100 below recommended threshold (70)"
                            print(f"⚠️  Health Warning: {quality_message}")
                        else:
                            print("✅ Quality gate passed")
                            
                        # Create quality gate report
                        quality_report = {
                            "pipeline_id": os.getenv("BUILD_ID"),
                            "build_number": os.getenv("BUILD_NUMBER"),
                            "status": quality_status,
                            "message": quality_message,
                            "metrics": {
                                "critical": critical_count,
                                "high": high_count,
                                "total_issues": total_issues,
                                "health_score": health_score
                            },
                            "thresholds": {
                                "critical": critical_threshold,
                                "high": high_threshold
                            }
                        }
                        
                        with open("reports/quality-gate-report.json", "w") as f:
                            json.dump(quality_report, f, indent=2)
                            
                        # Exit with appropriate code
                        if quality_status == "FAIL":
                            sys.exit(1)
                        elif quality_status == "WARN":
                            sys.exit(2)  # Warning exit code
                        PY
                    '''
                    
                    // Handle quality gate results
                    def qualityGateResult = currentBuild.result
                    if (qualityGateResult == 'FAILURE') {
                        error("Quality gate failed - critical issues detected")
                    } else if (qualityGateResult == 'UNSTABLE') {
                        echo "⚠️ Quality gate warning - review recommended"
                    }
                }
            }
        }
        
        stage('Security Analysis') {
            when {
                anyOf {
                    expression { return params.ANALYSIS_TYPE == 'security-only' }
                    expression { return params.ANALYSIS_TYPE == 'full' }
                }
            }
            steps {
                script {
                    echo "🔒 Running security-focused analysis"
                    
                    sh '''
                        source .venv/bin/activate
                        slowql --non-interactive \\
                            --input-file . \\
                            --analyzer security \\
                            --export json \\
                            --out ./${REPORTS_DIR}/security-report.json \\
                            --config .slowql.toml
                    '''
                    
                    // Security-specific evaluation
                    sh '''
                        source .venv/bin/activate
                        python3 - <<'PY'
                        import json, sys
                        
                        try:
                            with open("reports/security-report.json", "r") as f:
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
                            else:
                                print("✅ No critical security issues found")
                        except FileNotFoundError:
                            print("No security report found - no SQL files analyzed")
                        except Exception as e:
                            print(f"Error reading security report: {e}")
                        PY
                    '''
                }
            }
        }
        
        stage('Performance Analysis') {
            when {
                anyOf {
                    expression { return params.ANALYSIS_TYPE == 'performance-only' }
                    expression { return params.ANALYSIS_TYPE == 'full' }
                }
            }
            steps {
                script {
                    echo "⚡ Running performance-focused analysis"
                    
                    sh '''
                        source .venv/bin/activate
                        slowql --non-interactive \\
                            --input-file . \\
                            --analyzer performance \\
                            --export json \\
                            --out ./${REPORTS_DIR}/performance-report.json \\
                            --verbose
                    '''
                    
                    // Performance trend analysis (if previous builds exist)
                    script {
                        def previousBuild = Jenkins.instance.getItemByFullName(env.JOB_NAME).getLastBuild()
                        if (previousBuild && previousBuild.number != currentBuild.number) {
                            echo "📈 Comparing with previous build performance"
                            
                            // This would require storing previous build reports
                            // Implementation depends on your artifact storage strategy
                        }
                    }
                }
            }
        }
        
        stage('Generate Dashboard') {
            when {
                expression { return params.GENERATE_REPORTS }
            }
            steps {
                script {
                    echo "📊 Generating analysis dashboard"
                    
                    // Create a summary dashboard
                    sh '''
                        source .venv/bin/activate
                        python3 - <<'PY'
                        import json, glob, datetime
                        
                        # Find all report files
                        json_files = glob.glob("reports/slowql_results_*.json")
                        
                        if not json_files:
                            print("No reports found for dashboard generation")
                            exit(0)
                        
                        # Load the latest report
                        latest_report = max(json_files)
                        data = json.load(open(latest_report))
                        
                        # Generate dashboard HTML
                        dashboard_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>SlowQL Analysis Dashboard</title>
                            <style>
                                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                                .metric {{ display: inline-block; margin: 20px; padding: 20px; 
                                         border: 1px solid #ccc; border-radius: 5px; }}
                                .critical {{ background-color: #ffebee; }}
                                .high {{ background-color: #fff3e0; }}
                                .medium {{ background-color: #f3e5f5; }}
                                .low {{ background-color: #e8f5e8; }}
                            </style>
                        </head>
                        <body>
                            <h1>SlowQL Analysis Dashboard</h1>
                            <p>Generated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                            
                            <div class="metric">
                                <h3>Total Issues</h3>
                                <p>{data["statistics"].get("total_issues", 0)}</p>
                            </div>
                            
                            <div class="metric critical">
                                <h3>Critical</h3>
                                <p>{data["statistics"]["by_severity"].get("CRITICAL", 0)}</p>
                            </div>
                            
                            <div class="metric high">
                                <h3>High</h3>
                                <p>{data["statistics"]["by_severity"].get("HIGH", 0)}</p>
                            </div>
                            
                            <div class="metric medium">
                                <h3>Medium</h3>
                                <p>{data["statistics"]["by_severity"].get("MEDIUM", 0)}</p>
                            </div>
                            
                            <div class="metric low">
                                <h3>Low</h3>
                                <p>{data["statistics"]["by_severity"].get("LOW", 0)}</p>
                            </div>
                            
                            <div class="metric3>Health Score">
                                <h</h3>
                                <p>{data["statistics"].get("health_score", 100)}/100</p>
                            </div>
                        </body>
                        </html>
                        """
                        
                        with open("reports/dashboard.html", "w") as f:
                            f.write(dashboard_html)
                        
                        print("Dashboard generated successfully")
                        PY
                    '''
                }
            }
        }
        
        stage('Multi-Branch Comparison') {
            when {
                anyOf {
                    branch 'develop'
                    branch 'main'
                }
            }
            steps {
                script {
                    echo "🔄 Comparing with baseline branch"
                    
                    // Compare current analysis with main branch
                    sh '''
                        # This would require git operations to compare with baseline
                        # Implementation depends on your branching strategy
                        echo "Multi-branch comparison completed"
                    '''
                }
            }
        }
    }
    
    post {
        always {
            script {
                echo "📋 Post-build actions"
                
                // Archive all reports
                archiveArtifacts artifacts: 'reports/**', fingerprint: true, allowEmptyArchive: true
                
                // Publish HTML reports
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'reports',
                    reportFiles: '*.html',
                    reportName: 'SlowQL Analysis Reports'
                ])
                
                // Store test results (if using JUnit format)
                // junit 'reports/slowql_results_*.xml'
            }
        }
        
        success {
            script {
                echo "✅ Build completed successfully"
                
                // Send success notification
                if (env.BRANCH_NAME == 'main') {
                    echo "Main branch analysis completed successfully"
                }
            }
        }
        
        failure {
            script {
                echo "❌ Build failed"
                
                // Analyze failure type
                if (currentBuild.result == 'FAILURE') {
                    // Quality gate failure
                    echo "Quality gate failure - critical issues detected"
                    
                    // Send critical alert
                    // This would integrate with your notification system
                } else {
                    // Build failure
                    echo "Build process failure"
                }
            }
        }
        
        unstable {
            script {
                echo "⚠️ Build completed with warnings"
                
                // Quality gate warnings
                echo "Quality gate warnings detected - review recommended"
            }
        }
        
        cleanup {
            script {
                echo "🧹 Cleaning up workspace"
                
                // Clean up temporary files
                sh '''
                    rm -rf temp/
                    rm -rf .venv/
                '''
            }
        }
    }
}
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
compliance = true

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

[export.json]
include_statistics = true
include_suggestions = true
pretty_print = true

[export.html]
theme = "dark"
include_charts = true
standalone = true
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

## 🏗️ Jenkins Configuration

### Global Tool Configuration
```groovy
// In Jenkins Global Configuration
tools {
    python3 {
        version '3.12.0'
    }
}
```

### Shared Library Structure
```
vars/
├── slowqlAnalyze.groovy
├── slowqlQualityGate.groovy
└── slowqlNotify.groovy
```

### Shared Library: `slowqlAnalyze.groovy`
```groovy
def call(Map config = [:]) {
    def analysisType = config.analysisType ?: 'full'
    def outputFormats = config.outputFormats ?: 'json'
    def extraArgs = config.extraArgs ?: ''
    
    sh """
        source .venv/bin/activate
        slowql --non-interactive \\
            --input-file . \\
            ${extraArgs} \\
            --export ${outputFormats} \\
            --out ./reports/ \\
            --config .slowql.toml
    """
}
```

---

## 📊 Advanced Jenkins Features

### Blue Ocean Pipeline Visualization
```groovy
pipeline {
    agent any
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
    }
    
    stages {
        stage('🔍 Analyze') {
            steps {
                script {
                    slowqlAnalyze(analysisType: 'full')
                }
            }
        }
        
        stage('🎯 Quality Gate') {
            steps {
                script {
                    slowqlQualityGate()
                }
            }
        }
        
        stage('📊 Report') {
            steps {
                script {
                    slowqlNotify(type: 'success')
                }
            }
        }
    }
}
```

### Multibranch Pipeline Configuration
```groovy
// Jenkinsfile for multibranch pipeline
pipeline {
    agent any
    
    triggers {
        pollSCM('H/15 * * * *')
    }
    
    stages {
        stage('Conditional Analysis') {
            steps {
                script {
                    // Only run analysis if SQL files changed
                    def changedFiles = sh(
                        script: 'git diff --name-only HEAD~1',
                        returnStdout: true
                    ).trim()
                    
                    if (changedFiles.contains('.sql')) {
                        echo "SQL files changed - running analysis"
                        slowqlAnalyze()
                    } else {
                        echo "No SQL files changed - skipping analysis"
                    }
                }
            }
        }
    }
}
```

### Parallel Analysis Pipeline
```groovy
pipeline {
    agent any
    
    stages {
        stage('Parallel Analysis') {
            parallel {
                stage('Security') {
                    steps {
                        script {
                            slowqlAnalyze(analysisType: 'security-only', extraArgs: '--analyzer security')
                        }
                    }
                }
                
                stage('Performance') {
                    steps {
                        script {
                            slowqlAnalyze(analysisType: 'performance-only', extraArgs: '--analyzer performance')
                        }
                    }
                }
                
                stage('Compliance') {
                    steps {
                        script {
                            slowqlAnalyze(analysisType: 'compliance-only', extraArgs: '--analyzer compliance')
                        }
                    }
                }
            }
        }
        
        stage('Aggregate Results') {
            steps {
                script {
                    // Aggregate results from parallel analyses
                    sh '''
                        python3 - <<'PY'
                        import json, glob
                        
                        # Aggregate results from all parallel analyses
                        all_reports = glob.glob("reports/*_report.json")
                        
                        if all_reports:
                            # Combine reports logic here
                            print("Aggregating results from parallel analyses")
                        PY
                    '''
                }
            }
        }
    }
}
```

---

## 🔧 Jenkins Job Configuration

### Pipeline Script from SCM
```groovy
pipeline {
    agent any
    
    triggers {
        githubPush()  // GitHub webhook trigger
    }
    
    scm {
        git {
            remote {
                url 'https://github.com/your-org/your-repo.git'
                credentialsId 'github-credentials'
            }
            branch '*/main'
            extensions {
                cleanBeforeCheckout()
            }
        }
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Analyze') {
            steps {
                script {
                    // Your analysis logic here
                }
            }
        }
    }
}
```

### Parameters Configuration
```groovy
properties([
    parameters([
        choice(
            name: 'ANALYSIS_SCOPE',
            choices: ['changed-files', 'full-repository'],
            description: 'Scope of SQL analysis'
        ),
        booleanParam(
            name: 'STRICT_MODE',
            defaultValue: false,
            description: 'Enable strict quality gates'
        ),
        string(
            name: 'EXCLUDE_PATTERNS',
            defaultValue: '**/test_*.sql,**/legacy/*.sql',
            description: 'File patterns to exclude from analysis'
        )
    ])
])
```

---

## 🔔 Notification Integration

### Slack Integration
```groovy
post {
    always {
        script {
            def color = 'good'  // green
            def status = 'Success'
            
            if (currentBuild.result == 'FAILURE') {
                color = 'danger'  // red
                status = 'Failed'
            } else if (currentBuild.result == 'UNSTABLE') {
                color = 'warning'  // yellow
                status = 'Unstable'
            }
            
            // Send Slack notification
            if (env.SLACK_WEBHOOK_URL) {
                sh """
                    curl -X POST -H 'Content-type: application/json' \\
                        --data '{"text":"SlowQL Analysis ${status}","attachments":[{"color":"${color}","fields":[{"title":"Build","value":"${env.BUILD_NUMBER}","short":true},{"title":"Branch","value":"${env.BRANCH_NAME}","short":true},{"title":"Duration","value":"${currentBuild.durationString}","short":true}]}]}' \\
                        "${env.SLACK_WEBHOOK_URL}"
                """
            }
        }
    }
}
```

### Email Integration
```groovy
post {
    failure {
        script {
            emailext (
                subject: "SlowQL Analysis Failed - ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: """
                    SlowQL analysis failed for build ${env.BUILD_NUMBER}.
                    
                    Branch: ${env.BRANCH_NAME}
                    Commit: ${env.GIT_COMMIT}
                    Duration: ${currentBuild.durationString}
                    
                    View results: ${env.BUILD_URL}
                    
                    Please check the analysis reports and address any critical issues.
                """,
                to: "${env.CHANGE_AUTHOR_EMAIL}",
                attachmentsPattern: 'reports/**/*'
            )
        }
    }
}
```

---

## 🧠 Best Practices

### 1. Pipeline Organization
- **Modular stages**: Separate concerns into distinct stages
- **Conditional execution**: Use when conditions to optimize pipeline runs
- **Error handling**: Implement proper error handling and recovery
- **Resource management**: Clean up resources in post-build actions

### 2. Performance Optimization
```groovy
// Use caching to speed up builds
cache {
    key: "slowql-${env.BUILD_ID}"
    paths {
        ".venv/"
        ".cache/"
    }
}
```

### 3. Security Considerations
```groovy
// Use credentials management for sensitive data
withCredentials([string(credentialsId: 'slowql-config', variable: 'SLOWQL_CONFIG')]) {
    sh 'slowql --config $SLOWQL_CONFIG --input-file .'
}
```

### 4. Quality Gates Implementation
```groovy
def evaluateQualityGate(reportData) {
    def critical = reportData.statistics.by_severity.CRITICAL ?: 0
    def high = reportData.statistics.by_severity.HIGH ?: 0
    
    if (critical > 0) {
        currentBuild.result = 'FAILURE'
        error("Quality gate failed: ${critical} critical issues found")
    } else if (high > 5) {
        currentBuild.result = 'UNSTABLE'
        echo "Quality gate warning: ${high} high severity issues found"
    }
}
```

---

## 🔗 Related Examples

- [Basic Usage](basic-usage.md)
- [Docker & Podman Integration](docker-podman-integration.md)
- [GitHub Actions](github-actions.md)
- [GitLab CI](gitlab-ci.md)
- [Pre-Commit Hook](pre-commit-hook.md)

---

## 📚 Additional Resources

- [Jenkins Pipeline Documentation](https://www.jenkins.io/doc/book/pipeline/)
- [Pipeline Syntax Reference](https://www.jenkins.io/doc/pipeline/steps/)
- [Shared Libraries Documentation](https://www.jenkins.io/doc/book/pipeline/shared-libraries/)
- [Blue Ocean Documentation](https://www.jenkins.io/doc/book/blueocean/)
