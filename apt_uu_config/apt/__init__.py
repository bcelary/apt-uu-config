"""APT configuration handling for unattended upgrades."""

# Lazy imports to avoid apt_pkg dependency at import time
__all__ = [
    "get_distro_info",
    "DistroInfoError",
    "parse_apt_policy",
    "PolicyParseError",
    "read_uu_config",
    "UUConfigReadError",
]


def __getattr__(name: str):  # type: ignore[no-untyped-def]
    """Lazy import of apt module functions."""
    if name == "get_distro_info":
        from apt_uu_config.apt.distro_info import get_distro_info

        return get_distro_info
    elif name == "DistroInfoError":
        from apt_uu_config.apt.distro_info import DistroInfoError

        return DistroInfoError
    elif name == "parse_apt_policy":
        from apt_uu_config.apt.policy_parser import parse_apt_policy

        return parse_apt_policy
    elif name == "PolicyParseError":
        from apt_uu_config.apt.policy_parser import PolicyParseError

        return PolicyParseError
    elif name == "read_uu_config":
        from apt_uu_config.apt.uu_config_reader import read_uu_config

        return read_uu_config
    elif name == "UUConfigReadError":
        from apt_uu_config.apt.uu_config_reader import UUConfigReadError

        return UUConfigReadError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
