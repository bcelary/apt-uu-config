# apt-uu-config

A Python CLI tool for managing unattended upgrades configuration on Debian/Ubuntu systems.

## Overview

`apt-uu-config` simplifies the management of automatic security updates in Debian/Ubuntu based distributions. Instead of manually editing configuration files, use this tool to enable/disable automatic updates globally or control them on a per-repository basis with pattern matching support.

### Key Features

- **Simple CLI interface**: Easy commands for managing unattended upgrades
- **Global control**: Enable/disable automatic updates system-wide
- **Repository-level control**: Configure which repositories get automatic updates (e.g., only security repos)
- **Pattern matching**: Use wildcards to enable/disable multiple repositories at once
- **Clear status display**: See all repositories and their automatic update status
- **Safe modifications**: Automatic backups created before modifying configuration files
- **No manual editing**: Never touch `/etc/apt/apt.conf.d/` files directly again

## Installation

### Prerequisites

- Python 3.12 or higher
- Debian/Ubuntu based system with APT package manager
- Root/sudo access (required for modifying system configuration)
- **System package**: `python3-apt` (install with `sudo apt install python3-apt`)

### From Source

```sh
# Install system dependency
sudo apt install python3-apt

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

> **Note**: CLI commands are currently being rewritten. Documentation will be updated once implementation is complete.

## How It Works

The tool modifies two main APT configuration files:

1. **`/etc/apt/apt.conf.d/20auto-upgrades`** - Controls global enable/disable
2. **`/etc/apt/apt.conf.d/50unattended-upgrades`** - Controls which repositories are included

All modifications create automatic `.bak` backup files before making changes.

For detailed information about configuration pattern formats and advanced usage, see the [Configuration Guide](docs/CONFIGURATION.md).

## Development

### Setup

```sh
# Install system dependency
sudo apt install python3-apt

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
├── cli/                    # CLI commands (to be implemented)
├── apt/                    # APT config file readers/writers (to be implemented)
└── config/                 # Application configuration
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