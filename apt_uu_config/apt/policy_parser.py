"""APT policy parser.

This module parses the output of `apt-cache policy` to extract repository
metadata and create Repository objects.
"""

import subprocess
from typing import List, Optional
from urllib.parse import urlparse

from apt_uu_config.models.repository import Repository


class PolicyParseError(Exception):
    """Raised when apt-cache policy output cannot be parsed."""

    pass


def parse_apt_policy() -> List[Repository]:
    """
    Parse apt-cache policy output to get all repositories.

    Returns:
        List of Repository objects with metadata from apt-cache policy

    Raises:
        PolicyParseError: If apt-cache policy fails or output cannot be parsed
    """
    try:
        result = subprocess.run(
            ["apt-cache", "policy"],
            capture_output=True,
            text=True,
            check=True,
        )
        return _parse_policy_output(result.stdout)
    except FileNotFoundError as e:
        raise PolicyParseError("apt-cache command not found. Is APT installed?") from e
    except subprocess.CalledProcessError as e:
        raise PolicyParseError(f"apt-cache policy failed: {e.stderr}") from e


def _parse_policy_output(output: str) -> List[Repository]:
    """
    Parse the text output from apt-cache policy.

    Args:
        output: Raw output from apt-cache policy command

    Returns:
        List of Repository objects
    """
    repositories: List[Repository] = []
    lines = output.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for repository entry lines (start with priority number)
        # Example: " 500 http://archive.ubuntu.com/ubuntu noble/main amd64 Packages"
        if line.strip() and line[0].isspace() and len(line) > 1 and line.strip()[0].isdigit():
            repo = _parse_repository_entry(line, lines, i)
            if repo:
                repositories.append(repo)

        i += 1

    return repositories


def _parse_repository_entry(
    entry_line: str, all_lines: List[str], start_index: int
) -> Optional[Repository]:
    """
    Parse a single repository entry from apt-cache policy.

    Args:
        entry_line: The line with priority and URL
        all_lines: All lines from policy output
        start_index: Index of entry_line in all_lines

    Returns:
        Repository object or None if parsing fails
    """
    # Parse first line: priority and URL
    # Example: " 500 http://archive.ubuntu.com/ubuntu noble/main amd64 Packages"
    # Format: <priority> <url> <dist>/<component> <arch> <type>
    parts = entry_line.strip().split()
    if len(parts) < 2:
        return None

    try:
        priority = int(parts[0])
    except ValueError:
        return None

    # URL is the second element (index 1), not everything after priority
    url = parts[1]

    # Extract site from URL
    site = None
    try:
        parsed_url = urlparse(url)
        if parsed_url.netloc:
            site = parsed_url.netloc
        elif "://" in url:
            # Handle mirror:// URLs
            site = url.split("://")[1].split("/")[0]
    except Exception:
        pass

    # Look for release line (next non-empty line with metadata)
    # Example: "     release v=24.04,o=Ubuntu,a=noble,n=noble,l=Ubuntu,c=main,b=amd64"
    release_data = {}
    for i in range(start_index + 1, min(start_index + 5, len(all_lines))):
        line = all_lines[i].strip()
        # Stop if we hit the next repository entry (starts with digit)
        if line and line[0].isdigit():
            break
        if line.startswith("release "):
            release_data = _parse_release_line(line)
            break

    # Look for origin line (contains hostname)
    # Example: "     origin archive.ubuntu.com"
    if not site:
        for i in range(start_index + 1, min(start_index + 5, len(all_lines))):
            line = all_lines[i].strip()
            # Stop if we hit the next repository entry (starts with digit)
            if line and line[0].isdigit():
                break
            if line.startswith("origin "):
                site = line.split(maxsplit=1)[1] if len(line.split()) > 1 else None
                break

    return Repository(
        origin=release_data.get("o"),
        suite=release_data.get("a"),
        codename=release_data.get("n"),
        label=release_data.get("l"),
        component=release_data.get("c"),
        site=site,
        priority=priority,
        url=url,
        architecture=release_data.get("b"),
        version=release_data.get("v"),
    )


def _parse_release_line(line: str) -> dict[str, str]:
    """
    Parse a release line to extract field=value pairs.

    Args:
        line: Release line like "release v=24.04,o=Ubuntu,a=noble,..."

    Returns:
        Dictionary mapping field names to values
    """
    # Remove "release " prefix
    if line.startswith("release "):
        line = line[8:]

    data = {}
    # Split by comma, then by =
    for pair in line.split(","):
        pair = pair.strip()
        if "=" in pair:
            key, value = pair.split("=", 1)
            data[key.strip()] = value.strip()

    return data
