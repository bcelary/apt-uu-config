"""Origin data model for APT repositories."""

from typing import Optional

from pydantic import BaseModel, Field


class Origin(BaseModel):
    """
    Represents an APT repository origin.

    An origin identifies a specific repository source and suite combination,
    such as "Ubuntu jammy-security" or "Google LLC stable".
    """

    origin: str = Field(
        ...,
        description="The origin name (e.g., 'Ubuntu', 'Google LLC')",
    )
    suite: str = Field(
        ...,
        description="The suite name (e.g., 'jammy-security', 'stable')",
    )
    codename: Optional[str] = Field(
        default=None,
        description="The codename (e.g., 'jammy', 'noble')",
    )
    label: Optional[str] = Field(
        default=None,
        description="The label (e.g., 'Ubuntu')",
    )
    archive: Optional[str] = Field(
        default=None,
        description="The archive name",
    )
    enabled_for_uu: bool = Field(
        default=False,
        description="Whether this origin is enabled for unattended upgrades",
    )

    def matches_pattern(self, pattern: str) -> bool:
        """
        Check if this origin matches the given pattern.

        Patterns can be:
        - Exact origin: "Ubuntu"
        - Origin:suite: "Ubuntu:jammy-security"
        - Wildcards: "*-security", "Ubuntu:*"

        Args:
            pattern: The pattern to match against

        Returns:
            True if the origin matches the pattern, False otherwise
        """
        pattern = pattern.strip()

        # Handle origin:suite pattern
        if ":" in pattern:
            origin_pattern, suite_pattern = pattern.split(":", 1)
            return self._matches_glob(self.origin, origin_pattern) and self._matches_glob(
                self.suite, suite_pattern
            )

        # Handle origin-only pattern
        return self._matches_glob(self.origin, pattern) or self._matches_glob(self.suite, pattern)

    def _matches_glob(self, value: str, pattern: str) -> bool:
        """
        Check if a value matches a glob pattern.

        Args:
            value: The value to check
            pattern: The pattern (may contain * wildcards)

        Returns:
            True if matches, False otherwise
        """
        if pattern == "*":
            return True

        if "*" not in pattern:
            return value.lower() == pattern.lower()

        # Convert glob pattern to regex-like matching
        import re

        regex_pattern = pattern.replace("*", ".*")
        return bool(re.match(f"^{regex_pattern}$", value, re.IGNORECASE))

    def to_uu_pattern(self) -> str:
        """
        Convert this origin to an unattended-upgrades pattern string.

        Returns:
            Pattern string like "origin=Ubuntu,suite=jammy-security"
        """
        parts = [f"origin={self.origin}"]

        if self.suite:
            parts.append(f"suite={self.suite}")

        return ",".join(parts)

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return f"{self.origin}:{self.suite}"
