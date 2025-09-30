"""Tests for UUConfig model."""

from apt_uu_config.models.repository import Repository
from apt_uu_config.models.uu_config import UUConfig
from apt_uu_config.models.uu_pattern import UUPattern


def test_uu_config_creation_empty():
    """Test creating an empty UUConfig."""
    config = UUConfig()

    assert config.globally_enabled is False
    assert config.patterns == []


def test_uu_config_creation_with_patterns():
    """Test creating UUConfig with patterns."""
    patterns = [
        UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins"),
        UUPattern(pattern_string="Ubuntu:noble-updates", section="Allowed-Origins"),
    ]

    config = UUConfig(
        globally_enabled=True,
        patterns=patterns,
        distro_id="Ubuntu",
        distro_codename="noble",
    )

    assert config.globally_enabled is True
    assert len(config.patterns) == 2
    assert config.distro_id == "Ubuntu"
    assert config.distro_codename == "noble"


def test_is_repository_enabled_when_globally_disabled():
    """Test that repositories are not enabled when UU is globally disabled."""
    patterns = [
        UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins"),
    ]
    config = UUConfig(
        globally_enabled=False,
        patterns=patterns,
        distro_id="Ubuntu",
        distro_codename="noble",
    )

    repo = Repository(
        origin="Ubuntu",
        suite="noble-security",
        priority=500,
        url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
    )

    assert config.is_repository_enabled(repo) is False


def test_is_repository_enabled_matching_pattern():
    """Test repository is enabled when it matches a pattern."""
    patterns = [
        UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins"),
    ]
    config = UUConfig(
        globally_enabled=True,
        patterns=patterns,
        distro_id="Ubuntu",
        distro_codename="noble",
    )

    repo = Repository(
        origin="Ubuntu",
        suite="noble-security",
        priority=500,
        url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
    )

    assert config.is_repository_enabled(repo) is True


def test_is_repository_enabled_no_matching_pattern():
    """Test repository is not enabled when no pattern matches."""
    patterns = [
        UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins"),
    ]
    config = UUConfig(
        globally_enabled=True,
        patterns=patterns,
        distro_id="Ubuntu",
        distro_codename="noble",
    )

    repo = Repository(
        origin="Ubuntu",
        suite="noble-updates",
        priority=500,
        url="http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages",
    )

    assert config.is_repository_enabled(repo) is False


def test_get_enabled_repositories_when_globally_disabled():
    """Test get_enabled_repositories returns empty list when globally disabled."""
    patterns = [
        UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins"),
    ]
    config = UUConfig(
        globally_enabled=False,
        patterns=patterns,
        distro_id="Ubuntu",
        distro_codename="noble",
    )

    repos = [
        Repository(
            origin="Ubuntu",
            suite="noble-security",
            priority=500,
            url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
        ),
    ]

    enabled = config.get_enabled_repositories(repos)
    assert enabled == []


def test_get_enabled_repositories_filters_correctly():
    """Test get_enabled_repositories returns only matching repos."""
    patterns = [
        UUPattern(pattern_string="Ubuntu:*-security", section="Allowed-Origins"),
    ]
    config = UUConfig(
        globally_enabled=True,
        patterns=patterns,
        distro_id="Ubuntu",
        distro_codename="noble",
    )

    repos = [
        Repository(
            origin="Ubuntu",
            suite="noble-security",
            priority=500,
            url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
        ),
        Repository(
            origin="Ubuntu",
            suite="noble-updates",
            priority=500,
            url="http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages",
        ),
        Repository(
            origin="Ubuntu",
            suite="jammy-security",
            priority=500,
            url="http://security.ubuntu.com/ubuntu jammy-security/main amd64 Packages",
        ),
        Repository(
            origin="Debian",
            suite="bookworm-security",
            priority=500,
            url="http://security.debian.org/debian-security bookworm-security/main amd64 Packages",
        ),
    ]

    enabled = config.get_enabled_repositories(repos)

    assert len(enabled) == 2
    assert enabled[0].suite == "noble-security"
    assert enabled[1].suite == "jammy-security"


