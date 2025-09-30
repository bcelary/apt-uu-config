from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from apt_uu_config import __app_name__


class AptUnattendedConfigConfig(BaseSettings):
    app_name: str = __app_name__
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    apt_config_dir: Path = Path("/etc/apt")
    # Add more ...

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        env_file=".env",
        # if a setting is set to blah= in env, it will be ignored and
        # the default value will be used
        env_ignore_empty=True,
        # settings that are not in the model will be ignored
        extra="ignore",
        # if settings are re-defined the new ones will be validated
        validate_assignment=True,
    )
