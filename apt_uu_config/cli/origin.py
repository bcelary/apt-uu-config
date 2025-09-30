"""Origin command group for managing per-repository unattended upgrades."""

import click
from rich.console import Console

from apt_uu_config.app_context import AppContext
from apt_uu_config.apt.origins import OriginDetector


@click.group(name="origin")
@click.pass_context
def origin_command(ctx: click.Context) -> None:
    """
    Manage unattended upgrades for specific repository origins.

    Use this command to enable or disable automatic updates for
    individual repositories or groups of repositories using patterns.
    """
    pass


@origin_command.command(name="enable")
@click.argument("pattern", type=str)
@click.pass_context
def origin_enable(ctx: click.Context, pattern: str) -> None:
    """
    Enable unattended upgrades for repositories matching PATTERN.

    PATTERN can be:
    - Exact origin: "Ubuntu"
    - Origin:suite: "Ubuntu:jammy-security"
    - Wildcards: "*-security", "Ubuntu:*"

    Examples:
        sudo apt-unattended-config origin enable "Ubuntu:jammy-security"
        sudo apt-unattended-config origin enable "*-security"
        sudo apt-unattended-config origin enable "google-chrome"
    """
    console = Console()
    app_context: AppContext = ctx.obj

    try:
        # Read current configuration
        enabled_origins = app_context.config_reader.get_enabled_origins()

        # Get all available origins
        origin_detector = OriginDetector()
        all_origins = origin_detector.get_all_origins(enabled_origins)

        # Find origins matching the pattern
        matching_origins = [origin for origin in all_origins if origin.matches_pattern(pattern)]

        if not matching_origins:
            console.print(
                f"[yellow]Warning:[/yellow] No repositories found matching pattern '{pattern}'",
                style="bold",
            )
            console.print(
                "\n[dim]Run 'sudo apt-unattended-config status' to see available repositories.[/dim]\n"
            )
            ctx.exit(1)

        # Enable each matching origin
        for origin in matching_origins:
            if not origin.enabled_for_uu:
                app_context.config_writer.add_origin(origin)
                console.print(f"[green]✓[/green] Enabled: {origin.origin}:{origin.suite}")
            else:
                console.print(f"[dim]⊗ Already enabled: {origin.origin}:{origin.suite}[/dim]")

        console.print(
            "\n[dim]Configuration file updated: /etc/apt/apt.conf.d/50unattended-upgrades[/dim]"
        )
        console.print("[dim]Backup created: /etc/apt/apt.conf.d/50unattended-upgrades.bak[/dim]\n")

    except PermissionError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold")
        ctx.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to enable origin: {e}", style="bold")
        ctx.exit(1)


@origin_command.command(name="disable")
@click.argument("pattern", type=str)
@click.pass_context
def origin_disable(ctx: click.Context, pattern: str) -> None:
    """
    Disable unattended upgrades for repositories matching PATTERN.

    PATTERN can be:
    - Exact origin: "Ubuntu"
    - Origin:suite: "Ubuntu:jammy-security"
    - Wildcards: "*-security", "Ubuntu:*"

    Examples:
        sudo apt-unattended-config origin disable "Ubuntu:jammy-updates"
        sudo apt-unattended-config origin disable "*-backports"
    """
    console = Console()
    app_context: AppContext = ctx.obj

    try:
        # Read current configuration
        enabled_origins = app_context.config_reader.get_enabled_origins()

        # Get all available origins
        origin_detector = OriginDetector()
        all_origins = origin_detector.get_all_origins(enabled_origins)

        # Find origins matching the pattern
        matching_origins = [
            origin
            for origin in all_origins
            if origin.matches_pattern(pattern) and origin.enabled_for_uu
        ]

        if not matching_origins:
            console.print(
                f"[yellow]Warning:[/yellow] No enabled repositories found matching pattern '{pattern}'",
                style="bold",
            )
            console.print(
                "\n[dim]Run 'sudo apt-unattended-config status' to see enabled repositories.[/dim]\n"
            )
            ctx.exit(1)

        # Disable each matching origin
        for origin in matching_origins:
            app_context.config_writer.remove_origin(origin)
            console.print(f"[yellow]✓[/yellow] Disabled: {origin.origin}:{origin.suite}")

        console.print(
            "\n[dim]Configuration file updated: /etc/apt/apt.conf.d/50unattended-upgrades[/dim]"
        )
        console.print("[dim]Backup created: /etc/apt/apt.conf.d/50unattended-upgrades.bak[/dim]\n")

    except PermissionError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold")
        ctx.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to disable origin: {e}", style="bold")
        ctx.exit(1)
