from apt_uu_config import __app_name__
from apt_uu_config.config.app_config import AptUnattendedConfigConfig
from apt_uu_config.logging.logging import setup_logger


class AppContext:
    """Holds all the objects needed by commands"""

    def __init__(self) -> None:
        self.app_config = AptUnattendedConfigConfig(app_name=__app_name__)
        self.logger = setup_logger(log_level=self.app_config.log_level, app_name=__app_name__)
