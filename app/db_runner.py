from __future__ import annotations

import os
import time
from pathlib import Path
from urllib.parse import urlparse

import psycopg


class MigrationRunner:
    def __init__(self, database_url: str):
        self.database_url = database_url

    @classmethod
    def from_env(cls):
        return cls(
            os.getenv(
                "MG_DATABASE_URL",
                "postgresql://migrationguard:migrationguard@localhost:5433/migrationguard_test",
            )
        )

    def run(self, migration_files: list[Path]) -> dict:
        start = time.perf_counter()

        try:
            with psycopg.connect(self.database_url) as conn:
                conn.autocommit = True

                # Isolated test DB only. This schema is recreated on every scan.
                with conn.cursor() as cur:
                    cur.execute("DROP SCHEMA IF EXISTS public CASCADE;")
                    cur.execute("CREATE SCHEMA public;")

                    for migration_file in migration_files:
                        sql = migration_file.read_text(encoding="utf-8")
                        cur.execute(sql)

            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "status": "PASS",
                "message": "All migrations executed successfully in the isolated PostgreSQL container.",
                "execution_ms": elapsed_ms,
                "migrations_executed": len(migration_files),
            }

        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "status": "FAIL",
                "message": str(exc),
                "execution_ms": elapsed_ms,
                "migrations_executed": 0,
            }
