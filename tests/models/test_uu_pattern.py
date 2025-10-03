"""Tests for UUPattern model."""

from apt_uu_config.models.repository import Repository
from apt_uu_config.models.uu_pattern import UUPattern


# Test pattern matching - Allowed-Origins format
def test_pattern_matches_simple_colon_format():
    """Test matching with simple 'origin:suite' format."""
    pattern = UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins")

    repo_match = Repository(
        origin="Ubuntu",
        suite="noble-security",
        priority=500,
        url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
    )

    repo_no_match = Repository(
        origin="Ubuntu",
        suite="noble-updates",
        priority=500,
        url="http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages",
    )

    assert pattern.matches(repo_match, "Ubuntu", "noble") is True
    assert pattern.matches(repo_no_match, "Ubuntu", "noble") is False


def test_pattern_matches_explicit_key_value():
    """Test matching with explicit 'origin=X,suite=Y' format."""
    pattern = UUPattern(
        pattern_string="origin=Ubuntu,suite=noble-security", section="Allowed-Origins"
    )

    repo = Repository(
        origin="Ubuntu",
        suite="noble-security",
        priority=500,
        url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
    )

    assert pattern.matches(repo, "Ubuntu", "noble") is True


def test_pattern_matches_case_insensitive():
    """Test that pattern matching is case-insensitive."""
    pattern = UUPattern(pattern_string="ubuntu:NOBLE-SECURITY", section="Allowed-Origins")

    repo = Repository(
        origin="Ubuntu",
        suite="noble-security",
        priority=500,
        url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
    )

    assert pattern.matches(repo, "Ubuntu", "noble") is True


# Test pattern matching - Origins-Pattern format
def test_pattern_matches_origins_pattern_multi_field():
    """Test matching with Origins-Pattern multi-field format."""
    pattern = UUPattern(
        pattern_string="origin=Tailscale,site=pkgs.tailscale.com",
        section="Origins-Pattern",
    )

    repo_match = Repository(
        origin="Tailscale",
        codename="noble",
        site="pkgs.tailscale.com",
        priority=500,
        url="https://pkgs.tailscale.com/stable/ubuntu noble/main amd64 Packages",
    )

    repo_no_match = Repository(
        origin="Tailscale",
        codename="noble",
        site="different.example.com",
        priority=500,
        url="https://different.example.com/stable/ubuntu noble/main amd64 Packages",
    )

    assert pattern.matches(repo_match, "Ubuntu", "noble") is True
    assert pattern.matches(repo_no_match, "Ubuntu", "noble") is False


def test_pattern_matches_site_only():
    """Test matching with site-only pattern."""
    pattern = UUPattern(
        pattern_string="site=download.opensuse.org",
        section="Origins-Pattern",
    )

    repo = Repository(
        origin="OneDrive",
        site="download.opensuse.org",
        priority=500,
        url="https://download.opensuse.org/repositories/home:/foo/ ./",
    )

    assert pattern.matches(repo, "Ubuntu", "noble") is True


def test_pattern_matches_with_field_aliases():
    """Test matching with field aliases (o, a, n, l, c)."""
    pattern = UUPattern(
        pattern_string="o=Ubuntu,a=noble-security,c=main",
        section="Origins-Pattern",
    )

    repo = Repository(
        origin="Ubuntu",
        suite="noble-security",
        component="main",
        priority=500,
        url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
    )

    assert pattern.matches(repo, "Ubuntu", "noble") is True


# Test wildcard matching
def test_pattern_matches_wildcard_all():
    """Test matching with wildcard '*' (matches anything)."""
    pattern = UUPattern(pattern_string="origin=*", section="Origins-Pattern")

    repo = Repository(
        origin="AnyOrigin",
        suite="stable",
        priority=500,
        url="https://example.com/repo stable/main amd64 Packages",
    )

    assert pattern.matches(repo, "Ubuntu", "noble") is True


def test_pattern_matches_wildcard_suffix():
    """Test matching with wildcard suffix pattern."""
    pattern = UUPattern(pattern_string="Ubuntu:*-security", section="Allowed-Origins")

    repo_noble = Repository(
        origin="Ubuntu",
        suite="noble-security",
        priority=500,
        url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
    )

    repo_jammy = Repository(
        origin="Ubuntu",
        suite="jammy-security",
        priority=500,
        url="http://security.ubuntu.com/ubuntu jammy-security/main amd64 Packages",
    )

    repo_updates = Repository(
        origin="Ubuntu",
        suite="noble-updates",
        priority=500,
        url="http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages",
    )

    assert pattern.matches(repo_noble, "Ubuntu", "noble") is True
    assert pattern.matches(repo_jammy, "Ubuntu", "noble") is True
    assert pattern.matches(repo_updates, "Ubuntu", "noble") is False


