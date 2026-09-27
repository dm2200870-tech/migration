# MigrationGuard v0.3.0

MigrationGuard is a PostgreSQL migration safety checker designed to catch risky database changes before production deployment.

## Current capabilities

- PostgreSQL migration discovery
- Focused SQL safety rules
- Application code reference scanning
- Isolated PostgreSQL migration execution
- PASS / WARNING / BLOCK result
- Developer CLI
- JSON report for CI
- GitHub Actions pull-request integration
- Automatic PR comment
- CI enforcement through exit codes

## Architecture

```text
Application Repository
       |
       v
MigrationGuard CLI
       |
       +--> SQL Rules Engine
       |
       +--> Application Code Scanner
       |
       +--> Isolated PostgreSQL
       |
       v
PASS / WARNING / BLOCK
```

## Local Docker run

```bash
docker-compose up --build -d
```

Health:

```bash
curl http://localhost:8000/health
```

API scan:

```bash
curl -X POST http://localhost:8000/scan \
  -H 'Content-Type: application/json' \
  -d '{"project_path":"/workspace/project"}'
```

## CLI

Inside the API container:

```bash
docker-compose exec api migrationguard scan /workspace/project
```

JSON report:

```bash
docker-compose exec api migrationguard scan /workspace/project \
  --format json \
  --output /tmp/migrationguard-report.json
```

Exit codes:

```text
0 = PASS
1 = WARNING
2 = BLOCK / error
```

## GitHub Actions

The workflow is:

```text
.github/workflows/migrationguard.yml
```

For this demo repo it scans `sample_project`.

For a real application repository, copy the workflow and change:

```yaml
env:
  PROJECT_PATH: .
```

See `GITHUB_ACTIONS.md` for the detailed flow.

## Intentional demo failure

The sample contains:

```sql
ALTER TABLE users
DROP COLUMN phone;
```

while application code still references `phone`.

Expected result:

```text
DROP_COLUMN           -> HIGH
APPLICATION_REFERENCE -> CRITICAL
PostgreSQL test       -> PASS
FINAL                 -> BLOCK
```

## v0.3 limitations

This prototype still uses focused regular-expression SQL rules and a conservative text-based code scanner. It does not yet understand real PostgreSQL lock duration, table size, rollback safety, schema drift, multiple databases, authentication, or production deployment orchestration.
