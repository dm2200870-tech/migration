from __future__ import annotations

import re
from pathlib import Path

SKIP_DIRS = {
    ".git",
    "node_modules",
    "vendor",
    "__pycache__",
    ".next",
    "dist",
    "build",
}

# Database migration directories must not be treated as application source.
SKIP_RELATIVE_DIRS = {
    Path("database/migrations"),
    Path("migrations"),
    Path("db/migrations"),
}


class CodeReferenceScanner:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()

    def find_references(self, table: str, column: str | None) -> list[dict]:
        tokens = [column] if column else [table]
        tokens = [t for t in tokens if t]

        patterns = [
            re.compile(rf"\b{re.escape(t)}\b", re.IGNORECASE)
            for t in tokens
        ]

        references: list[dict] = []

        for path in self._iter_source_files():
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            for line_number, line in enumerate(content.splitlines(), start=1):
                if any(pattern.search(line) for pattern in patterns):
                    references.append({
                        "file": str(path.relative_to(self.project_root)),
                        "line": line_number,
                        "match": line.strip()[:300],
                        "table": table,
                        "column": column,
                    })

        return references

    def _is_skipped_directory(self, path: Path) -> bool:
        relative = path.relative_to(self.project_root)

        # Exclude hidden/dependency/build directories anywhere in the tree.
        if any(part in SKIP_DIRS for part in relative.parts):
            return True

        # Exclude migration directories specifically, even though .sql is
        # otherwise allowed for application query files.
        for skip_dir in SKIP_RELATIVE_DIRS:
            if relative == skip_dir or skip_dir in relative.parents:
                return True

        return False

    def _iter_source_files(self):
        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue

            if self._is_skipped_directory(path.parent):
                continue

            if path.suffix.lower() in {
                ".php", ".js", ".ts", ".jsx", ".tsx", ".py", ".go",
                ".java", ".rb", ".sql", ".vue"
            }:
                yield path