def test_pattern_matches_empty_suite():
    """Test matching with empty suite pattern (e.g., 'MEGA:')."""
    pattern = UUPattern(pattern_string="MEGA:", section="Allowed-Origins")

    # Repository with None suite (common for flat repos)
    repo_none_suite = Repository(
        origin="MEGA",
        suite=None,
        site="mega.nz",
        priority=500,
        url="https://mega.nz/linux/repo/xUbuntu_24.04 ./ Packages",
    )

    # Repository with empty string suite
    repo_empty_suite = Repository(
        origin="MEGA",
        suite="",
        site="mega.nz",
        priority=500,
        url="https://mega.nz/linux/repo/xUbuntu_24.04 ./ Packages",
    )

    # Repository with actual suite (should not match)
    repo_with_suite = Repository(
        origin="MEGA",
        suite="stable",
        site="mega.nz",
        priority=500,
        url="https://mega.nz/linux/repo stable/main amd64 Packages",
    )

    assert pattern.matches(repo_none_suite, "Ubuntu", "noble") is True
    assert pattern.matches(repo_empty_suite, "Ubuntu", "noble") is True
    assert pattern.matches(repo_with_suite, "Ubuntu", "noble") is False


def test_pattern_matches_empty_component():
    """Test matching with empty component pattern."""
    pattern = UUPattern(pattern_string="o=MEGA,c=", section="Origins-Pattern")

    # Repository with None component
    repo_none_component = Repository(
        origin="MEGA",
        component=None,
        site="mega.nz",
        priority=500,
        url="https://mega.nz/linux/repo/xUbuntu_24.04 ./ Packages",
    )

    # Repository with empty string component (c= in release line)
    repo_empty_component = Repository(
        origin="MEGA",
        component="",
        site="mega.nz",
        priority=500,
        url="https://mega.nz/linux/repo/xUbuntu_24.04 ./ Packages",
    )

    # Repository with actual component (should not match)
    repo_with_component = Repository(
        origin="MEGA",
        component="main",
        site="mega.nz",
        priority=500,
        url="https://mega.nz/linux/repo stable/main amd64 Packages",
    )

    assert pattern.matches(repo_none_component, "Ubuntu", "noble") is True
    assert pattern.matches(repo_empty_component, "Ubuntu", "noble") is True
    assert pattern.matches(repo_with_component, "Ubuntu", "noble") is False


# Test pattern suggestion
def test_suggest_pattern_complete_metadata():
    """Test pattern suggestion with complete metadata."""
    repo = Repository(
        origin="Brave Software",
        suite="stable",
        codename="stable",
        site="brave-browser-apt-release.s3.brave.com",
        priority=500,
        url="https://brave-browser-apt-release.s3.brave.com/ stable/main amd64 Packages",
    )

    pattern = UUPattern.suggest_for_repository(repo)

    assert pattern.pattern_string == "Brave Software:stable"
    assert pattern.section == "Allowed-Origins"


def test_suggest_pattern_missing_suite():
    """Test pattern suggestion when suite is missing."""
    repo = Repository(
        origin="Tailscale",
        codename="noble",
        site="pkgs.tailscale.com",
        priority=500,
        url="https://pkgs.tailscale.com/stable/ubuntu noble/main amd64 Packages",
    )

    pattern = UUPattern.suggest_for_repository(repo)

    assert pattern.pattern_string == "origin=Tailscale,codename=noble"
    assert pattern.section == "Origins-Pattern"


def test_suggest_pattern_dot_suite():
    """Test pattern suggestion when suite is just a dot."""
    repo = Repository(
        origin="OneDrive",
        suite=".",
        codename="xUbuntu_24.04",
        site="download.opensuse.org",
        priority=500,
        url="https://download.opensuse.org/repositories/home:/foo/ ./",
    )

    pattern = UUPattern.suggest_for_repository(repo)

    # Dot is meaningless, should fall through to origin+codename
    assert pattern.pattern_string == "origin=OneDrive,codename=xUbuntu_24.04"
    assert pattern.section == "Origins-Pattern"


def test_suggest_pattern_no_codename():
    """Test pattern suggestion when codename is missing but site exists."""
    repo = Repository(
        origin="CustomRepo",
        site="repo.example.com",
        priority=500,
        url="https://repo.example.com/debian/ stable/main amd64 Packages",
    )

    pattern = UUPattern.suggest_for_repository(repo)

    assert pattern.pattern_string == "origin=CustomRepo,site=repo.example.com"
    assert pattern.section == "Origins-Pattern"


