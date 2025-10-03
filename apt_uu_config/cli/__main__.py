# apt_uu_config/cli/__main__.py

"""
CLI for apt-uu-config.

Manage unattended upgrades configuration for Debian/Ubuntu systems.

For more info, run:

```sh
apt-uu-config --help
```
"""

import click
from rich.console import Console

from apt_uu_config import __version__
from apt_uu_config.app_context import AppContext
from apt_uu_config.cli.show import show

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"], default_map={"obj": {}})


console = Console()


@click.version_option(__version__, "--version", "-v")
@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Manage unattended upgrades configuration for APT.

    This tool simplifies the configuration of automatic updates
    in Debian/Ubuntu based systems.
    """

    ctx.obj = AppContext()


# Register commands
cli.add_command(show)


if __name__ == "__main__":
    cli()
