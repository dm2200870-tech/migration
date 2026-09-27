from app.rules import RuleEngine


def test_drop_column_is_high_risk():
    sql = "ALTER TABLE users DROP COLUMN phone;"
    issues = RuleEngine().analyze(sql, "003_drop_phone.sql")

    assert any(i["rule"] == "DROP_COLUMN" for i in issues)
    assert any(i["severity"] == "HIGH" for i in issues)


def test_safe_add_nullable_column_has_no_block():
    sql = "ALTER TABLE users ADD COLUMN nickname TEXT;"
    issues = RuleEngine().analyze(sql, "004_add_nickname.sql")

    assert not any(i["severity"] in {"CRITICAL", "HIGH"} for i in issues)
