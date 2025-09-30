# apt-uu-config

A Python CLI tool for managing unattended upgrades configuration on Debian/Ubuntu systems.

## Overview

`apt-uu-config` simplifies the management of automatic security updates in Debian/Ubuntu based distributions. Instead of manually editing configuration files, use this tool to enable/disable automatic updates globally or control them on a per-repository basis with pattern matching support.

### Key Features

- **Simple CLI interface**: Easy commands for managing unattended upgrades
- **Global control**: Enable/disable automatic updates system-wide
- **Repository-level control**: Configure which repositories get automatic updates (e.g., only security repos)
- **Pattern matching**: Use wildcards to enable/disable multiple repositories at once
- **Clear status display**: See all repositories and their automatic update status in a formatted table
- **Safe modifications**: Automatic backups created before modifying configuration files
- **No manual editing**: Never touch `/etc/apt/apt.conf.d/` files directly again

## Installation

### Prerequisites

- Python 3.12 or higher
- Debian/Ubuntu based system with APT package manager
- Root/sudo access (required for modifying system configuration)

### From Source

```sh
git clone https://github.com/bcelary/apt-uu-config.git
cd apt-uu-config
uv sync
```

Then run using:
```sh
sudo uv run apt-uu-config <command>
```

## Usage

### Quick Examples

```sh
# Check current status and list all repositories
sudo uv run apt-uu-config status

# Enable unattended upgrades globally
sudo uv run apt-uu-config enable

# Disable unattended upgrades globally
sudo uv run apt-uu-config disable

# Enable automatic updates for a specific repository
sudo uv run apt-uu-config origin enable "google-chrome"

# Disable automatic updates for a repository pattern
sudo uv run apt-uu-config origin disable "ubuntu:jammy-updates"

# Enable automatic updates for all security repositories
sudo uv run apt-uu-config origin enable "*-security"
```

### Command Reference

### `status`

Displays the current configuration status:
- Global unattended upgrades status (enabled/disabled)
- All APT repositories and their automatic update status

**Example output:**
```
Unattended Upgrades: ✓ ENABLED

Repository Origins:
┌─────────────────────────┬───────────────────┬──────────┐
│ Origin                  │ Suite             │ Status   │
├─────────────────────────┼───────────────────┼──────────┤
│ Ubuntu                  │ jammy-security    │ ENABLED  │
│ Ubuntu                  │ jammy-updates     │ DISABLED │
│ Google LLC              │ stable            │ ENABLED  │
└─────────────────────────┴───────────────────┴──────────┘
```

### `enable` / `disable`

Globally enable or disable unattended upgrades system-wide.

Modifies: `/etc/apt/apt.conf.d/20auto-upgrades`

**Examples:**
```sh
sudo uv run apt-uu-config enable
# Output: ✓ Unattended upgrades enabled successfully

sudo uv run apt-uu-config disable
# Output: ✓ Unattended upgrades disabled successfully
```

### `origin enable <pattern>` / `origin disable <pattern>`

Enable or disable automatic updates for specific repositories using pattern matching.

Modifies: `/etc/apt/apt.conf.d/50unattended-upgrades`

**Pattern types:**
- Exact origin: `google-chrome`
- Origin with suite: `ubuntu:jammy-security`
- Wildcards: `*-security`, `ubuntu:*`

**Examples:**
```sh
# Enable security updates for Ubuntu 22.04
sudo uv run apt-uu-config origin enable "ubuntu:jammy-security"

# Enable all security repositories
sudo uv run apt-uu-config origin enable "*-security"

# Disable updates repository
sudo uv run apt-uu-config origin disable "ubuntu:jammy-updates"

# Enable Chrome repository
sudo uv run apt-uu-config origin enable "google-chrome"
```

## Use Cases

### Enable Security Updates Only

```sh
# Enable unattended upgrades globally
sudo uv run apt-uu-config enable

# Enable only security repositories
sudo uv run apt-uu-config origin enable "*-security"
```

### Add Third-Party Repository Updates

```sh
# After adding a third-party repository (e.g., Docker, Chrome)
# Enable automatic updates for it
sudo uv run apt-uu-config origin enable "google-chrome"
sudo uv run apt-uu-config origin enable "docker"
```

### Disable All But Security Updates

```sh
# Check what's currently enabled
sudo uv run apt-uu-config status

# Disable non-security repos
sudo uv run apt-uu-config origin disable "ubuntu:*-updates"
sudo uv run apt-uu-config origin disable "ubuntu:*-backports"
```

## How It Works

The tool modifies two main APT configuration files:

1. **`/etc/apt/apt.conf.d/20auto-upgrades`** - Controls global enable/disable
2. **`/etc/apt/apt.conf.d/50unattended-upgrades`** - Controls which repositories are included

All modifications create automatic `.bak` backup files before making changes.

## Development

### Setup

```sh
# Clone and install dependencies
git clone https://github.com/bcelary/apt-uu-config.git
cd apt-uu-config
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
apt_unattended_config/
├── cli/                    # CLI commands (status, enable, disable, origin)
├── apt/                    # APT config file readers/writers
├── models/                 # Data models (Origin, UnattendedUpgradesConfig)
└── config/                 # Application configuration
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests and quality checks pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **GitHub:** [https://github.com/bcelary/apt-uu-config](https://github.com/bcelary/apt-uu-config)
- **Issues:** [https://github.com/bcelary/apt-uu-config/issues](https://github.com/bcelary/apt-uu-config/issues)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)

