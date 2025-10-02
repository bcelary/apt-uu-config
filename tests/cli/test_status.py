"""Tests for status CLI command."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from apt_uu_config.cli.status import status
from apt_uu_config.models.repository import Repository
from apt_uu_config.models.uu_config import UUConfig
from apt_uu_config.models.uu_pattern import UUPattern


@pytest.fixture
def sample_repositories():
    """Sample repository data for testing."""
    return [
        Repository(
            origin="Ubuntu",
            suite="noble-security",
            codename="noble",
            site="security.ubuntu.com",
            component="main",
            label="Ubuntu",
            architecture="amd64",
            version="24.04",
            priority=500,
            url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
        ),
        Repository(
            origin="Ubuntu",
            suite="noble-updates",
            codename="noble",
            site="archive.ubuntu.com",
            component="main",
            label="Ubuntu",
            architecture="amd64",
            version="24.04",
            priority=500,
            url="http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages",
        ),
        Repository(
            origin="Brave Software",
            suite="stable",
            codename="stable",
            site="brave-browser-apt-release.s3.brave.com",
            component="main",
            label="Brave",
            architecture="amd64",
            priority=500,
            url="https://brave-browser-apt-release.s3.brave.com stable/main amd64 Packages",
        ),
    ]


@pytest.fixture
def sample_config():
    """Sample UU config for testing."""
    return UUConfig(
        globally_enabled=True,
        patterns=[
            UUPattern(
                pattern_string="${distro_id}:${distro_codename}-security", section="Allowed-Origins"
            ),
            UUPattern(pattern_string="Brave Software:stable", section="Allowed-Origins"),
        ],
        distro_id="Ubuntu",
        distro_codename="noble",
    )


@pytest.fixture
def mock_system_state(sample_config, sample_repositories):
    """Mock the _load_system_state function."""
    with patch("apt_uu_config.cli.status._load_system_state") as mock:
        mock.return_value = (sample_config, sample_repositories)
        yield mock


class TestStatusSourcesCommand:
    """Tests for 'status sources' command."""

    def test_sources_text_output(self, mock_system_state):
        """Test sources command with default text output."""
        runner = CliRunner(env={"COLUMNS": "200"})
        result = runner.invoke(status, ["sources"])

        assert result.exit_code == 0
        assert "APT Repositories" in result.output
        assert "Ubuntu" in result.output
        assert "noble-security" in result.output
        assert "Brave Software" in result.output
        assert "Arch" in result.output  # Verify arch column is present

    def test_sources_text_verbose(self, mock_system_state):
        """Test sources command with verbose flag."""
        runner = CliRunner()
        result = runner.invoke(status, ["sources", "--verbose"])

        assert result.exit_code == 0
        assert "Label" in result.output
        assert "Arch" in result.output
        # Priority column might be abbreviated as "Prio" in narrow terminals
        assert "Priority" in result.output or "Prio" in result.output
        assert "URL" in result.output

    def test_sources_json_output(self, mock_system_state):
        """Test sources command with JSON output."""
        runner = CliRunner()
        result = runner.invoke(status, ["--format", "json", "sources"])

        assert result.exit_code == 0
        assert '"repositories"' in result.output
        assert '"origin": "Ubuntu"' in result.output
        assert '"suite": "noble-security"' in result.output

    def test_sources_json_includes_all_fields(self, mock_system_state):
        """Test that JSON output includes all repository fields."""
        runner = CliRunner()
        result = runner.invoke(status, ["--format", "json", "sources"])

        assert result.exit_code == 0
        # Check for all major fields
        assert '"origin"' in result.output
        assert '"suite"' in result.output
        assert '"site"' in result.output
        assert '"component"' in result.output
        assert '"priority"' in result.output
        assert '"url"' in result.output


class TestStatusPatternsCommand:
    """Tests for 'status patterns' command."""

    def test_patterns_text_output(self, mock_system_state):
        """Test patterns command with default text output."""
        runner = CliRunner()
        result = runner.invoke(status, ["patterns"])

        assert result.exit_code == 0
        assert "Configured Patterns" in result.output
        assert "Allowed-Origins" in result.output
        assert "${distro_id}:${distro_codename}-security" in result.output
        assert "Brave Software:stable" in result.output

    def test_patterns_shows_match_indicator(self, mock_system_state):
        """Test that patterns show match indicators."""
        runner = CliRunner()
        result = runner.invoke(status, ["patterns"])

        assert result.exit_code == 0
        # Both patterns should match (✓)
        assert "✓" in result.output

    def test_patterns_verbose_shows_details(self, mock_system_state):
        """Test patterns verbose mode shows detailed matches."""
        runner = CliRunner()
        result = runner.invoke(status, ["patterns", "--verbose"])

        assert result.exit_code == 0
        assert "Detailed Match Listing" in result.output
        assert "Ubuntu:noble-security" in result.output
        assert "Brave Software:stable" in result.output
        # Verify additional details are shown
        assert "component=main" in result.output
        assert "codename=noble" in result.output
        assert "label=Ubuntu" in result.output
        assert "arch=amd64" in result.output
        assert "version=24.04" in result.output

    def test_patterns_json_output(self, mock_system_state):
        """Test patterns JSON output contains only pattern config."""
        runner = CliRunner()
        result = runner.invoke(status, ["--format", "json", "patterns"])

        assert result.exit_code == 0
        assert '"patterns"' in result.output
        assert '"pattern_string"' in result.output
        assert '"section"' in result.output
        # JSON should NOT include match information
        assert '"matches"' not in result.output

    def test_patterns_no_matches(self, mock_system_state):
        """Test patterns that don't match any repos."""
        # Create config with non-matching pattern
        no_match_config = UUConfig(
            globally_enabled=True,
            patterns=[
                UUPattern(pattern_string="NonExistent:repo", section="Allowed-Origins"),
            ],
            distro_id="Ubuntu",
            distro_codename="noble",
        )

        with patch("apt_uu_config.cli.status._load_system_state") as mock:
            mock.return_value = (no_match_config, [])
            runner = CliRunner()
            result = runner.invoke(status, ["patterns"])

            assert result.exit_code == 0
            assert "✗" in result.output


