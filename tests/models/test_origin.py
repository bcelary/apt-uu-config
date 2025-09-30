"""Tests for Origin model."""

import pytest

from apt_uu_config.models.origin import Origin


def test_origin_creation() -> None:
    """Test creating an Origin instance"""
    origin = Origin(
        origin="Ubuntu",
        suite="jammy-security",
        codename="jammy",
        enabled_for_uu=True,
    )

    assert origin.origin == "Ubuntu"
    assert origin.suite == "jammy-security"
    assert origin.codename == "jammy"
    assert origin.enabled_for_uu is True


def test_origin_matches_exact_origin() -> None:
    """Test pattern matching with exact origin"""
    origin = Origin(origin="Ubuntu", suite="jammy-security")

    assert origin.matches_pattern("Ubuntu")
    assert not origin.matches_pattern("Debian")


def test_origin_matches_origin_suite() -> None:
    """Test pattern matching with origin:suite"""
    origin = Origin(origin="Ubuntu", suite="jammy-security")

    assert origin.matches_pattern("Ubuntu:jammy-security")
    assert not origin.matches_pattern("Ubuntu:jammy-updates")


def test_origin_matches_wildcard_suite() -> None:
    """Test pattern matching with wildcard in suite"""
    origin = Origin(origin="Ubuntu", suite="jammy-security")

    assert origin.matches_pattern("*-security")
    assert origin.matches_pattern("Ubuntu:*")
    assert not origin.matches_pattern("*-updates")


def test_origin_to_uu_pattern() -> None:
    """Test converting origin to unattended-upgrades pattern"""
    origin = Origin(origin="Ubuntu", suite="jammy-security")

    pattern = origin.to_uu_pattern()
    assert pattern == "origin=Ubuntu,suite=jammy-security"


def test_origin_str_representation() -> None:
    """Test string representation of origin"""
    origin = Origin(origin="Ubuntu", suite="jammy-security")

    assert str(origin) == "Ubuntu:jammy-security"