# MigrationGuard v0.2 CLI

## Install locally

From the MigrationGuard repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

Then:

```bash
migrationguard --help
```

## Run the scan

The PostgreSQL test database must be running:

```bash
docker-compose up -d postgres
```

Then from the repository root:

```bash
migrationguard scan sample_project
```

Expected exit status for the included sample project:

```text
2
```

because the sample migration is intentionally BLOCKED.

## Exit codes

```text
0 = PASS
1 = WARNING
2 = BLOCK / scan error
```

This is intentional because GitHub Actions and other CI systems can use the exit code to decide whether a check passes.

## Example

```text
MigrationGuard v0.2
================================================
Project:   sample_project
Database:  PostgreSQL
Migrations: 3

Migration results
------------------------------------------------
✓ PASS    001_create_users.sql
✓ PASS    002_create_orders.sql
✗ BLOCK   003_drop_phone.sql
    [HIGH] DROP_COLUMN:1
    [CRITICAL] APPLICATION_REFERENCE
      -> app/UserController.php:9
      -> app/UserService.php:9
      -> api/user.js:5

PostgreSQL test
------------------------------------------------
✓ PASS
  All migrations executed successfully...

Summary
------------------------------------------------
PASS: 2  WARNING: 0  BLOCK: 1

================================================
✗ FINAL STATUS: BLOCK
================================================
```

## Why this matters

This same command can later run inside:

```text
GitHub Pull Request
      ↓
GitHub Actions runner
      ↓
migrationguard scan .
      ↓
exit code
      ↓
GitHub Check
```
