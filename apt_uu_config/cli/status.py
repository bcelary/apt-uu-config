"""Status command for displaying unattended-upgrades configuration."""

import json
from typing import List

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from apt_uu_config.apt.distro_info import DistroInfoError
from apt_uu_config.apt.policy_parser import PolicyParseError, parse_apt_policy
from apt_uu_config.apt.uu_config_reader import UUConfigReadError, read_uu_config
from apt_uu_config.models.repository import Repository
from apt_uu_config.models.uu_config import UUConfig
from apt_uu_config.models.uu_pattern import UUPattern

console = Console()


def get_matching_patterns(repo: Repository, config: UUConfig) -> List[UUPattern]:
    """
    Get all patterns that match a given repository.

    Args:
        repo: The repository to check
        config: The unattended-upgrades configuration

    Returns:
        List of patterns that match this repository
    """
    matching = []
    for pattern in config.patterns:
        if pattern.matches(repo, config.distro_id, config.distro_codename):
            matching.append(pattern)
    return matching


@click.command()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show all repositories (default: show summary only)",
)
@click.option(
    "--enabled-only",
    is_flag=True,
    help="Show only repositories enabled for auto-updates",
)
@click.option(
    "--disabled-only",
    is_flag=True,
    help="Show only repositories disabled for auto-updates",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output as JSON for scripting",
)
def status(verbose: bool, enabled_only: bool, disabled_only: bool, json_output: bool) -> None:
    """
    Show current unattended-upgrades configuration and repository status.

    Displays:
    - Global enable/disable status
    - Configured patterns for automatic updates
    - Repository status (which repos are enabled for auto-updates)
    """
    try:
        # Read system state
        config = read_uu_config()
        repositories = parse_apt_policy()

        if json_output:
            _output_json(config, repositories)
        else:
            _output_formatted(config, repositories, verbose, enabled_only, disabled_only)

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


def _output_formatted(
    config: UUConfig,
    repositories: List[Repository],
    verbose: bool,
    enabled_only: bool,
    disabled_only: bool,
) -> None:
    """Display formatted output using Rich."""
    # Configured patterns (printed first so status panel can match its width)
    table_width = None
    if config.patterns:
        table_width = _print_patterns_table(config, repositories)
        console.print()

    # Global status panel (matches patterns table width)
    _print_global_status(config, repositories, width=table_width)

    # Repository status
    if verbose or enabled_only or disabled_only:
        console.print()
        _print_repositories_table(config, repositories, enabled_only, disabled_only)


def _print_global_status(
    config: UUConfig, repositories: List[Repository], width: int | None = None
) -> None:
    """Print global status panel."""
    enabled_repos = config.get_enabled_repositories(repositories)

    status_text = Text()
    status_text.append("Unattended-Upgrades: ", style="bold")
    if config.globally_enabled:
        status_text.append("✓ Enabled", style="bold green")
    else:
        status_text.append("✗ Disabled", style="bold red")

    status_text.append("\n")
    status_text.append("Distribution: ", style="bold")
    status_text.append(f"{config.distro_id} {config.distro_codename}")

    status_text.append("\n")
    status_text.append("Variables: ", style="bold")
    status_text.append("${distro_id}=", style="dim")
    status_text.append(f"{config.distro_id}", style="yellow")
    status_text.append(", ", style="dim")
    status_text.append("${distro_codename}=", style="dim")
    status_text.append(f"{config.distro_codename}", style="yellow")

    status_text.append("\n")
    status_text.append("Total repositories: ", style="bold")
    status_text.append(str(len(repositories)))

    status_text.append("\n")
    status_text.append("Enabled for auto-updates: ", style="bold")
    if config.globally_enabled:
        status_text.append(str(len(enabled_repos)), style="green")
    else:
        status_text.append("0", style="dim")
        status_text.append(" (globally disabled)", style="dim")

    panel = Panel(status_text, title="[bold]Status[/bold]", border_style="blue", width=width)
    console.print(panel)


def _print_patterns_table(config: UUConfig, repositories: List[Repository]) -> int:
    """
    Print configured patterns table.

    Returns:
        The width of the printed table (for matching other components)
    """
    table = Table(title="Configured Patterns", show_header=True, header_style="bold")
    table.add_column("Section", style="cyan")
    table.add_column("Pattern", style="yellow")
    table.add_column("Matches", justify="right", style="dim")

    for pattern in config.patterns:
        # Count how many repositories match this pattern
        match_count = 0
        if config.globally_enabled:
            for repo in repositories:
                if pattern.matches(repo, config.distro_id, config.distro_codename):
                    match_count += 1

        # Format match count
        if config.globally_enabled:
            if match_count == 0:
                matches_str = "[dim]0 repos[/dim]"
            elif match_count == 1:
                matches_str = "[green]1 repo[/green]"
            else:
                matches_str = f"[green]{match_count} repos[/green]"
        else:
            matches_str = "[dim]—[/dim]"

        table.add_row(pattern.section, pattern.pattern_string, matches_str)

    # Measure the table width using Rich's measurement API
    from rich.console import Console as MeasureConsole
    from rich.measure import Measurement

    measure_console = MeasureConsole()
    measurement = Measurement.get(measure_console, measure_console.options, table)
    # Use maximum width for consistent sizing
    table_width = measurement.maximum

    console.print(table)
    return table_width


def _print_repositories_table(
    config: UUConfig,
    repositories: List[Repository],
    enabled_only: bool,
    disabled_only: bool,
) -> None:
    """Print repositories status table."""
    table = Table(title="Repository Status", show_header=True, header_style="bold")
    table.add_column("Origin", style="cyan")
    table.add_column("Suite", style="yellow")
    table.add_column("Component", style="magenta")
    table.add_column("Site", style="blue", overflow="fold")
    table.add_column("Status", justify="center")
    table.add_column("Matching Pattern", style="dim", overflow="fold")

    for repo in repositories:
        is_enabled = config.is_repository_enabled(repo)

        # Apply filters
        if enabled_only and not is_enabled:
            continue
        if disabled_only and is_enabled:
            continue

        # Format status
        if is_enabled:
            status = "[green]✓ Enabled[/green]"
        else:
            status = "[red]✗ Disabled[/red]"

        # Get matching patterns
        matching = get_matching_patterns(repo, config)
        if matching:
            # Show first matching pattern, truncate if too long
            pattern_str = matching[0].pattern_string
            if len(pattern_str) > 40:
                pattern_str = pattern_str[:37] + "..."
            matching_str = pattern_str
            if len(matching) > 1:
                matching_str += f" (+{len(matching)-1} more)"
        else:
            matching_str = "—"

        table.add_row(
            repo.origin or "—",
            repo.suite or "—",
            repo.component or "—",
            repo.site or "—",
            status,
            matching_str,
        )

    console.print(table)


def _output_json(config: UUConfig, repositories: List[Repository]) -> None:
    """Output as JSON."""
    enabled_repos = config.get_enabled_repositories(repositories)

    output = {
        "globally_enabled": config.globally_enabled,
        "distro_id": config.distro_id,
        "distro_codename": config.distro_codename,
        "patterns": [{"section": p.section, "pattern": p.pattern_string} for p in config.patterns],
        "total_repositories": len(repositories),
        "enabled_repositories": len(enabled_repos),
        "repositories": [
            {
                "origin": repo.origin,
                "suite": repo.suite,
                "codename": repo.codename,
                "component": repo.component,
                "site": repo.site,
                "priority": repo.priority,
                "enabled": config.is_repository_enabled(repo),
            }
            for repo in repositories
        ],
    }

    console.print(json.dumps(output, indent=2))
