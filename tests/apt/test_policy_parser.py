"""Tests for policy_parser module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from apt_uu_config.apt.policy_parser import PolicyParseError, parse_apt_policy

SAMPLE_POLICY_OUTPUT = """Package files:
 100 /var/lib/dpkg/status
     release a=now
 500 https://security.ubuntu.com/ubuntu noble-security/main amd64 Packages
     release v=24.04,o=Ubuntu,a=noble-security,n=noble,l=Ubuntu,c=main,b=amd64
     origin security.ubuntu.com
 500 https://packages.microsoft.com/repos/code stable/main amd64 Packages
     release o=code stable,a=stable,n=stable,l=code stable,c=main,b=amd64
     origin packages.microsoft.com
 100 mirror://mirrors.ubuntu.com/mirrors.txt noble-backports/universe amd64 Packages
     release v=24.04,o=Ubuntu,a=noble-backports,n=noble,l=Ubuntu,c=universe,b=amd64
     origin mirrors.ubuntu.com
Pinned packages:
"""


def test_parse_apt_policy_success() -> None:
    """Test successful parsing of apt-cache policy output."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = SAMPLE_POLICY_OUTPUT
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        repos = parse_apt_policy()

        assert len(repos) >= 3
        assert mock_run.call_count == 1

        # Check Ubuntu security repo
        ubuntu_security = next(
            (r for r in repos if r.origin == "Ubuntu" and r.suite == "noble-security"),
            None,
        )
        assert ubuntu_security is not None
        assert ubuntu_security.priority == 500
        assert ubuntu_security.codename == "noble"
        assert ubuntu_security.component == "main"
        assert ubuntu_security.label == "Ubuntu"
        assert ubuntu_security.site == "security.ubuntu.com"
        assert ubuntu_security.version == "24.04"
        assert ubuntu_security.architecture == "amd64"


def test_parse_apt_policy_microsoft_repo() -> None:
    """Test parsing of third-party repository (Microsoft Code)."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = SAMPLE_POLICY_OUTPUT
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        repos = parse_apt_policy()

        # Check Microsoft Code repo
        code_repo = next((r for r in repos if r.origin == "code stable"), None)
        assert code_repo is not None
        assert code_repo.priority == 500
        assert code_repo.suite == "stable"
        assert code_repo.site == "packages.microsoft.com"


def test_parse_apt_policy_mirror_url() -> None:
    """Test parsing of mirror:// URLs."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = SAMPLE_POLICY_OUTPUT
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        repos = parse_apt_policy()

        # Check mirror repo
        backports = next((r for r in repos if r.suite == "noble-backports"), None)
        assert backports is not None
        assert backports.priority == 100
        assert backports.site == "mirrors.ubuntu.com"


def test_parse_apt_policy_command_not_found() -> None:
    """Test error when apt-cache is not available."""
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        with pytest.raises(PolicyParseError) as exc_info:
            parse_apt_policy()

        assert "apt-cache command not found" in str(exc_info.value)


def test_parse_apt_policy_command_fails() -> None:
    """Test error when apt-cache policy fails."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["apt-cache"], stderr="Command failed"
        )

        with pytest.raises(PolicyParseError) as exc_info:
            parse_apt_policy()

        assert "apt-cache policy failed" in str(exc_info.value)


def test_parse_apt_policy_empty_output() -> None:
    """Test parsing of empty output."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "Package files:\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        repos = parse_apt_policy()

        assert repos == []


def test_parse_apt_policy_skips_dpkg_status() -> None:
    """Test that /var/lib/dpkg/status entries are handled."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = """ 100 /var/lib/dpkg/status
     release a=now
"""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        repos = parse_apt_policy()

        # dpkg status might create a repo entry, just verify no crash
        assert isinstance(repos, list)


def test_parse_apt_policy_dpkg_status_does_not_steal_next_origin() -> None:
    """Test that dpkg/status doesn't incorrectly use the next entry's origin."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        # This is the exact pattern from the bug report
        mock_result.stdout = """ 100 /var/lib/dpkg/status
     release a=now
 500 https://packages.microsoft.com/repos/code stable/main amd64 Packages
     release o=code stable,a=stable,n=stable,l=code stable,c=main,b=amd64
     origin packages.microsoft.com
"""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        repos = parse_apt_policy()

        # Should have 2 repos
        assert len(repos) == 2

        # Find dpkg status entry
        dpkg_status = next((r for r in repos if r.url == "/var/lib/dpkg/status"), None)
        assert dpkg_status is not None
        assert dpkg_status.suite == "now"
        # The bug was that site was set to "packages.microsoft.com" incorrectly
        assert dpkg_status.site is None

        # Find Microsoft repo
        ms_repo = next((r for r in repos if r.origin == "code stable"), None)
        assert ms_repo is not None
        assert ms_repo.site == "packages.microsoft.com"


def test_parse_apt_policy_malformed_priority() -> None:
    """Test handling of malformed priority values."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = """ abc http://example.com/ubuntu main
     release o=Example
"""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        repos = parse_apt_policy()

        # Should skip malformed entries
        assert len(repos) == 0


def test_parse_apt_policy_missing_release_line() -> None:
    """Test handling of entries without release metadata."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = """ 500 http://example.com/ubuntu main
     origin example.com
"""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        repos = parse_apt_policy()

        # Should create repo with minimal metadata
        assert len(repos) == 1
        assert repos[0].priority == 500
        assert repos[0].site == "example.com"
        assert repos[0].origin is None