def test_get_enabled_repositories_multiple_patterns():
    """Test repository matching multiple patterns."""
    patterns = [
        UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins"),
        UUPattern(pattern_string="Brave Software:stable", section="Allowed-Origins"),
    ]
    config = UUConfig(
        globally_enabled=True,
        patterns=patterns,
        distro_id="Ubuntu",
        distro_codename="noble",
    )

    repos = [
        Repository(
            origin="Ubuntu",
            suite="noble-security",
            priority=500,
            url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
        ),
        Repository(
            origin="Brave Software",
            suite="stable",
            priority=500,
            url="https://brave-browser-apt-release.s3.brave.com/ stable/main amd64 Packages",
        ),
        Repository(
            origin="Docker",
            suite="noble",
            priority=500,
            url="https://download.docker.com/linux/ubuntu noble/stable amd64 Packages",
        ),
    ]

    enabled = config.get_enabled_repositories(repos)

    assert len(enabled) == 2
    assert enabled[0].origin == "Ubuntu"
    assert enabled[1].origin == "Brave Software"


def test_add_pattern():
    """Test adding a pattern to config."""
    config = UUConfig(globally_enabled=True, distro_id="Ubuntu", distro_codename="noble")

    pattern = UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins")
    config.add_pattern(pattern)

    assert len(config.patterns) == 1
    assert config.patterns[0] == pattern


def test_add_pattern_duplicate():
    """Test adding duplicate pattern does not create duplicates."""
    pattern = UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins")
    config = UUConfig(
        globally_enabled=True,
        patterns=[pattern],
        distro_id="Ubuntu",
        distro_codename="noble",
    )

    config.add_pattern(pattern)

    assert len(config.patterns) == 1


def test_remove_pattern_exists():
    """Test removing a pattern that exists."""
    pattern = UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins")
    config = UUConfig(
        globally_enabled=True,
        patterns=[pattern],
        distro_id="Ubuntu",
        distro_codename="noble",
    )

    result = config.remove_pattern(pattern)

    assert result is True
    assert len(config.patterns) == 0


def test_remove_pattern_not_exists():
    """Test removing a pattern that doesn't exist."""
    pattern1 = UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins")
    pattern2 = UUPattern(pattern_string="Ubuntu:noble-updates", section="Allowed-Origins")
    config = UUConfig(
        globally_enabled=True,
        patterns=[pattern1],
        distro_id="Ubuntu",
        distro_codename="noble",
    )

    result = config.remove_pattern(pattern2)

    assert result is False
    assert len(config.patterns) == 1


def test_get_patterns_for_section():
    """Test getting patterns for specific section."""
    patterns = [
        UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins"),
        UUPattern(pattern_string="Ubuntu:noble-updates", section="Allowed-Origins"),
        UUPattern(
            pattern_string="origin=Tailscale,site=pkgs.tailscale.com",
            section="Origins-Pattern",
        ),
    ]
    config = UUConfig(
        globally_enabled=True,
        patterns=patterns,
        distro_id="Ubuntu",
        distro_codename="noble",
    )

    allowed_origins = config.get_patterns_for_section("Allowed-Origins")
    origins_pattern = config.get_patterns_for_section("Origins-Pattern")

    assert len(allowed_origins) == 2
    assert len(origins_pattern) == 1
    assert origins_pattern[0].pattern_string == "origin=Tailscale,site=pkgs.tailscale.com"


def test_uu_config_str_representation():
    """Test string representation."""
    config = UUConfig(
        globally_enabled=True,
        patterns=[
            UUPattern(pattern_string="Ubuntu:noble-security", section="Allowed-Origins"),
        ],
    )

    assert str(config) == "UUConfig(status=enabled, patterns=1)"


def test_uu_config_str_disabled():
    """Test string representation when disabled."""
    config = UUConfig(globally_enabled=False)

    assert str(config) == "UUConfig(status=disabled, patterns=0)"
