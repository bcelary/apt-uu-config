"""Tests for config CLI command."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from apt_uu_config.cli.config import config
from apt_uu_config.models.repository import Repository


@pytest.fixture
def sample_repositories():
    """Sample repository data for testing, including dpkg/status."""
    return [
        # Ubuntu distribution repos (should get variable-based patterns)
        Repository(
            origin="Ubuntu",
            suite="noble-security",
            codename="noble",
            site="security.ubuntu.com",
            component="main",
            architecture="amd64",
            priority=500,
            url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
        ),
        Repository(
            origin="Ubuntu",
            suite="noble-updates",
            codename="noble",
            site="archive.ubuntu.com",
            component="main",
            architecture="amd64",
            priority=500,
            url="http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages",
        ),
        # Third-party repo (should get hardcoded pattern)
        Repository(
            origin="Brave Software",
            suite="stable",
            codename="stable",
            site="brave-browser-apt-release.s3.brave.com",
            component="main",
            architecture="amd64",
            priority=500,
            url="https://brave-browser-apt-release.s3.brave.com/ stable/main amd64 Packages",
        ),
        # Repo with missing suite (should use Origins-Pattern)
        Repository(
            origin="Tailscale",
            codename="noble",
            site="pkgs.tailscale.com",
            component="main",
            architecture="amd64",
            priority=500,
            url="https://pkgs.tailscale.com/stable/ubuntu noble/main amd64 Packages",
        ),
        # dpkg/status pseudo-repository (should be filtered out)
        Repository(
            suite="now",
            priority=100,
            url="/var/lib/dpkg/status",
        ),
    ]


@pytest.fixture
def mock_system_data(sample_repositories):
    """Mock both get_distro_info and parse_apt_policy."""
    with patch("apt_uu_config.cli.config.get_distro_info") as mock_distro, patch(
        "apt_uu_config.cli.config.parse_apt_policy"
    ) as mock_policy:
        mock_distro.return_value = ("Ubuntu", "noble")
        mock_policy.return_value = sample_repositories
        yield mock_distro, mock_policy


def test_config_command_basic(mock_system_data):
    """Test basic config command execution."""
    runner = CliRunner()
    result = runner.invoke(config)

    assert result.exit_code == 0
    assert "Suggested unattended-upgrades patterns for Ubuntu noble" in result.output


def test_config_filters_dpkg_status(mock_system_data):
    """Test that dpkg/status pseudo-repository is filtered out."""
    runner = CliRunner()
    result = runner.invoke(config)

    assert result.exit_code == 0
    # Should not see dpkg/status in output
    assert "/var/lib/dpkg/status" not in result.output
    assert 'suite="now"' not in result.output


def test_config_generates_variable_patterns(mock_system_data):
    """Test that distribution repos get variable-based patterns."""
    runner = CliRunner()
    result = runner.invoke(config)

    assert result.exit_code == 0
    # Should have variable-based patterns for Ubuntu repos
    assert "${distro_id}:${distro_codename}-security" in result.output
    assert "${distro_id}:${distro_codename}-updates" in result.output


def test_config_generates_hardcoded_patterns(mock_system_data):
    """Test that third-party repos get hardcoded patterns."""
    runner = CliRunner()
    result = runner.invoke(config)

    assert result.exit_code == 0
    # Should have hardcoded pattern for Brave
    assert "Brave Software:stable" in result.output


def test_config_uses_origins_pattern_section(mock_system_data):
    """Test that repos without suite use Origins-Pattern section."""
    runner = CliRunner()
    result = runner.invoke(config)

    assert result.exit_code == 0
    # Tailscale repo should be in Origins-Pattern section
    assert "Unattended-Upgrade::Origins-Pattern" in result.output
    assert "origin=Tailscale,codename=noble" in result.output


def test_config_shows_both_sections(mock_system_data):
    """Test that both configuration sections are shown when applicable."""
    runner = CliRunner()
    result = runner.invoke(config)

    assert result.exit_code == 0
    assert "Unattended-Upgrade::Allowed-Origins" in result.output
    assert "Unattended-Upgrade::Origins-Pattern" in result.output


def test_config_shows_summary(mock_system_data):
    """Test that config command generates patterns for all real repos."""
    runner = CliRunner()
    result = runner.invoke(config)

    assert result.exit_code == 0
    # 4 real repos (5 total - 1 dpkg/status) should generate patterns
    assert "${distro_id}:${distro_codename}-security" in result.output
    assert "${distro_id}:${distro_codename}-updates" in result.output
    assert "Brave Software:stable" in result.output
    assert "origin=Tailscale,codename=noble" in result.output


def test_config_no_repositories():
    """Test config command when no repositories are found."""
    with patch("apt_uu_config.cli.config.get_distro_info") as mock_distro, patch(
        "apt_uu_config.cli.config.parse_apt_policy"
    ) as mock_policy:
        mock_distro.return_value = ("Ubuntu", "noble")
        mock_policy.return_value = []

        runner = CliRunner()
        result = runner.invoke(config)

        assert result.exit_code == 0
        assert "No repositories found" in result.output


def test_config_only_dpkg_status():
    """Test config command when only dpkg/status exists."""
    dpkg_repo = Repository(
        suite="now",
        priority=100,
        url="/var/lib/dpkg/status",
    )

    with patch("apt_uu_config.cli.config.get_distro_info") as mock_distro, patch(
        "apt_uu_config.cli.config.parse_apt_policy"
    ) as mock_policy:
        mock_distro.return_value = ("Ubuntu", "noble")
        mock_policy.return_value = [dpkg_repo]

        runner = CliRunner()
        result = runner.invoke(config)

        assert result.exit_code == 0
        # All repos filtered out
        assert "No repositories found" in result.output


def test_config_shows_repository_comments(mock_system_data):
    """Test that repository information is shown as comments with --verbose."""
    runner = CliRunner()
    result = runner.invoke(config, ["--verbose"])

    assert result.exit_code == 0
    # Should have comments showing repo details
    assert "security.ubuntu.com" in result.output
    assert "archive.ubuntu.com" in result.output
    assert "brave-browser-apt-release.s3.brave.com" in result.output
    assert "pkgs.tailscale.com" in result.output


def test_config_groups_repos_by_pattern():
    """Test that multiple repos with same pattern are grouped together."""
    # Create two repos that should generate the same pattern
    repos = [
        Repository(
            origin="Ubuntu",
            suite="noble-security",
            codename="noble",
            site="security.ubuntu.com",
            component="main",
            architecture="amd64",
            priority=500,
            url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
        ),
        Repository(
            origin="Ubuntu",
            suite="noble-security",
            codename="noble",
            site="security.ubuntu.com",
            component="universe",  # Different component
            architecture="amd64",
            priority=500,
            url="http://security.ubuntu.com/ubuntu noble-security/universe amd64 Packages",
        ),
    ]

    with patch("apt_uu_config.cli.config.get_distro_info") as mock_distro, patch(
        "apt_uu_config.cli.config.parse_apt_policy"
    ) as mock_policy:
        mock_distro.return_value = ("Ubuntu", "noble")
        mock_policy.return_value = repos

        runner = CliRunner()
        result = runner.invoke(config, ["--verbose"])

        assert result.exit_code == 0
        # Pattern should appear only once
        pattern_count = result.output.count("${distro_id}:${distro_codename}-security")
        assert (
            pattern_count == 1
        ), f"Expected pattern to appear once, but found {pattern_count} times"

        # Both repos should be listed as comments
        assert "noble-security/main" in result.output
        assert "noble-security/universe" in result.output


def test_config_verbose_flag(mock_system_data):
    """Test that --verbose shows repository details."""
    runner = CliRunner()
    result = runner.invoke(config, ["--verbose"])

    assert result.exit_code == 0
    # Should show repository details as comments
    assert "security.ubuntu.com" in result.output
    assert "archive.ubuntu.com" in result.output
    assert "brave-browser-apt-release.s3.brave.com" in result.output
    assert "pkgs.tailscale.com" in result.output
    # Comments should be prefixed with #
    assert "# " in result.output


def test_config_without_verbose_no_repo_details(mock_system_data):
    """Test that default output (without --verbose) doesn't show repo details."""
    runner = CliRunner()
    result = runner.invoke(config)

    assert result.exit_code == 0
    # Should show patterns
    assert "${distro_id}:${distro_codename}-security" in result.output
    # Should NOT show repository details (no comment lines)
    assert "# " not in result.output


