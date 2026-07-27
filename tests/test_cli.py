"""Smoke tests for the CLI entry point."""

import pytest

from region_classifier.cli import main


def test_cli_runs_with_no_args_headless():
    # bundled default scenario, run fast, no wall-clock pacing
    rc = main(["--no-realtime", "--no-color", "--duration", "5"])
    assert rc == 0


def test_cli_validate_reports_accuracy(capsys):
    rc = main(["--no-realtime", "--no-color", "--validate", "--duration", "10"])
    assert rc == 0
    assert "accuracy vs ground truth" in capsys.readouterr().out


def test_cli_missing_config_is_clean_error():
    rc = main(["--config", "does_not_exist.yaml", "--no-realtime", "--duration", "1"])
    assert rc == 2


def test_cli_version():
    with pytest.raises(SystemExit) as e:  # argparse action='version' exits 0
        main(["--version"])
    assert e.value.code == 0
