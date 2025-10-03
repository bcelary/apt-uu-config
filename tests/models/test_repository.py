"""Tests for Repository model."""

from apt_uu_config.models.repository import Repository


def test_repository_creation_complete_metadata():
    """Test creating a Repository with complete metadata."""
    repo = Repository(
        origin="Ubuntu",
        suite="noble-security",
        codename="noble",
        label="Ubuntu",
        component="main",
        site="security.ubuntu.com",
        priority=500,
        url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
        architecture="amd64",
        version="24.04",
    )

    assert repo.origin == "Ubuntu"
    assert repo.suite == "noble-security"
    assert repo.codename == "noble"
    assert repo.label == "Ubuntu"
    assert repo.component == "main"
    assert repo.site == "security.ubuntu.com"
    assert repo.priority == 500
    assert repo.architecture == "amd64"
    assert repo.version == "24.04"


def test_repository_creation_minimal_metadata():
    """Test creating a Repository with minimal metadata."""
    repo = Repository(
        origin="Tailscale",
        codename="noble",
        site="pkgs.tailscale.com",
        priority=500,
        url="https://pkgs.tailscale.com/stable/ubuntu noble/main amd64 Packages",
    )

    assert repo.origin == "Tailscale"
    assert repo.suite is None  # Missing suite
    assert repo.codename == "noble"
    assert repo.site == "pkgs.tailscale.com"


def test_repository_str_representation():
    """Test string representation."""
    repo = Repository(
        origin="Brave Software",
        suite="stable",
        priority=500,
        url="https://brave-browser-apt-release.s3.brave.com/ stable/main amd64 Packages",
    )

    assert str(repo) == "Brave Software:stable"


def test_repository_str_with_missing_fields():
    """Test string representation when fields are missing."""
    repo = Repository(
        priority=500,
        url="https://example.com/repo stable/main amd64 Packages",
    )

    assert str(repo) == "Unknown:Unknown"


def test_repository_repr():
    """Test repr representation."""
    repo = Repository(
        origin="Docker",
        suite="noble",
        site="download.docker.com",
        priority=500,
        url="https://download.docker.com/linux/ubuntu noble/stable amd64 Packages",
    )

    assert repr(repo) == "Repository(origin='Docker', suite='noble', site='download.docker.com')"


def test_repository_with_special_characters():
    """Test repository with spaces and special characters in origin."""
    repo = Repository(
        origin="Google LLC",
        suite="stable",
        priority=500,
        url="https://dl.google.com/linux/chrome/deb/ stable/main amd64 Packages",
    )

    assert repo.origin == "Google LLC"
    assert str(repo) == "Google LLC:stable"


def test_format_compact_complete():
    """Test format_compact with all fields present."""
    repo = Repository(
        origin="Ubuntu",
        suite="noble-security",
        component="main",
        architecture="amd64",
        priority=500,
        url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
    )

    assert repo.format_compact() == "Ubuntu:noble-security/main [amd64]"


def test_format_compact_minimal():
    """Test format_compact with minimal fields."""
    repo = Repository(
        origin="Ubuntu",
        suite="noble",
        priority=500,
        url="http://archive.ubuntu.com/ubuntu noble amd64 Packages",
    )

    assert repo.format_compact() == "Ubuntu:noble [?]"


def test_format_compact_missing_origin():
    """Test format_compact when origin is missing."""
    repo = Repository(
        suite="stable",
        component="main",
        architecture="amd64",
        priority=500,
        url="https://example.com/repo stable/main amd64 Packages",
    )

    assert repo.format_compact() == "?:stable/main [amd64]"


def test_format_compact_long_origin_truncated():
    """Test format_compact with long origin that gets truncated."""
    long_origin = "obs://build.opensuse.org/home:npreining:debian-ubuntu-onedrive/xUbuntu_24.04"
    repo = Repository(
        origin=long_origin,
        suite="?",
        component="main",
        architecture="amd64",
        priority=500,
        url="https://download.opensuse.org/repositories/ ./ Packages",
    )

    result = repo.format_compact(truncate_origin=True)
    # Should truncate: keep first 15 + last 12 with ... in middle
    assert result == "obs://build.ope...Ubuntu_24.04:?/main [amd64]"


def test_format_compact_long_origin_no_truncate():
    """Test format_compact with long origin but truncation disabled."""
    long_origin = "obs://build.opensuse.org/home:npreining:debian-ubuntu-onedrive/xUbuntu_24.04"
    repo = Repository(
        origin=long_origin,
        suite="?",
        priority=500,
        url="https://download.opensuse.org/repositories/ ./ Packages",
    )

    result = repo.format_compact(truncate_origin=False)
    # Should NOT truncate
    assert result == f"{long_origin}:? [?]"


def test_format_full_basic():
    """Test format_full with basic repository."""
    repo = Repository(
        origin="Ubuntu",
        suite="noble-security",
        component="main",
        architecture="amd64",
        site="security.ubuntu.com",
        priority=500,
        url="http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages",
    )

    # When origin != site, site should be included
    assert repo.format_full() == "Ubuntu:noble-security/main [amd64] @security.ubuntu.com"


def test_format_full_same_origin_site():
    """Test format_full when origin and site are the same."""
    repo = Repository(
        origin="pkgs.tailscale.com",
        suite="stable",
        component="main",
        architecture="amd64",
        site="pkgs.tailscale.com",
        priority=500,
        url="https://pkgs.tailscale.com/stable/ubuntu stable/main amd64 Packages",
    )

    # When origin == site, site should be omitted
    assert repo.format_full() == "pkgs.tailscale.com:stable/main [amd64]"


def test_format_full_long_origin_truncated():
    """Test format_full with long origin that gets truncated."""
    long_origin = "obs://build.opensuse.org/home:npreining:debian-ubuntu-onedrive/xUbuntu_24.04"
    repo = Repository(
        origin=long_origin,
        suite="?",
        component="main",
        architecture="amd64",
        site="download.opensuse.org",
        priority=500,
        url="https://download.opensuse.org/repositories/ ./ Packages",
    )

    result = repo.format_full(truncate_origin=True)
    # Should truncate: keep first 15 + last 12 with ... in middle
    assert result == "obs://build.ope...Ubuntu_24.04:?/main [amd64] @download.opensuse.org"


def test_format_full_long_origin_no_truncate():
    """Test format_full with long origin but truncation disabled."""
    long_origin = "obs://build.opensuse.org/home:npreining:debian-ubuntu-onedrive/xUbuntu_24.04"
    repo = Repository(
        origin=long_origin,
        suite="?",
        site="download.opensuse.org",
        priority=500,
        url="https://download.opensuse.org/repositories/ ./ Packages",
    )

    result = repo.format_full(truncate_origin=False)
    # Should NOT truncate
    assert result == f"{long_origin}:? [?] @download.opensuse.org"


def test_format_full_no_site():
    """Test format_full when site is missing."""
    repo = Repository(
        origin="Ubuntu",
        suite="noble",
        component="main",
        architecture="amd64",
        priority=500,
        url="http://archive.ubuntu.com/ubuntu noble/main amd64 Packages",
    )

    assert repo.format_full() == "Ubuntu:noble/main [amd64]"
