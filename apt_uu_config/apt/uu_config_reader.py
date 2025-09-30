"""Unattended-upgrades configuration reader.

This module reads unattended-upgrades configuration from APT using apt_pkg,
which gives us the merged view of all configuration files.
"""

from typing import List

import apt_pkg

from apt_uu_config.apt.distro_info import get_distro_info
from apt_uu_config.models.uu_config import UUConfig
from apt_uu_config.models.uu_pattern import UUPattern


class UUConfigReadError(Exception):
    """Raised when unattended-upgrades configuration cannot be read."""

    pass


def read_uu_config() -> UUConfig:
    """
    Read unattended-upgrades configuration from APT.

    Uses apt_pkg to read the merged configuration from all sources,
    including /etc/apt/apt.conf.d/ and any other configuration files.

    Returns:
        UUConfig object with current configuration state

    Raises:
        UUConfigReadError: If configuration cannot be read
    """
    try:
        # Initialize apt_pkg
        apt_pkg.init()

        # Get distro variables for variable substitution
        distro_id, distro_codename = get_distro_info()

        # Read globally_enabled flag
        # APT::Periodic::Unattended-Upgrade can be "0", "1", or empty
        uu_enabled = apt_pkg.config.find("APT::Periodic::Unattended-Upgrade", "0")
        globally_enabled = uu_enabled == "1"

        # Read pattern lists
        allowed_origins = apt_pkg.config.value_list("Unattended-Upgrade::Allowed-Origins")
        origins_pattern = apt_pkg.config.value_list("Unattended-Upgrade::Origins-Pattern")

        # Create UUPattern objects
        patterns: List[UUPattern] = []

        for pattern_string in allowed_origins:
            patterns.append(UUPattern(pattern_string=pattern_string, section="Allowed-Origins"))

        for pattern_string in origins_pattern:
            patterns.append(UUPattern(pattern_string=pattern_string, section="Origins-Pattern"))

        return UUConfig(
            globally_enabled=globally_enabled,
            patterns=patterns,
            distro_id=distro_id,
            distro_codename=distro_codename,
        )

    except Exception as e:
        raise UUConfigReadError(f"Failed to read unattended-upgrades configuration: {e}") from e