def test_config_verbose_spacing():
    """Test that --verbose has blank lines between pattern groups."""
    repos = [
        Repository(
            origin="Ubuntu",
            suite="noble-security",
            codename="noble",
            site="security.ubuntu.com",
            component="main",
            architecture="amd64",
            priority=500,
            url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
        ),
        Repository(
            origin="Ubuntu",
            suite="noble-updates",
            codename="noble",
            site="archive.ubuntu.com",
            component="main",
            architecture="amd64",
            priority=500,
            url="http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages",
        ),
    ]

    with patch("apt_uu_config.cli.config.get_distro_info") as mock_distro, patch(
        "apt_uu_config.cli.config.parse_apt_policy"
    ) as mock_policy:
        mock_distro.return_value = ("Ubuntu", "noble")
        mock_policy.return_value = repos

        runner = CliRunner()
        result = runner.invoke(config, ["--verbose"])

        assert result.exit_code == 0
        # With verbose, should have blank lines between pattern groups
        lines = result.output.split("\n")
        # Find the two pattern lines
        security_line_idx = next(
            i
            for i, line in enumerate(lines)
            if "-security" in line and line.strip().startswith('"')
        )
        updates_line_idx = next(
            i for i, line in enumerate(lines) if "-updates" in line and line.strip().startswith('"')
        )
        # There should be blank lines between them (security pattern + comment lines + blank + updates pattern)
        assert updates_line_idx > security_line_idx + 1


def test_config_without_verbose_no_spacing():
    """Test that default output (without --verbose) has no blank lines between patterns."""
    repos = [
        Repository(
            origin="Ubuntu",
            suite="noble-security",
            codename="noble",
            site="security.ubuntu.com",
            component="main",
            architecture="amd64",
            priority=500,
            url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
        ),
        Repository(
            origin="Ubuntu",
            suite="noble-updates",
            codename="noble",
            site="archive.ubuntu.com",
            component="main",
            architecture="amd64",
            priority=500,
            url="http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages",
        ),
    ]

    with patch("apt_uu_config.cli.config.get_distro_info") as mock_distro, patch(
        "apt_uu_config.cli.config.parse_apt_policy"
    ) as mock_policy:
        mock_distro.return_value = ("Ubuntu", "noble")
        mock_policy.return_value = repos

        runner = CliRunner()
        result = runner.invoke(config)

        assert result.exit_code == 0
        # Without verbose, should have no blank lines between patterns
        lines = result.output.split("\n")
        # Find the two pattern lines
        security_line_idx = next(
            i
            for i, line in enumerate(lines)
            if "-security" in line and line.strip().startswith('"')
        )
        updates_line_idx = next(
            i for i, line in enumerate(lines) if "-updates" in line and line.strip().startswith('"')
        )
        # They should be consecutive (no blank lines between)
        assert updates_line_idx == security_line_idx + 1
