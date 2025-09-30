from click.testing import CliRunner

from apt_uu_config.cli.__main__ import cli


def test_cli_invalid_command(cli_runner: CliRunner, cli_env: None) -> None:
    """Test invalid command handling"""
    result = cli_runner.invoke(cli, ["invalid"])
    assert result.exit_code != 0
    assert "No such command" in result.output


def test_cli_help(cli_runner: CliRunner, cli_env: None) -> None:
    """Test help command"""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Options:" in result.output


def test_cli_version(cli_runner: CliRunner, cli_env: None) -> None:
    """Test version option"""
    result = cli_runner.invoke(cli, ["--version"])
    assert result.exit_code == 0


def test_cli_has_status_command(cli_runner: CliRunner, cli_env: None) -> None:
    """Test that status command is registered"""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "status" in result.output


def test_cli_has_enable_command(cli_runner: CliRunner, cli_env: None) -> None:
    """Test that enable command is registered"""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "enable" in result.output


def test_cli_has_disable_command(cli_runner: CliRunner, cli_env: None) -> None:
    """Test that disable command is registered"""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "disable" in result.output


def test_cli_has_origin_command(cli_runner: CliRunner, cli_env: None) -> None:
    """Test that origin command is registered"""
    result = cli_runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "origin" in result.output
