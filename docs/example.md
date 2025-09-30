# Architecture

## Overview

apt-uu-config is structured in three main layers:

1. **CLI Layer** - Command-line interface using Click
2. **Business Logic Layer** - APT configuration management
3. **Data Layer** - Models and configuration readers/writers

## Component Diagram

```mermaid
graph TD
    CLI[CLI Commands] --> ConfigReader[Config Reader]
    CLI --> ConfigWriter[Config Writer]
    CLI --> OriginDetector[Origin Detector]

    ConfigReader --> Models[Data Models]
    ConfigWriter --> Models
    OriginDetector --> Models

    ConfigReader --> APT[APT Config Files]
    ConfigWriter --> APT
    OriginDetector --> APT

    Models --> Origin[Origin Model]
    Models --> UUConfig[UU Config Model]
```

## Key Components

### CLI Commands

- **status**: Display current configuration and repository list
- **enable/disable**: Toggle unattended upgrades globally
- **origin enable/disable**: Manage per-repository settings

### APT Module

- **ConfigReader**: Reads APT configuration files
  - `/etc/apt/apt.conf.d/20auto-upgrades`
  - `/etc/apt/apt.conf.d/50unattended-upgrades`

- **ConfigWriter**: Writes APT configuration with backups
  - Creates `.bak` files before modifications
  - Validates configuration syntax

- **OriginDetector**: Discovers available repositories
  - Parses `apt-cache policy` output
  - Reads `/var/lib/apt/lists/` Release files

- **SourcesParser**: Parses sources.list files
  - `/etc/apt/sources.list`
  - `/etc/apt/sources.list.d/*.list`

### Models

- **Origin**: Represents a repository origin
  - Includes origin name, suite, codename
  - Pattern matching for wildcards

- **UnattendedUpgradesConfig**: Configuration state
  - Global enabled/disabled status
  - List of enabled origins

## Configuration Flow

```mermaid
sequenceDiagram
    User->>CLI: apt-uu-config status
    CLI->>ConfigReader: is_globally_enabled()
    ConfigReader->>APT: Read 20auto-upgrades
    APT-->>ConfigReader: Status
    CLI->>ConfigReader: get_enabled_origins()
    ConfigReader->>APT: Read 50unattended-upgrades
    APT-->>ConfigReader: Origin list
    CLI->>OriginDetector: get_all_origins()
    OriginDetector->>APT: apt-cache policy
    APT-->>OriginDetector: Repository info
    OriginDetector-->>CLI: All origins
    CLI-->>User: Display table
```
