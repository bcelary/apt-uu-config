"""Unattended upgrades configuration model."""

from typing import List

from pydantic import BaseModel, Field

from apt_uu_config.models.origin import Origin


class UnattendedUpgradesConfig(BaseModel):
    """
    Represents the complete unattended upgrades configuration.

    This includes both the global enabled/disabled state and the list
    of origins that are configured for automatic updates.
    """

    globally_enabled: bool = Field(
        default=False,
        description="Whether unattended upgrades are globally enabled",
    )
    enabled_origins: List[Origin] = Field(
        default_factory=list,
        description="List of origins enabled for unattended upgrades",
    )
    all_origins: List[Origin] = Field(
        default_factory=list,
        description="List of all available origins in the system",
    )

    def is_origin_enabled(self, origin: Origin) -> bool:
        """
        Check if a specific origin is enabled for unattended upgrades.

        Args:
            origin: The origin to check

        Returns:
            True if enabled, False otherwise
        """
        for enabled in self.enabled_origins:
            if (
                enabled.origin.lower() == origin.origin.lower()
                and enabled.suite.lower() == origin.suite.lower()
            ):
                return True
        return False

    def get_enabled_origin_patterns(self) -> List[str]:
        """
        Get list of origin patterns that are enabled.

        Returns:
            List of pattern strings suitable for unattended-upgrades config
        """
        return [origin.to_uu_pattern() for origin in self.enabled_origins]
