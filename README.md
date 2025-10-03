# apt-uu-config

A Python CLI tool for managing unattended-upgrades configuration on Debian/Ubuntu systems.

**What it does:**
- **View repositories** and **Check status** - Lists system's APT repositories and shows which repositories are enabled for unattended upgrades
- **View patterns** - Displays configured unattended-upgrades patterns and their repository matches
- **Generate configuration** - Suggests optimized unattended-upgrades patterns for all system repositories

Perfect for auditing your automatic update configuration or quickly generating a complete unattended-upgrades setup for your system if you have many additional repositories.

## Installation

Requires Python 3.12+ and Debian/Ubuntu based system. We recommend using [uv](https://docs.astral.sh/uv/) for package management.

```sh
# Install system dependencies
sudo apt install python3-apt lsb-release
```

### Option 1: Install as a uv tool (recommended)

```sh
# Install directly from the repository
uv tool install --python-preference system git+https://github.com/bcelary/apt-uu-config.git

# Run
apt-uu-config <command>

# If you get permission errors, use sudo
sudo apt-uu-config <command>
```

### Option 2: Clone and run from source

```sh
# Clone and install
git clone https://github.com/bcelary/apt-uu-config.git
cd apt-uu-config
uv venv --system-site-packages
uv sync

# Activate virtual environment
source .venv/bin/activate

# Run from anywhere
apt-uu-config <command>

# If you get permission errors, use sudo
sudo apt-uu-config <command>

# Deactivate when done
deactivate
```

## Usage

> **Note:** Run `sudo apt update` before using this tool to ensure repository information is current. If the tool fails with permission errors, prefix with `sudo`.

### View Repositories

See which repositories are enabled for automatic updates:

```bash
apt-uu-config show repos
apt-uu-config show repos --enabled-only # Filter to enabled only
apt-uu-config show repos --format json  # JSON output
```

### View Patterns

See configured patterns and their repository matches:

```bash
apt-uu-config show patterns
apt-uu-config show patterns --verbose   # Show detailed matches
```

### Generate Configuration

Generate suggested unattended-upgrades patterns for your system:

```bash
apt-uu-config config                    # Show suggested patterns
apt-uu-config config --verbose          # as above but with matching repository info as comments
```

This analyzes all configured repositories and suggests appropriate patterns for `/etc/apt/apt.conf.d/50unattended-upgrades`. **The tool only displays the suggested configuration - it does not modify any files.** Copy the output into your configuration file manually.

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
