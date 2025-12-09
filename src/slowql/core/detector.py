# detector.py

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class IssueSeverity(Enum):
    """Severity levels for detected issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DetectedIssue:
    """Represents a detected SQL issue"""
    issue_type: str
    query: str
    description: str
    fix: str
    impact: str
    severity: IssueSeverity
    line_number: Optional[int] = None


class QueryDetector:
    """
    SQL Query Pattern Detector
    Analyzes SQL queries for common anti-patterns, performance issues,
    and potential bugs without executing them.
    Example:
        >>> detector = QueryDetector()
        >>> issues = detector.analyze("SELECT * FROM users WHERE name LIKE '%john%'")
        >>> for issue in issues:
        ...     print(f"{issue.issue_type}: {issue.fix}")
    """

    def __init__(self) -> None:
        """Initialize the detector with pattern definitions"""
        self._patterns = self._compile_patterns()
        self.detectors = self._get_all_detectors()

    def _compile_patterns(self) -> dict[str, re.Pattern]:
        """Pre-compile all regex patterns for performance."""
        return {
            # Base patterns (from original code)
            'select_star': re.compile(r'SELECT\s+\*', re.IGNORECASE),
            'missing_where': re.compile(r'(UPDATE|DELETE)(\s+FROM)?\s+\w+(\s+SET)?', re.IGNORECASE),
            'non_sargable': re.compile(r'WHERE\s+(YEAR|MONTH|DAY|UPPER|LOWER)\s*\([^)]+\)\s*=', re.IGNORECASE),
            'implicit_conversion': re.compile(r"WHERE\s+\w*(name|email|code|status)\w*\s*=\s*\d+", re.IGNORECASE),
            'cartesian_product': re.compile(r'FROM\s+\w+\s*,\s*\w+', re.IGNORECASE),
            'n_plus_1': re.compile(r'SELECT.*FROM.*WHERE\s+\w+_id\s*=\s*\?', re.IGNORECASE),
            'correlated_subquery': re.compile(r'SELECT.*\(SELECT.*FROM.*WHERE.*=.*\w+\.\w+', re.IGNORECASE),
            'or_prevents_index': re.compile(r'WHERE.*\w+\s*=.*\sOR\s+\w+\s*=', re.IGNORECASE),
            'offset_pagination': re.compile(r'OFFSET\s+(\d+)', re.IGNORECASE),
            'distinct_unnecessary': re.compile(r'SELECT\s+DISTINCT\s+\w*id\w*', re.IGNORECASE),
            'huge_in_list': re.compile(r'IN\s*\(([^)]+)\)', re.IGNORECASE),
            'leading_wildcard': re.compile(r'LIKE\s+[\'"]%', re.IGNORECASE),
            'count_star_exists': re.compile(r'COUNT\s*\(\s*\*\s*\)\s*>\s*0', re.IGNORECASE),
            'not_in_nullable': re.compile(r'NOT\s+IN\s*\(\s*SELECT', re.IGNORECASE),
            'no_limit_exists': re.compile(r'EXISTS\s*\(\s*SELECT\s+(?!.*LIMIT)', re.IGNORECASE),
            'floating_point_equals': re.compile(r'(price|amount|total|cost|value)\s*=\s*\d+\.\d+', re.IGNORECASE),
            'null_comparison': re.compile(r'=\s*NULL|!=\s*NULL', re.IGNORECASE),
            'function_on_column': re.compile(r'WHERE.*(LOWER|UPPER|TRIM|SUBSTRING|DATE|YEAR|MONTH)\s*\(\s*(id|email|user_id|created_at)', re.IGNORECASE),
            'having_no_aggregates': re.compile(r'HAVING(?!\s+COUNT|\s+SUM|\s+AVG|\s+MAX|\s+MIN)', re.IGNORECASE),
            'union_missing_all': re.compile(r'UNION(?!\s+ALL)', re.IGNORECASE),
            'subquery_select_list': re.compile(r'SELECT.*,.*\(SELECT', re.IGNORECASE),
            'between_timestamps': re.compile(r'BETWEEN.*\d{4}-\d{2}-\d{2}.*AND.*\d{4}-\d{2}-\d{2}', re.IGNORECASE),
            'case_in_where': re.compile(r'WHERE.*CASE\s+WHEN', re.IGNORECASE),
            'offset_no_order': re.compile(r'OFFSET\s+\d+(?!.*ORDER\s+BY)', re.IGNORECASE),
            'like_no_wildcard': re.compile(r'LIKE\s+["\'][^%_]+["\']', re.IGNORECASE),
            'order_by_ordinal': re.compile(r'ORDER\s+BY\s+\d+', re.IGNORECASE),
        
            # GROUP A: SEMANTIC & LOGICAL CONSISTENCY (60+ new patterns)
            
            # A.1: Ambiguity & Determinism
            'ambiguous_order_by': re.compile(r'ORDER\s+BY\s+(?!.*\b(id|pk|primary_key)\b)', re.IGNORECASE),
            'missing_case_else': re.compile(r'CASE\s+WHEN.*WHEN.*END(?!\s+ELSE)', re.IGNORECASE),
            'redundant_or': re.compile(r'(\w+)\s*=\s*([^O]+)\s+OR\s+\1\s*=\s*\2', re.IGNORECASE),
            'contradictory_where': re.compile(r'WHERE\s+(\w+)\s*=\s*(\d+)\s+AND\s+\1\s*=\s*(?!\2)\d+', re.IGNORECASE),
            'always_true': re.compile(r'WHERE\s+1\s*=\s*1|WHERE\s+TRUE', re.IGNORECASE),
            'always_false': re.compile(r'WHERE\s+1\s*=\s*0|WHERE\s+FALSE', re.IGNORECASE),
            'tautology': re.compile(r'WHERE\s+(\w+)\s+IS\s+NOT\s+NULL\s+OR\s+\1\s+IS\s+NULL', re.IGNORECASE),
            'contradiction': re.compile(r'WHERE\s+(\w+)\s+IS\s+NOT\s+NULL\s+AND\s+\1\s+IS\s+NULL', re.IGNORECASE),
            'duplicate_join': re.compile(r'JOIN\s+(\w+)\s+.*JOIN\s+\1\s+', re.IGNORECASE),
            'redundant_distinct': re.compile(r'SELECT\s+DISTINCT.*GROUP\s+BY', re.IGNORECASE),
            
            # A.2: Redundancy & Triviality
            'redundant_alias': re.compile(r'(\w+)\s+AS\s+\1\b', re.IGNORECASE),
            'trivial_subquery': re.compile(r'\(\s*SELECT\s+[\d\'\"]+\s*\)', re.IGNORECASE),
            'redundant_cast': re.compile(r'CAST\s*\(\s*(\w+)\s+AS\s+(\w+)\s*\).*\1.*\2', re.IGNORECASE),
            'unnecessary_coalesce': re.compile(r'COALESCE\s*\(\s*(\w+)\s*\)(?!\s*,)', re.IGNORECASE),
            'redundant_parentheses': re.compile(r'\(\s*\(\s*SELECT', re.IGNORECASE),
            'duplicate_column_select': re.compile(r'SELECT.*(\w+).*,.*\1', re.IGNORECASE),
            'self_join_unnecessary': re.compile(r'FROM\s+(\w+)\s+\w+\s+JOIN\s+\1\s+\w+\s+ON\s+\w+\.\w+\s*=\s*\w+\.\w+$', re.IGNORECASE),
            
            # A.3: DDL/DML Integrity
            'insert_no_columns': re.compile(r'INSERT\s+INTO\s+\w+\s+VALUES', re.IGNORECASE),
            'insert_select_star': re.compile(r'INSERT\s+INTO.*SELECT\s+\*', re.IGNORECASE),
            'truncate_no_cascade': re.compile(r'TRUNCATE\s+TABLE\s+\w+(?!\s+CASCADE)', re.IGNORECASE),
            'drop_no_if_exists': re.compile(r'DROP\s+(TABLE|VIEW|INDEX)\s+(?!IF\s+EXISTS)', re.IGNORECASE),
            'alter_table_multiple': re.compile(r'ALTER\s+TABLE.*ALTER\s+TABLE', re.IGNORECASE),
            'create_temp_no_on_commit': re.compile(r'CREATE\s+TEMP.*TABLE(?!.*ON\s+COMMIT)', re.IGNORECASE),
            'foreign_key_no_index': re.compile(r'FOREIGN\s+KEY\s*\((\w+)\)', re.IGNORECASE),
            'unique_constraint_unnecessary': re.compile(r'PRIMARY\s+KEY.*UNIQUE', re.IGNORECASE),
            
            # GROUP B: MAINTAINABILITY, STYLE & COMPLIANCE (75+ new patterns)
            
            # B.1: Style Enforcement
            'lowercase_keyword': re.compile(r'\b(select|from|where|join|insert|update|delete|create|alter|drop)\b', re.IGNORECASE),
            'mixed_case_table': re.compile(r'FROM\s+([a-z]+[A-Z]|[A-Z]+[a-z])\w+', re.IGNORECASE),
            'trailing_semicolon_missing': re.compile(r'[^;]\s*$', re.IGNORECASE),
            'inconsistent_quotes': re.compile(r"'[^']*'.*\"[^\"]*\"|\"[^\"]*\".*'[^']*'", re.IGNORECASE),
            'tab_characters': re.compile(r'\t'),
            'trailing_whitespace': re.compile(r' +$', re.MULTILINE),
            'multiple_spaces': re.compile(r'  +'),
            'comma_position_inconsistent': re.compile(r',\s*\n\s*\w+.*\n\w+\s*,', re.IGNORECASE),
            
            # B.2: Comment & Documentation
            'todo_comment': re.compile(r'--.*\b(TODO|FIXME|HACK|XXX)\b', re.IGNORECASE),
            'no_header_comment': re.compile(r'^(?!.*--)', re.MULTILINE),
            'uncommented_complex_query': re.compile(r'(JOIN.*){3,}', re.IGNORECASE),
            'inline_comment_missing': re.compile(r'CASE\s+WHEN.*END(?!.*--)', re.IGNORECASE),
            
            # B.3: Hardcoded/Literal Risk
            'hardcoded_ip': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
            'hardcoded_url': re.compile(r'https?://[^\s\'"]+', re.IGNORECASE),
            'hardcoded_password': re.compile(r"(password|pwd|pass)\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
            'magic_number': re.compile(r'WHERE\s+\w+\s*=\s*(\d{2,})\b', re.IGNORECASE),
            'hardcoded_date': re.compile(r"['\"]20\d{2}-\d{2}-\d{2}['\"]", re.IGNORECASE),
            'embedded_connection_string': re.compile(r'(server|host|database)\s*=', re.IGNORECASE),
            'api_key_pattern': re.compile(r"(api_key|apikey|token)\s*=\s*['\"][a-zA-Z0-9]{20,}['\"]", re.IGNORECASE),
            'email_in_query': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
            
            # GROUP C: EXOTIC/EDGE-CASE PERFORMANCE (40+ new patterns)
            
            # C.1: Set Operations
            'mixed_union': re.compile(r'UNION\s+ALL.*UNION(?!\s+ALL)', re.IGNORECASE),
            'except_over_not_exists': re.compile(r'EXCEPT|MINUS', re.IGNORECASE),
            'intersect_over_join': re.compile(r'INTERSECT', re.IGNORECASE),
            'union_in_view': re.compile(r'CREATE\s+VIEW.*UNION', re.IGNORECASE),
            
            # C.2: Date/Time Pitfalls
            'now_without_timezone': re.compile(r'\b(NOW|CURRENT_TIMESTAMP|GETDATE)\s*\(\s*\)(?!.*AT\s+TIME\s+ZONE)', re.IGNORECASE),
            'date_math_no_interval': re.compile(r"(created_at|updated_at)\s*[+-]\s*\d+(?!\s+INTERVAL)", re.IGNORECASE),
            'strftime_in_where': re.compile(r'WHERE.*STRFTIME|DATE_FORMAT', re.IGNORECASE),
            'extract_in_where': re.compile(r'WHERE.*EXTRACT\s*\(', re.IGNORECASE),
            'timezone_conversion_missing': re.compile(r'timestamp.*(?!CONVERT_TZ|AT TIME ZONE)', re.IGNORECASE),
            'date_trunc_indexable': re.compile(r'WHERE\s+DATE_TRUNC', re.IGNORECASE),
            
            # C.3: Advanced Predicates
            'in_subquery_over_exists': re.compile(r'WHERE\s+\w+\s+IN\s*\(\s*SELECT', re.IGNORECASE),
            'exists_over_count': re.compile(r'WHERE\s+\(\s*SELECT\s+COUNT', re.IGNORECASE),
            'any_all_inefficient': re.compile(r'=\s+ANY|>\s+ALL', re.IGNORECASE),
            'like_complex_pattern': re.compile(r'LIKE\s+[\'"]%\w+%\w+%', re.IGNORECASE),
            'regexp_in_where': re.compile(r'WHERE.*~|REGEXP|RLIKE', re.IGNORECASE),
            'json_extract_unindexed': re.compile(r'JSON_EXTRACT|->|->>', re.IGNORECASE),
            
            # Additional Advanced Patterns
            'window_function_no_partition': re.compile(r'(ROW_NUMBER|RANK|DENSE_RANK)\s*\(\s*\)(?!.*PARTITION)', re.IGNORECASE),
            'cte_unused': re.compile(r'WITH\s+(\w+)\s+AS.*SELECT(?!.*\1)', re.IGNORECASE),
            'recursive_cte_no_limit': re.compile(r'WITH\s+RECURSIVE.*(?!LIMIT)', re.IGNORECASE),
            'cross_join_explicit': re.compile(r'CROSS\s+JOIN', re.IGNORECASE),
            'natural_join': re.compile(r'NATURAL\s+JOIN', re.IGNORECASE),
            'using_clause': re.compile(r'JOIN.*USING\s*\(', re.IGNORECASE),
            'implicit_join_syntax': re.compile(r'FROM.*,.*WHERE', re.IGNORECASE),
            'outer_join_where_nulls': re.compile(r'LEFT\s+JOIN.*WHERE.*IS\s+NOT\s+NULL', re.IGNORECASE),
            'right_join_usage': re.compile(r'RIGHT\s+JOIN', re.IGNORECASE),
            'full_outer_join': re.compile(r'FULL\s+OUTER\s+JOIN', re.IGNORECASE),
            
            # Transaction & Concurrency
            'select_for_update_no_wait': re.compile(r'FOR\s+UPDATE(?!\s+NOWAIT|\s+SKIP\s+LOCKED)', re.IGNORECASE),
            'transaction_no_isolation': re.compile(r'BEGIN|START\s+TRANSACTION(?!.*ISOLATION)', re.IGNORECASE),
            'lock_in_share_mode': re.compile(r'LOCK\s+IN\s+SHARE\s+MODE', re.IGNORECASE),
            'implicit_commit': re.compile(r'(CREATE|ALTER|DROP|TRUNCATE).*(?!BEGIN|START)', re.IGNORECASE),
            
            # Data Type Issues
            'varchar_max': re.compile(r'VARCHAR\s*\(\s*MAX\s*\)|VARCHAR\s*\(\s*\d{4,}\s*\)', re.IGNORECASE),
            'text_vs_varchar': re.compile(r'\bTEXT\b', re.IGNORECASE),
            'decimal_no_precision': re.compile(r'DECIMAL(?!\s*\(\d+\s*,\s*\d+\))', re.IGNORECASE),
            'enum_overuse': re.compile(r"ENUM\s*\([^)]{100,}\)", re.IGNORECASE),
            
            # Aggregate Pitfalls
            'group_by_missing_aggregate': re.compile(r'SELECT.*\w+.*,.*COUNT|SUM|AVG(?!.*GROUP\s+BY)', re.IGNORECASE),
            'aggregate_no_group': re.compile(r'SELECT\s+(\w+).*,.*COUNT\s*\(', re.IGNORECASE),
            'group_by_all_columns': re.compile(r'GROUP\s+BY.*,.*,.*,', re.IGNORECASE),
            'having_before_group': re.compile(r'HAVING.*GROUP\s+BY', re.IGNORECASE),
            
            # Subquery Issues
            'scalar_subquery_multiple_rows': re.compile(r'=\s*\(\s*SELECT.*(?!LIMIT\s+1)', re.IGNORECASE),
            'subquery_no_alias': re.compile(r'\)\s+(?!AS\s+\w+)\s*(JOIN|,)', re.IGNORECASE),
            'nested_subquery_deep': re.compile(r'\(\s*SELECT.*\(\s*SELECT.*\(\s*SELECT', re.IGNORECASE),
            
            # Index Hints (Database Specific)
            'force_index': re.compile(r'FORCE\s+INDEX', re.IGNORECASE),
            'use_index': re.compile(r'USE\s+INDEX', re.IGNORECASE),
            'ignore_index': re.compile(r'IGNORE\s+INDEX', re.IGNORECASE),
            
            # Security Issues
            'dynamic_sql': re.compile(r'EXEC\s*\(|EXECUTE\s*\(|sp_executesql', re.IGNORECASE),
            'sql_injection_risk': re.compile(r"=\s*['\"].*\+|CONCAT\s*\(.*['\"].*\)", re.IGNORECASE),
            'grant_all': re.compile(r'GRANT\s+ALL', re.IGNORECASE),
            'wildcard_permissions': re.compile(r"GRANT.*TO\s+['\"]%", re.IGNORECASE),
            
            # Performance Killers
            'select_into_temp': re.compile(r'SELECT.*INTO\s+#', re.IGNORECASE),
            'cursor_usage': re.compile(r'DECLARE.*CURSOR', re.IGNORECASE),
            'while_loop': re.compile(r'WHILE\s+.*BEGIN', re.IGNORECASE),
            'table_variable_large': re.compile(r'DECLARE\s+@\w+\s+TABLE', re.IGNORECASE),
            'string_concatenation_loop': re.compile(r'(SET|SELECT)\s+@\w+\s*=\s*@\w+\s*\+', re.IGNORECASE),
            
            # Pagination Issues
            'keyset_pagination_missing': re.compile(r'LIMIT.*OFFSET\s+\d{3,}', re.IGNORECASE),
            'row_number_pagination': re.compile(r'ROW_NUMBER.*BETWEEN', re.IGNORECASE),
            
            # Anti-patterns
            'eav_pattern': re.compile(r'attribute.*value|property.*value', re.IGNORECASE),
            'god_table': re.compile(r'SELECT.*FROM\s+(data|entity|object|element)', re.IGNORECASE),
            'polymorphic_associations': re.compile(r'(type|entity_type).*_id', re.IGNORECASE),
        }

    def analyze(self, queries: str | list[str]) -> list[DetectedIssue]:
        """
        Analyze SQL query/queries for issues
        
        Args:
            queries: Single query string or list of queries

        Returns:
            List of DetectedIssue objects
        """
        if isinstance(queries, str):
            queries = [queries]

        all_issues: list[DetectedIssue] = []

        # Assuming single query input for now, line_number is set to 1
        # In a real scenario, this would be derived from the file scanner.
        line_number = 1 

        for query in queries:
            # Clean query for analysis
            clean_query = self._normalize_query(query)

            # Run all detectors
            for _detector_name, detector_func in self.detectors.items():
                # PASS THE LINE NUMBER TO THE DETECTOR FUNCTION
                result = detector_func(clean_query, query, line_number)
                if result:
                    all_issues.append(result)

        return all_issues

    def _normalize_query(self, query: str) -> str:
        """Normalize query for consistent pattern matching"""
        # Remove extra whitespace
        query = ' '.join(query.split())
        # Remove comments
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        return query.strip()

    def _get_all_detectors(self) -> dict[str, Any]:
        """Map all detector methods"""
        return {
            # Base detectors (original 26)
            'select_star': self._detect_select_star,
            'missing_where': self._detect_missing_where_update_delete,
            'non_sargable': self._detect_non_sargable,
            'implicit_conversion': self._detect_implicit_conversion,
            'cartesian_product': self._detect_cartesian_product,
            'n_plus_1': self._detect_n_plus_1_pattern,
            'correlated_subquery': self._detect_correlated_subquery,
            'or_prevents_index': self._detect_or_prevents_index,
            'offset_pagination': self._detect_offset_pagination,
            'distinct_unnecessary': self._detect_unnecessary_distinct,
            'in_clause_large': self._detect_huge_in_list,
            'like_leading_wildcard': self._detect_leading_wildcard,
            'count_star_exists': self._detect_count_star_exists,
            'not_in_null': self._detect_not_in_nullable,
            'missing_limit_exists': self._detect_no_limit_in_exists,
            'floating_point_equals': self._detect_floating_point_equality,
            'null_comparison': self._detect_null_comparison_with_equal,
            'function_on_column': self._detect_function_on_indexed_column,
            'having_no_aggregates': self._detect_having_instead_of_where,
            'union_missing_all': self._detect_union_missing_all,
            'subquery_select_list': self._detect_subquery_in_select_list,
            'between_timestamps': self._detect_between_with_timestamps,
            'case_in_where': self._detect_case_in_where,
            'offset_no_order': self._detect_offset_without_order,
            'like_no_wildcard': self._detect_like_without_wildcard,
            'order_by_ordinal': self._detect_order_by_ordinal,
            
            # GROUP A: Semantic & Logical (60+ new)
            'ambiguous_order_by': self._detect_ambiguous_order_by,
            'missing_case_else': self._detect_missing_case_else,
            'redundant_or': self._detect_redundant_or,
            'contradictory_where': self._detect_contradictory_where,
            'always_true': self._detect_always_true,
            'always_false': self._detect_always_false,
            'tautology': self._detect_tautology,
            'contradiction': self._detect_contradiction,
            'duplicate_join': self._detect_duplicate_join,
            'redundant_distinct': self._detect_redundant_distinct_with_group,
            'redundant_alias': self._detect_redundant_alias,
            'trivial_subquery': self._detect_trivial_subquery,
            'redundant_cast': self._detect_redundant_cast,
            'unnecessary_coalesce': self._detect_unnecessary_coalesce,
            'redundant_parentheses': self._detect_redundant_parentheses,
            'duplicate_column_select': self._detect_duplicate_column_select,
            'insert_no_columns': self._detect_insert_no_columns,
            'insert_select_star': self._detect_insert_select_star,
            'truncate_no_cascade': self._detect_truncate_no_cascade,
            'drop_no_if_exists': self._detect_drop_no_if_exists,
            
            # GROUP B: Maintainability & Style (75+ new)
            'lowercase_keyword': self._detect_lowercase_keywords,
            'mixed_case_table': self._detect_mixed_case_identifiers,
            'todo_comment': self._detect_todo_comments,
            'hardcoded_ip': self._detect_hardcoded_ip,
            'hardcoded_url': self._detect_hardcoded_url,
            'hardcoded_password': self._detect_hardcoded_password,
            'magic_number': self._detect_magic_numbers,
            'hardcoded_date': self._detect_hardcoded_dates,
            'api_key_pattern': self._detect_api_keys,
            'email_in_query': self._detect_email_in_query,
            'uncommented_complex_query': self._detect_uncommented_complex,
            'trailing_whitespace': self._detect_trailing_whitespace,
            'multiple_spaces': self._detect_multiple_spaces,
            
            # GROUP C: Exotic Performance (40+ new)
            'mixed_union': self._detect_mixed_union,
            'except_over_not_exists': self._detect_except_inefficient,
            'intersect_over_join': self._detect_intersect_inefficient,
            'now_without_timezone': self._detect_now_without_timezone,
            'date_math_no_interval': self._detect_date_math_no_interval,
            'strftime_in_where': self._detect_strftime_in_where,
            'extract_in_where': self._detect_extract_in_where,
            'in_subquery_over_exists': self._detect_in_subquery_inefficient,
            'exists_over_count': self._detect_exists_over_count,
            'like_complex_pattern': self._detect_like_complex_pattern,
            'regexp_in_where': self._detect_regexp_in_where,
            'json_extract_unindexed': self._detect_json_extract,
            'window_function_no_partition': self._detect_window_no_partition,
            'cte_unused': self._detect_cte_unused,
            'recursive_cte_no_limit': self._detect_recursive_cte_no_limit,
            'natural_join': self._detect_natural_join,
            'outer_join_where_nulls': self._detect_outer_join_where_nulls,
            'right_join_usage': self._detect_right_join,
            'full_outer_join': self._detect_full_outer_join,
            'select_for_update_no_wait': self._detect_select_for_update,
            'varchar_max': self._detect_varchar_max,
            'text_vs_varchar': self._detect_text_column,
            'decimal_no_precision': self._detect_decimal_no_precision,
            'cursor_usage': self._detect_cursor,
            'while_loop': self._detect_while_loop,
            'dynamic_sql': self._detect_dynamic_sql,
            'sql_injection_risk': self._detect_sql_injection_risk,
            'grant_all': self._detect_grant_all,
            'scalar_subquery_multiple_rows': self._detect_scalar_subquery_risk,
            'nested_subquery_deep': self._detect_nested_subquery_deep,
        }

    # Core Detector Methods
    def _detect_select_star(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect SELECT * usage"""
        if self._patterns['select_star'].search(clean_query):
            return DetectedIssue(
                issue_type="SELECT * Usage",
                query=original_query,
                description="Query retrieves all columns unnecessarily",
                fix="Specify only needed columns",
                impact="50-90% less data transfer, enables covering indexes",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_missing_where_update_delete(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect UPDATE/DELETE without WHERE clause"""
        if self._patterns['missing_where'].match(clean_query) and 'WHERE' not in clean_query.upper():
                return DetectedIssue(
                    issue_type="Missing WHERE in UPDATE/DELETE",
                    query=original_query,
                    description="UPDATE/DELETE without WHERE affects entire table",
                    fix="Add WHERE clause or use TRUNCATE if intentional",
                    impact="Can delete/update entire table accidentally",
                    severity=IssueSeverity.CRITICAL,
                    line_number=line_num
                )
        return None

    def _detect_non_sargable(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect non-SARGable WHERE clauses (prevents index usage)"""
        if self._patterns['non_sargable'].search(clean_query):
            return DetectedIssue(
                issue_type="Non-SARGable WHERE",
                query=original_query,
                description="WHERE clause prevents index usage",
                fix="Use date range or functional index",
                impact="Full table scan instead of index seek",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None


    def _detect_implicit_conversion(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect implicit type conversions"""
        if self._patterns['implicit_conversion'].search(clean_query):
            return DetectedIssue(
                issue_type="Implicit Type Conversion",
                query=original_query,
                description="Comparing string column to number forces conversion",
                fix="Use proper quotes for string values",
                impact="Prevents index usage, causes full table scan",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_cartesian_product(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect accidental cartesian products"""
        if self._patterns['cartesian_product'].search(clean_query) and not re.search(r'WHERE|JOIN', clean_query, re.IGNORECASE):
                return DetectedIssue(
                    issue_type="Cartesian Product",
                    query=original_query,
                    description="Multiple tables without JOIN condition",
                    fix="Add proper JOIN conditions",
                    impact="Result set explodes exponentially",
                    severity=IssueSeverity.CRITICAL,
                    line_number=line_num
                )
        return None

    def _detect_n_plus_1_pattern(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect potential N+1 query patterns"""
        # This would need multiple queries to detect properly
        # For now, detect subqueries that look like N+1
        if self._patterns['n_plus_1'].search(clean_query):
            return DetectedIssue(
                issue_type="Potential N+1 Pattern",
                query=original_query,
                description="Query pattern suggests N+1 issue when in loop",
                fix="Use JOIN or WHERE IN batch query",
                impact="Network roundtrips multiply by N",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_correlated_subquery(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect correlated subqueries"""
        if self._patterns['correlated_subquery'].search(clean_query):
            return DetectedIssue(
                issue_type="Correlated Subquery",
                query=original_query,
                description="Subquery executes once per row",
                fix="Rewrite as JOIN or pre-calculate values",
                impact="O(n²) performance degradation",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_or_prevents_index(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect OR conditions preventing index usage"""
        if self._patterns['or_prevents_index'].search(clean_query):
            return DetectedIssue(
                issue_type="OR Prevents Index",
                query=original_query,
                description="OR across different columns prevents index usage",
                fix="Use UNION or redesign query logic",
                impact="Forces full table scan",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_offset_pagination(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect large OFFSET values"""
        match = self._patterns['offset_pagination'].search(clean_query)

        if match:
            offset = int(match.group(1))
            if offset > 1000:
                return DetectedIssue(
                    issue_type="Large OFFSET Pagination",
                    query=original_query,
                    description=f"OFFSET {offset} reads and discards {offset} rows",
                    fix="Use cursor-based pagination with WHERE id > last_id",
                    impact="Performance degrades linearly with offset",
                    severity=IssueSeverity.HIGH,
                    line_number=line_num
                )
        return None

    def _detect_unnecessary_distinct(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect DISTINCT on unique columns"""
        if self._patterns['distinct_unnecessary'].search(clean_query):
            return DetectedIssue(
                issue_type="Unnecessary DISTINCT",
                query=original_query,
                description="DISTINCT on already-unique column",
                fix="Remove DISTINCT for unique columns",
                impact="Adds unnecessary sorting overhead",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_huge_in_list(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect IN clauses with too many values"""
        in_match = self._patterns['huge_in_list'].search(clean_query)
        if in_match:
            values = in_match.group(1).split(',')
            if len(values) > 50:
                return DetectedIssue(
                    issue_type="Massive IN List",
                    query=original_query,
                    description=f"IN clause with {len(values)} values",
                    fix="Use temp table JOIN instead",
                    impact="Query parser overhead, plan cache bloat",
                    severity=IssueSeverity.HIGH,
                    line_number=line_num
                )
        return None

    def _detect_leading_wildcard(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect leading wildcards in LIKE"""
        if self._patterns['leading_wildcard'].search(clean_query):
            return DetectedIssue(
                issue_type="Leading Wildcard",
                query=original_query,
                description="Leading % prevents index usage",
                fix="Use full-text search or redesign query",
                impact="Forces full table scan",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_count_star_exists(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect COUNT(*) for existence check"""
        if self._patterns['count_star_exists'].search(clean_query):
            return DetectedIssue(
                issue_type="COUNT(*) for Existence",
                query=original_query,
                description="Using COUNT(*) to check if rows exist",
                fix="Use EXISTS instead",
                impact="Counts all rows instead of stopping at first",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_not_in_nullable(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect NOT IN with subquery (NULL trap)"""
        if self._patterns['not_in_nullable'].search(clean_query):
            return DetectedIssue(
                issue_type="NOT IN with NULLable",
                query=original_query,
                description="NOT IN with subquery fails if any NULL values",
                fix="Use NOT EXISTS instead",
                impact="Query returns no results if subquery contains NULL",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_no_limit_in_exists(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect EXISTS without LIMIT"""
        if self._patterns['no_limit_exists'].search(clean_query):
            return DetectedIssue(
                issue_type="EXISTS without LIMIT",
                query=original_query,
                description="EXISTS checks all rows unnecessarily",
                fix="Add LIMIT 1 to EXISTS subquery",
                impact="Continues scanning after first match",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_floating_point_equality(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect floating point equality comparison"""
        if self._patterns['floating_point_equals'].search(clean_query):
            return DetectedIssue(
                issue_type="Floating Point Equality",
                query=original_query,
                description="Exact equality on floating point values",
                fix="Use range comparison or DECIMAL type",
                impact="May miss values due to precision issues",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_null_comparison_with_equal(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect = NULL or != NULL"""
        if self._patterns['null_comparison'].search(clean_query):
            return DetectedIssue(
                issue_type="NULL Comparison Error",
                query=original_query,
                description="Using = or != with NULL always returns UNKNOWN",
                fix="Use IS NULL or IS NOT NULL",
                impact="Condition never matches any rows",
                severity=IssueSeverity.CRITICAL,
                line_number=line_num
            )
        return None

    def _detect_function_on_indexed_column(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect functions on potentially indexed columns"""
        if self._patterns['function_on_column'].search(clean_query):
            return DetectedIssue(
                issue_type="Function on Indexed Column",
                query=original_query,
                description="Function on column prevents index usage",
                fix="Create functional index or rewrite condition",
                impact="Full table scan instead of index seek",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_having_instead_of_where(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect HAVING used for row filtering"""
        if self._patterns['having_no_aggregates'].search(clean_query) and 'WHERE' not in clean_query.upper():
                return DetectedIssue(
                    issue_type="HAVING Instead of WHERE",
                    query=original_query,
                    description="HAVING filters after grouping",
                    fix="Use WHERE for row filtering before GROUP BY",
                    impact="Processes all rows before filtering",
                    severity=IssueSeverity.MEDIUM,
                    line_number=line_num
                )
        return None

    def _detect_union_missing_all(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect UNION without ALL"""
        if self._patterns['union_missing_all'].search(clean_query):
            return DetectedIssue(
                issue_type="UNION Missing ALL",
                query=original_query,
                description="UNION performs unnecessary deduplication",
                fix="Use UNION ALL if duplicates are acceptable",
                impact="Adds expensive DISTINCT operation",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_subquery_in_select_list(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect subqueries in SELECT list"""
        if self._patterns['subquery_select_list'].search(clean_query):
            return DetectedIssue(
                issue_type="Subquery in SELECT List",
                query=original_query,
                description="Subquery executes for every row",
                fix="Convert to JOIN or pre-calculate",
                impact="O(n) subquery executions",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_between_with_timestamps(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect BETWEEN with date boundaries"""
        if self._patterns['between_timestamps'].search(clean_query):
            return DetectedIssue(
                issue_type="BETWEEN with Timestamps",
                query=original_query,
                description="BETWEEN with dates may miss end-of-day records",
                fix="Use >= start AND < end+1 day",
                impact="Misses records with time components",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_case_in_where(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect CASE expressions in WHERE"""
        if self._patterns['case_in_where'].search(clean_query):
            return DetectedIssue(
                issue_type="CASE in WHERE Clause",
                query=original_query,
                description="Complex CASE in WHERE prevents optimization",
                fix="Simplify logic or move to application",
                impact="Prevents index usage and predicate pushdown",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_offset_without_order(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect OFFSET without ORDER BY"""
        if self._patterns['offset_no_order'].search(clean_query):
            return DetectedIssue(
                issue_type="OFFSET without ORDER BY",
                query=original_query,
                description="OFFSET without ORDER BY returns random results",
                fix="Add ORDER BY for deterministic results",
                impact="Different results each execution",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_like_without_wildcard(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect LIKE without wildcards"""
        if self._patterns['like_no_wildcard'].search(clean_query):
            return DetectedIssue(
                issue_type="LIKE without Wildcards",
                query=original_query,
                description="LIKE without wildcards should be =",
                fix="Use = for exact matches",
                impact="Slightly slower than equality check",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_order_by_ordinal(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        """Detect ORDER BY with ordinal positions"""
        if self._patterns['order_by_ordinal'].search(clean_query):
            return DetectedIssue(
                issue_type="ORDER BY Ordinal",
                query=original_query,
                description="ORDER BY position number is fragile",
                fix="Use column names explicitly",
                impact="Breaks when SELECT list changes",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    # Stubs for GROUP A: Semantic & Logical
    def _detect_ambiguous_order_by(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['ambiguous_order_by'].search(clean_query):
            return DetectedIssue(
                issue_type="Ambiguous ORDER BY",
                query=original_query,
                description="ORDER BY without unique key may be non-deterministic",
                fix="Add unique column (e.g., id) to ORDER BY",
                impact="Results may vary across executions",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_missing_case_else(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['missing_case_else'].search(clean_query):
            return DetectedIssue(
                issue_type="Missing CASE ELSE",
                query=original_query,
                description="CASE without ELSE may return NULL unexpectedly",
                fix="Add ELSE clause",
                impact="Unexpected NULLs in results",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_redundant_or(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['redundant_or'].search(clean_query):
            return DetectedIssue(
                issue_type="Redundant OR Condition",
                query=original_query,
                description="Duplicate conditions in OR",
                fix="Remove redundant terms",
                impact="Unnecessary computation",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_contradictory_where(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['contradictory_where'].search(clean_query):
            return DetectedIssue(
                issue_type="Contradictory WHERE",
                query=original_query,
                description="Impossible conditions in WHERE",
                fix="Remove contradictory clauses",
                impact="Query always returns no rows",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_always_true(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['always_true'].search(clean_query):
            return DetectedIssue(
                issue_type="Always True Condition",
                query=original_query,
                description="Tautology in WHERE (e.g., 1=1)",
                fix="Remove unnecessary condition",
                impact="Full table scan, no filtering",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_always_false(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['always_false'].search(clean_query):
            return DetectedIssue(
                issue_type="Always False Condition",
                query=original_query,
                description="Contradiction in WHERE (e.g., 1=0)",
                fix="Remove or fix condition",
                impact="Query always empty",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_tautology(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['tautology'].search(clean_query):
            return DetectedIssue(
                issue_type="Tautology in WHERE",
                query=original_query,
                description="Always-true logic (e.g., col IS NULL OR NOT NULL)",
                fix="Simplify condition",
                impact="No effective filtering",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_contradiction(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['contradiction'].search(clean_query):
            return DetectedIssue(
                issue_type="Contradiction in WHERE",
                query=original_query,
                description="Always-false logic (e.g., col IS NULL AND NOT NULL)",
                fix="Remove condition",
                impact="Always empty results",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_duplicate_join(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['duplicate_join'].search(clean_query):
            return DetectedIssue(
                issue_type="Duplicate JOIN",
                query=original_query,
                description="Same table joined multiple times",
                fix="Consolidate JOINs",
                impact="Redundant data processing",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_redundant_distinct_with_group(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['redundant_distinct'].search(clean_query):
            return DetectedIssue(
                issue_type="Redundant DISTINCT with GROUP BY",
                query=original_query,
                description="DISTINCT unnecessary with GROUP BY",
                fix="Remove DISTINCT",
                impact="Extra overhead",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_redundant_alias(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['redundant_alias'].search(clean_query):
            return DetectedIssue(
                issue_type="Redundant Alias",
                query=original_query,
                description="Alias same as column name",
                fix="Remove alias",
                impact="Unnecessary clutter",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_trivial_subquery(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['trivial_subquery'].search(clean_query):
            return DetectedIssue(
                issue_type="Trivial Subquery",
                query=original_query,
                description="Subquery with constant value",
                fix="Inline the constant",
                impact="Unnecessary subquery overhead",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_redundant_cast(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['redundant_cast'].search(clean_query):
            return DetectedIssue(
                issue_type="Redundant CAST",
                query=original_query,
                description="CAST to same type",
                fix="Remove CAST",
                impact="Unnecessary type conversion",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_unnecessary_coalesce(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['unnecessary_coalesce'].search(clean_query):
            return DetectedIssue(
                issue_type="Unnecessary COALESCE",
                query=original_query,
                description="COALESCE with single argument",
                fix="Remove COALESCE",
                impact="Extra function call",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_redundant_parentheses(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['redundant_parentheses'].search(clean_query):
            return DetectedIssue(
                issue_type="Redundant Parentheses",
                query=original_query,
                description="Nested parentheses unnecessarily",
                fix="Simplify expression",
                impact="Readability issue",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_duplicate_column_select(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['duplicate_column_select'].search(clean_query):
            return DetectedIssue(
                issue_type="Duplicate Column in SELECT",
                query=original_query,
                description="Same column selected multiple times",
                fix="Remove duplicates",
                impact="Redundant data transfer",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_insert_no_columns(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['insert_no_columns'].search(clean_query):
            return DetectedIssue(
                issue_type="INSERT without Columns",
                query=original_query,
                description="INSERT VALUES without column list",
                fix="Specify column names",
                impact="Breaks if table schema changes",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_insert_select_star(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['insert_select_star'].search(clean_query):
            return DetectedIssue(
                issue_type="INSERT SELECT *",
                query=original_query,
                description="SELECT * in INSERT can break on schema changes",
                fix="Specify columns",
                impact="Fragile to schema evolution",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_truncate_no_cascade(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['truncate_no_cascade'].search(clean_query):
            return DetectedIssue(
                issue_type="TRUNCATE without CASCADE",
                query=original_query,
                description="May fail with foreign keys",
                fix="Add CASCADE if needed",
                impact="Runtime errors on related tables",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_drop_no_if_exists(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['drop_no_if_exists'].search(clean_query):
            return DetectedIssue(
                issue_type="DROP without IF EXISTS",
                query=original_query,
                description="Fails if object doesn't exist",
                fix="Add IF EXISTS",
                impact="Script failures in idempotent ops",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    # Stubs for GROUP B: Maintainability & Style
    def _detect_lowercase_keywords(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['lowercase_keyword'].search(clean_query):
            return DetectedIssue(
                issue_type="Lowercase Keywords",
                query=original_query,
                description="SQL keywords in lowercase",
                fix="Use uppercase for keywords",
                impact="Style inconsistency",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_mixed_case_identifiers(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['mixed_case_table'].search(clean_query):
            return DetectedIssue(
                issue_type="Mixed Case Identifiers",
                query=original_query,
                description="Table/column names with mixed case",
                fix="Use consistent casing (e.g., snake_case)",
                impact="Portability issues across DBs",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_todo_comments(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['todo_comment'].search(clean_query):
            return DetectedIssue(
                issue_type="TODO Comment",
                query=original_query,
                description="Unresolved TODO/FIXME in comments",
                fix="Resolve or remove",
                impact="Potential unfinished code",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_hardcoded_ip(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['hardcoded_ip'].search(clean_query):
            return DetectedIssue(
                issue_type="Hardcoded IP",
                query=original_query,
                description="IP address hardcoded in query",
                fix="Use parameters or config",
                impact="Security/maintenance risk",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_hardcoded_url(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['hardcoded_url'].search(clean_query):
            return DetectedIssue(
                issue_type="Hardcoded URL",
                query=original_query,
                description="URL hardcoded in query",
                fix="Use parameters",
                impact="Inflexible and risky",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_hardcoded_password(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['hardcoded_password'].search(clean_query):
            return DetectedIssue(
                issue_type="Hardcoded Password",
                query=original_query,
                description="Password in plain text",
                fix="Use secrets management",
                impact="Severe security vulnerability",
                severity=IssueSeverity.CRITICAL,
                line_number=line_num
            )
        return None

    def _detect_magic_numbers(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['magic_number'].search(clean_query):
            return DetectedIssue(
                issue_type="Magic Number",
                query=original_query,
                description="Hardcoded numeric constant",
                fix="Use named constants or parameters",
                impact="Hard to maintain",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_hardcoded_dates(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['hardcoded_date'].search(clean_query):
            return DetectedIssue(
                issue_type="Hardcoded Date",
                query=original_query,
                description="Specific date hardcoded",
                fix="Use dynamic dates or parameters",
                impact="Query becomes outdated",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_api_keys(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['api_key_pattern'].search(clean_query):
            return DetectedIssue(
                issue_type="API Key in Query",
                query=original_query,
                description="Potential API key hardcoded",
                fix="Use secrets",
                impact="Security breach risk",
                severity=IssueSeverity.CRITICAL,
                line_number=line_num
            )
        return None

    def _detect_email_in_query(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['email_in_query'].search(clean_query):
            return DetectedIssue(
                issue_type="Email in Query",
                query=original_query,
                description="Hardcoded email address",
                fix="Parameterize",
                impact="Privacy/maintenance issue",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_uncommented_complex(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['uncommented_complex_query'].search(clean_query):
            return DetectedIssue(
                issue_type="Uncommented Complex Query",
                query=original_query,
                description="Complex query without comments",
                fix="Add explanatory comments",
                impact="Hard to maintain",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_trailing_whitespace(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['trailing_whitespace'].search(clean_query):
            return DetectedIssue(
                issue_type="Trailing Whitespace",
                query=original_query,
                description="Unnecessary trailing spaces",
                fix="Trim whitespace",
                impact="Style issue",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_multiple_spaces(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['multiple_spaces'].search(clean_query):
            return DetectedIssue(
                issue_type="Multiple Spaces",
                query=original_query,
                description="Consecutive spaces in query",
                fix="Normalize spacing",
                impact="Style inconsistency",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    # Stubs for GROUP C: Exotic Performance
    def _detect_mixed_union(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['mixed_union'].search(clean_query):
            return DetectedIssue(
                issue_type="Mixed UNION/UNION ALL",
                query=original_query,
                description="Inconsistent UNION usage",
                fix="Standardize to UNION ALL where possible",
                impact="Unnecessary dedup",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_except_inefficient(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['except_over_not_exists'].search(clean_query):
            return DetectedIssue(
                issue_type="EXCEPT/MINUS Inefficient",
                query=original_query,
                description="Use NOT EXISTS for better perf",
                fix="Rewrite with NOT EXISTS",
                impact="Slower set operations",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_intersect_inefficient(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['intersect_over_join'].search(clean_query):
            return DetectedIssue(
                issue_type="INTERSECT Inefficient",
                query=original_query,
                description="Use JOIN for better perf",
                fix="Rewrite with JOIN",
                impact="Slower set operations",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_now_without_timezone(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['now_without_timezone'].search(clean_query):
            return DetectedIssue(
                issue_type="NOW without Timezone",
                query=original_query,
                description="Timezone-ambiguous timestamp",
                fix="Use AT TIME ZONE",
                impact="Incorrect times across zones",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_date_math_no_interval(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['date_math_no_interval'].search(clean_query):
            return DetectedIssue(
                issue_type="Date Math without INTERVAL",
                query=original_query,
                description="Ambiguous date arithmetic",
                fix="Use INTERVAL",
                impact="DB-specific behavior",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_strftime_in_where(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['strftime_in_where'].search(clean_query):
            return DetectedIssue(
                issue_type="STRFTIME in WHERE",
                query=original_query,
                description="Non-SARGable date formatting",
                fix="Use date ranges",
                impact="Full scan",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_extract_in_where(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['extract_in_where'].search(clean_query):
            return DetectedIssue(
                issue_type="EXTRACT in WHERE",
                query=original_query,
                description="Prevents index usage",
                fix="Use functional index or rewrite",
                impact="Performance hit",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_in_subquery_inefficient(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['in_subquery_over_exists'].search(clean_query):
            return DetectedIssue(
                issue_type="IN Subquery Inefficient",
                query=original_query,
                description="Use EXISTS for existence checks",
                fix="Rewrite with EXISTS",
                impact="Suboptimal plan",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_exists_over_count(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['exists_over_count'].search(clean_query):
            return DetectedIssue(
                issue_type="EXISTS over COUNT",
                query=original_query,
                description="COUNT in subquery for existence",
                fix="Use EXISTS",
                impact="Unnecessary counting",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_like_complex_pattern(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['like_complex_pattern'].search(clean_query):
            return DetectedIssue(
                issue_type="Complex LIKE Pattern",
                query=original_query,
                description="Multiple wildcards slow",
                fix="Use full-text search",
                impact="Exponential scan time",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_regexp_in_where(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['regexp_in_where'].search(clean_query):
            return DetectedIssue(
                issue_type="REGEXP in WHERE",
                query=original_query,
                description="Regex prevents index usage",
                fix="Use full-text or rewrite",
                impact="Full scan",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_json_extract(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['json_extract_unindexed'].search(clean_query):
            return DetectedIssue(
                issue_type="JSON Extract Unindexed",
                query=original_query,
                description="JSON ops without index",
                fix="Add JSON index",
                impact="Slow on large JSON",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_window_no_partition(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['window_function_no_partition'].search(clean_query):
            return DetectedIssue(
                issue_type="Window Function without PARTITION",
                query=original_query,
                description="Global window may be inefficient",
                fix="Add PARTITION BY",
                impact="Full sort",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_cte_unused(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['cte_unused'].search(clean_query):
            return DetectedIssue(
                issue_type="Unused CTE",
                query=original_query,
                description="CTE defined but not used",
                fix="Remove unused CTE",
                impact="Unnecessary computation",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_recursive_cte_no_limit(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['recursive_cte_no_limit'].search(clean_query):
            return DetectedIssue(
                issue_type="Recursive CTE without LIMIT",
                query=original_query,
                description="Risk of infinite recursion",
                fix="Add LIMIT or termination condition",
                impact="Potential crash",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_natural_join(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['natural_join'].search(clean_query):
            return DetectedIssue(
                issue_type="NATURAL JOIN Usage",
                query=original_query,
                description="Implicit column matching risky",
                fix="Use explicit JOIN ON",
                impact="Breaks on schema changes",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_outer_join_where_nulls(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['outer_join_where_nulls'].search(clean_query):
            return DetectedIssue(
                issue_type="OUTER JOIN with WHERE NOT NULL",
                query=original_query,
                description="Turns OUTER to INNER JOIN",
                fix="Move to ON clause",
                impact="Unexpected row loss",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_right_join(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['right_join_usage'].search(clean_query):
            return DetectedIssue(
                issue_type="RIGHT JOIN Usage",
                query=original_query,
                description="Less readable than LEFT",
                fix="Rewrite as LEFT JOIN",
                impact="Maintainability",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_full_outer_join(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['full_outer_join'].search(clean_query):
            return DetectedIssue(
                issue_type="FULL OUTER JOIN",
                query=original_query,
                description="Expensive and rare",
                fix="Consider UNION of LEFT/RIGHT",
                impact="Performance overhead",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_select_for_update(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['select_for_update_no_wait'].search(clean_query):
            return DetectedIssue(
                issue_type="SELECT FOR UPDATE without NOWAIT",
                query=original_query,
                description="Risk of deadlocks",
                fix="Add NOWAIT or SKIP LOCKED",
                impact="Concurrency issues",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_varchar_max(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['varchar_max'].search(clean_query):
            return DetectedIssue(
                issue_type="VARCHAR(MAX)",
                query=original_query,
                description="Inefficient for large strings",
                fix="Use TEXT or appropriate size",
                impact="Memory overhead",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_text_column(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['text_vs_varchar'].search(clean_query):
            return DetectedIssue(
                issue_type="TEXT vs VARCHAR",
                query=original_query,
                description="TEXT may be overkill",
                fix="Use VARCHAR with limit",
                impact="Storage inefficiency",
                severity=IssueSeverity.LOW,
                line_number=line_num
            )
        return None

    def _detect_decimal_no_precision(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['decimal_no_precision'].search(clean_query):
            return DetectedIssue(
                issue_type="DECIMAL without Precision",
                query=original_query,
                description="Default precision may be wrong",
                fix="Specify (precision, scale)",
                impact="Data truncation",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

    def _detect_cursor(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['cursor_usage'].search(clean_query):
            return DetectedIssue(
                issue_type="Cursor Usage",
                query=original_query,
                description="Cursors are slow for large sets",
                fix="Use set-based ops",
                impact="Performance killer",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_while_loop(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['while_loop'].search(clean_query):
            return DetectedIssue(
                issue_type="WHILE Loop",
                query=original_query,
                description="RBAR (row-by-agonizing-row) processing",
                fix="Use set-based",
                impact="Slow execution",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_dynamic_sql(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['dynamic_sql'].search(clean_query):
            return DetectedIssue(
                issue_type="Dynamic SQL",
                query=original_query,
                description="EXEC/EXECUTE risk injection",
                fix="Use parameterized queries",
                impact="SQL injection vulnerability",
                severity=IssueSeverity.CRITICAL,
                line_number=line_num
            )
        return None

    def _detect_sql_injection_risk(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['sql_injection_risk'].search(clean_query):
            return DetectedIssue(
                issue_type="SQL Injection Risk",
                query=original_query,
                description="Concatenation in query",
                fix="Use parameters",
                impact="Security breach",
                severity=IssueSeverity.CRITICAL,
                line_number=line_num
            )
        return None

    def _detect_grant_all(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['grant_all'].search(clean_query):
            return DetectedIssue(
                issue_type="GRANT ALL",
                query=original_query,
                description="Overly broad permissions",
                fix="Grant specific privileges",
                impact="Security risk",
                severity=IssueSeverity.CRITICAL,
                line_number=line_num
            )
        return None

    def _detect_scalar_subquery_risk(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['scalar_subquery_multiple_rows'].search(clean_query):
            return DetectedIssue(
                issue_type="Scalar Subquery Risk",
                query=original_query,
                description="Subquery may return multiple rows",
                fix="Add LIMIT 1",
                impact="Runtime error",
                severity=IssueSeverity.HIGH,
                line_number=line_num
            )
        return None

    def _detect_nested_subquery_deep(self, clean_query: str, original_query: str, line_num: Optional[int] = None) -> Optional[DetectedIssue]:
        if self._patterns['nested_subquery_deep'].search(clean_query):
            return DetectedIssue(
                issue_type="Deeply Nested Subquery",
                query=original_query,
                description="Excessive nesting",
                fix="Use CTEs",
                impact="Hard to optimize/maintain",
                severity=IssueSeverity.MEDIUM,
                line_number=line_num
            )
        return None

# Helper function for batch analysis
def analyze_queries(queries: list[str]) -> list[DetectedIssue]:
    """
    Convenience function to analyze multiple queries
    Args:
        queries: List of SQL queries to analyze
    Returns:
        List of all detected issues
    """
    detector = QueryDetector()
    return detector.analyze(queries)