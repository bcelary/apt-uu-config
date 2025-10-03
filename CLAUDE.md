# Development Guide for Claude

Development conventions and architectural guidelines for apt-uu-config.

## Code Quality

- **Type Safety**: Full type hints required (strict mypy)
- **Error Handling**: No silent failures - re-raise with context or provide clear user messages
- **Principles**: KISS, DRY, YAGNI - simple, maintainable code over clever solutions
- **Testing**: All features need tests (happy path + error cases), mock file operations
- **Quality Check**: Run `pre-commit run --all-files` before committing

## Architecture

**Layer separation:**
- CLI → handles user interaction and formatting
- APT → handles file I/O and parsing
- Models → handles data validation and business logic

**Dependency direction:** CLI → APT → Models (no reverse dependencies)

## APT Configuration

**Key files:**
- `/etc/apt/apt.conf.d/20auto-upgrades` - global enable/disable
- `/etc/apt/apt.conf.d/50unattended-upgrades` - origin configuration
- `/var/lib/apt/lists/*_Release` - repository metadata

**See [docs/APT_GUIDE.md](docs/APT_GUIDE.md) for APT config format details.**

**Safety:**
- Always backup files before modification (`.bak` suffix)
- Handle `PermissionError` with clear "use sudo" messages
- APT configs use variables like `${distro_id}` - handle specially in pattern matching

## Conventions

- **Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`)
- **Code style**: Follow existing patterns, ruff auto-formats