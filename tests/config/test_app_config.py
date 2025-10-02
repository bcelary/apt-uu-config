from apt_uu_config.config.app_config import AptUnattendedConfigConfig


def test_settings() -> None:
    settings = AptUnattendedConfigConfig()
    assert settings.app_name == "apt-uu-config"
    assert settings.log_level in ["INFO", "DEBUG"]
