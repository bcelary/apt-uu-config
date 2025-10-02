# apt-uu-config

A Python CLI tool for managing unattended upgrades configuration on Debian/Ubuntu systems.

## Overview

`apt-uu-config` helps you understand and manage automatic security updates in Debian/Ubuntu based distributions. The tool reads your unattended-upgrades configuration and shows you exactly which repositories are enabled for automatic updates.

### Current Features

- **Clear status display**: See all repositories and their automatic update status
- **Pattern visualization**: View configured patterns and how many repositories they match
- **Flexible filtering**: Show only enabled or disabled repositories
- **Rich formatting**: Color-coded tables with detailed information
- **Variable expansion**: Shows resolved values for `${distro_id}` and `${distro_codename}`

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

### View Configuration Status

```bash
# View current configuration and status
sudo apt-uu-config status
```

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