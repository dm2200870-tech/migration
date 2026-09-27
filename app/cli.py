from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.scanner import ProjectScanner


STATUS_ICON = {
    "PASS": "✓",
    "WARNING": "!",
    "BLOCK": "✗",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="migrationguard",
        description="Check PostgreSQL migrations for deployment safety.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser(
        "scan",
        help="Scan a project and return PASS, WARNING, or BLOCK.",
    )
    scan.add_argument(
        "project",
        nargs="?",
        default=".",
        help="Project directory (default: current directory).",
    )
    scan.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Report format (default: text).",
    )
    scan.add_argument(
        "--output",
        help="Write the report to this file as JSON. Useful in CI.",
    )
    return parser


def print_report(report: dict) -> None:
    status = report["status"]
    icon = STATUS_ICON.get(status, "?")

    print()
    print("MigrationGuard v0.3")
    print("=" * 48)
    print(f"Project:    {report['project']}")
    print(f"Database:   {report['database']}")
    print(f"Migrations: {report['migrations_scanned']}")
    print()

    print("Migration results")
    print("-" * 48)

    for migration in report["migrations"]:
        migration_icon = STATUS_ICON.get(migration["status"], "?")
        print(f"{migration_icon} {migration['status']:<7} {migration['file']}")

        for issue in migration["issues"]:
            severity = issue["severity"]
            rule = issue["rule"]
            line = issue.get("line")
            location = f":{line}" if line else ""
            print(f"    [{severity}] {rule}{location}")
            print(f"      {issue['message']}")

            refs = issue.get("references") or []
            for ref in refs:
                print(
                    f"      -> {ref['file']}:{ref['line']}  "
                    f"{ref['match']}"
                )

    db = report.get("database_test") or {}
    print()
    print("PostgreSQL test")
    print("-" * 48)
    db_status = db.get("status", "UNKNOWN")
    print(f"{STATUS_ICON.get(db_status, '?')} {db_status}")
    print(f"  {db.get('message', '')}")

    if db.get("execution_ms") is not None:
        print(f"  Execution: {db['execution_ms']} ms")

    summary = report["summary"]
    print()
    print("Summary")
    print("-" * 48)
    print(
        f"PASS: {summary['pass']}  "
        f"WARNING: {summary['warning']}  "
        f"BLOCK: {summary['block']}"
    )

    print()
    print("=" * 48)
    print(f"{icon} FINAL STATUS: {status}")
    print("=" * 48)
    print()


def exit_code_for_status(status: str) -> int:
    if status == "PASS":
        return 0
    if status == "WARNING":
        return 1
    return 2


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command != "scan":
        parser.print_help()
        return 2

    project = Path(args.project).resolve()
    if not project.exists() or not project.is_dir():
        print(f"Error: project directory not found: {project}", file=sys.stderr)
        return 2

    try:
        report = ProjectScanner(project).scan()
    except Exception as exc:
        print(f"Error: scan failed: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print_report(report)

    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    return exit_code_for_status(report["status"])


if __name__ == "__main__":
    raise SystemExit(main())
