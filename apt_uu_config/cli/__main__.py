# apt-unattended-config/cli/__main__.py

"""
CLI for apt-unattended-config.

Manage unattended upgrades configuration for Debian/Ubuntu systems.

For more info, run:

```sh
apt-unattended-config --help
```
"""

import click
from rich.console import Console

from apt_uu_config.app_context import AppContext
from apt_uu_config.cli.status import status

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"], default_map={"obj": {}})


console = Console()


@click.version_option(None, "--version", "-v")
@click.option(
    "--config-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=str),
    default=None,
    help="Custom APT configuration directory (default: /etc/apt)",
    envvar="APT_CONFIG_DIR",
)
@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx: click.Context, config_dir: str | None) -> None:
    """
    Manage unattended upgrades configuration for APT.

    This tool simplifies the configuration of automatic updates
    in Debian/Ubuntu based systems.
    """

    ctx.obj = AppContext()


# Register commands
cli.add_command(status)


if __name__ == "__main__":
    cli()
