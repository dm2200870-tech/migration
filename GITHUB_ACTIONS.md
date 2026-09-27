# MigrationGuard v0.3 — GitHub Actions

MigrationGuard now runs automatically on pull requests.

## Flow

```text
Pull Request
     |
     v
GitHub Actions
     |
     +--> PostgreSQL 17 service container
     |
     +--> install MigrationGuard
     |
     +--> migrationguard scan
     |
     +--> JSON report
     |
     +--> PR comment
     |
     v
PASS / WARNING / BLOCK
```

## Demo repository

This starter repository stores the demo application under:

```text
sample_project/
```

Therefore the workflow uses:

```yaml
env:
  PROJECT_PATH: sample_project
```

When you copy the workflow into a real application repository where migrations are at the repository root, change it to:

```yaml
env:
  PROJECT_PATH: .
```

## What happens on a PR?

1. GitHub checks out the code.
2. PostgreSQL 17 starts as a service container.
3. MigrationGuard is installed from `pyproject.toml`.
4. `migrationguard scan` runs.
5. A JSON report is created.
6. The report is uploaded as a workflow artifact.
7. MigrationGuard adds or updates a PR comment.
8. The final workflow step fails when the scanner returns WARNING or BLOCK.

## Exit codes

```text
0 = PASS
1 = WARNING
2 = BLOCK / scan error
```

The current workflow intentionally treats both WARNING and BLOCK as a failed CI check. Make that policy configurable later as part of project settings.

## No production DB connection

v0.3 uses an isolated GitHub-hosted PostgreSQL service container. Do not add production database credentials to this workflow.