class TestStatusConfigCommand:
    """Tests for 'status config' command."""

    def test_config_by_repo_default(self, mock_system_state):
        """Test config command with default by-repo grouping."""
        runner = CliRunner()
        result = runner.invoke(status, ["config"])

        assert result.exit_code == 0
        assert "Unattended-Upgrades Global Status" in result.output
        assert "enabled" in result.output
        assert "Repository Configuration Status" in result.output
        assert "UU Enabled" in result.output

    def test_config_shows_global_status_enabled(self, mock_system_state):
        """Test that global status is displayed correctly when enabled."""
        runner = CliRunner()
        result = runner.invoke(status, ["config"])

        assert result.exit_code == 0
        assert "enabled" in result.output

    def test_config_shows_global_status_disabled(self, mock_system_state, sample_repositories):
        """Test that global status is displayed correctly when disabled."""
        disabled_config = UUConfig(
            globally_enabled=False,
            patterns=[],
            distro_id="Ubuntu",
            distro_codename="noble",
        )

        with patch("apt_uu_config.cli.status._load_system_state") as mock:
            mock.return_value = (disabled_config, sample_repositories)
            runner = CliRunner()
            result = runner.invoke(status, ["config"])

            assert result.exit_code == 0
            assert "disabled" in result.output

    def test_config_by_repo_shows_matches(self, mock_system_state):
        """Test config by-repo shows which patterns match."""
        runner = CliRunner()
        result = runner.invoke(status, ["config", "--by-repo"])

        assert result.exit_code == 0
        assert "Matched By" in result.output
        # Ubuntu:noble-security should be matched by the pattern
        assert "Ubuntu:noble-security" in result.output

    def test_config_by_repo_enabled_only(self, mock_system_state):
        """Test config by-repo with enabled-only filter."""
        runner = CliRunner()
        result = runner.invoke(status, ["config", "--by-repo", "--enabled-only"])

        assert result.exit_code == 0
        # Should show enabled repos
        assert "Ubuntu:noble-security" in result.output
        assert "Brave Software:stable" in result.output
        # Should not show disabled repos (noble-updates not in patterns)

    def test_config_by_repo_disabled_only(self, mock_system_state):
        """Test config by-repo with disabled-only filter."""
        runner = CliRunner()
        result = runner.invoke(status, ["config", "--by-repo", "--disabled-only"])

        assert result.exit_code == 0
        # Should show disabled repo
        assert "Ubuntu:noble-updates" in result.output
        # Should not show enabled repos
        assert "noble-security" not in result.output

    def test_config_by_pattern(self, mock_system_state):
        """Test config command with by-pattern grouping."""
        runner = CliRunner()
        result = runner.invoke(status, ["config", "--by-pattern"])

        assert result.exit_code == 0
        assert "Pattern Configuration Status" in result.output
        assert "Repos Matched" in result.output
        assert "${distro_id}:${distro_codename}-security" in result.output

    def test_config_by_pattern_verbose(self, mock_system_state):
        """Test config by-pattern with verbose flag."""
        runner = CliRunner()
        result = runner.invoke(status, ["config", "--by-pattern", "--verbose"])

        assert result.exit_code == 0
        assert "Matched Repositories" in result.output

    def test_config_json_by_repo(self, mock_system_state):
        """Test config JSON output with by-repo grouping."""
        runner = CliRunner()
        result = runner.invoke(status, ["--format", "json", "config", "--by-repo"])

        assert result.exit_code == 0
        assert '"globally_enabled": true' in result.output
        assert '"repositories"' in result.output
        assert '"enabled"' in result.output
        assert '"matched_by"' in result.output

    def test_config_json_by_pattern(self, mock_system_state):
        """Test config JSON output with by-pattern grouping."""
        runner = CliRunner()
        result = runner.invoke(status, ["--format", "json", "config", "--by-pattern"])

        assert result.exit_code == 0
        assert '"globally_enabled": true' in result.output
        assert '"patterns"' in result.output
        assert '"count"' in result.output
        assert '"matched_repos"' in result.output


