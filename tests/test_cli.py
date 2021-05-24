from typer.testing import CliRunner

from scribe import __version__
from scribe.cli import _configuration_path, app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__

    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_config_show():
    result = runner.invoke(app, ["config", "path"])
    assert result.exit_code == 0
    assert result.stdout.strip() == str(_configuration_path())
