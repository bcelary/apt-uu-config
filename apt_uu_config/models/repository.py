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
        """Human-readable string representation for logging/debugging."""
        origin = self.origin or "Unknown"
        suite = self.suite or "Unknown"
        return f"{origin}:{suite}"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"Repository(origin={self.origin!r}, suite={self.suite!r}, site={self.site!r})"

    def format_compact(self, truncate_origin: bool = True, color: bool = False) -> str:
        """
        Format repository with essential identifying information.

        Args:
            truncate_origin: If True, truncate long origins (>30 chars) intelligently
            color: If True, apply Rich markup for colored output

        Returns format: origin:suite/component [arch]
        - Architecture always shown (uses ? if not specified)
        Example: "Ubuntu:noble-security/main [amd64]"
        Example (long origin): "obs://build.ope...Ubuntu_24.04:?/main [amd64]"
        Example (no arch): "Ubuntu:noble [?]"
        """
        origin = self.origin or "?"

        # Smart truncation for long origins (like obs:// URLs)
        if truncate_origin and len(origin) > 30:
            # Keep first 15 and last 12 chars with ... in middle
            origin = f"{origin[:15]}...{origin[-12:]}"

        suite = self.suite or "?"

        if color:
            origin = f"[cyan]{origin}[/cyan]"
            suite = f"[blue]{suite}[/blue]"

        parts = [f"{origin}:{suite}"]

        if self.component:
            component = self.component
            if color:
                component = f"[yellow]{component}[/yellow]"
            parts.append(f"/{component}")

        arch = self.architecture or "?"
        if color:
            arch = f"[white]{arch}[/white]"
        parts.append(f" [{arch}]")
        return "".join(parts)

    def format_full(self, truncate_origin: bool = True, color: bool = False) -> str:
        """
        Format repository with full identifying information and smart truncation.

        Args:
            truncate_origin: If True, truncate long origins (>30 chars) intelligently
            color: If True, apply Rich markup for colored output

        Returns format: origin:suite/component [arch] @site
        - Architecture always shown (uses ? if not specified)
        - Site shown only when different from origin
        Example: "Ubuntu:noble-security/main [amd64]"
        Example (long origin): "obs://build.op...Ubuntu_24.04:?/main [amd64] @download.opensuse.org"
        Example (no arch): "Ubuntu:noble [?] @archive.ubuntu.com"
        """
        origin = self.origin or "?"

        # Smart truncation for long origins (like obs:// URLs)
        if truncate_origin and len(origin) > 30:
            # Keep first 15 and last 12 chars with ... in middle
            origin = f"{origin[:15]}...{origin[-12:]}"

        suite = self.suite or "?"

        if color:
            origin = f"[cyan]{origin}[/cyan]"
            suite = f"[blue]{suite}[/blue]"

        parts = [f"{origin}:{suite}"]

        if self.component:
            component = self.component
            if color:
                component = f"[yellow]{component}[/yellow]"
            parts.append(f"/{component}")

        arch = self.architecture or "?"
        if color:
            arch = f"[white]{arch}[/white]"
        parts.append(f" [{arch}]")

        if self.site and self.site != self.origin:
            # Add site if it's different from origin (often more recognizable)
            parts.append(f" @{self.site}")

        return "".join(parts)

    def format_details(self, color: bool = False) -> str:
        """
        Format additional repository metadata not shown in compact/full format.

        Args:
            color: If True, apply Rich markup for colored output

        Returns format: codename=X, label=Y, version=Z
        - Only includes fields that have values
        - Returns empty string if no additional details available
        Example: "codename=noble, label=Ubuntu, version=24.04"
        Example: "codename=stable, label=Brave"
        """
        details = []

        if self.codename:
            codename = self.codename
            if color:
                codename = f"[magenta]{codename}[/magenta]"
            details.append(f"codename={codename}")

        if self.label:
            details.append(f"label={self.label}")

        if self.version:
            details.append(f"version={self.version}")

        return ", ".join(details)
