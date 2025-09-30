"""Read APT and unattended-upgrades configuration files."""

import re
from pathlib import Path
from typing import List

from apt_uu_config.models.origin import Origin


class ConfigReader:
    """
    Read APT configuration files related to unattended upgrades.

    This class handles reading:
    - /etc/apt/apt.conf.d/20auto-upgrades (global enable/disable)
    - /etc/apt/apt.conf.d/50unattended-upgrades (origin configuration)
    """

    AUTO_UPGRADES_PATH = Path("/etc/apt/apt.conf.d/20auto-upgrades")
    UNATTENDED_UPGRADES_PATH = Path("/etc/apt/apt.conf.d/50unattended-upgrades")

    def is_globally_enabled(self) -> bool:
        """
        Check if unattended upgrades are globally enabled.

        Returns:
            True if enabled, False otherwise
        """
        if not self.AUTO_UPGRADES_PATH.exists():
            return False

        try:
            content = self.AUTO_UPGRADES_PATH.read_text()

            # Look for APT::Periodic::Unattended-Upgrade "1";
            match = re.search(
                r'APT::Periodic::Unattended-Upgrade\s+"(\d+)";', content
            )
            if match:
                return match.group(1) == "1"

            return False
        except PermissionError:
            raise PermissionError(
                f"Permission denied reading {self.AUTO_UPGRADES_PATH}. "
                "Try running with sudo."
            )
        except Exception as e:
            raise RuntimeError(
                f"Error reading {self.AUTO_UPGRADES_PATH}: {e}"
            ) from e

    def get_enabled_origins(self) -> List[Origin]:
        """
        Get the list of origins enabled for unattended upgrades.

        Returns:
            List of Origin objects that are enabled
        """
        if not self.UNATTENDED_UPGRADES_PATH.exists():
            return []

        try:
            content = self.UNATTENDED_UPGRADES_PATH.read_text()
            return self._parse_origins_from_config(content)
        except PermissionError:
            raise PermissionError(
                f"Permission denied reading {self.UNATTENDED_UPGRADES_PATH}. "
                "Try running with sudo."
            )
        except Exception as e:
            raise RuntimeError(
                f"Error reading {self.UNATTENDED_UPGRADES_PATH}: {e}"
            ) from e

    def _parse_origins_from_config(self, content: str) -> List[Origin]:
        """
        Parse origin patterns from unattended-upgrades configuration.

        Args:
            content: The configuration file content

        Returns:
            List of Origin objects
        """
        origins: List[Origin] = []

        # Look for Unattended-Upgrade::Allowed-Origins or Origins-Pattern
        # Example patterns:
        # "${distro_id}:${distro_codename}-security";
        # "origin=Ubuntu,suite=jammy-security";

        # Find all origin/suite patterns
        # Pattern 1: "${distro_id}:${distro_codename}-security"
        pattern1 = re.finditer(
            r'"\$\{distro_id\}:\$\{distro_codename\}(-\w+)"', content
        )
        for match in pattern1:
            suite_suffix = match.group(1)
            # This will be resolved at runtime based on actual distro
            # For now, we'll create placeholder origins
            origins.append(
                Origin(
                    origin="${distro_id}",
                    suite="${distro_codename}" + suite_suffix,
                    enabled_for_uu=True,
                )
            )

        # Pattern 2: "origin=Ubuntu,suite=jammy-security"
        pattern2 = re.finditer(r'"origin=([^,]+),suite=([^"]+)"', content)
        for match in pattern2:
            origin_name = match.group(1)
            suite_name = match.group(2)
            origins.append(
                Origin(
                    origin=origin_name, suite=suite_name, enabled_for_uu=True
                )
            )

        # Pattern 3: Simple "${distro_id} ${distro_codename}-security"
        pattern3 = re.finditer(
            r'"\$\{distro_id\} \$\{distro_codename\}(-\w+)"', content
        )
        for match in pattern3:
            suite_suffix = match.group(1)
            origins.append(
                Origin(
                    origin="${distro_id}",
                    suite="${distro_codename}" + suite_suffix,
                    enabled_for_uu=True,
                )
            )

        return origins

    def get_config_backup_path(self, config_path: Path) -> Path:
        """
        Get the backup path for a configuration file.

        Args:
            config_path: The original config file path

        Returns:
            Path to the backup file
        """
        return config_path.with_suffix(config_path.suffix + ".bak")