class TestStatusErrorHandling:
    """Tests for error handling in status commands."""

    def test_handles_permission_error(self):
        """Test that permission errors are handled gracefully."""
        with patch("apt_uu_config.cli.status._load_system_state") as mock:
            mock.side_effect = PermissionError("Permission denied")
            runner = CliRunner()
            result = runner.invoke(status, ["sources"])

            assert result.exit_code == 1
            assert "Permission denied" in result.output
            assert "sudo" in result.output

    def test_handles_distro_info_error(self):
        """Test that distro info errors are handled."""
        from apt_uu_config.apt.distro_info import DistroInfoError

        with patch("apt_uu_config.cli.status._load_system_state") as mock:
            mock.side_effect = DistroInfoError("Cannot determine distro")
            runner = CliRunner()
            result = runner.invoke(status, ["sources"])

            assert result.exit_code == 1
            assert "Error" in result.output

    def test_handles_uu_config_read_error(self):
        """Test that UU config read errors are handled."""
        from apt_uu_config.apt.uu_config_reader import UUConfigReadError

        with patch("apt_uu_config.cli.status._load_system_state") as mock:
            mock.side_effect = UUConfigReadError("Cannot read config")
            runner = CliRunner()
            result = runner.invoke(status, ["sources"])

            assert result.exit_code == 1
            assert "Error reading unattended-upgrades configuration" in result.output

    def test_handles_policy_parse_error(self):
        """Test that policy parse errors are handled."""
        from apt_uu_config.apt.policy_parser import PolicyParseError

        with patch("apt_uu_config.cli.status._load_system_state") as mock:
            mock.side_effect = PolicyParseError("Cannot parse policy")
            runner = CliRunner()
            result = runner.invoke(status, ["sources"])

            assert result.exit_code == 1
            assert "Error reading repository information" in result.output


class TestStatusFormatOption:
    """Tests for --format option inheritance."""

    def test_format_option_inherited_by_sources(self, mock_system_state):
        """Test that --format option works with sources command."""
        runner = CliRunner()
        result = runner.invoke(status, ["--format", "json", "sources"])

        assert result.exit_code == 0
        assert result.output.strip().startswith("{")

    def test_format_option_inherited_by_patterns(self, mock_system_state):
        """Test that --format option works with patterns command."""
        runner = CliRunner()
        result = runner.invoke(status, ["--format", "json", "patterns"])

        assert result.exit_code == 0
        assert result.output.strip().startswith("{")

    def test_format_option_inherited_by_config(self, mock_system_state):
        """Test that --format option works with config command."""
        runner = CliRunner()
        result = runner.invoke(status, ["--format", "json", "config"])

        assert result.exit_code == 0
        assert result.output.strip().startswith("{")

    def test_default_format_is_text(self, mock_system_state):
        """Test that default format is text."""
        runner = CliRunner()
        result = runner.invoke(status, ["sources"])

        assert result.exit_code == 0
        # Text output contains table formatting
        assert "APT Repositories" in result.output
