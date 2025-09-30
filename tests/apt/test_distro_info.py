"""Tests for distro_info module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from apt_uu_config.apt.distro_info import DistroInfoError, get_distro_info


def test_get_distro_info_success() -> None:
    """Test successful retrieval of distro info."""
    with patch("subprocess.run") as mock_run:
        # Mock lsb_release -is
        mock_is = MagicMock()
        mock_is.stdout = "Ubuntu\n"
        mock_is.returncode = 0

        # Mock lsb_release -cs
        mock_cs = MagicMock()
        mock_cs.stdout = "noble\n"
        mock_cs.returncode = 0

        mock_run.side_effect = [mock_is, mock_cs]

        distro_id, distro_codename = get_distro_info()

        assert distro_id == "Ubuntu"
        assert distro_codename == "noble"
        assert mock_run.call_count == 2


def test_get_distro_info_debian() -> None:
    """Test retrieval of Debian distro info."""
    with patch("subprocess.run") as mock_run:
        mock_is = MagicMock()
        mock_is.stdout = "Debian"
        mock_is.returncode = 0

        mock_cs = MagicMock()
        mock_cs.stdout = "bookworm"
        mock_cs.returncode = 0

        mock_run.side_effect = [mock_is, mock_cs]

        distro_id, distro_codename = get_distro_info()

        assert distro_id == "Debian"
        assert distro_codename == "bookworm"


def test_get_distro_info_lsb_release_not_found() -> None:
    """Test error when lsb_release is not installed."""
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        with pytest.raises(DistroInfoError) as exc_info:
            get_distro_info()

        assert "lsb_release command not found" in str(exc_info.value)
        assert "sudo apt install lsb-release" in str(exc_info.value)


def test_get_distro_info_command_fails() -> None:
    """Test error when lsb_release command fails."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["lsb_release"], stderr="Command failed"
        )

        with pytest.raises(DistroInfoError) as exc_info:
            get_distro_info()

        assert "Failed to get distribution information" in str(exc_info.value)


def test_get_distro_info_empty_output() -> None:
    """Test error when lsb_release returns empty values."""
    with patch("subprocess.run") as mock_run:
        mock_is = MagicMock()
        mock_is.stdout = ""
        mock_is.returncode = 0

        mock_cs = MagicMock()
        mock_cs.stdout = "noble"
        mock_cs.returncode = 0

        mock_run.side_effect = [mock_is, mock_cs]

        with pytest.raises(DistroInfoError) as exc_info:
            get_distro_info()

        assert "returned empty values" in str(exc_info.value)


def test_get_distro_info_strips_whitespace() -> None:
    """Test that output is properly stripped."""
    with patch("subprocess.run") as mock_run:
        mock_is = MagicMock()
        mock_is.stdout = "  Ubuntu  \n"
        mock_is.returncode = 0

        mock_cs = MagicMock()
        mock_cs.stdout = "\nnoble  "
        mock_cs.returncode = 0

        mock_run.side_effect = [mock_is, mock_cs]

        distro_id, distro_codename = get_distro_info()

        assert distro_id == "Ubuntu"
        assert distro_codename == "noble"
