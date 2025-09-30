"""Tests for uu_config_reader module."""

from unittest.mock import MagicMock, patch

import pytest

from apt_uu_config.apt.uu_config_reader import UUConfigReadError, read_uu_config


@patch("apt_uu_config.apt.uu_config_reader.apt_pkg")
@patch("apt_uu_config.apt.uu_config_reader.get_distro_info")
def test_read_uu_config_success(mock_get_distro_info: MagicMock, mock_apt_pkg: MagicMock) -> None:
    """Test successful reading of UU configuration."""
    # Mock distro info
    mock_get_distro_info.return_value = ("Ubuntu", "noble")

    # Mock apt_pkg
    mock_config = MagicMock()
    mock_config.find.return_value = "1"
    mock_config.value_list.side_effect = [
        [
            "${distro_id}:${distro_codename}-security",
            "Brave Software:stable",
        ],
        [
            "origin=Tailscale,site=pkgs.tailscale.com",
        ],
    ]
    mock_apt_pkg.config = mock_config

    config = read_uu_config()

    assert config.globally_enabled is True
    assert config.distro_id == "Ubuntu"
    assert config.distro_codename == "noble"
    assert len(config.patterns) == 3

    # Check Allowed-Origins patterns
    allowed_patterns = config.get_patterns_for_section("Allowed-Origins")
    assert len(allowed_patterns) == 2
    assert allowed_patterns[0].pattern_string == "${distro_id}:${distro_codename}-security"
    assert allowed_patterns[1].pattern_string == "Brave Software:stable"

    # Check Origins-Pattern patterns
    origin_patterns = config.get_patterns_for_section("Origins-Pattern")
    assert len(origin_patterns) == 1
    assert origin_patterns[0].pattern_string == "origin=Tailscale,site=pkgs.tailscale.com"


@patch("apt_uu_config.apt.uu_config_reader.apt_pkg")
@patch("apt_uu_config.apt.uu_config_reader.get_distro_info")
def test_read_uu_config_globally_disabled(
    mock_get_distro_info: MagicMock, mock_apt_pkg: MagicMock
) -> None:
    """Test reading config when UU is globally disabled."""
    mock_get_distro_info.return_value = ("Ubuntu", "noble")

    mock_config = MagicMock()
    mock_config.find.return_value = "0"  # Disabled
    mock_config.value_list.side_effect = [[], []]
    mock_apt_pkg.config = mock_config

    config = read_uu_config()

    assert config.globally_enabled is False


@patch("apt_uu_config.apt.uu_config_reader.apt_pkg")
@patch("apt_uu_config.apt.uu_config_reader.get_distro_info")
def test_read_uu_config_empty_value(
    mock_get_distro_info: MagicMock, mock_apt_pkg: MagicMock
) -> None:
    """Test reading config when value is empty (default to disabled)."""
    mock_get_distro_info.return_value = ("Debian", "bookworm")

    mock_config = MagicMock()
    mock_config.find.return_value = "0"  # Empty defaults to "0"
    mock_config.value_list.side_effect = [[], []]
    mock_apt_pkg.config = mock_config

    config = read_uu_config()

    assert config.globally_enabled is False
    assert config.distro_id == "Debian"
    assert config.distro_codename == "bookworm"


@patch("apt_uu_config.apt.uu_config_reader.apt_pkg")
@patch("apt_uu_config.apt.uu_config_reader.get_distro_info")
def test_read_uu_config_no_patterns(
    mock_get_distro_info: MagicMock, mock_apt_pkg: MagicMock
) -> None:
    """Test reading config with no patterns configured."""
    mock_get_distro_info.return_value = ("Ubuntu", "noble")

    mock_config = MagicMock()
    mock_config.find.return_value = "1"
    mock_config.value_list.side_effect = [[], []]  # Empty pattern lists
    mock_apt_pkg.config = mock_config

    config = read_uu_config()

    assert config.globally_enabled is True
    assert len(config.patterns) == 0


@patch("apt_uu_config.apt.uu_config_reader.apt_pkg")
@patch("apt_uu_config.apt.uu_config_reader.get_distro_info")
def test_read_uu_config_distro_info_error(
    mock_get_distro_info: MagicMock, mock_apt_pkg: MagicMock
) -> None:
    """Test error when distro info cannot be obtained."""
    from apt_uu_config.apt.distro_info import DistroInfoError

    mock_get_distro_info.side_effect = DistroInfoError("lsb_release not found")

    with pytest.raises(UUConfigReadError) as exc_info:
        read_uu_config()

    assert "Failed to read unattended-upgrades configuration" in str(exc_info.value)


@patch("apt_uu_config.apt.uu_config_reader.apt_pkg")
@patch("apt_uu_config.apt.uu_config_reader.get_distro_info")
def test_read_uu_config_apt_pkg_init_called(
    mock_get_distro_info: MagicMock, mock_apt_pkg: MagicMock
) -> None:
    """Test that apt_pkg.init() is called."""
    mock_get_distro_info.return_value = ("Ubuntu", "noble")

    mock_config = MagicMock()
    mock_config.find.return_value = "1"
    mock_config.value_list.side_effect = [[], []]
    mock_apt_pkg.config = mock_config

    read_uu_config()

    mock_apt_pkg.init.assert_called_once()


@patch("apt_uu_config.apt.uu_config_reader.apt_pkg")
@patch("apt_uu_config.apt.uu_config_reader.get_distro_info")
def test_read_uu_config_preserves_variables(
    mock_get_distro_info: MagicMock, mock_apt_pkg: MagicMock
) -> None:
    """Test that variable substitution patterns are preserved as-is."""
    mock_get_distro_info.return_value = ("Ubuntu", "noble")

    mock_config = MagicMock()
    mock_config.find.return_value = "1"
    mock_config.value_list.side_effect = [
        [
            "${distro_id}:${distro_codename}",
            "${distro_id}ESM:${distro_codename}-infra-security",
        ],
        [],
    ]
    mock_apt_pkg.config = mock_config

    config = read_uu_config()

    # Verify patterns are stored with variables intact
    assert config.patterns[0].pattern_string == "${distro_id}:${distro_codename}"
    assert config.patterns[1].pattern_string == "${distro_id}ESM:${distro_codename}-infra-security"
