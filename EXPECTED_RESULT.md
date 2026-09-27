# Expected v0.3 result

For the included sample project:

```bash
docker-compose up --build -d
docker-compose exec api migrationguard scan /workspace/project
```

Expected final status:

```text
BLOCK
```

The report should contain exactly three application references for `users.phone`:

```text
app/UserController.php:9
app/UserService.php:9
api/user.js:5
```

The PostgreSQL test should be:

```text
PASS
```

The CLI should return exit code `2` because the migration is intentionally blocked.
