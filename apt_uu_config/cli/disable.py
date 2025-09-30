"""Disable command to globally disable unattended upgrades."""

import click
from rich.console import Console

from apt_uu_config.app_context import AppContext


@click.command(name="disable")
@click.pass_context
def disable_command(ctx: click.Context) -> None:
    """
    Disable unattended upgrades globally.

    This modifies /etc/apt/apt.conf.d/20auto-upgrades to disable
    automatic package updates.
    """
    console = Console()
    app_context: AppContext = ctx.obj

    try:
        app_context.config_writer.set_globally_enabled(False)

        console.print(
            "[yellow]✓[/yellow] Unattended upgrades disabled successfully",
            style="bold",
        )
        console.print(
            "\n[dim]Configuration file updated: /etc/apt/apt.conf.d/20auto-upgrades[/dim]"
        )
        console.print("[dim]Backup created: /etc/apt/apt.conf.d/20auto-upgrades.bak[/dim]\n")

    except PermissionError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold")
        ctx.exit(1)
    except Exception as e:
        console.print(
            f"[red]Error:[/red] Failed to disable unattended upgrades: {e}",
            style="bold",
        )
        ctx.exit(1)
