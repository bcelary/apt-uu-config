"""APT repository data model.

This module contains the pure data model for APT repositories as they exist
on the system. It contains no business logic about unattended-upgrades.
"""

from typing import Optional

from pydantic import BaseModel, Field


class Repository(BaseModel):
    """
    Represents a single APT repository with its metadata.

    This is pure data from apt-cache policy - it represents what exists on
    the system, not configuration decisions about what to auto-update.

    Metadata fields come from the repository's Release file:
    - origin (o=): Who provides the repository
    - suite/archive (a=): What channel/pocket (e.g., stable, noble-security)
    - codename (n=): Distribution release name (e.g., noble, jammy)
    - label (l=): Repository label/purpose
    - component (c=): Licensing subdivision (e.g., main, universe)
    - site: Repository hostname (derived from URL)

    Example from apt-cache policy:
        500 http://archive.ubuntu.com/ubuntu noble/main amd64 Packages
            release v=24.04,o=Ubuntu,a=noble,n=noble,l=Ubuntu,c=main,b=amd64
    """

    # Core metadata fields (from Release file)
    origin: Optional[str] = Field(
        default=None,
        description="Repository origin/provider (o= field). Examples: 'Ubuntu', 'Brave Software'",
    )
    suite: Optional[str] = Field(
        default=None,
        description="Suite/archive name (a= field). Examples: 'stable', 'noble-security'",
    )
    codename: Optional[str] = Field(
        default=None,
        description="Distribution codename (n= field). Examples: 'noble', 'jammy'",
    )
    label: Optional[str] = Field(
        default=None,
        description="Repository label (l= field). Examples: 'Ubuntu', 'Debian-Security'",
    )
    component: Optional[str] = Field(
        default=None,
        description="Component (c= field). Examples: 'main', 'universe', 'contrib'",
    )
    site: Optional[str] = Field(
        default=None,
        description="Repository hostname. Examples: 'archive.ubuntu.com', 'pkgs.tailscale.com'",
    )

    # APT-specific metadata (useful context but not used for UU matching)
    priority: int = Field(
        description="Package priority from apt-cache policy. Higher = preferred.",
    )
    url: str = Field(
        description="Full package list URL from apt-cache policy",
    )
    architecture: Optional[str] = Field(
        default=None,
        description="Architecture (b= field). Examples: 'amd64', 'arm64'",
    )
    version: Optional[str] = Field(
        default=None,
        description="Distribution version (v= field). Example: '24.04'",
    )

    def __str__(self) -> str:
        """Human-readable string representation."""
        origin = self.origin or "Unknown"
        suite = self.suite or "Unknown"
        return f"{origin}:{suite}"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"Repository(origin={self.origin!r}, suite={self.suite!r}, site={self.site!r})"
