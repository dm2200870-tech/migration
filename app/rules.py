from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class EntityRef:
    table: str
    column: str | None = None


class RuleEngine:
    """
    v0.1 intentionally uses focused PostgreSQL regex rules.

    This is not a full SQL AST analyzer yet. That is a later milestone.
    """

    def analyze(self, sql: str, filename: str) -> list[dict]:
        issues: list[dict] = []

        patterns = [
            (
                r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)",
                "DROP_TABLE",
                "CRITICAL",
                "Dropping a table can permanently remove application data.",
            ),
            (
                r"\bALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)\s+DROP\s+COLUMN\s+(?:IF\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)",
                "DROP_COLUMN",
                "HIGH",
                "Dropping a column can break application versions that still read or write it.",
            ),
            (
                r"\bALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)\s+RENAME\s+COLUMN\s+([A-Za-z_][A-Za-z0-9_]*)\s+TO\s+([A-Za-z_][A-Za-z0-9_]*)",
                "RENAME_COLUMN",
                "HIGH",
                "Renaming a column can break application code and SQL queries.",
            ),
            (
                r"\bALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)\s+ALTER\s+COLUMN\s+([A-Za-z_][A-Za-z0-9_]*)\s+TYPE\b",
                "ALTER_TYPE",
                "HIGH",
                "Changing a column type can cause data conversion failures or application incompatibility.",
            ),
            (
                r"\bALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)\s+ALTER\s+COLUMN\s+([A-Za-z_][A-Za-z0-9_]*)\s+SET\s+NOT\s+NULL",
                "ADD_NOT_NULL",
                "HIGH",
                "Adding NOT NULL can fail when existing rows contain NULL values.",
            ),
            (
                r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+([A-Za-z_][A-Za-z0-9_]*)\s+ON\s+([A-Za-z_][A-Za-z0-9_]*)",
                "CREATE_INDEX",
                "WARNING",
                "Index creation may consume CPU, I/O and locks on large tables.",
            ),
        ]

        for pattern, rule, severity, message in patterns:
            for match in re.finditer(pattern, sql, flags=re.IGNORECASE):
                issues.append({
                    "rule": rule,
                    "severity": severity,
                    "message": message,
                    "file": filename,
                    "line": sql.count("\n", 0, match.start()) + 1,
                })

        return issues

    def extract_entities(self, sql: str) -> list[EntityRef]:
        result: list[EntityRef] = []

        for match in re.finditer(
            r"\bALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)\s+DROP\s+COLUMN\s+(?:IF\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)",
            sql,
            flags=re.IGNORECASE,
        ):
            result.append(EntityRef(match.group(1), match.group(2)))

        for match in re.finditer(
            r"\bALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)\s+RENAME\s+COLUMN\s+([A-Za-z_][A-Za-z0-9_]*)\s+TO\s+([A-Za-z_][A-Za-z0-9_]*)",
            sql,
            flags=re.IGNORECASE,
        ):
            result.append(EntityRef(match.group(1), match.group(2)))

        for match in re.finditer(
            r"\bALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)\s+ALTER\s+COLUMN\s+([A-Za-z_][A-Za-z0-9_]*)",
            sql,
            flags=re.IGNORECASE,
        ):
            result.append(EntityRef(match.group(1), match.group(2)))

        return result

    def status_for(self, issues: list[dict]) -> str:
        severities = {i["severity"] for i in issues}
        if "CRITICAL" in severities or "HIGH" in severities:
            return "BLOCK"
        if "WARNING" in severities:
            return "WARNING"
        return "PASS"

    def overall_status(self, all_issues: list[dict], db_status: str | None) -> str:
        if any(i["severity"] == "CRITICAL" for i in all_issues):
            return "BLOCK"
        if any(i["severity"] == "HIGH" for i in all_issues):
            return "BLOCK"
        if db_status == "FAIL":
            return "BLOCK"
        if any(i["severity"] == "WARNING" for i in all_issues):
            return "WARNING"
        return "PASS"
