from pathlib import Path

from app.code_scanner import CodeReferenceScanner


def test_migration_files_are_not_counted_as_application_references(tmp_path: Path):
    (tmp_path / "database" / "migrations").mkdir(parents=True)
    (tmp_path / "app").mkdir()

    (tmp_path / "database" / "migrations" / "001_users.sql").write_text(
        "CREATE TABLE users (phone TEXT);",
        encoding="utf-8",
    )
    (tmp_path / "database" / "migrations" / "003_drop_phone.sql").write_text(
        "ALTER TABLE users DROP COLUMN phone;",
        encoding="utf-8",
    )
    (tmp_path / "app" / "User.php").write_text(
        'return $user["phone"];',
        encoding="utf-8",
    )

    refs = CodeReferenceScanner(tmp_path).find_references("users", "phone")

    assert len(refs) == 1
    assert refs[0]["file"] == "app/User.php"
