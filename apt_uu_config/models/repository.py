"""APT repository data model.

This module contains the pure data model for APT repositories as they exist
on the system. It contains no business logic about unattended-upgrades.
"""

from typing import ClassVar, Optional

from pydantic import BaseModel, Field
from rich.markup import escape


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

    # Color/style constants for presentation
    ORIGIN_STYLE: ClassVar[str] = "cyan"
    SUITE_STYLE: ClassVar[str] = "blue"
    COMP_STYLE: ClassVar[str] = "yellow"
    ARCH_STYLE: ClassVar[str] = ""  # "white on bright_black"
    SITE_STYLE: ClassVar[str] = "dim white on black"
    CODENAME_STYLE: ClassVar[str] = "magenta"
    LABEL_STYLE: ClassVar[str] = "white on bright_black"
    VER_STYLE: ClassVar[str] = "white on bright_black"
    PRIO_STYLE: ClassVar[str] = "white on bright_black"
    URL_STYLE: ClassVar[str] = "dim white on bright_black"

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
            # Escape brackets in content
            origin = escape(origin)
            suite = escape(suite)

            # Apply styles
            if self.ORIGIN_STYLE:
                origin = f"[{self.ORIGIN_STYLE}]{origin}[/{self.ORIGIN_STYLE}]"
            if self.SUITE_STYLE:
                suite = f"[{self.SUITE_STYLE}]{suite}[/{self.SUITE_STYLE}]"

        parts = [f"{origin}:{suite}"]

        if self.component:
            component = self.component
            if color:
                component = escape(component)
                if self.COMP_STYLE:
                    component = f"[{self.COMP_STYLE}]{component}[/{self.COMP_STYLE}]"
            parts.append(f"/{component}")

        arch = (self.architecture or "").strip() or "?"
        if color:
            arch = escape(arch)
            if self.ARCH_STYLE:
                arch = f"[{self.ARCH_STYLE}]{arch}[/{self.ARCH_STYLE}]"
            parts.append(f" \\[{arch}]")
        else:
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
        - Site always shown when available
        Example: "Ubuntu:noble-security/main [amd64] @archive.ubuntu.com"
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
            # Escape brackets in content
            origin = escape(origin)
            suite = escape(suite)

            # Apply styles
            if self.ORIGIN_STYLE:
                origin = f"[{self.ORIGIN_STYLE}]{origin}[/{self.ORIGIN_STYLE}]"
            if self.SUITE_STYLE:
                suite = f"[{self.SUITE_STYLE}]{suite}[/{self.SUITE_STYLE}]"

        parts = [f"{origin}:{suite}"]

        if self.component:
            component = self.component
            if color:
                component = escape(component)
                if self.COMP_STYLE:
                    component = f"[{self.COMP_STYLE}]{component}[/{self.COMP_STYLE}]"
            parts.append(f"/{component}")

        arch = (self.architecture or "").strip() or "?"
        if color:
            arch = escape(arch)
            if self.ARCH_STYLE:
                arch = f"[{self.ARCH_STYLE}]{arch}[/{self.ARCH_STYLE}]"
            parts.append(f" \\[{arch}]")
        else:
            parts.append(f" [{arch}]")

        if self.site:
            site = self.site
            if color:
                site = escape(site)
                if self.SITE_STYLE:
                    site = f"[{self.SITE_STYLE}]{site}[/{self.SITE_STYLE}]"
            parts.append(f" @{site}")

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
                codename = escape(codename)
                if self.CODENAME_STYLE:
                    codename = f"[{self.CODENAME_STYLE}]{codename}[/{self.CODENAME_STYLE}]"
            details.append(f"codename={codename}")

        if self.label:
            label = self.label
            if color:
                label = escape(label)
                if self.LABEL_STYLE:
                    label = f"[{self.LABEL_STYLE}]{label}[/{self.LABEL_STYLE}]"
            details.append(f"label={label}")

        if self.version:
            version = self.version
            if color:
                version = escape(version)
                if self.VER_STYLE:
                    version = f"[{self.VER_STYLE}]{version}[/{self.VER_STYLE}]"
            details.append(f"version={version}")

        return ", ".join(details)

    def is_dpkg_status(self) -> bool:
        """
        Check if this is the dpkg/status pseudo-repository.

        The dpkg/status entry represents currently installed packages, not a real
        repository. It should be filtered out when generating unattended-upgrades
        patterns.

        Characteristics of dpkg/status:
        - suite: "now"
        - URL: "/var/lib/dpkg/status"
        - Not a source of updates, just shows installed packages

        Returns:
            True if this is the dpkg/status pseudo-repository, False otherwise
        """
        return self.suite == "now" and "/var/lib/dpkg/status" in self.url
