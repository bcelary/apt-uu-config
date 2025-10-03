# apt-uu-config

A Python CLI tool for viewing unattended-upgrades configuration on Debian/Ubuntu systems.

Shows which APT repositories are enabled for automatic security updates by reading your unattended-upgrades configuration and matching patterns against available repositories.

> **Note**: Currently read-only. Configuration modification features are planned for future releases.

## Installation

Requires Python 3.12+ and Debian/Ubuntu based system.

```sh
# Install system dependencies
sudo apt install python3-apt lsb-release

# Clone and install
git clone https://github.com/bcelary/apt-uu-config.git
cd apt-uu-config
uv venv --system-site-packages
uv sync

# Run (some systems require sudo to read APT config)
sudo uv run apt-uu-config <command>
```

## Usage

### View Repositories

See which repositories are enabled for automatic updates:

```bash
sudo apt-uu-config show repos
sudo apt-uu-config show repos --enabled-only     # Filter to enabled only
sudo apt-uu-config show repos --format json      # JSON output
```

### View Patterns

See configured patterns and their repository matches:

```bash
sudo apt-uu-config show patterns
sudo apt-uu-config show patterns --verbose       # Show detailed matches
```

### Generate Configuration

Generate suggested unattended-upgrades patterns for your system:

```bash
apt-uu-config config                             # Show suggested patterns
apt-uu-config config --verbose                   # Show repository details as comments
```

This analyzes all configured repositories and suggests appropriate patterns for `/etc/apt/apt.conf.d/50unattended-upgrades`. The output can be copied directly into your configuration file.

### Common Options

- `--format [text|json]` - Output format (default: text)
- `--verbose` - Show additional details
- `--enabled-only` / `--disabled-only` - Filter repositories
- `--primary-arch-only` - Filter to primary architecture

## Development

```sh
# Install system dependencies
sudo apt install python3-apt lsb-release

# Clone and setup
git clone https://github.com/bcelary/apt-uu-config.git
cd apt-uu-config
uv venv --system-site-packages
uv sync
uv run pre-commit install

# Run tests and checks
uv run pytest tests/
pre-commit run --all-files
```

## Contributing

Contributions welcome! Please ensure tests pass (`pre-commit run --all-files`) before submitting a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **GitHub:** [https://github.com/bcelary/apt-uu-config](https://github.com/bcelary/apt-uu-config)
- **Issues:** [https://github.com/bcelary/apt-uu-config/issues](https://github.com/bcelary/apt-uu-config/issues)
