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
from apt_uu_config.cli.disable import disable_command
from apt_uu_config.cli.enable import enable_command
from apt_uu_config.cli.origin import origin_command
from apt_uu_config.cli.status import status_command

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"], default_map={"obj": {}})


console = Console()


@click.version_option(None, "--version", "-v")
@click.group(context_settings=CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Manage unattended upgrades configuration for APT.

    This tool simplifies the configuration of automatic updates
    in Debian/Ubuntu based systems.
    """
    # Putting all objects in context so that they don't have to be
    # recreated for each command
    ctx.ensure_object(AppContext)


# Register commands
cli.add_command(status_command)
cli.add_command(enable_command)
cli.add_command(disable_command)
cli.add_command(origin_command)


if __name__ == "__main__":
    cli()
