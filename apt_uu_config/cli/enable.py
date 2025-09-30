"""Enable command to globally enable unattended upgrades."""

import click
from rich.console import Console

from apt_uu_config.apt.config_writer import ConfigWriter


@click.command(name="enable")
@click.pass_context
def enable_command(ctx: click.Context) -> None:
    """
    Enable unattended upgrades globally.

    This modifies /etc/apt/apt.conf.d/20auto-upgrades to enable
    automatic package updates.
    """
    console = Console()

    try:
        config_writer = ConfigWriter()
        config_writer.set_globally_enabled(True)

        console.print(
            "[green]✓[/green] Unattended upgrades enabled successfully",
            style="bold",
        )
        console.print(
            "\n[dim]Configuration file updated: /etc/apt/apt.conf.d/20auto-upgrades[/dim]"
        )
        console.print(
            "[dim]Backup created: /etc/apt/apt.conf.d/20auto-upgrades.bak[/dim]\n"
        )

    except PermissionError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold")
        ctx.exit(1)
    except Exception as e:
        console.print(
            f"[red]Error:[/red] Failed to enable unattended upgrades: {e}",
            style="bold",
        )
        ctx.exit(1)