"""Detect and manage APT repository origins."""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from apt_uu_config.models.origin import Origin


class OriginDetector:
    """
    Detect repository origins from APT's internal data.

    This class reads from /var/lib/apt/lists/ to discover actual
    repository origins as APT sees them.
    """

    APT_LISTS_DIR = Path("/var/lib/apt/lists")

    def get_all_origins(self, enabled_origins: List[Origin]) -> List[Origin]:
        """
        Get all available repository origins.

        Args:
            enabled_origins: List of origins that are currently enabled

        Returns:
            List of all Origin objects with enabled_for_uu flag set appropriately
        """
        origins_dict: Dict[str, Origin] = {}

        # Try to use apt-cache policy to get repository information
        try:
            result = subprocess.run(
                ["apt-cache", "policy"],
                capture_output=True,
                text=True,
                check=True,
            )
            origins_from_policy = self._parse_apt_cache_policy(result.stdout)

            for origin in origins_from_policy:
                key = f"{origin.origin}:{origin.suite}"
                if key not in origins_dict:
                    # Check if this origin is in the enabled list
                    origin.enabled_for_uu = self._is_origin_enabled(origin, enabled_origins)
                    origins_dict[key] = origin

        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: try to parse Release files directly
            origins_from_files = self._get_origins_from_release_files()
            for origin in origins_from_files:
                key = f"{origin.origin}:{origin.suite}"
                if key not in origins_dict:
                    origin.enabled_for_uu = self._is_origin_enabled(origin, enabled_origins)
                    origins_dict[key] = origin

        return list(origins_dict.values())

    def _parse_apt_cache_policy(self, output: str) -> List[Origin]:
        """
        Parse output from apt-cache policy.

        Args:
            output: Output from apt-cache policy command

        Returns:
            List of Origin objects
        """
        origins = []
        current_release = {}

        for line in output.split("\n"):
            line = line.strip()

            # Look for "release" lines which contain origin info
            # Example: "release v=22.04,o=Ubuntu,a=jammy-security,n=jammy,l=Ubuntu"
            if line.startswith("release "):
                release_info = line.replace("release ", "")
                current_release = self._parse_release_info(release_info)

                if "o" in current_release and "a" in current_release:
                    origin = Origin(
                        origin=current_release["o"],
                        suite=current_release["a"],
                        codename=current_release.get("n"),
                        label=current_release.get("l"),
                    )
                    origins.append(origin)

        return origins

    def _parse_release_info(self, release_str: str) -> Dict[str, str]:
        """
        Parse release information string.

        Args:
            release_str: Release info string like "v=22.04,o=Ubuntu,a=jammy-security"

        Returns:
            Dictionary mapping short keys to values
        """
        info = {}
        for part in release_str.split(","):
            if "=" in part:
                key, value = part.split("=", 1)
                info[key.strip()] = value.strip()
        return info

    def _get_origins_from_release_files(self) -> List[Origin]:
        """
        Get origins by parsing Release files in /var/lib/apt/lists/.

        Returns:
            List of Origin objects
        """
        origins: List[Origin] = []

        if not self.APT_LISTS_DIR.exists():
            return origins

        # Look for *_Release files
        for release_file in self.APT_LISTS_DIR.glob("*_Release"):
            try:
                origin_data = self._parse_release_file(release_file)
                if origin_data:
                    origins.append(origin_data)
            except Exception:
                # Skip files we can't parse
                continue

        return origins

    def _parse_release_file(self, file_path: Path) -> Optional[Origin]:
        """
        Parse a single Release file.

        Args:
            file_path: Path to the Release file

        Returns:
            Origin object or None if parsing fails
        """
        try:
            content = file_path.read_text()
            origin = None
            suite = None
            codename = None
            label = None

            for line in content.split("\n"):
                if line.startswith("Origin:"):
                    origin = line.split(":", 1)[1].strip()
                elif line.startswith("Suite:"):
                    suite = line.split(":", 1)[1].strip()
                elif line.startswith("Codename:"):
                    codename = line.split(":", 1)[1].strip()
                elif line.startswith("Label:"):
                    label = line.split(":", 1)[1].strip()

            if origin and suite:
                return Origin(
                    origin=origin,
                    suite=suite,
                    codename=codename,
                    label=label,
                )

        except Exception:
            pass

        return None

    def _is_origin_enabled(self, origin: Origin, enabled_origins: List[Origin]) -> bool:
        """
        Check if an origin is in the enabled list.

        Args:
            origin: The origin to check
            enabled_origins: List of enabled origins

        Returns:
            True if the origin is enabled, False otherwise
        """
        for enabled in enabled_origins:
            # Handle variable substitution patterns
            if enabled.origin == "${distro_id}" or enabled.suite.startswith("${distro_codename}"):
                # Try to match against common patterns
                if self._matches_distro_pattern(origin, enabled):
                    return True
            # Exact match
            elif (
                enabled.origin.lower() == origin.origin.lower()
                and enabled.suite.lower() == origin.suite.lower()
            ):
                return True

        return False

    def _matches_distro_pattern(self, origin: Origin, pattern: Origin) -> bool:
        """
        Check if an origin matches a distro pattern like ${distro_codename}-security.

        Args:
            origin: The actual origin
            pattern: The pattern with variables

        Returns:
            True if matches, False otherwise
        """
        # Common distro origins
        distro_origins = ["Ubuntu", "Debian"]

        if origin.origin not in distro_origins:
            return False

        # Check if suite matches the pattern
        if pattern.suite.startswith("${distro_codename}"):
            suffix = pattern.suite.replace("${distro_codename}", "")
            # Check if origin's suite ends with the suffix
            if origin.codename and origin.suite.startswith(origin.codename):
                return origin.suite.endswith(suffix.lstrip("-"))

        return False
