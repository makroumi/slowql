# tests/unit/test_detector.py
import pytest

from slowql.core.detector import IssueSeverity, QueryDetector


@pytest.fixture
def detector():
    return QueryDetector()

# -------------------------------
# Parametrized coverage for all detectors
# -------------------------------
@pytest.mark.parametrize("query,expected,severity", [
    # SELECT *
    ("SELECT * FROM users", "SELECT * Usage", IssueSeverity.MEDIUM),
    # Missing WHERE
    ("DELETE FROM users", "Missing WHERE in UPDATE/DELETE", IssueSeverity.CRITICAL),
    # Non-SARGable
    ("SELECT * FROM users WHERE YEAR(created_at)=2023", "Non-SARGable WHERE", IssueSeverity.HIGH),
    # Implicit conversion
    ("SELECT * FROM users WHERE email = 123", "Implicit Type Conversion", IssueSeverity.HIGH),
    # Cartesian product
    ("SELECT * FROM a, b", "Cartesian Product", IssueSeverity.CRITICAL),
    # N+1 pattern
    ("SELECT * FROM users WHERE user_id = ?", "Potential N+1 Pattern", IssueSeverity.HIGH),
    # OR prevents index
    ("SELECT * FROM users WHERE id=1 OR name='x'", "OR Prevents Index", IssueSeverity.MEDIUM),
    # OFFSET pagination
    ("SELECT * FROM users OFFSET 5000", "Large OFFSET Pagination", IssueSeverity.HIGH),
    # DISTINCT unnecessary
    ("SELECT DISTINCT id FROM users", "Unnecessary DISTINCT", IssueSeverity.LOW),
    # Huge IN list
    ("SELECT * FROM users WHERE id IN (" + ",".join(map(str, range(100))) + ")", "Massive IN List", IssueSeverity.HIGH),
    # Leading wildcard
    ("SELECT * FROM users WHERE name LIKE '%john%'", "Leading Wildcard", IssueSeverity.HIGH),
    # COUNT(*) exists
    ("SELECT COUNT(*) FROM users WHERE id > 0 HAVING COUNT(*) > 0", "COUNT(*) for Existence", IssueSeverity.MEDIUM),
    # NOT IN nullable
    ("SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM orders)", "NOT IN with NULLable", IssueSeverity.HIGH),
    # EXISTS without LIMIT
    ("SELECT * FROM users WHERE EXISTS (SELECT * FROM orders)", "EXISTS without LIMIT", IssueSeverity.LOW),
    # Floating point equality
    ("SELECT * FROM users WHERE price = 19.99", "Floating Point Equality", IssueSeverity.MEDIUM),
    # NULL comparison
    ("SELECT * FROM users WHERE status = NULL", "NULL Comparison Error", IssueSeverity.CRITICAL),
    # Function on column
    ("SELECT * FROM users WHERE UPPER(email) = 'X'", "Function on Indexed Column", IssueSeverity.HIGH),
    # HAVING instead of WHERE
    ("SELECT * FROM users HAVING status='active'", "HAVING Instead of WHERE", IssueSeverity.MEDIUM),
    # UNION missing ALL
    ("SELECT * FROM users UNION SELECT * FROM orders", "UNION Missing ALL", IssueSeverity.MEDIUM),
    # Subquery in SELECT list
    ("SELECT id, (SELECT COUNT(*) FROM orders) FROM users", "Subquery in SELECT List", IssueSeverity.HIGH),
    # BETWEEN timestamps
    ("SELECT * FROM users WHERE created BETWEEN '2023-01-01' AND '2023-12-31'", "BETWEEN with Timestamps", IssueSeverity.MEDIUM),
    # CASE in WHERE
    ("SELECT * FROM users WHERE CASE WHEN status=1 THEN true END", "CASE in WHERE Clause", IssueSeverity.MEDIUM),
    # OFFSET without ORDER
    ("SELECT * FROM users OFFSET 100", "OFFSET without ORDER BY", IssueSeverity.HIGH),
    # LIKE without wildcard
    ("SELECT * FROM users WHERE name LIKE 'John'", "LIKE without Wildcards", IssueSeverity.LOW),
    # Multiple wildcards (original test query now maps to new detector)
    ("SELECT * FROM users WHERE name LIKE '%%%test%%%'","Multiple Wildcards", IssueSeverity.HIGH),
    # Complex LIKE Pattern (new test query for existing detector)
    ("SELECT * FROM users WHERE name LIKE '%first%last%'", "Complex LIKE Pattern", IssueSeverity.HIGH),
    # ORDER BY ordinal
    ("SELECT * FROM users ORDER BY 1", "ORDER BY Ordinal", IssueSeverity.LOW),
])
def test_detector_patterns(detector, query, expected, severity):
    issues = detector.analyze(query)
    assert any(i.issue_type == expected and i.severity == severity for i in issues), f"Failed for: {query}"