def test_suggest_pattern_site_only():
    """Test pattern suggestion with minimal metadata (site only)."""
    repo = Repository(
        site="minimal.example.com",
        priority=500,
        url="https://minimal.example.com/repo/ ./",
    )

    pattern = UUPattern.suggest_for_repository(repo)

    assert pattern.pattern_string == "site=minimal.example.com"
    assert pattern.section == "Origins-Pattern"


# Test string representations
def test_pattern_str_representation():
    """Test string representation of pattern."""
    pattern = UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins")

    assert str(pattern) == "Allowed-Origins: Ubuntu:noble-security"


def test_pattern_repr():
    """Test repr representation of pattern."""
    pattern = UUPattern(
        pattern_string="origin=Tailscale,site=pkgs.tailscale.com",
        section="Origins-Pattern",
    )

    assert (
        repr(pattern)
        == "UUPattern(pattern_string='origin=Tailscale,site=pkgs.tailscale.com', section='Origins-Pattern')"
    )


# Test format method
def test_pattern_format_without_color():
    """Test format method without color markup."""
    pattern = UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins")

    assert pattern.format(color=False) == "Allowed-Origins: Ubuntu:noble-security"


def test_pattern_format_with_color():
    """Test format method with color markup."""
    pattern = UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins")

    result = pattern.format(color=True)
    # Check that color tags are present using class constants
    assert f"[{UUPattern.SECTION_STYLE}]Allowed-Origins[/{UUPattern.SECTION_STYLE}]" in result
    assert f"[{UUPattern.PATTERN_STYLE}]Ubuntu:noble-security[/{UUPattern.PATTERN_STYLE}]" in result
    assert ": " in result


def test_pattern_format_origins_pattern_with_color():
    """Test format method for Origins-Pattern section with color."""
    pattern = UUPattern(
        pattern_string="origin=Tailscale,site=pkgs.tailscale.com",
        section="Origins-Pattern",
    )

    result = pattern.format(color=True)
    # Check that color tags are present using class constants
    assert f"[{UUPattern.SECTION_STYLE}]Origins-Pattern[/{UUPattern.SECTION_STYLE}]" in result
    assert (
        f"[{UUPattern.PATTERN_STYLE}]origin=Tailscale,site=pkgs.tailscale.com[/{UUPattern.PATTERN_STYLE}]"
        in result
    )


# Test variable-based pattern suggestion
def test_suggest_pattern_variable_based_security():
    """Test pattern suggestion generates variable-based pattern for distro security repos."""
    repo = Repository(
        origin="Ubuntu",
        suite="noble-security",
        codename="noble",
        site="security.ubuntu.com",
        priority=500,
        url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
    )

    pattern = UUPattern.suggest_for_repository(repo, distro_id="Ubuntu", distro_codename="noble")

    assert pattern.pattern_string == "${distro_id}:${distro_codename}-security"
    assert pattern.section == "Allowed-Origins"


def test_suggest_pattern_variable_based_updates():
    """Test pattern suggestion generates variable-based pattern for distro updates repos."""
    repo = Repository(
        origin="Ubuntu",
        suite="noble-updates",
        codename="noble",
        site="archive.ubuntu.com",
        priority=500,
        url="http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages",
    )

    pattern = UUPattern.suggest_for_repository(repo, distro_id="Ubuntu", distro_codename="noble")

    assert pattern.pattern_string == "${distro_id}:${distro_codename}-updates"
    assert pattern.section == "Allowed-Origins"


def test_suggest_pattern_variable_based_backports():
    """Test pattern suggestion generates variable-based pattern for distro backports repos."""
    repo = Repository(
        origin="Ubuntu",
        suite="noble-backports",
        codename="noble",
        site="archive.ubuntu.com",
        priority=500,
        url="http://archive.ubuntu.com/ubuntu noble-backports/main amd64 Packages",
    )

    pattern = UUPattern.suggest_for_repository(repo, distro_id="Ubuntu", distro_codename="noble")

    assert pattern.pattern_string == "${distro_id}:${distro_codename}-backports"
    assert pattern.section == "Allowed-Origins"


def test_suggest_pattern_variable_based_base():
    """Test pattern suggestion generates variable-based pattern for base distro repos."""
    repo = Repository(
        origin="Ubuntu",
        suite="noble",
        codename="noble",
        site="archive.ubuntu.com",
        priority=500,
        url="http://archive.ubuntu.com/ubuntu noble/main amd64 Packages",
    )

    pattern = UUPattern.suggest_for_repository(repo, distro_id="Ubuntu", distro_codename="noble")

    assert pattern.pattern_string == "${distro_id}:${distro_codename}"
    assert pattern.section == "Allowed-Origins"


