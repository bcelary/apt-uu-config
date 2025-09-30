"""Parse APT sources.list files."""

import re
from pathlib import Path
from typing import List, Tuple


class SourcesParser:
    """
    Parse APT sources.list files to discover repositories.

    This parser reads:
    - /etc/apt/sources.list
    - /etc/apt/sources.list.d/*.list
    """

    SOURCES_LIST = Path("/etc/apt/sources.list")
    SOURCES_LIST_D = Path("/etc/apt/sources.list.d")

    def get_all_sources(self) -> List[Tuple[str, str, List[str]]]:
        """
        Get all APT sources from sources.list files.

        Returns:
            List of tuples: (url, distribution, components)
            Example: ('http://archive.ubuntu.com/ubuntu', 'jammy', ['main', 'restricted'])
        """
        sources = []

        # Parse main sources.list
        if self.SOURCES_LIST.exists():
            sources.extend(self._parse_sources_file(self.SOURCES_LIST))

        # Parse sources.list.d/*.list files
        if self.SOURCES_LIST_D.exists():
            for list_file in self.SOURCES_LIST_D.glob("*.list"):
                sources.extend(self._parse_sources_file(list_file))

        return sources

    def _parse_sources_file(
        self, file_path: Path
    ) -> List[Tuple[str, str, List[str]]]:
        """
        Parse a single sources.list file.

        Args:
            file_path: Path to the sources.list file

        Returns:
            List of tuples: (url, distribution, components)
        """
        sources = []

        try:
            content = file_path.read_text()

            for line in content.split("\n"):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Parse deb or deb-src lines
                # Format: deb [options] url distribution components...
                match = re.match(
                    r"^(deb|deb-src)\s+(?:\[.*?\]\s+)?(\S+)\s+(\S+)\s+(.*?)$",
                    line,
                )
                if match:
                    url = match.group(2)
                    distribution = match.group(3)
                    components = match.group(4).split()

                    sources.append((url, distribution, components))

        except PermissionError:
            raise PermissionError(
                f"Permission denied reading {file_path}. Try running with sudo."
            )
        except Exception:
            # Log warning but don't fail - some files might be malformed
            pass

        return sources