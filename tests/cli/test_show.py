"""Tests for show CLI command."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from apt_uu_config.cli.show import show
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
        Repository(
            origin="Ubuntu",
            suite="noble",
            codename="noble",
            site="archive.ubuntu.com",
            component="main",
            label="Ubuntu",
            architecture="i386",
            version="24.04",
            priority=500,
            url="http://archive.ubuntu.com/ubuntu noble/main i386 Packages",
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
    with patch("apt_uu_config.cli.show._load_system_state") as mock:
        mock.return_value = (sample_config, sample_repositories)
        yield mock


@pytest.fixture
def mock_system_state_with_primary_arch_only(sample_config, sample_repositories):
    """Mock the _load_system_state function with primary arch filtering."""

    def side_effect(primary_arch_only=False):
        if primary_arch_only:
            # Simulate filtering to only amd64 repositories
            filtered_repos = [r for r in sample_repositories if r.architecture == "amd64"]
            return (sample_config, filtered_repos)
        return (sample_config, sample_repositories)

    with patch("apt_uu_config.cli.show._load_system_state", side_effect=side_effect) as mock:
        with patch("apt_pkg.config") as apt_config_mock:
            apt_config_mock.__getitem__.return_value = "amd64"  # Mock primary arch
            yield mock


class TestShowReposCommand:
    """Tests for 'show repos' command."""

    def test_repos_text_output(self, mock_system_state):
        """Test repos command with default text output."""
        runner = CliRunner(env={"COLUMNS": "200"})
        result = runner.invoke(show, ["repos"])

        assert result.exit_code == 0
        assert "Unattended-Upgrades:" in result.output
        assert "enabled" in result.output
        assert "Repositories" in result.output
        assert "Ubuntu" in result.output
        assert "noble-security" in result.output
        assert "Brave Software" in result.output
        assert "Arch" in result.output  # Verify arch column is present
        assert "UU" in result.output  # UU status column

    def test_repos_text_verbose(self, mock_system_state):
        """Test repos command with verbose flag."""
        runner = CliRunner(env={"COLUMNS": "200"})
        result = runner.invoke(show, ["repos", "--verbose"])

        assert result.exit_code == 0
        assert "Label" in result.output
        assert "Arch" in result.output
        assert "Priority" in result.output or "Prio" in result.output
        assert "URL" in result.output
        assert "UU Pattern Match" in result.output  # Pattern match column in verbose

    def test_repos_json_output(self, mock_system_state):
        """Test repos command with JSON output."""
        runner = CliRunner()
        result = runner.invoke(show, ["repos", "--format", "json"])

        assert result.exit_code == 0
        assert '"globally_enabled": true' in result.output
        assert '"repositories"' in result.output
        assert '"origin": "Ubuntu"' in result.output
        assert '"suite": "noble-security"' in result.output
        assert '"uu_enabled"' in result.output
        assert '"matched_by"' in result.output

    def test_repos_json_includes_all_fields(self, mock_system_state):
        """Test that JSON output includes all repository fields."""
        runner = CliRunner()
        result = runner.invoke(show, ["repos", "--format", "json"])

        assert result.exit_code == 0
        # Check for all major fields
        assert '"origin"' in result.output
        assert '"suite"' in result.output
        assert '"site"' in result.output
        assert '"component"' in result.output
        assert '"priority"' in result.output
        assert '"url"' in result.output
        assert '"uu_enabled"' in result.output
        assert '"matched_by"' in result.output

    def test_repos_primary_arch_only_filters_foreign(
        self, mock_system_state_with_primary_arch_only
    ):
        """Test repos command with --primary-arch-only flag filters out foreign architectures."""
        runner = CliRunner(env={"COLUMNS": "200"})
        result = runner.invoke(show, ["repos", "--primary-arch-only"])

        assert result.exit_code == 0
        # Should show amd64 repos
        assert "noble-security" in result.output
        assert "noble-updates" in result.output
        assert "Brave Software" in result.output
        # Should NOT show i386 repo
        assert "i386" not in result.output

    def test_repos_enabled_only_filter(self, mock_system_state):
        """Test repos command with --enabled-only filter."""
        runner = CliRunner(env={"COLUMNS": "200"})
        result = runner.invoke(show, ["repos", "--enabled-only"])

        assert result.exit_code == 0
        # Should show enabled repos - check for Origin and Suite/Codename that won't be truncated
        assert "security.ubuntu.com" in result.output  # noble-security repo
        assert "Brave Software" in result.output  # Brave repo
        # Should not show disabled repos
        assert "noble-updates" not in result.output

    def test_repos_disabled_only_filter(self, mock_system_state):
        """Test repos command with --disabled-only filter."""
        runner = CliRunner(env={"COLUMNS": "200"})
        result = runner.invoke(show, ["repos", "--disabled-only"])

        assert result.exit_code == 0
        # Should show disabled repo
        assert "noble-updates" in result.output
        # Should not show enabled repos
        assert "noble-security" not in result.output

    def test_repos_conflicting_filters_error(self, mock_system_state):
        """Test that using both --enabled-only and --disabled-only raises an error."""
        runner = CliRunner()
        result = runner.invoke(show, ["repos", "--enabled-only", "--disabled-only"])

        assert result.exit_code == 1
        assert "Error" in result.output
        assert "Cannot use --enabled-only and --disabled-only together" in result.output

    def test_repos_shows_global_status_enabled(self, mock_system_state):
        """Test that global UU status is displayed correctly when enabled."""
        runner = CliRunner()
        result = runner.invoke(show, ["repos"])

        assert result.exit_code == 0
        assert "Unattended-Upgrades:" in result.output
        assert "enabled" in result.output

    def test_repos_shows_global_status_disabled(self, mock_system_state, sample_repositories):
        """Test that global UU status is displayed correctly when disabled."""
        disabled_config = UUConfig(
            globally_enabled=False,
            patterns=[],
            distro_id="Ubuntu",
            distro_codename="noble",
        )

        with patch("apt_uu_config.cli.show._load_system_state") as mock:
            mock.return_value = (disabled_config, sample_repositories)
            runner = CliRunner()
            result = runner.invoke(show, ["repos"])

            assert result.exit_code == 0
            assert "Unattended-Upgrades:" in result.output
            assert "disabled" in result.output


class TestShowPatternsCommand:
    """Tests for 'status patterns' command."""

    def test_patterns_text_output(self, mock_system_state):
        """Test patterns command with default text output."""
        runner = CliRunner()
        result = runner.invoke(show, ["patterns"])

        assert result.exit_code == 0
        assert "Allowed-Origins" in result.output
        assert "${distro_id}:${distro_codename}-security" in result.output
        assert "Brave Software:stable" in result.output

    def test_patterns_shows_match_indicator(self, mock_system_state):
        """Test that patterns show matched repositories."""
        runner = CliRunner()
        result = runner.invoke(show, ["patterns"])

        assert result.exit_code == 0
        # Both patterns should show matched repos
        assert "Ubuntu:noble-security" in result.output
        assert "Brave Software:stable" in result.output

    def test_patterns_verbose_shows_details(self, mock_system_state):
        """Test patterns verbose mode shows detailed matches."""
        runner = CliRunner()
        result = runner.invoke(show, ["patterns", "--verbose"])

        assert result.exit_code == 0
        assert "Ubuntu:noble-security" in result.output
        assert "Brave Software:stable" in result.output
        # Verify format_full() shows component and arch in main identifier
        assert "Ubuntu:noble-security/main" in result.output
        assert "[amd64]" in result.output
        # Verify additional details are shown in details section
        assert "codename=noble" in result.output
        assert "label=Ubuntu" in result.output
        assert "version=24.04" in result.output

    def test_patterns_json_output(self, mock_system_state):
        """Test patterns JSON output contains pattern config and matches."""
        runner = CliRunner()
        result = runner.invoke(show, ["patterns", "--format", "json"])

        assert result.exit_code == 0
        assert '"patterns"' in result.output
        assert '"pattern_string"' in result.output
        assert '"section"' in result.output
        # JSON should include match information
        assert '"matches"' in result.output
        # Verify matched repository fields are present
        assert '"origin"' in result.output
        assert '"suite"' in result.output
        assert '"url"' in result.output

    def test_patterns_json_includes_all_match_fields(self, mock_system_state):
        """Test that JSON matches include all repository fields."""
        runner = CliRunner()
        result = runner.invoke(show, ["patterns", "--format", "json"])

        assert result.exit_code == 0
        # Verify all repository fields are in matches
        assert '"origin"' in result.output
        assert '"suite"' in result.output
        assert '"site"' in result.output
        assert '"component"' in result.output
        assert '"codename"' in result.output
        assert '"architecture"' in result.output
        assert '"label"' in result.output
        assert '"version"' in result.output
        assert '"priority"' in result.output
        assert '"url"' in result.output

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

        with patch("apt_uu_config.cli.show._load_system_state") as mock:
            mock.return_value = (no_match_config, [])
            runner = CliRunner()
            result = runner.invoke(show, ["patterns"])

            assert result.exit_code == 0
            assert "(no matches)" in result.output

    def test_patterns_json_no_matches(self, mock_system_state):
        """Test patterns JSON output when there are no matches."""
        # Create config with non-matching pattern
        no_match_config = UUConfig(
            globally_enabled=True,
            patterns=[
                UUPattern(pattern_string="NonExistent:repo", section="Allowed-Origins"),
            ],
            distro_id="Ubuntu",
            distro_codename="noble",
        )

        with patch("apt_uu_config.cli.show._load_system_state") as mock:
            mock.return_value = (no_match_config, [])
            runner = CliRunner()
            result = runner.invoke(show, ["patterns", "--format", "json"])

            assert result.exit_code == 0
            assert '"matches": []' in result.output

    def test_patterns_primary_arch_only_filters_matched_repos(
        self, mock_system_state_with_primary_arch_only
    ):
        """Test patterns command with --primary-arch-only flag shows fewer matches."""
        runner = CliRunner()
        result = runner.invoke(show, ["patterns", "--verbose", "--primary-arch-only"])

        assert result.exit_code == 0
        # Should still show patterns, with matches
        assert "${distro_id}:${distro_codename}-security" in result.output
        # The i386 repo would be filtered out, so matches are from amd64 repos


class TestShowErrorHandling:
    """Tests for error handling in show commands."""

    def test_handles_permission_error(self):
        """Test that permission errors are handled gracefully."""
        with patch("apt_uu_config.cli.show._load_system_state") as mock:
            mock.side_effect = PermissionError("Permission denied")
            runner = CliRunner()
            result = runner.invoke(show, ["repos"])

            assert result.exit_code == 1
            assert "Permission denied" in result.output
            assert "sudo" in result.output

    def test_handles_distro_info_error(self):
        """Test that distro info errors are handled."""
        from apt_uu_config.apt.distro_info import DistroInfoError

        with patch("apt_uu_config.cli.show._load_system_state") as mock:
            mock.side_effect = DistroInfoError("Cannot determine distro")
            runner = CliRunner()
            result = runner.invoke(show, ["repos"])

            assert result.exit_code == 1
            assert "Error" in result.output

    def test_handles_uu_config_read_error(self):
        """Test that UU config read errors are handled."""
        from apt_uu_config.apt.uu_config_reader import UUConfigReadError

        with patch("apt_uu_config.cli.show._load_system_state") as mock:
            mock.side_effect = UUConfigReadError("Cannot read config")
            runner = CliRunner()
            result = runner.invoke(show, ["repos"])

            assert result.exit_code == 1
            assert "Error reading unattended-upgrades configuration" in result.output

    def test_handles_policy_parse_error(self):
        """Test that policy parse errors are handled."""
        from apt_uu_config.apt.policy_parser import PolicyParseError

        with patch("apt_uu_config.cli.show._load_system_state") as mock:
            mock.side_effect = PolicyParseError("Cannot parse policy")
            runner = CliRunner()
            result = runner.invoke(show, ["repos"])

            assert result.exit_code == 1
            assert "Error reading repository information" in result.output


class TestShowFormatOption:
    """Tests for --format option."""

    def test_format_option_with_repos(self, mock_system_state):
        """Test that --format option works with repos command."""
        runner = CliRunner()
        result = runner.invoke(show, ["repos", "--format", "json"])

        assert result.exit_code == 0
        assert result.output.strip().startswith("{")

    def test_format_option_with_patterns(self, mock_system_state):
        """Test that --format option works with patterns command."""
        runner = CliRunner()
        result = runner.invoke(show, ["patterns", "--format", "json"])

        assert result.exit_code == 0
        assert result.output.strip().startswith("{")

    def test_default_format_is_text(self, mock_system_state):
        """Test that default format is text."""
        runner = CliRunner()
        result = runner.invoke(show, ["repos"])

        assert result.exit_code == 0
        # Text output contains table formatting
        assert "Repositories" in result.output
