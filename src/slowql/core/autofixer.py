"""
Autofix engine for SlowQL.

This module provides a conservative, text-based fix application engine.
It intentionally avoids schema-aware rewrites or heuristic SQL rewriting.
Only exact, explicit replacements are supported.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff

from slowql.core.models import Fix, FixConfidence


@dataclass(frozen=True, slots=True)
class AppliedFix:
    """Record of a successfully applied fix."""

    rule_id: str
    description: str
    confidence: str
    original: str
    replacement: str


class AutoFixer:
    """
    Conservative autofix engine.

    Safety principles:
    - only exact text replacements
    - no schema inference
    - no guessed SQL generation
    - no file writes
    """

    def apply_fix(self, query: str, fix: Fix) -> str:
        """
        Apply a single fix to a query.

        The fix is only applied if:
        - fix.original is non-empty
        - fix.original exists in query

        Only the first occurrence is replaced.

        Args:
            query: Original SQL query text.
            fix: Fix to apply.

        Returns:
            Updated query text if applied, otherwise original query text.
        """
        if not fix.original:
            return query

        if fix.original not in query:
            return query

        return query.replace(fix.original, fix.replacement, 1)

    def apply_all_fixes(self, query: str, fixes: list[Fix]) -> str:
        """
        Apply multiple fixes deterministically.

        Fixes are applied in a stable order:
        - longer original text first
        - then by rule_id
        - then by description

        A fix is skipped if:
        - fix.original is empty
        - fix.original was not present in the original query
        - the target text is no longer present in the current updated query

        This prevents a previously applied fix from introducing new text
        that triggers a later fix unexpectedly.

        Args:
            query: Original SQL query text.
            fixes: List of fixes.

        Returns:
            Updated query text.
        """
        ordered = sorted(
            fixes,
            key=lambda f: (
                -len(f.original or ""),
                f.rule_id,
                f.description,
            ),
        )

        original_query = query
        updated = query

        for fix in ordered:
            if not fix.original:
                continue
            if fix.original not in original_query:
                continue
            if fix.original not in updated:
                continue
            updated = updated.replace(fix.original, fix.replacement, 1)

        return updated

    def preview_fixes(self, query: str, fixes: list[Fix]) -> str:
        """
        Generate a unified diff preview for applying fixes.

        Args:
            query: Original SQL query text.
            fixes: List of fixes.

        Returns:
            Unified diff string. Empty string if no changes.
        """
        updated = self.apply_all_fixes(query, fixes)

        if updated == query:
            return ""

        diff = unified_diff(
            query.splitlines(),
            updated.splitlines(),
            fromfile="original.sql",
            tofile="fixed.sql",
            lineterm="",
        )
        return "\n".join(diff)

    def generate_fix_report(self, applied: list[Fix]) -> dict[str, object]:
        """
        Generate a structured report of fixes.

        Args:
            applied: List of fixes considered applied.

        Returns:
            Serializable report dictionary.
        """
        return {
            "total_fixes": len(applied),
            "by_confidence": {
                "safe": sum(1 for f in applied if f.confidence == FixConfidence.SAFE),
                "probable": sum(1 for f in applied if f.confidence == FixConfidence.PROBABLE),
                "unsafe": sum(1 for f in applied if f.confidence == FixConfidence.UNSAFE),
                "legacy_numeric": sum(1 for f in applied if not isinstance(f.confidence, FixConfidence)),
            },
            "fixes": [
                {
                    "rule_id": f.rule_id,
                    "description": f.description,
                    "confidence": f.confidence.value if isinstance(f.confidence, FixConfidence) else f.confidence,
                    "original": f.original,
                    "replacement": f.replacement,
                    "is_safe": f.is_safe,
                }
                for f in applied
            ],
        }
