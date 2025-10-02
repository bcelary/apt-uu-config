"""Status command for displaying unattended-upgrades configuration."""

import click
from rich.console import Console

from apt_uu_config.apt.distro_info import DistroInfoError
from apt_uu_config.apt.policy_parser import PolicyParseError, parse_apt_policy
from apt_uu_config.apt.uu_config_reader import UUConfigReadError, read_uu_config

console = Console()


@click.command()
def status(verbose: bool, enabled_only: bool, disabled_only: bool, json_output: bool) -> None:
    """
    Show current unattended-upgrades configuration and repository status.

    This is a TODO command!
    """
    try:
        # Read system state
        config = read_uu_config()
        repositories = parse_apt_policy()

        if not config or not repositories:
            console.print("This is a stub only print...")

    except DistroInfoError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold")
        raise click.Abort()
    except UUConfigReadError as e:
        console.print(
            f"[red]Error reading unattended-upgrades configuration:[/red] {e}",
            style="bold",
        )
        raise click.Abort()
    except PolicyParseError as e:
        console.print(f"[red]Error reading repository information:[/red] {e}", style="bold")
        raise click.Abort()
    except PermissionError:
        console.print("[red]Permission denied.[/red] Try running with sudo.", style="bold")
        raise click.Abort()
