"""Test apt_uu_config."""

import apt_uu_config


def test_import() -> None:
    """Test that the package can be imported."""
    assert isinstance(apt_uu_config.__name__, str)