# -------------------------------
# Edge Cases
# -------------------------------
def test_normalize_multiline_query(detector):
    query = """
    SELECT *
    -- Comment here
    FROM users
    /* Block comment */
    WHERE id = 1
    """
    issues = detector.analyze(query)
    assert any(i.issue_type == "SELECT * Usage" for i in issues)

def test_false_positive_no_issue(detector):
    query = "SELECT 1"
    issues = detector.analyze(query)
    assert issues == []

def test_case_insensitivity(detector):
    query = "select * from USERS"
    issues = detector.analyze(query)
    assert any(i.issue_type == "SELECT * Usage" for i in issues)

def test_multiple_issues_in_one_query(detector):
    query = "SELECT * FROM users WHERE YEAR(created_at)=2023 OR id=1"
    issues = detector.analyze(query)
    types = [i.issue_type for i in issues]
    assert "Non-SARGable WHERE" in types
    assert "OR Prevents Index" in types





    assert "Non-SARGable WHERE" in types
    assert "OR Prevents Index" in types


@pytest.mark.parametrize("query", [
    # Core Detector Methods - Clean Scenarios
    ("SELECT id FROM users"),
    ("UPDATE users SET name = 'test' WHERE id = 1"),
    ("SELECT id FROM users WHERE created_at = CURRENT_DATE"),
    ("SELECT id FROM users WHERE email = 'testuser'"),
    ("SELECT id FROM a JOIN b ON a.id = b.a_id"),
    ("SELECT id FROM users"), # No subquery with ?
    ("SELECT id FROM users"), # No correlated subquery
    ("SELECT id FROM users WHERE id=1 AND name='x'"),
    ("SELECT id FROM users LIMIT 10 OFFSET 100 ORDER BY id"), # Offset <= 1000
    ("SELECT DISTINCT name FROM users"), # Name might not be unique
    ("SELECT id FROM users WHERE id IN (1, 2, 3)"), # Small IN list
    ("SELECT id FROM users WHERE name LIKE 'john%'"), # Trailing wildcard
    ("SELECT id FROM users"), # No COUNT(*) > 0
    ("SELECT id FROM users WHERE id = 1"), # No subquery
    ("SELECT id FROM users WHERE EXISTS (SELECT id FROM orders LIMIT 1)"), # Has LIMIT 1
    ("SELECT id FROM users WHERE quantity > 10"), # Range comparison
    ("SELECT id FROM users WHERE status = 'active'"), # Uses IS NULL
    ("SELECT id FROM users WHERE email = 'X'"), # No function on column
    ("SELECT COUNT(*) FROM users GROUP BY status HAVING COUNT(*) > 1"), # Has aggregate
    ("SELECT id FROM users UNION ALL SELECT id FROM orders"), # Uses UNION ALL
    ("SELECT id, name FROM users"),
    ("SELECT id FROM users WHERE created > CURRENT_DATE"), # Not BETWEEN
    ("SELECT id FROM users WHERE status = 'active'"), # No CASE in WHERE
    ("SELECT id FROM users OFFSET 100 ORDER BY id"), # Has ORDER BY
    ("SELECT id FROM users WHERE name = 'John'"), # Uses =
    ("SELECT id FROM users ORDER BY id"), # Uses column name

    # Group A: Semantic & Logical - Clean Scenarios
    ("SELECT id FROM users ORDER BY id"),
    ("SELECT CASE WHEN status=1 THEN 'Active' ELSE 'Inactive' END FROM users"),
    ("SELECT id FROM users WHERE id = 1 AND name = 'test'"),
    ("SELECT id FROM users WHERE id = 1"),
    ("SELECT id FROM users WHERE id = 1"),
    ("SELECT id FROM users WHERE id = 1"),
    ("SELECT id FROM users WHERE id IS NULL"),
    ("SELECT id FROM users WHERE id IS NULL"),
    ("SELECT id FROM a JOIN b ON a.id = b.a_id"),
    ("SELECT id FROM users"),
    ("SELECT id AS user_id FROM users"),
    ("SELECT id FROM users WHERE id = (SELECT max(id) FROM other LIMIT 1)"),
    ("SELECT CAST(id AS VARCHAR(255)) FROM users"), # Not casting to same type
    ("SELECT (id) FROM users"),
    ("SELECT id, name FROM users"),
    ("INSERT INTO users (id, name) VALUES (1, 'test')"),
    ("INSERT INTO users (id, name) SELECT id, name FROM other_users"),
    ("TRUNCATE TABLE users CASCADE"), # Has CASCADE
    ("DROP TABLE IF EXISTS users"),

    # Group B: Maintainability & Style - Clean Scenarios
    ("SELECT ID FROM USERS WHERE ID = 1"),
    ("SELECT id FROM users"), # No mixed case table
    ("SELECT id FROM users"), # No todo comment
    ("SELECT id FROM users"), # No hardcoded IP
    ("SELECT id FROM users"), # No hardcoded URL
    ("SELECT id FROM users WHERE secret = 'safepassword123'"), # Not keyword 'password'
    ("SELECT id FROM users WHERE id = 1"), # Small number
    ("SELECT id FROM users WHERE created_at = CURRENT_DATE"),
    ("SELECT id FROM users WHERE token = 'valid_jwt_token'"), # Not a simple pattern
    ("SELECT id FROM users WHERE username = 'john.doe'"),
    ("SELECT id FROM users JOIN orders ON users.id = orders.user_id"), # Simple join
    ("SELECT id FROM users"), # No trailing whitespace
    ("SELECT id FROM users"), # Single spaces

    # Group C: Exotic Performance - Clean Scenarios
    ("SELECT id FROM users UNION ALL SELECT id FROM orders"),
    ("SELECT id FROM users WHERE NOT EXISTS (SELECT 1 FROM other_users WHERE other_users.id > 0 LIMIT 1)"), # No subquery
    ("SELECT id FROM users JOIN orders ON users.id = orders.user_id"),
    ("SELECT NOW() AT TIME ZONE 'UTC'"),
    ("SELECT created_at + INTERVAL '1 day' FROM users"),
    ("SELECT id FROM users WHERE created_at > CURRENT_DATE"),
    ("SELECT id FROM users WHERE created_at > CURRENT_DATE"),
    ("SELECT id FROM users WHERE EXISTS (SELECT 1 FROM orders WHERE orders.user_id = 1 LIMIT 1)"),
    ("SELECT id FROM users WHERE EXISTS (SELECT 1 FROM orders WHERE orders.user_id = 1 LIMIT 1)"),
    ("SELECT id FROM users WHERE name LIKE 'john%'"),
    ("SELECT id FROM users WHERE name LIKE 'john%'"),
    ("SELECT id FROM users WHERE name = 'John'"),
    ("SELECT id FROM users"), # No JSON extract
    ("SELECT ROW_NUMBER() OVER (PARTITION BY id) FROM users"),
    ("WITH my_cte AS (SELECT 1 as val) SELECT val FROM my_cte"),
    ("WITH RECURSIVE my_cte AS (SELECT col FROM my_cte WHERE col < 10) SELECT col + 1 FROM my_cte LIMIT 10"), # Has LIMIT
    ("SELECT id FROM a JOIN b ON a.id = b.id"),
    ("SELECT id FROM a LEFT JOIN b ON a.id = b.a_id"),
    ("SELECT id FROM a LEFT JOIN b ON a.id = b.id"),
    ("SELECT id FROM a LEFT JOIN b ON a.id = b.id"),
    ("SELECT id FROM users FOR UPDATE NOWAIT"),
    ("CREATE TABLE t (col VARCHAR(255))"),
    ("CREATE TABLE t (col VARCHAR(255))"),
    ("CREATE TABLE t (col DECIMAL(10, 2))"),
    ("SELECT id FROM users"), # No cursor
    ("SELECT id FROM users"), # No while loop
    ("SELECT id FROM users"), # No dynamic SQL
    ("SELECT id FROM users WHERE name = 'John'"),
    ("GRANT SELECT ON users TO public"),
    ("SELECT 1 FROM users"),
    ("SELECT (SELECT 1 FROM orders) FROM users"),
])
def test_detector_clean_queries(detector, query):
    """Test that various queries expected to be clean return an empty list of issues."""
    issues = detector.analyze(query)
    assert issues == []



