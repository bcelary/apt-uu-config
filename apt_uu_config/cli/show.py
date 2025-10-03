"""Show command for displaying unattended-upgrades configuration."""

import functools
import json
from typing import Any, Callable, Dict, List, Tuple, TypedDict

import apt_pkg
import click
from rich.console import Console
from rich.table import Table

from apt_uu_config.apt.distro_info import DistroInfoError
from apt_uu_config.apt.policy_parser import PolicyParseError, parse_apt_policy
from apt_uu_config.apt.uu_config_reader import UUConfigReadError, read_uu_config
from apt_uu_config.models.repository import Repository
from apt_uu_config.models.uu_config import UUConfig

console = Console(highlight=False)


class ReposDataDict(TypedDict):
    """Type for combined repository data dictionary."""

    origin: str | None
    suite: str | None
    site: str | None
    component: str | None
    codename: str | None
    architecture: str | None
    label: str | None
    version: str | None
    priority: int
    url: str
    uu_enabled: bool
    matched_by: List[str]


def _load_system_state(primary_arch_only: bool = False) -> Tuple[UUConfig, List[Repository]]:
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

    if primary_arch_only:
        apt_pkg.init_config()
        primary_arch = apt_pkg.config["APT::Architecture"]
        # Include repos for primary arch, repos with no arch specified, and universal "all" arch packages
        repositories = [r for r in repositories if r.architecture in [primary_arch, None, "all"]]

    return config, repositories


def _output_json(data: Dict[str, Any]) -> None:
    """Output data as formatted JSON without any color formatting."""
    # Use plain print() instead of Rich console to avoid ANSI color codes
    # This ensures clean output when piping to files or other tools
    print(json.dumps(data, indent=2))  # noqa: T201 `print` is intentional


def _output_table(table: Table) -> None:
    """Output a Rich table."""
    console.print(table)


def _get_column_overflow_kwargs(no_truncate: bool) -> Dict[str, Any]:
    """
    Get column overflow kwargs based on truncation mode.

    Returns either fold (for no_truncate) or no_wrap (for truncate with ellipsis).
    """
    kwargs: Dict[str, Any] = {}

    if no_truncate:
        kwargs["overflow"] = "fold"
    else:
        kwargs["no_wrap"] = True

    return kwargs


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


