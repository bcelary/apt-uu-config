"""Config command for generating suggested unattended-upgrades patterns."""

import functools
from typing import Any, Callable, List

import click
from rich.console import Console
from rich.markup import escape

from apt_uu_config.apt.distro_info import DistroInfoError, get_distro_info
from apt_uu_config.apt.policy_parser import PolicyParseError, parse_apt_policy
from apt_uu_config.models.repository import Repository
from apt_uu_config.models.uu_pattern import UUPattern

console = Console(highlight=False)


def _handle_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to handle common errors for config command."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except DistroInfoError as e:
            console.print(f"[red]Error:[/red] {e}", style="bold")
            raise click.Abort()
        except PolicyParseError as e:
            console.print(f"[red]Error reading repository information:[/red] {e}", style="bold")
            raise click.Abort()
        except PermissionError:
            console.print("[red]Permission denied.[/red] Try running with sudo.", style="bold")
            raise click.Abort()

    return wrapper


@click.command()
@click.option("--verbose", is_flag=True, help="Show matching repositories for each pattern")
@_handle_errors
def config(verbose: bool) -> None:
    """
    Generate suggested unattended-upgrades configuration patterns.

    Analyzes all configured repositories and suggests appropriate patterns
    for /etc/apt/apt.conf.d/50unattended-upgrades.

    The command:
    - Collects all repositories from apt-cache policy
    - Filters out the dpkg/status pseudo-repository
    - Suggests the best pattern for each repository
    - Groups patterns by configuration section
    - Uses variable-based patterns when appropriate
    """
    # Get distribution info
    distro_id, distro_codename = get_distro_info()

    # Get all repositories
    repositories = parse_apt_policy()

    # Filter out dpkg/status pseudo-repository
    real_repos = [repo for repo in repositories if not repo.is_dpkg_status()]

    if not real_repos:
        console.print("[yellow]No repositories found.[/yellow]")
        return

    # Generate suggested patterns and group repositories by pattern
    # Using dict to group: key = (section, pattern_string), value = list of repos
    from collections import defaultdict

    pattern_to_repos: dict[tuple[str, str], list[Repository]] = defaultdict(list)

    for repo in real_repos:
        pattern = UUPattern.suggest_for_repository(repo, distro_id, distro_codename)
        key = (pattern.section, pattern.pattern_string)
        pattern_to_repos[key].append(repo)

    # Separate by section, preserving order
    allowed_origins: List[tuple[str, List[Repository]]] = []
    origins_pattern: List[tuple[str, List[Repository]]] = []

    for (section, pattern_str), repos in pattern_to_repos.items():
        if section == "Allowed-Origins":
            allowed_origins.append((pattern_str, repos))
        else:
            origins_pattern.append((pattern_str, repos))

    # Display results
    console.print(
        f"\n[bold]Suggested unattended-upgrades patterns for {distro_id} {distro_codename}:[/bold]\n"
    )

    # Show Allowed-Origins section
    if allowed_origins:
        console.print("[bold cyan]Unattended-Upgrade::Allowed-Origins {[/bold cyan]")
        for idx, (pattern_str, repos) in enumerate(allowed_origins):
            # Add blank line between entries when verbose (but not before first entry)
            if idx > 0 and verbose:
                console.print()
            console.print(f'    "{pattern_str}";', style="bold white")
            if verbose:
                for repo in repos:
                    repo_str = repo.format_full()  # Plain text, no color
                    details = repo.format_details()  # Plain text, no color
                    if details:
                        repo_str = f"{repo_str} ({details})"
                    repo_str = escape(repo_str)  # Escape brackets before Rich markup
                    console.print(f"    [dim]# {repo_str}[/dim]")
        console.print("[bold cyan]};[/bold cyan]\n")

    # Show Origins-Pattern section
    if origins_pattern:
        console.print("[bold cyan]Unattended-Upgrade::Origins-Pattern {[/bold cyan]")
        for idx, (pattern_str, repos) in enumerate(origins_pattern):
            # Add blank line between entries when verbose (but not before first entry)
            if idx > 0 and verbose:
                console.print()
            console.print(f'    "{pattern_str}";', style="bold white")
            if verbose:
                for repo in repos:
                    repo_str = repo.format_full()  # Plain text, no color
                    details = repo.format_details()  # Plain text, no color
                    if details:
                        repo_str = f"{repo_str} ({details})"
                    repo_str = escape(repo_str)  # Escape brackets before Rich markup
                    console.print(f"    [dim]# {repo_str}[/dim]")
        console.print("[bold cyan]};[/bold cyan]\n")
