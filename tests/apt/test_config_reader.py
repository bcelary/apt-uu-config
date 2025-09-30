"""Tests for ConfigReader."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from apt_uu_config.apt.config_reader import ConfigReader


@pytest.fixture
def temp_config_dir() -> Path:
    """Create a temporary config directory for testing."""
    with TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        apt_conf_d = config_dir / "apt.conf.d"
        apt_conf_d.mkdir(parents=True)
        yield config_dir


def test_parse_simple_origin_suite_format(temp_config_dir: Path) -> None:
    """Test parsing simple 'origin:suite' format (Pattern 4)."""
    config_path = temp_config_dir / "apt.conf.d" / "50unattended-upgrades"
    config_content = """
Unattended-Upgrade::Allowed-Origins {
    "Brave Software:stable";
    "Docker:noble";
    "Google LLC:stable";
};
"""
    config_path.write_text(config_content)

    reader = ConfigReader(config_dir=temp_config_dir)
    origins = reader.get_enabled_origins()

    # Should have 3 origins
    assert len(origins) == 3

    # Check Brave Software
    brave = next((o for o in origins if o.origin == "Brave Software"), None)
    assert brave is not None
    assert brave.suite == "stable"
    assert brave.enabled_for_uu is True

    # Check Docker
    docker = next((o for o in origins if o.origin == "Docker"), None)
    assert docker is not None
    assert docker.suite == "noble"
    assert docker.enabled_for_uu is True

    # Check Google LLC
    google = next((o for o in origins if o.origin == "Google LLC"), None)
    assert google is not None
    assert google.suite == "stable"
    assert google.enabled_for_uu is True


def test_parse_origin_suite_with_spaces(temp_config_dir: Path) -> None:
    """Test parsing origins with spaces in the name."""
    config_path = temp_config_dir / "apt.conf.d" / "50unattended-upgrades"
    config_content = """
Unattended-Upgrade::Allowed-Origins {
    "edge stable:stable";
    "code stable:stable";
};
"""
    config_path.write_text(config_content)

    reader = ConfigReader(config_dir=temp_config_dir)
    origins = reader.get_enabled_origins()

    assert len(origins) == 2

    edge = next((o for o in origins if o.origin == "edge stable"), None)
    assert edge is not None
    assert edge.suite == "stable"

    code = next((o for o in origins if o.origin == "code stable"), None)
    assert code is not None
    assert code.suite == "stable"


def test_parse_variable_patterns_still_work(temp_config_dir: Path) -> None:
    """Test that variable patterns (Pattern 1) still work correctly."""
    config_path = temp_config_dir / "apt.conf.d" / "50unattended-upgrades"
    config_content = """
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}:${distro_codename}-updates";
};
"""
    config_path.write_text(config_content)

    reader = ConfigReader(config_dir=temp_config_dir)
    origins = reader.get_enabled_origins()

    assert len(origins) == 2

    security = next((o for o in origins if o.suite == "${distro_codename}-security"), None)
    assert security is not None
    assert security.origin == "${distro_id}"

    updates = next((o for o in origins if o.suite == "${distro_codename}-updates"), None)
    assert updates is not None
    assert updates.origin == "${distro_id}"


def test_parse_origin_equals_format_still_works(temp_config_dir: Path) -> None:
    """Test that 'origin=X,suite=Y' format (Pattern 2) still works."""
    config_path = temp_config_dir / "apt.conf.d" / "50unattended-upgrades"
    config_content = """
Unattended-Upgrade::Allowed-Origins {
    "origin=Ubuntu,suite=jammy-security";
};
"""
    config_path.write_text(config_content)

    reader = ConfigReader(config_dir=temp_config_dir)
    origins = reader.get_enabled_origins()

    assert len(origins) == 1
    assert origins[0].origin == "Ubuntu"
    assert origins[0].suite == "jammy-security"


def test_parse_mixed_formats(temp_config_dir: Path) -> None:
    """Test parsing a config with multiple format types."""
    config_path = temp_config_dir / "apt.conf.d" / "50unattended-upgrades"
    config_content = """
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "origin=Ubuntu,suite=jammy-updates";
    "Brave Software:stable";
    "Docker:noble";
};
"""
    config_path.write_text(config_content)

    reader = ConfigReader(config_dir=temp_config_dir)
    origins = reader.get_enabled_origins()

    # Should have 4 origins
    assert len(origins) == 4

    # Check variable pattern
    distro = next((o for o in origins if o.origin == "${distro_id}"), None)
    assert distro is not None

    # Check origin= pattern
    ubuntu = next((o for o in origins if o.origin == "Ubuntu" and o.suite == "jammy-updates"), None)
    assert ubuntu is not None

    # Check simple origin:suite patterns
    brave = next((o for o in origins if o.origin == "Brave Software"), None)
    assert brave is not None

    docker = next((o for o in origins if o.origin == "Docker"), None)
    assert docker is not None


def test_parse_empty_config(temp_config_dir: Path) -> None:
    """Test parsing an empty or minimal config."""
    config_path = temp_config_dir / "apt.conf.d" / "50unattended-upgrades"
    config_content = """
Unattended-Upgrade::Allowed-Origins {
};
"""
    config_path.write_text(config_content)

    reader = ConfigReader(config_dir=temp_config_dir)
    origins = reader.get_enabled_origins()

    assert len(origins) == 0


def test_config_file_does_not_exist(temp_config_dir: Path) -> None:
    """Test behavior when config file doesn't exist."""
    reader = ConfigReader(config_dir=temp_config_dir)
    origins = reader.get_enabled_origins()

    assert len(origins) == 0
