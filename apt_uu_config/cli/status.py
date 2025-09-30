"""Status command to display current unattended upgrades configuration."""

import click
from rich.console import Console
from rich.table import Table

from apt_uu_config.app_context import AppContext
from apt_uu_config.apt.origins import OriginDetector


@click.command(name="status")
@click.pass_context
def status_command(ctx: click.Context) -> None:
    """
    Display the current unattended upgrades configuration status.

    Shows:
    - Global enabled/disabled status
    - List of all repository origins
    - Which origins have automatic updates enabled
    """
    console = Console()
    app_context: AppContext = ctx.obj

    try:
        # Read current configuration
        globally_enabled = app_context.config_reader.is_globally_enabled()
        enabled_origins = app_context.config_reader.get_enabled_origins()

        # Get all available origins
        origin_detector = OriginDetector()
        all_origins = origin_detector.get_all_origins(enabled_origins)

        # Display global status
        status_symbol = "✓" if globally_enabled else "✗"
        status_text = "ENABLED" if globally_enabled else "DISABLED"
        status_color = "green" if globally_enabled else "red"

        console.print(
            f"\nUnattended Upgrades: [{status_color}]{status_symbol} {status_text}[/{status_color}]\n"
        )

        # Create table for origins
        table = Table(title="Repository Origins")
        table.add_column("Origin", style="cyan", no_wrap=True)
        table.add_column("Suite", style="magenta")
        table.add_column("Status", style="bold")

        # Sort origins: enabled first, then alphabetically
        sorted_origins = sorted(
            all_origins,
            key=lambda o: (not o.enabled_for_uu, o.origin, o.suite),
        )

        for origin in sorted_origins:
            status_text = "ENABLED" if origin.enabled_for_uu else "DISABLED"
            status_style = (
                "[green]ENABLED[/green]" if origin.enabled_for_uu else "[dim]DISABLED[/dim]"
            )

            table.add_row(origin.origin, origin.suite, status_style)

        console.print(table)
        console.print()

    except PermissionError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold")
        ctx.exit(1)
    except Exception as e:
        console.print(
            f"[red]Error:[/red] Failed to read configuration: {e}",
            style="bold",
        )
        ctx.exit(1)
