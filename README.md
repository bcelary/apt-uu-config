# apt-uu-config

A Python CLI tool for managing unattended upgrades configuration on Debian/Ubuntu systems.

## Overview

`apt-uu-config` helps you understand and manage automatic security updates in Debian/Ubuntu based distributions. The tool reads your unattended-upgrades configuration and shows you exactly which repositories are enabled for automatic updates.

### Current Features

- **Three focused status views**:
  - `sources`: View all APT repositories on your system
  - `patterns`: See configured unattended-upgrades patterns
  - `config`: Check which repos are enabled and why
- **Flexible output formats**:
  - Rich formatted tables with color (default)
  - JSON output for scripting and automation
- **Detailed filtering**: Show only enabled/disabled repositories
- **Verbose mode**: Show additional metadata when needed
- **Variable expansion**: Resolves `${distro_id}` and `${distro_codename}`
- **Smart grouping**: View config by repository or by pattern

### Planned Features

- **Global control**: Enable/disable automatic updates system-wide
- **Repository-level control**: Configure which repositories get automatic updates
- **Pattern management**: Add/remove patterns for repository matching
- **Safe modifications**: Automatic backups before modifying configuration files

## Installation

### Prerequisites

- Python 3.12 or higher
- Debian/Ubuntu based system with APT package manager
- Root/sudo access (may be required to read APT configuration on some systems)
- **System packages**:
  - `python3-apt` - for apt_pkg library (install with `sudo apt install python3-apt`)
  - `lsb-release` - for distribution detection (usually pre-installed)

### From Source

```sh
# Install system dependencies
sudo apt install python3-apt lsb-release

# Clone and install
git clone https://github.com/bcelary/apt-uu-config.git
cd apt-uu-config

# Create venv with access to system packages (required for python3-apt)
uv venv --system-site-packages
uv sync
```

Then run using:
```sh
sudo uv run apt-uu-config <command>
```

## Usage

The `status` command provides three focused views for understanding your unattended-upgrades configuration:

### View All APT Sources

See all repositories visible to APT on your system:

```bash
# Show all repositories (basic info)
sudo apt-uu-config status sources

# Show all repository metadata
sudo apt-uu-config status sources --verbose

# Output as JSON
sudo apt-uu-config status sources --format json
```

### View Configured Patterns

See what patterns are configured in unattended-upgrades:

```bash
# Show configured patterns and if they match anything
sudo apt-uu-config status patterns

# Show detailed list of repositories matched by each pattern
sudo apt-uu-config status patterns --verbose

# Output as JSON (configuration data only)
sudo apt-uu-config status patterns --format json
```

### View Configuration Status

See which repositories are enabled for automatic updates and why:

```bash
# Show which repositories are enabled (grouped by repository)
sudo apt-uu-config status config

# Group by pattern instead
sudo apt-uu-config status config --by-pattern

# Show only enabled repositories
sudo apt-uu-config status config --enabled-only

# Show only disabled repositories
sudo apt-uu-config status config --disabled-only

# Show additional metadata
sudo apt-uu-config status config --verbose

# Output as JSON
sudo apt-uu-config status config --format json
```

### Global Options

All status commands support the `--format` option:

- `--format text` (default): Rich formatted tables with color
- `--format json`: Machine-readable JSON output for scripting

> **Note**: Configuration modification commands (enable/disable, add/remove patterns) are planned for future releases. Currently, the tool provides read-only status and reporting.

## How It Works

The tool reads APT configuration using the `apt_pkg` library, which provides a merged view of all configuration sources:

1. **Global status** - Read via `apt_pkg` (APT::Periodic::Unattended-Upgrade)
2. **Configured patterns** - Read via `apt_pkg` (Unattended-Upgrade::Allowed-Origins and Origins-Pattern)
3. **Repository metadata** - Parsed from `apt-cache policy` command output
4. **Distribution info** - Detected using `lsb_release` for variable substitution

The tool combines this information to show which repositories are enabled for automatic updates based on the configured patterns.

## Development

### Setup

```sh
# Install system dependencies
sudo apt install python3-apt lsb-release

# Clone and install dependencies
git clone https://github.com/bcelary/apt-uu-config.git
cd apt-uu-config

# Create venv with system-site-packages (required for python3-apt)
uv venv --system-site-packages
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

### Common Tasks

```sh
# Run tests
task test

# Check code quality (lint + type check)
task qa

# Format code
task lint-fix

# View test coverage
task coverage
```

### Project Structure

```
apt_uu_config/
├── models/                 # Data models (Repository, UUPattern, UUConfig)
├── cli/                    # CLI commands (status implemented, write commands planned)
├── apt/                    # APT config file readers (writers planned)
├── config/                 # Application configuration
└── logging/                # Logging setup
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design documentation.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests and quality checks pass
5. Submit a pull request

See [CLAUDE.md](CLAUDE.md) for development guidelines when working with AI assistants.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **GitHub:** [https://github.com/bcelary/apt-uu-config](https://github.com/bcelary/apt-uu-config)
- **Issues:** [https://github.com/bcelary/apt-uu-config/issues](https://github.com/bcelary/apt-uu-config/issues)