def common_options(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for common CLI options shared between repos and patterns commands."""
    f = click.option(
        "--format",
        "output_format",
        type=click.Choice(["text", "json"]),
        default="text",
        help="Output format",
    )(f)
    f = click.option("--verbose", is_flag=True, help="Show additional details in output")(f)
    f = click.option(
        "--primary-arch-only",
        is_flag=True,
        help="Show only repositories for the primary system architecture",
    )(f)
    f = click.option(
        "--no-truncate",
        is_flag=True,
        help="Disable text truncation in tables, show full text with wrapping",
    )(f)
    return f


@click.group()
def show() -> None:
    """Show unattended-upgrades configuration and repository information."""
    pass


@show.command()
@_handle_errors
@click.option(
    "--enabled-only",
    is_flag=True,
    help="Show only repositories enabled for unattended-upgrades",
)
@click.option(
    "--disabled-only",
    is_flag=True,
    help="Show only repositories disabled for unattended-upgrades",
)
@common_options
def repos(
    output_format: str,
    verbose: bool,
    primary_arch_only: bool,
    no_truncate: bool,
    enabled_only: bool,
    disabled_only: bool,
) -> None:
    """Show all repositories with unattended-upgrades status."""
    if enabled_only and disabled_only:
        console.print(
            "[red]Error:[/red] Cannot use --enabled-only and --disabled-only together",
            style="bold",
        )
        raise click.Abort()

    config, repositories = _load_system_state(primary_arch_only=primary_arch_only)

    # Build combined data
    repo_data: List[ReposDataDict] = []
    for repo in repositories:
        is_enabled = config.is_repository_enabled(repo)

        # Apply filters
        if enabled_only and not is_enabled:
            continue
        if disabled_only and is_enabled:
            continue

        # Find matching patterns
        matched_patterns = [
            p.pattern_string
            for p in config.patterns
            if p.matches(repo, config.distro_id, config.distro_codename)
        ]

        repo_data.append(
            {
                "origin": repo.origin,
                "suite": repo.suite,
                "site": repo.site,
                "component": repo.component,
                "codename": repo.codename,
                "architecture": repo.architecture,
                "label": repo.label,
                "version": repo.version,
                "priority": repo.priority,
                "url": repo.url,
                "uu_enabled": is_enabled,
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
        # Show global status
        global_status = (
            "[green]enabled[/green]" if config.globally_enabled else "[red]disabled[/red]"
        )
        console.print(f"\n[bold]Unattended-Upgrades:[/bold] {global_status}\n")

        # Build table
        table = Table(title="Repositories")
        table.add_column(
            "Origin",
            style=Repository.ORIGIN_STYLE,
            max_width=15,
            **_get_column_overflow_kwargs(no_truncate),
        )
        table.add_column(
            "Suite", style=Repository.SUITE_STYLE, **_get_column_overflow_kwargs(no_truncate)
        )
        table.add_column(
            "Site",
            style=Repository.SITE_STYLE,
            max_width=22,
            **_get_column_overflow_kwargs(no_truncate),
        )
        table.add_column(
            "Component", style=Repository.COMP_STYLE, **_get_column_overflow_kwargs(no_truncate)
        )
        table.add_column(
            "Codename", style=Repository.CODENAME_STYLE, **_get_column_overflow_kwargs(no_truncate)
        )
        table.add_column(
            "Arch",
            style=Repository.ARCH_STYLE,
            min_width=5,
            **_get_column_overflow_kwargs(no_truncate),
        )

        if verbose:
            table.add_column(
                "Label",
                style=Repository.LABEL_STYLE,
                max_width=15,
                **_get_column_overflow_kwargs(no_truncate),
            )
            table.add_column(
                "Version", style=Repository.VER_STYLE, **_get_column_overflow_kwargs(no_truncate)
            )
            table.add_column(
                "Priority",
                style=Repository.PRIO_STYLE,
                min_width=3,
                **_get_column_overflow_kwargs(no_truncate),
            )
            table.add_column(
                "URL",
                style=Repository.URL_STYLE,
                max_width=25,
                **_get_column_overflow_kwargs(no_truncate),
            )
            table.add_column(
                "UU Pattern Match", max_width=40, **_get_column_overflow_kwargs(no_truncate)
            )
        else:
            table.add_column("UU", min_width=3)

        for data in repo_data:
            row = [
                data["origin"] or "",
                data["suite"] or "",
                data["site"] or "",
                data["component"] or "",
                data["codename"] or "",
                data["architecture"] or "",
            ]

            if verbose:
                # Show matched pattern(s) in green, or red ✗ if no match
                if data["matched_by"]:
                    pattern_match = "[green]" + ", ".join(data["matched_by"]) + "[/green]"
                else:
                    pattern_match = "[red]✗[/red]"

                row.extend(
                    [
                        data["label"] or "",
                        data["version"] or "",
                        str(data["priority"]),
                        data["url"],
                        pattern_match,
                    ]
                )
            else:
                # Just show ✓/✗
                status_icon = "[green]✓[/green]" if data["uu_enabled"] else "[red]✗[/red]"
                row.append(status_icon)

            table.add_row(*row)

        _output_table(table)


@show.command()
@_handle_errors
@common_options
def patterns(output_format: str, verbose: bool, primary_arch_only: bool, no_truncate: bool) -> None:
    """Show configured unattended-upgrades patterns and their matches."""
    config, repositories = _load_system_state(primary_arch_only=primary_arch_only)

    # Calculate matches for each pattern
    pattern_matches = []
    for pattern in config.patterns:
        matched_repos = [
            repo
            for repo in repositories
            if pattern.matches(repo, config.distro_id, config.distro_codename)
        ]
        pattern_matches.append((pattern, matched_repos))

    if output_format == "json":
        # JSON: Patterns with their matched repositories
        patterns_data = []
        for pattern, matched_repos in pattern_matches:
            # Convert matched repositories to dictionaries
            matches = [
                {
                    "origin": repo.origin,
                    "suite": repo.suite,
                    "site": repo.site,
                    "component": repo.component,
                    "codename": repo.codename,
                    "architecture": repo.architecture,
                    "label": repo.label,
                    "version": repo.version,
                    "priority": repo.priority,
                    "url": repo.url,
                }
                for repo in matched_repos
            ]
            pattern_dict = pattern.model_dump()
            pattern_dict["matches"] = matches
            patterns_data.append(pattern_dict)

        _output_json({"patterns": patterns_data})
    else:
        # Show pattern listing
        for pattern, matched_repos in pattern_matches:
            console.print(pattern.format(color=True))
            if matched_repos:
                for repo in matched_repos:
                    # Main identifier line with colored formatting
                    console.print(f"  • {repo.format_full(color=True)}")

                    # Verbose: Show additional details
                    if verbose:
                        details = repo.format_details(color=True)
                        if details:
                            console.print(f"    {details}")
            else:
                console.print("  [dim](no matches)[/dim]")
            console.print()
