"""Unattended-upgrades configuration state model.

This module contains the model representing the complete unattended-upgrades
configuration state.
"""

from typing import List

from pydantic import BaseModel, Field

from apt_uu_config.models.repository import Repository
from apt_uu_config.models.uu_pattern import UUPattern


class UUConfig(BaseModel):
    """
    Represents the complete unattended-upgrades configuration state.

    This model separates the concerns:
    - globally_enabled: Is UU enabled at all?
    - patterns: What patterns are configured? (configuration data)
    - distro_id, distro_codename: Values for variable substitution

    It provides methods to answer questions like:
    - Which repositories are enabled for auto-updates?
    - Is a specific repository enabled?

    Note: This model does NOT store repository data. Repositories are passed
    in as arguments to query methods.
    """

    globally_enabled: bool = Field(
        default=False,
        description="Whether unattended-upgrades is globally enabled "
        "(from /etc/apt/apt.conf.d/20auto-upgrades)",
    )
    patterns: List[UUPattern] = Field(
        default_factory=list,
        description="List of patterns configured in Allowed-Origins or Origins-Pattern",
    )
    distro_id: str = Field(
        default="",
        description="Distribution ID for variable substitution (e.g., 'Ubuntu', 'Debian')",
    )
    distro_codename: str = Field(
        default="",
        description="Distribution codename for variable substitution (e.g., 'noble', 'bookworm')",
    )

    def get_enabled_repositories(self, all_repositories: List[Repository]) -> List[Repository]:
        """
        Get all repositories that match any configured pattern.

        Args:
            all_repositories: All available repositories on the system

        Returns:
            List of repositories that are enabled for unattended-upgrades
        """
        if not self.globally_enabled:
            return []

        enabled = []
        for repo in all_repositories:
            if self.is_repository_enabled(repo):
                enabled.append(repo)
        return enabled

    def is_repository_enabled(self, repo: Repository) -> bool:
        """
        Check if a specific repository is enabled for unattended-upgrades.

        A repository is enabled if:
        1. UU is globally enabled, AND
        2. At least one configured pattern matches the repository

        Args:
            repo: The repository to check

        Returns:
            True if the repository is enabled, False otherwise
        """
        if not self.globally_enabled:
            return False

        return any(
            pattern.matches(repo, self.distro_id, self.distro_codename) for pattern in self.patterns
        )

    def add_pattern(self, pattern: UUPattern) -> None:
        """
        Add a new pattern to the configuration.

        Args:
            pattern: The pattern to add
        """
        if pattern not in self.patterns:
            self.patterns.append(pattern)

    def remove_pattern(self, pattern: UUPattern) -> bool:
        """
        Remove a pattern from the configuration.

        Args:
            pattern: The pattern to remove

        Returns:
            True if pattern was removed, False if it wasn't in the list
        """
        try:
            self.patterns.remove(pattern)
            return True
        except ValueError:
            return False

    def get_patterns_for_section(self, section: str) -> List[UUPattern]:
        """
        Get all patterns for a specific configuration section.

        Args:
            section: "Allowed-Origins" or "Origins-Pattern"

        Returns:
            List of patterns in that section
        """
        return [p for p in self.patterns if p.section == section]

    def __str__(self) -> str:
        """Human-readable string representation."""
        status = "enabled" if self.globally_enabled else "disabled"
        return f"UUConfig(status={status}, patterns={len(self.patterns)})"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"UUConfig(globally_enabled={self.globally_enabled}, patterns={self.patterns!r})"
