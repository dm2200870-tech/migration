from __future__ import annotations

from pathlib import Path
from typing import Any

from app.code_scanner import CodeReferenceScanner
from app.db_runner import MigrationRunner
from app.rules import RuleEngine


MIGRATION_DIR_NAMES = (
    "database/migrations",
    "migrations",
    "db/migrations",
)


class ProjectScanner:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.rule_engine = RuleEngine()
        self.code_scanner = CodeReferenceScanner(project_root)

    def locate_migrations(self) -> Path:
        for relative in MIGRATION_DIR_NAMES:
            candidate = self.project_root / relative
            if candidate.is_dir():
                return candidate
        raise FileNotFoundError(
            "No migration directory found. Expected one of: "
            + ", ".join(MIGRATION_DIR_NAMES)
        )

    def scan(self) -> dict[str, Any]:
        migration_dir = self.locate_migrations()
        migration_files = sorted(migration_dir.glob("*.sql"))

        migrations = []
        all_issues = []
        database_test = {
            "status": "SKIPPED",
            "message": "No SQL migrations found.",
        }

        for path in migration_files:
            sql = path.read_text(encoding="utf-8")
            sql_issues = self.rule_engine.analyze(sql, path.name)

            references = []
            for entity in self.rule_engine.extract_entities(sql):
                references.extend(
                    self.code_scanner.find_references(entity.table, entity.column)
                )

            # Deduplicate references.
            unique_refs = []
            seen = set()
            for ref in references:
                key = (ref["file"], ref["line"], ref["match"])
                if key not in seen:
                    seen.add(key)
                    unique_refs.append(ref)

            issues = list(sql_issues)

            if unique_refs:
                # Code references make destructive changes materially unsafe.
                destructive = any(i["rule"] in {
                    "DROP_COLUMN", "DROP_TABLE", "RENAME_COLUMN", "ALTER_TYPE"
                } for i in issues)

                if destructive:
                    issues.append({
                        "rule": "APPLICATION_REFERENCE",
                        "severity": "CRITICAL",
                        "message": (
                            f"Application code still references {unique_refs[0]['table']}"
                            + (f".{unique_refs[0]['column']}" if unique_refs[0]["column"] else "")
                            + f"; found {len(unique_refs)} reference(s)."
                        ),
                        "file": path.name,
                        "line": None,
                        "references": unique_refs,
                    })

            migration_record = {
                "file": path.name,
                "issues": issues,
                "status": self.rule_engine.status_for(issues),
            }
            migrations.append(migration_record)
            all_issues.extend(issues)

        if migration_files:
            runner = MigrationRunner.from_env()
            database_test = runner.run(migration_files)

        final_status = self.rule_engine.overall_status(
            all_issues, database_test.get("status")
        )

        return {
            "version": "0.1.0",
            "project": self.project_root.name,
            "database": "PostgreSQL",
            "migrations_scanned": len(migration_files),
            "status": final_status,
            "database_test": database_test,
            "migrations": migrations,
            "summary": {
                "pass": sum(m["status"] == "PASS" for m in migrations),
                "warning": sum(m["status"] == "WARNING" for m in migrations),
                "block": sum(m["status"] == "BLOCK" for m in migrations),
            },
        }
