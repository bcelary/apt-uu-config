"""Status command for displaying unattended-upgrades configuration."""

import functools
import json
from typing import Any, Callable, Dict, List, Tuple, TypedDict

import click
from rich.console import Console
from rich.table import Table

from apt_uu_config.apt.distro_info import DistroInfoError
from apt_uu_config.apt.policy_parser import PolicyParseError, parse_apt_policy
from apt_uu_config.apt.uu_config_reader import UUConfigReadError, read_uu_config
from apt_uu_config.models.repository import Repository
from apt_uu_config.models.uu_config import UUConfig

console = Console()


class RepoDataDict(TypedDict):
    """Type for repository data dictionary."""

    repository: str
    origin: str | None
    suite: str | None
    site: str | None
    component: str | None
    architecture: str | None
    enabled: bool
    matched_by: List[str]


class PatternDataDict(TypedDict):
    """Type for pattern data dictionary."""

    section: str
    pattern: str
    count: int
    matched_repos: List[str]


def _load_system_state() -> Tuple[UUConfig, List[Repository]]:
    """
    Load UU configuration and repository data from the system.

    Returns:
        Tuple of (UUConfig, List of Repositories)

    Raises:
        DistroInfoError: If distribution info cannot be determined
        UUConfigReadError: If UU config cannot be read
        PolicyParseError: If apt-cache policy cannot be parsed
        PermissionError: If insufficient permissions to read config
    """
    config = read_uu_config()
    repositories = parse_apt_policy()
    return config, repositories


def _output_json(data: Dict[str, Any]) -> None:
    """Output data as formatted JSON without any color formatting."""
    # Use plain print() instead of Rich console to avoid ANSI color codes
    # This ensures clean output when piping to files or other tools
    print(json.dumps(data, indent=2))  # noqa: T201 `print` is intentional


def _output_table(table: Table) -> None:
    """Output a Rich table."""
    console.print(table)


def _handle_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to handle common errors for status subcommands."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
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

    return wrapper


@click.group()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.pass_context
def status(ctx: click.Context, output_format: str) -> None:
    """Show unattended-upgrades configuration and repository status."""
    ctx.ensure_object(dict)
    ctx.obj["format"] = output_format


@status.command()
@click.option("--verbose", is_flag=True, help="Show additional repository metadata")
@click.pass_context
@_handle_errors
def sources(ctx: click.Context, verbose: bool) -> None:
    """Show all repositories visible to APT."""
    _, repositories = _load_system_state()
    output_format = ctx.obj["format"]

    if output_format == "json":
        # JSON: Include ALL repository fields
        data = {"repositories": [repo.model_dump() for repo in repositories]}
        _output_json(data)
    else:
        # Text: Curated columns
        table = Table(title="APT Repositories")

        # Default columns
        table.add_column("Origin", style="cyan")
        table.add_column("Suite", style="green")
        table.add_column("Site", style="blue")
        table.add_column("Component", style="yellow")
        table.add_column("Codename", style="magenta")
        table.add_column("Arch", style="white")

        # Verbose columns
        if verbose:
            table.add_column("Label", style="white")
            table.add_column("Version", style="white")
            table.add_column("Priority", style="white")
            table.add_column("URL", style="dim", overflow="fold")

        for repo in repositories:
            row = [
                repo.origin or "",
                repo.suite or "",
                repo.site or "",
                repo.component or "",
                repo.codename or "",
                repo.architecture or "",
            ]

            if verbose:
                row.extend(
                    [
                        repo.label or "",
                        repo.version or "",
                        str(repo.priority),
                        repo.url,
                    ]
                )

            table.add_row(*row)

        _output_table(table)


@status.command()
@click.option("--verbose", is_flag=True, help="Show detailed list of matched repositories")
@click.pass_context
@_handle_errors
def patterns(ctx: click.Context, verbose: bool) -> None:
    """Show configured unattended-upgrades patterns."""
    config, repositories = _load_system_state()
    output_format = ctx.obj["format"]

    if output_format == "json":
        # JSON: Only the patterns themselves (config data)
        data = {"patterns": [p.model_dump() for p in config.patterns]}
        _output_json(data)
    else:
        # Text: Show pattern list with match indicator
        table = Table(title="Configured Patterns")
        table.add_column("Section", style="cyan")
        table.add_column("Pattern", style="yellow")
        table.add_column("Has Matches", style="green")

        # Calculate matches for each pattern
        pattern_matches = []
        for pattern in config.patterns:
            matched_repos = [
                repo
                for repo in repositories
                if pattern.matches(repo, config.distro_id, config.distro_codename)
            ]
            pattern_matches.append((pattern, matched_repos))

            # Add row to table
            has_matches = "✓" if matched_repos else "✗"
            table.add_row(pattern.section, pattern.pattern_string, has_matches)

        _output_table(table)

        # Verbose: Show detailed match listing
        if verbose:
            console.print("\n[bold]Detailed Match Listing:[/bold]\n")
            for pattern, matched_repos in pattern_matches:
                console.print(
                    f"[cyan]{pattern.section}:[/cyan] [yellow]{pattern.pattern_string}[/yellow]"
                )
                if matched_repos:
                    for repo in matched_repos:
                        # Main identifier line
                        console.print(
                            f"  • {repo.origin or '?'}:{repo.suite or '?'} ({repo.site or 'no-site'})"
                        )
                        # Additional details
                        details = []
                        if repo.component:
                            details.append(f"component={repo.component}")
                        if repo.codename:
                            details.append(f"codename={repo.codename}")
                        if repo.label:
                            details.append(f"label={repo.label}")
                        if repo.architecture:
                            details.append(f"arch={repo.architecture}")
                        if repo.version:
                            details.append(f"version={repo.version}")
                        if details:
                            console.print(f"    [dim]{', '.join(details)}[/dim]")
                else:
                    console.print("  [dim](no matches)[/dim]")
                console.print()


