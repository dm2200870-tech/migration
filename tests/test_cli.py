from app.cli import build_parser, exit_code_for_status


def test_scan_command_defaults_to_current_directory():
    parser = build_parser()
    args = parser.parse_args(["scan"])
    assert args.command == "scan"
    assert args.project == "."
    assert args.format == "text"


def test_scan_command_accepts_project_and_json_output():
    parser = build_parser()
    args = parser.parse_args([
        "scan", "/tmp/example", "--format", "json", "--output", "report.json"
    ])
    assert args.command == "scan"
    assert args.project == "/tmp/example"
    assert args.format == "json"
    assert args.output == "report.json"


def test_ci_exit_codes():
    assert exit_code_for_status("PASS") == 0
    assert exit_code_for_status("WARNING") == 1
    assert exit_code_for_status("BLOCK") == 2
