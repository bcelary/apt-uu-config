"""Unattended-upgrades pattern matching logic.

This module contains pattern models and matching logic for determining which
repositories should receive automatic updates.
"""

import re
from typing import ClassVar, Literal, Optional

from pydantic import BaseModel, Field

from apt_uu_config.models.repository import Repository


class UUPattern(BaseModel):
    """
    A pattern that matches repositories for unattended-upgrades.

    This represents a configuration entry (a selector/filter), not a repository.
    Patterns are written to /etc/apt/apt.conf.d/50unattended-upgrades and
    determine which repositories get automatic updates.

    Two pattern formats exist:
    1. Allowed-Origins: Simple "origin:suite" format
       Example: "Ubuntu:noble-security"

    2. Origins-Pattern: Multi-field "key=value,key=value" format
       Example: "origin=Tailscale,site=pkgs.tailscale.com"
    """

    # Color/style constants for presentation
    SECTION_STYLE: ClassVar[str] = "dim bold white"
    PATTERN_STYLE: ClassVar[str] = "bold white"

    pattern_string: str = Field(
        description="The pattern as it appears in UU config. "
        "Examples: 'Ubuntu:noble-security', 'origin=Tailscale,site=pkgs.tailscale.com'",
    )
    section: Literal["Allowed-Origins", "Origins-Pattern"] = Field(
        description="Which UU config section this pattern belongs to",
    )

    def matches(self, repo: Repository, distro_id: str, distro_codename: str) -> bool:
        """
        Check if this pattern matches a given repository.

        Args:
            repo: The repository to match against
            distro_id: Distribution ID for variable substitution (e.g., 'Ubuntu')
            distro_codename: Distribution codename for variable substitution (e.g., 'noble')

        Returns:
            True if the pattern matches the repository, False otherwise
        """
        # Expand variables in pattern
        expanded_pattern = self._expand_variables(distro_id, distro_codename)

        if self.section == "Allowed-Origins":
            return self._matches_allowed_origins(repo, expanded_pattern)
        else:
            return self._matches_origins_pattern(repo, expanded_pattern)

    def _expand_variables(self, distro_id: str, distro_codename: str) -> str:
        """
        Expand ${distro_id} and ${distro_codename} variables in pattern.

        Args:
            distro_id: Value to substitute for ${distro_id}
            distro_codename: Value to substitute for ${distro_codename}

        Returns:
            Pattern string with variables expanded
        """
        pattern = self.pattern_string
        pattern = pattern.replace("${distro_id}", distro_id)
        pattern = pattern.replace("${distro_codename}", distro_codename)
        return pattern

    def _matches_allowed_origins(self, repo: Repository, pattern: str) -> bool:
        """
        Match Allowed-Origins format: "origin:suite" or "origin=X,suite=Y"

        Handles:
        - Simple colon format: "Ubuntu:noble-security"
        - Explicit key=value: "origin=Ubuntu,suite=noble-security"
        - Variables have already been expanded by caller

        Args:
            repo: Repository to match against
            pattern: Expanded pattern string (variables already substituted)

        Returns:
            True if pattern matches repository
        """
        pattern = pattern.strip()

        # Handle explicit key=value format
        if "=" in pattern:
            return self._match_key_value_pairs(repo, pattern)

        # Handle simple colon format: "origin:suite"
        if ":" in pattern:
            origin_pattern, suite_pattern = pattern.split(":", 1)
            return self._field_matches(repo.origin, origin_pattern) and self._field_matches(
                repo.suite, suite_pattern
            )

        # Fallback: match against origin or suite
        return self._field_matches(repo.origin, pattern) or self._field_matches(repo.suite, pattern)

    def _matches_origins_pattern(self, repo: Repository, pattern: str) -> bool:
        """
        Match Origins-Pattern format: "key=value,key=value,..."

        All specified fields must match. Omitted fields act as wildcards.
        Variables have already been expanded by caller.

        Args:
            repo: Repository to match against
            pattern: Expanded pattern string (variables already substituted)

        Returns:
            True if pattern matches repository

        Example: "origin=Tailscale,site=pkgs.tailscale.com"
        """
        return self._match_key_value_pairs(repo, pattern)

    def _match_key_value_pairs(self, repo: Repository, pattern: str) -> bool:
        """
        Match comma-separated key=value pairs against repository.

        Args:
            repo: Repository to match
            pattern: Pattern like "origin=Ubuntu,suite=noble-security"

        Returns:
            True if ALL specified fields match
        """
        # Parse pattern into field requirements
        requirements = {}
        for pair in pattern.split(","):
            pair = pair.strip()
            if "=" not in pair:
                continue
            key, value = pair.split("=", 1)
            key = key.strip()
            value = value.strip()
            requirements[key] = value

        # Map pattern keys to repository attributes
        field_mapping = {
            "origin": repo.origin,
            "o": repo.origin,
            "suite": repo.suite,
            "archive": repo.suite,
            "a": repo.suite,
            "codename": repo.codename,
            "n": repo.codename,
            "label": repo.label,
            "l": repo.label,
            "component": repo.component,
            "c": repo.component,
            "site": repo.site,
        }

        # Check if all requirements are satisfied
        for key, required_value in requirements.items():
            repo_value = field_mapping.get(key)
            if not self._field_matches(repo_value, required_value):
                return False

        return True

    def _field_matches(self, field_value: Optional[str], pattern: str) -> bool:
        """
        Check if a field value matches a pattern (with wildcard support).

        Args:
            field_value: The repository field value (can be None)
            pattern: The pattern to match against (may contain *)

        Returns:
            True if matches, False otherwise
        """
        # None field value matches empty pattern (e.g., "MEGA:" matches repos with no suite)
        if field_value is None:
            return pattern == ""

        # Wildcard: matches anything
        if pattern == "*":
            return True

        # Empty pattern matches empty string but not None (already handled above)
        if pattern == "":
            return field_value == ""

        # Exact match (case-insensitive)
        if "*" not in pattern:
            return field_value.lower() == pattern.lower()

        # Glob pattern with wildcards
        regex_pattern = pattern.replace("*", ".*")
        return bool(re.match(f"^{regex_pattern}$", field_value, re.IGNORECASE))

    @classmethod
    def suggest_for_repository(cls, repo: Repository) -> "UUPattern":
        """
        Suggest the best unattended-upgrades pattern for a repository.

        Uses a priority system:
        1. Simple "origin:suite" format (if both exist and suite is meaningful)
        2. "origin=X,codename=Y" (if origin exists but no suite)
        3. "origin=X,site=Y" (if origin exists and site available)
        4. "site=hostname" (fallback for minimal metadata)

        Args:
            repo: The repository to generate a pattern for

        Returns:
            Suggested UUPattern with explanation in pattern_string
        """
        # Priority 1: Simple origin:suite format
        if repo.origin and repo.suite and repo.suite.strip() and repo.suite != ".":
            return cls(
                pattern_string=f"{repo.origin}:{repo.suite}",
                section="Allowed-Origins",
            )

        # Priority 2: Origin + codename (when suite is missing/unclear)
        if repo.origin and repo.codename:
            return cls(
                pattern_string=f"origin={repo.origin},codename={repo.codename}",
                section="Origins-Pattern",
            )

        # Priority 3: Origin + site (provides specificity)
        if repo.origin and repo.site:
            return cls(
                pattern_string=f"origin={repo.origin},site={repo.site}",
                section="Origins-Pattern",
            )

        # Priority 4: Site only (fallback for minimal metadata)
        if repo.site:
            return cls(
                pattern_string=f"site={repo.site}",
                section="Origins-Pattern",
            )

        # Ultimate fallback: explicit origin+suite even if suite is unclear
        return cls(
            pattern_string=f"origin={repo.origin},suite={repo.suite}",
            section="Origins-Pattern",
        )

    def format(self, color: bool = False) -> str:
        """
        Format pattern for display.

        Args:
            color: If True, apply Rich markup for colored output

        Returns:
            Formatted pattern string like "Section: pattern"
        """
        section_str: str = self.section
        pattern_str: str = self.pattern_string

        if color:
            section_str = f"[{self.SECTION_STYLE}]{section_str}[/{self.SECTION_STYLE}]"
            pattern_str = f"[{self.PATTERN_STYLE}]{pattern_str}[/{self.PATTERN_STYLE}]"

        return f"{section_str}: {pattern_str}"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.section}: {self.pattern_string}"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"UUPattern(pattern_string={self.pattern_string!r}, section={self.section!r})"
