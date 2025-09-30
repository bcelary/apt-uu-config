"""Distribution information helper.

This module provides functions to get distribution ID and codename,
which are used for variable substitution in unattended-upgrades patterns.
"""

import subprocess
from typing import Tuple


class DistroInfoError(Exception):
    """Raised when distribution information cannot be obtained."""

    pass


def get_distro_info() -> Tuple[str, str]:
    """
    Get distribution ID and codename using lsb_release.

    This uses the same method as unattended-upgrades itself.

    Returns:
        Tuple of (distro_id, distro_codename)
        Example: ("Ubuntu", "noble")

    Raises:
        DistroInfoError: If lsb_release is not available or fails
    """
    try:
        distro_id = subprocess.run(
            ["lsb_release", "-is"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        distro_codename = subprocess.run(
            ["lsb_release", "-cs"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        if not distro_id or not distro_codename:
            raise DistroInfoError("lsb_release returned empty values for distribution information")

        return distro_id, distro_codename

    except FileNotFoundError as e:
        raise DistroInfoError(
            "lsb_release command not found. Please install the lsb-release package: "
            "sudo apt install lsb-release"
        ) from e
    except subprocess.CalledProcessError as e:
        raise DistroInfoError(f"Failed to get distribution information: {e.stderr}") from e
