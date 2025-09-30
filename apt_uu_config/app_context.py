from apt_uu_config import __app_name__
from apt_uu_config.apt.config_reader import ConfigReader
from apt_uu_config.apt.config_writer import ConfigWriter
from apt_uu_config.config.app_config import AptUnattendedConfigConfig
from apt_uu_config.logging.logging import setup_logger


class AppContext:
    """Holds all the objects needed by commands"""

    def __init__(self) -> None:
        self.app_config = AptUnattendedConfigConfig(app_name=__app_name__)
        self.logger = setup_logger(log_level=self.app_config.log_level, app_name=__app_name__)
        self.config_reader = ConfigReader(config_dir=self.app_config.apt_config_dir)
        self.config_writer = ConfigWriter(config_dir=self.app_config.apt_config_dir)