@status.command()
@click.option(
    "--by-repo",
    "grouping",
    flag_value="repo",
    default=True,
    help="Group by repository (default)",
)
@click.option(
    "--by-pattern",
    "grouping",
    flag_value="pattern",
    help="Group by pattern",
)
@click.option(
    "--enabled-only", is_flag=True, help="Show only enabled repositories (--by-repo only)"
)
@click.option(
    "--disabled-only", is_flag=True, help="Show only disabled repositories (--by-repo only)"
)
@click.option("--verbose", is_flag=True, help="Show additional metadata")
@click.pass_context
@_handle_errors
def config(
    ctx: click.Context,
    grouping: str,
    enabled_only: bool,
    disabled_only: bool,
    verbose: bool,
) -> None:
    """Show unattended-upgrades configuration status."""
    uu_config, repositories = _load_system_state()
    output_format = ctx.obj["format"]

    # Show global status header (text only)
    if output_format == "text":
        global_status = (
            "[green]enabled[/green]" if uu_config.globally_enabled else "[red]disabled[/red]"
        )
        console.print(f"\n[bold]Unattended-Upgrades Global Status:[/bold] {global_status}\n")

    if grouping == "repo":
        _show_config_by_repo(
            uu_config, repositories, output_format, enabled_only, disabled_only, verbose
        )
    else:
        _show_config_by_pattern(uu_config, repositories, output_format, verbose)


def _show_config_by_repo(
    config: UUConfig,
    repositories: List[Repository],
    output_format: str,
    enabled_only: bool,
    disabled_only: bool,
    verbose: bool,
) -> None:
    """Show config grouped by repository."""
    # Build repo status data
    repo_data: List[RepoDataDict] = []
    for repo in repositories:
        is_enabled = config.is_repository_enabled(repo)

        # Apply filters
        if enabled_only and not is_enabled:
            continue
        if disabled_only and is_enabled:
            continue

        # Find which patterns match this repo
        matched_patterns = [
            p.pattern_string
            for p in config.patterns
            if p.matches(repo, config.distro_id, config.distro_codename)
        ]

        repo_data.append(
            {
                "repository": f"{repo.origin or '?'}:{repo.suite or '?'}",
                "origin": repo.origin,
                "suite": repo.suite,
                "site": repo.site,
                "component": repo.component,
                "architecture": repo.architecture,
                "enabled": is_enabled,
                "matched_by": matched_patterns,
            }
        )

    if output_format == "json":
        _output_json(
            {
                "globally_enabled": config.globally_enabled,
                "repositories": repo_data,
            }
        )
    else:
        table = Table(title="Repository Configuration Status")
        table.add_column("Repository", style="cyan")
        table.add_column("UU Enabled", style="green")
        table.add_column("Matched By", style="yellow")
        table.add_column("Arch", style="white")

        if verbose:
            table.add_column("Site", style="blue")
            table.add_column("Component", style="magenta")

        for data in repo_data:
            status_icon = "✓" if data["enabled"] else "✗"
            matched_by = ", ".join(data["matched_by"]) if data["matched_by"] else "[dim]none[/dim]"

            row: List[str] = [
                data["repository"],
                status_icon,
                matched_by,
                str(data["architecture"] or ""),
            ]

            if verbose:
                row.extend([str(data["site"] or ""), str(data["component"] or "")])

            table.add_row(*row)

        _output_table(table)


def _show_config_by_pattern(
    config: UUConfig,
    repositories: List[Repository],
    output_format: str,
    verbose: bool,
) -> None:
    """Show config grouped by pattern."""
    # Build pattern status data
    pattern_data: List[PatternDataDict] = []
    for pattern in config.patterns:
        matched_repos = [
            repo
            for repo in repositories
            if pattern.matches(repo, config.distro_id, config.distro_codename)
        ]

        pattern_data.append(
            {
                "section": pattern.section,
                "pattern": pattern.pattern_string,
                "count": len(matched_repos),
                "matched_repos": [f"{r.origin or '?'}:{r.suite or '?'}" for r in matched_repos],
            }
        )

    if output_format == "json":
        _output_json(
            {
                "globally_enabled": config.globally_enabled,
                "patterns": pattern_data,
            }
        )
    else:
        table = Table(title="Pattern Configuration Status")
        table.add_column("Section", style="cyan")
        table.add_column("Pattern", style="yellow")
        table.add_column("Repos Matched", style="green")

        if verbose:
            table.add_column("Matched Repositories", style="blue", overflow="fold")

        for data in pattern_data:
            row: List[str] = [data["section"], data["pattern"], str(data["count"])]

            if verbose:
                row.append(
                    ", ".join(data["matched_repos"]) if data["matched_repos"] else "[dim]none[/dim]"
                )

            table.add_row(*row)

        _output_table(table)
