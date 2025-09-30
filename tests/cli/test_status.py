"""Tests for status CLI command."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from apt_uu_config.apt.distro_info import DistroInfoError
from apt_uu_config.apt.policy_parser import PolicyParseError
from apt_uu_config.apt.uu_config_reader import UUConfigReadError
from apt_uu_config.cli.status import get_matching_patterns, status
from apt_uu_config.models.repository import Repository
from apt_uu_config.models.uu_config import UUConfig
from apt_uu_config.models.uu_pattern import UUPattern


@pytest.fixture
def sample_config() -> UUConfig:
    """Create a sample UU config for testing."""
    return UUConfig(
        globally_enabled=True,
        patterns=[
            UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins"),
            UUPattern(pattern_string="Brave Software:stable", section="Allowed-Origins"),
            UUPattern(
                pattern_string="origin=Tailscale,site=pkgs.tailscale.com",
                section="Origins-Pattern",
            ),
        ],
        distro_id="Ubuntu",
        distro_codename="noble",
    )


@pytest.fixture
def sample_repositories() -> list[Repository]:
    """Create sample repositories for testing."""
    return [
        Repository(
            origin="Ubuntu",
            suite="noble-security",
            component="main",
            site="security.ubuntu.com",
            priority=500,
            url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
        ),
        Repository(
            origin="Ubuntu",
            suite="noble-updates",
            component="main",
            site="archive.ubuntu.com",
            priority=500,
            url="http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages",
        ),
        Repository(
            origin="Brave Software",
            suite="stable",
            component="main",
            site="brave-browser-apt-release.s3.brave.com",
            priority=500,
            url="https://brave-browser-apt-release.s3.brave.com/ stable/main amd64 Packages",
        ),
        Repository(
            origin="Tailscale",
            suite="stable",
            component="main",
            site="pkgs.tailscale.com",
            priority=500,
            url="https://pkgs.tailscale.com/stable/ubuntu noble/main amd64 Packages",
        ),
        Repository(
            origin="Docker",
            suite="noble",
            component="stable",
            site="download.docker.com",
            priority=500,
            url="https://download.docker.com/linux/ubuntu noble/stable amd64 Packages",
        ),
    ]


def test_get_matching_patterns_single_match(
    sample_config: UUConfig, sample_repositories: list[Repository]
) -> None:
    """Test get_matching_patterns with single match."""
    ubuntu_security = sample_repositories[0]
    matching = get_matching_patterns(ubuntu_security, sample_config)

    assert len(matching) == 1
    assert matching[0].pattern_string == "Ubuntu:noble-security"


def test_get_matching_patterns_no_match(
    sample_config: UUConfig, sample_repositories: list[Repository]
) -> None:
    """Test get_matching_patterns with no matches."""
    docker_repo = sample_repositories[4]
    matching = get_matching_patterns(docker_repo, sample_config)

    assert len(matching) == 0


def test_get_matching_patterns_origins_pattern_format(
    sample_config: UUConfig, sample_repositories: list[Repository]
) -> None:
    """Test get_matching_patterns with Origins-Pattern format."""
    tailscale_repo = sample_repositories[3]
    matching = get_matching_patterns(tailscale_repo, sample_config)

    assert len(matching) == 1
    assert matching[0].section == "Origins-Pattern"
    assert "Tailscale" in matching[0].pattern_string


@patch("apt_uu_config.cli.status.read_uu_config")
@patch("apt_uu_config.cli.status.parse_apt_policy")
def test_status_command_default_output(
    mock_parse_policy: MagicMock,
    mock_read_config: MagicMock,
    sample_config: UUConfig,
    sample_repositories: list[Repository],
) -> None:
    """Test status command with default output."""
    mock_read_config.return_value = sample_config
    mock_parse_policy.return_value = sample_repositories

    runner = CliRunner()
    result = runner.invoke(status)

    assert result.exit_code == 0
    assert "✓ Enabled" in result.output
    assert "Ubuntu noble" in result.output
    assert "Total repositories: 5" in result.output
    assert "Enabled for auto-updates: 3" in result.output


@patch("apt_uu_config.cli.status.read_uu_config")
@patch("apt_uu_config.cli.status.parse_apt_policy")
def test_status_command_verbose(
    mock_parse_policy: MagicMock,
    mock_read_config: MagicMock,
    sample_config: UUConfig,
    sample_repositories: list[Repository],
) -> None:
    """Test status command with --verbose flag."""
    mock_read_config.return_value = sample_config
    mock_parse_policy.return_value = sample_repositories

    runner = CliRunner()
    result = runner.invoke(status, ["--verbose"])

    assert result.exit_code == 0
    assert "Repository Status" in result.output
    assert "Ubuntu" in result.output
    assert "Brave Software" in result.output
    assert "Tailscale" in result.output
    assert "Docker" in result.output


@patch("apt_uu_config.cli.status.read_uu_config")
@patch("apt_uu_config.cli.status.parse_apt_policy")
def test_status_command_enabled_only(
    mock_parse_policy: MagicMock,
    mock_read_config: MagicMock,
    sample_config: UUConfig,
    sample_repositories: list[Repository],
) -> None:
    """Test status command with --enabled-only flag."""
    mock_read_config.return_value = sample_config
    mock_parse_policy.return_value = sample_repositories

    runner = CliRunner()
    result = runner.invoke(status, ["--enabled-only"])

    assert result.exit_code == 0
    assert "Repository Status" in result.output
    # Should show enabled repos
    assert "Ubuntu" in result.output or "noble-security" in result.output
    # Docker should not be shown (disabled)
    assert "✗ Disabled" not in result.output


@patch("apt_uu_config.cli.status.read_uu_config")
@patch("apt_uu_config.cli.status.parse_apt_policy")
def test_status_command_disabled_only(
    mock_parse_policy: MagicMock,
    mock_read_config: MagicMock,
    sample_config: UUConfig,
    sample_repositories: list[Repository],
) -> None:
    """Test status command with --disabled-only flag."""
    mock_read_config.return_value = sample_config
    mock_parse_policy.return_value = sample_repositories

    runner = CliRunner()
    result = runner.invoke(status, ["--disabled-only"])

    assert result.exit_code == 0
    assert "Repository Status" in result.output
    # Should only show disabled repos in the table
    # Count enabled/disabled markers in the repository table only
    # (ignore the global status panel)
    table_start = result.output.find("Repository Status")
    if table_start > 0:
        table_section = result.output[table_start:]
        # Check that the table shows only disabled repos
        assert "✗ Disabled" in table_section
        # Docker should be in the table (it's disabled)
        assert "Docker" in table_section or "noble" in table_section


@patch("apt_uu_config.cli.status.read_uu_config")
@patch("apt_uu_config.cli.status.parse_apt_policy")
def test_status_command_json_output(
    mock_parse_policy: MagicMock,
    mock_read_config: MagicMock,
    sample_config: UUConfig,
    sample_repositories: list[Repository],
) -> None:
    """Test status command with --json flag."""
    mock_read_config.return_value = sample_config
    mock_parse_policy.return_value = sample_repositories

    runner = CliRunner()
    result = runner.invoke(status, ["--json"])

    assert result.exit_code == 0

    # Parse JSON output
    output = json.loads(result.output)

    assert output["globally_enabled"] is True
    assert output["distro_id"] == "Ubuntu"
    assert output["distro_codename"] == "noble"
    assert len(output["patterns"]) == 3
    assert output["total_repositories"] == 5
    assert output["enabled_repositories"] == 3
    assert len(output["repositories"]) == 5

    # Check first pattern
    assert output["patterns"][0]["section"] == "Allowed-Origins"
    assert output["patterns"][0]["pattern"] == "Ubuntu:noble-security"

    # Check first repository
    ubuntu_sec = output["repositories"][0]
    assert ubuntu_sec["origin"] == "Ubuntu"
    assert ubuntu_sec["suite"] == "noble-security"
    assert ubuntu_sec["enabled"] is True


@patch("apt_uu_config.cli.status.read_uu_config")
@patch("apt_uu_config.cli.status.parse_apt_policy")
def test_status_command_globally_disabled(
    mock_parse_policy: MagicMock,
    mock_read_config: MagicMock,
    sample_repositories: list[Repository],
) -> None:
    """Test status command when UU is globally disabled."""
    disabled_config = UUConfig(
        globally_enabled=False,
        patterns=[
            UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins"),
        ],
        distro_id="Ubuntu",
        distro_codename="noble",
    )
    mock_read_config.return_value = disabled_config
    mock_parse_policy.return_value = sample_repositories

    runner = CliRunner()
    result = runner.invoke(status)

    assert result.exit_code == 0
    assert "✗ Disabled" in result.output
    assert "0 (globally disabled)" in result.output


@patch("apt_uu_config.cli.status.read_uu_config")
@patch("apt_uu_config.cli.status.parse_apt_policy")
def test_status_command_empty_patterns(
    mock_parse_policy: MagicMock,
    mock_read_config: MagicMock,
    sample_repositories: list[Repository],
) -> None:
    """Test status command with no configured patterns."""
    empty_config = UUConfig(
        globally_enabled=True,
        patterns=[],
        distro_id="Ubuntu",
        distro_codename="noble",
    )
    mock_read_config.return_value = empty_config
    mock_parse_policy.return_value = sample_repositories

    runner = CliRunner()
    result = runner.invoke(status)

    assert result.exit_code == 0
    # Should not show patterns table
    assert "Configured Patterns" not in result.output


@patch("apt_uu_config.cli.status.read_uu_config")
@patch("apt_uu_config.cli.status.parse_apt_policy")
def test_status_command_permission_error(
    mock_parse_policy: MagicMock, mock_read_config: MagicMock
) -> None:
    """Test status command with permission error."""
    mock_read_config.side_effect = PermissionError("Permission denied")

    runner = CliRunner()
    result = runner.invoke(status)

    assert result.exit_code != 0
    assert "Permission denied" in result.output or "sudo" in result.output


@patch("apt_uu_config.cli.status.read_uu_config")
@patch("apt_uu_config.cli.status.parse_apt_policy")
def test_status_command_config_read_error(
    mock_parse_policy: MagicMock, mock_read_config: MagicMock
) -> None:
    """Test status command with config read error."""
    mock_read_config.side_effect = UUConfigReadError("Failed to read config")

    runner = CliRunner()
    result = runner.invoke(status)

    assert result.exit_code != 0
    assert "Error" in result.output


@patch("apt_uu_config.cli.status.read_uu_config")
@patch("apt_uu_config.cli.status.parse_apt_policy")
def test_status_command_policy_parse_error(
    mock_parse_policy: MagicMock, mock_read_config: MagicMock, sample_config: UUConfig
) -> None:
    """Test status command with policy parse error."""
    mock_read_config.return_value = sample_config
    mock_parse_policy.side_effect = PolicyParseError("Failed to parse policy")

    runner = CliRunner()
    result = runner.invoke(status)

    assert result.exit_code != 0
    assert "Error" in result.output


@patch("apt_uu_config.cli.status.read_uu_config")
@patch("apt_uu_config.cli.status.parse_apt_policy")
def test_status_command_distro_info_error(
    mock_parse_policy: MagicMock, mock_read_config: MagicMock
) -> None:
    """Test status command with distro info error."""
    mock_read_config.side_effect = DistroInfoError("Failed to get distro info")

    runner = CliRunner()
    result = runner.invoke(status)

    assert result.exit_code != 0
    assert "Error" in result.output


@patch("apt_uu_config.cli.status.read_uu_config")
@patch("apt_uu_config.cli.status.parse_apt_policy")
def test_status_command_patterns_table_shows_match_counts(
    mock_parse_policy: MagicMock,
    mock_read_config: MagicMock,
    sample_config: UUConfig,
    sample_repositories: list[Repository],
) -> None:
    """Test that patterns table shows match counts."""
    mock_read_config.return_value = sample_config
    mock_parse_policy.return_value = sample_repositories

    runner = CliRunner()
    result = runner.invoke(status)

    assert result.exit_code == 0
    assert "Configured Patterns" in result.output
    # Should show match counts in the patterns table
    assert "repo" in result.output.lower() or "match" in result.output.lower()


@patch("apt_uu_config.cli.status.read_uu_config")
@patch("apt_uu_config.cli.status.parse_apt_policy")
def test_status_command_repository_table_shows_matching_patterns(
    mock_parse_policy: MagicMock,
    mock_read_config: MagicMock,
    sample_config: UUConfig,
    sample_repositories: list[Repository],
) -> None:
    """Test that repository table shows matching patterns."""
    mock_read_config.return_value = sample_config
    mock_parse_policy.return_value = sample_repositories

    runner = CliRunner()
    result = runner.invoke(status, ["--verbose"])

    assert result.exit_code == 0
    assert "Repository Status" in result.output
    # Should have matching pattern column
    assert "Matching Pattern" in result.output or "Pattern" in result.output
