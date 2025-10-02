# Development Guide for Claude

This document contains development conventions and architectural guidelines specific to apt-uu-config. For setup, usage, and general project information, see [README.md](README.md).

## Core Development Principles

### Code Quality Standards

1. **Type Safety**: All code must be fully typed
   - Use type hints for all function parameters and return values
   - Run `mypy` with strict mode (already configured)
   - No `type: ignore` comments without detailed justification

2. **Error Handling**: Address root causes, don't mask errors
   - Avoid bare `except Exception: pass` blocks
   - When catching exceptions, handle them appropriately:
     - Re-raise with context if you can't handle it
     - Provide clear error messages to users
     - Only suppress errors when there's a valid reason (document why)
   - Prefer specific exception types over broad catches

3. **Code Principles**:
   - **KISS** (Keep It Simple, Stupid): Simple solutions over complex ones
   - **DRY** (Don't Repeat Yourself): Extract common logic into reusable functions
   - **YAGNI** (You Aren't Gonna Need It): Don't add features/abstractions until they're needed
   - Write code that's easy to understand and maintain

### Testing

- All new features require tests
- Tests should cover both happy paths and error cases
- Use pytest fixtures for common test setup
- Mock file system operations to avoid requiring sudo in tests
- Aim for meaningful coverage, not just high percentages

### Running Tests and Type Checking

**Quick QA check** (runs all checks):
```bash
pre-commit run --all-files
```

**Individual commands** (when you need specific tools):

Option 1: Activate virtual environment (recommended for interactive development):
```bash
source .venv/bin/activate
mypy apt_uu_config
pytest tests/
ruff check apt_uu_config
ruff format apt_uu_config
deactivate
```

Option 2: Use `uv run` without activation:
```bash
uv run mypy apt_uu_config
uv run pytest tests/
uv run ruff check apt_uu_config
uv run ruff format apt_uu_config
```

Note: If `uv run` commands fail with "command not found", the venv may have stale paths (e.g., after renaming the project directory). Recreate it with: `rm -rf .venv && uv sync --all-groups`

### Code Style

- Follow existing code patterns in the project
- Use `ruff` for formatting and linting (auto-fix enabled)
- Pre-commit hooks enforce all quality checks automatically (ruff, mypy, pytest)

## Architecture

### Design Patterns

1. **Separation of Concerns**:
   - CLI layer handles user interaction and formatting
   - APT layer handles file I/O and parsing
   - Models layer handles data validation and business logic

2. **Single Responsibility**:
   - ConfigReader only reads, ConfigWriter only writes
   - Each CLI command handles one specific action
   - Models encapsulate data and related operations

3. **Dependency Direction**:
   - CLI depends on APT and Models
   - APT depends on Models
   - Models have no dependencies on other layers

## Working with APT Configuration

### File Locations

- **Global enable/disable**: `/etc/apt/apt.conf.d/20auto-upgrades`
- **Origin configuration**: `/etc/apt/apt.conf.d/50unattended-upgrades`
- **Repository metadata**: `/var/lib/apt/lists/*_Release`

### Configuration Format

APT configuration uses a specific syntax:
```
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";

Unattended-Upgrade::Allowed-Origins {
    "origin=Ubuntu,suite=jammy-security";
    "${distro_id}:${distro_codename}-security";
};
```

For comprehensive documentation on all supported pattern formats, see [docs/APT_GUIDE.md](docs/APT_GUIDE.md).

### Safety Measures

- **Always create backups** before modifying configuration files (`.bak` suffix)
- **Validate patterns** before writing to avoid malformed configurations
- **Handle permission errors** gracefully with clear messages to use sudo
- **Parse carefully** - APT config format is sensitive to syntax

## Git Conventions

- Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
- Pre-commit hooks will enforce quality checks automatically

## Common Pitfalls

1. **Config file modifications** - Always call `_backup_file()` first
2. **Permission assumptions** - Check for `PermissionError` and guide users to use sudo
3. **Parse errors** - APT configs are fragile; handle malformed input gracefully
4. **Hardcoded paths** - Use Path constants defined in classes
5. **Missing type hints** - All functions must have complete type annotations
6. **Silent exception suppression** - Re-raise with context or provide clear error messages

## Handling Edge Cases

### Missing Configuration Files

- Not all systems have unattended-upgrades installed
- Create sensible defaults when files don't exist
- Provide clear messages about what's missing

### Permission Issues

- Many operations require root/sudo
- Catch `PermissionError` and provide helpful messages
- Don't fail silently - tell users what's needed

### Variable Substitution

APT configs use variables like `${distro_id}` and `${distro_codename}`:
- Match these patterns when comparing origins
- Expand them when possible for display
- Handle them specially in pattern matching

## Testing Philosophy

- **Unit tests**: Test individual functions/methods in isolation
- **Integration tests**: Test full command execution (without sudo)
- **Mock external dependencies**: File system operations, subprocess calls
- **Test error conditions**: Test failure paths, not just happy paths
- **Meaningful coverage**: Focus on testing behavior, not chasing percentage numbers

## When In Doubt

- **Architecture**: Follow existing patterns in similar modules
- **APT specifics**: Refer to [Debian UnattendedUpgrades docs](https://wiki.debian.org/UnattendedUpgrades)
- **Code quality**: If `pre-commit run --all-files` passes, you're on the right track
- **Philosophy**: Choose simple, readable code over clever solutions