def test_suggest_pattern_variable_based_case_insensitive():
    """Test that variable-based patterns work with different case."""
    repo = Repository(
        origin="ubuntu",  # lowercase origin
        suite="noble-security",
        codename="noble",
        site="security.ubuntu.com",
        priority=500,
        url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
    )

    pattern = UUPattern.suggest_for_repository(repo, distro_id="Ubuntu", distro_codename="noble")

    # Should still match and generate variable pattern
    assert pattern.pattern_string == "${distro_id}:${distro_codename}-security"
    assert pattern.section == "Allowed-Origins"


def test_suggest_pattern_non_distro_repo_no_variables():
    """Test that non-distribution repos don't get variable-based patterns."""
    repo = Repository(
        origin="Brave Software",
        suite="stable",
        codename="stable",
        site="brave-browser-apt-release.s3.brave.com",
        priority=500,
        url="https://brave-browser-apt-release.s3.brave.com/ stable/main amd64 Packages",
    )

    pattern = UUPattern.suggest_for_repository(repo, distro_id="Ubuntu", distro_codename="noble")

    # Should use hardcoded pattern, not variables
    assert pattern.pattern_string == "Brave Software:stable"
    assert pattern.section == "Allowed-Origins"


def test_suggest_pattern_no_distro_info_fallback():
    """Test that pattern suggestion falls back without distro_id/codename."""
    repo = Repository(
        origin="Ubuntu",
        suite="noble-security",
        codename="noble",
        site="security.ubuntu.com",
        priority=500,
        url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
    )

    # Don't provide distro_id/codename
    pattern = UUPattern.suggest_for_repository(repo)

    # Should fall back to hardcoded pattern
    assert pattern.pattern_string == "Ubuntu:noble-security"
    assert pattern.section == "Allowed-Origins"


def test_suggest_pattern_debian_variable_based():
    """Test variable-based pattern generation for Debian repos."""
    repo = Repository(
        origin="Debian",
        suite="bookworm-security",
        codename="bookworm",
        site="security.debian.org",
        priority=500,
        url="http://security.debian.org/debian-security bookworm-security/main amd64 Packages",
    )

    pattern = UUPattern.suggest_for_repository(repo, distro_id="Debian", distro_codename="bookworm")

    assert pattern.pattern_string == "${distro_id}:${distro_codename}-security"
    assert pattern.section == "Allowed-Origins"


def test_suggest_pattern_ubuntu_esm_apps():
    """Test variable-based pattern generation for Ubuntu ESM Apps repos."""
    repo = Repository(
        origin="UbuntuESMApps",
        suite="noble-apps-security",
        codename="noble",
        site="esm.ubuntu.com",
        priority=500,
        url="https://esm.ubuntu.com/apps/ubuntu noble-apps-security/main amd64 Packages",
    )

    pattern = UUPattern.suggest_for_repository(repo, distro_id="Ubuntu", distro_codename="noble")

    assert pattern.pattern_string == "${distro_id}ESMApps:${distro_codename}-apps-security"
    assert pattern.section == "Allowed-Origins"


def test_suggest_pattern_ubuntu_esm_infra():
    """Test variable-based pattern generation for Ubuntu ESM Infrastructure repos."""
    repo = Repository(
        origin="UbuntuESM",
        suite="noble-infra-security",
        codename="noble",
        site="esm.ubuntu.com",
        priority=500,
        url="https://esm.ubuntu.com/infra/ubuntu noble-infra-security/main amd64 Packages",
    )

    pattern = UUPattern.suggest_for_repository(repo, distro_id="Ubuntu", distro_codename="noble")

    assert pattern.pattern_string == "${distro_id}ESM:${distro_codename}-infra-security"
    assert pattern.section == "Allowed-Origins"


def test_suggest_pattern_codename_in_middle_of_suite():
    """Test that codename can be matched anywhere in the suite."""
    repo = Repository(
        origin="Ubuntu",
        suite="proposed-noble-testing",
        codename="noble",
        site="archive.ubuntu.com",
        priority=500,
        url="http://archive.ubuntu.com/ubuntu proposed-noble-testing/main amd64 Packages",
    )

    pattern = UUPattern.suggest_for_repository(repo, distro_id="Ubuntu", distro_codename="noble")

    assert pattern.pattern_string == "${distro_id}:proposed-${distro_codename}-testing"
    assert pattern.section == "Allowed-Origins"
