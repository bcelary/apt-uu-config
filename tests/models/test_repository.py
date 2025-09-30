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
