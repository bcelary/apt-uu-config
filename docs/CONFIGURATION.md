# Unattended-Upgrades Configuration Guide

This guide explains how to configure unattended-upgrades origin patterns in `/etc/apt/apt.conf.d/50unattended-upgrades`. Understanding these patterns helps you control exactly which repositories receive automatic updates.

## Table of Contents

- [Overview](#overview)
- [Terminology](#terminology)
- [Configuration Sections](#configuration-sections)
- [Pattern Formats](#pattern-formats)
- [Matching Fields Reference](#matching-fields-reference)
- [Common Scenarios](#common-scenarios)
- [Variable Substitution](#variable-substitution)
- [Troubleshooting](#troubleshooting)

## Overview

The unattended-upgrades system determines which packages to automatically update by matching repository metadata against configured patterns. There are two main configuration sections, each with different syntax and capabilities.

## Terminology

Understanding these terms will help you configure unattended-upgrades effectively:

### Core Concepts

**Repository (Repo)**
A server or collection of servers that hosts software packages. Think of it as an "app store" for your Linux system. Ubuntu and Debian maintain official repositories, while companies like Google, Docker, and Brave maintain their own repositories for their software.

**Origin**
The organization or entity that maintains a repository. Examples:
- `Ubuntu` - Canonical's official repositories
- `Debian` - Debian project repositories
- `Google LLC` - Google's software (Chrome, Earth)
- `Brave Software` - Brave Browser
- `Docker` - Docker containerization platform

**Suite (also called Archive)**
A specific "channel" or "pocket" within a repository that categorizes packages by purpose or stability. Common suites:
- `stable` - Well-tested, production-ready software
- `noble-security` - Security fixes for Ubuntu 24.04
- `noble-updates` - Bug fixes and improvements for Ubuntu 24.04
- `noble-backports` - Newer software versions backported to Ubuntu 24.04
- `jammy-security` - Security fixes for Ubuntu 22.04

**Codename**
The release codename for a specific version of a distribution:
- Ubuntu: `noble` (24.04), `jammy` (22.04), `focal` (20.04)
- Debian: `bookworm` (12), `bullseye` (11), `buster` (10)

Codenames make it easier to refer to releases and configure software that works across versions.

**Distribution (Distro)**
The Linux distribution you're running. Examples: Ubuntu, Debian, Linux Mint. Each distribution has its own package repositories and release cycle.

### Package Categories

**Security Updates**
Critical patches that fix security vulnerabilities. These are the highest priority updates and should almost always be installed automatically. Identified by suites ending in `-security` (e.g., `noble-security`).

**Updates**
Bug fixes, minor improvements, and non-security patches for released software. Generally safe to install automatically. Identified by suites ending in `-updates` (e.g., `noble-updates`).

**Backports**
Newer versions of software "backported" (adapted) to work with older distribution releases. These are optional and slightly riskier than regular updates since they introduce more significant changes. Identified by suites ending in `-backports`.

**Proposed Updates**
Pre-release updates being tested before general availability. These are **not recommended** for production systems unless you're helping test updates. Identified by suites ending in `-proposed`.

### Repository Structure

**Component**
A subdivision within a repository based on licensing and support level:
- `main` - Free/open-source software officially supported
- `universe` (Ubuntu) - Free/open-source software community-maintained
- `restricted` (Ubuntu) - Proprietary drivers and firmware
- `multiverse` (Ubuntu) - Software with licensing restrictions
- `contrib` (Debian) - Free software that depends on non-free software
- `non-free` (Debian) - Proprietary software

**Label**
An identifier for the repository's purpose or maintainer. Often similar to the origin but can provide additional context:
- `Ubuntu` - Standard Ubuntu repositories
- `Debian-Security` - Debian security updates
- `Ubuntu-Security` - Ubuntu security updates

**Site**
The hostname of the server hosting the repository:
- `archive.ubuntu.com` - Ubuntu's main archive
- `security.ubuntu.com` - Ubuntu security updates
- `pkgs.tailscale.com` - Tailscale's package server
- `download.docker.com` - Docker's package server

Useful for matching repositories that don't have standard origin/suite metadata.

### APT-Specific Terms

**Unattended Upgrades**
The system that automatically downloads and installs package updates without manual intervention. Configured through `/etc/apt/apt.conf.d/` files.

**APT (Advanced Package Tool)**
The package management system used by Debian, Ubuntu, and related distributions. Commands like `apt`, `apt-get`, and `apt-cache` are part of APT.

**Release File**
Metadata file published by repositories that contains information about the repository's origin, suite, codename, supported architectures, and more. This is what unattended-upgrades matches against.

### Variable Substitution

**${distro_id}**
A variable that automatically expands to your distribution name:
- Expands to `Ubuntu` on Ubuntu systems
- Expands to `Debian` on Debian systems

**${distro_codename}**
A variable that automatically expands to your release codename:
- Expands to `noble` on Ubuntu 24.04
- Expands to `jammy` on Ubuntu 22.04
- Expands to `bookworm` on Debian 12

These variables make configurations portable across different releases and distributions.

### Example: Putting It Together

When you see:
```
"${distro_id}:${distro_codename}-security"
```

On Ubuntu 24.04, this matches:
- **Origin**: Ubuntu
- **Suite**: noble-security
- **Meaning**: Security updates for Ubuntu 24.04

When you see:
```
"Brave Software:stable"
```

This matches:
- **Origin**: Brave Software
- **Suite**: stable
- **Meaning**: Stable releases from Brave Browser's official repository

## Configuration Sections

### 1. `Unattended-Upgrade::Allowed-Origins`

**Purpose**: Simple, straightforward origin matching

**Syntax**: `"origin:suite"` format (colon-separated pairs)

**When to use**:
- Most common cases
- Simple repository matching
- Distribution-provided repositories

**Example**:
```
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "Ubuntu:noble-updates";
    "Brave Software:stable";
    "Docker:noble";
};
```

### 2. `Unattended-Upgrade::Origins-Pattern`

**Purpose**: Advanced, multi-field pattern matching

**Syntax**: `"key=value,key=value"` format (comma-separated key-value pairs)

**When to use**:
- Repositories lacking standard origin/suite metadata
- Complex matching requirements (e.g., matching by site)
- Wildcard patterns across multiple fields

**Example**:
```
Unattended-Upgrade::Origins-Pattern {
    "origin=Tailscale,site=pkgs.tailscale.com";
    "origin=Oracle Corporation,codename=noble";
    "site=download.opensuse.org";
    "origin=*";
};
```

## Pattern Formats

### Format 1: Variable Substitution (Colon-Separated)

**Syntax**: `"${distro_id}:${distro_codename}[-suffix]"`

**Use case**: Distribution-provided repositories (security, updates, backports)

**Examples**:
```
"${distro_id}:${distro_codename}";           # Base release (noble)
"${distro_id}:${distro_codename}-security";  # Security updates
"${distro_id}:${distro_codename}-updates";   # General updates
"${distro_id}:${distro_codename}-backports"; # Backported packages
```

**How it works**: At runtime, variables are replaced with actual values:
- `${distro_id}` → `Ubuntu` (or `Debian`)
- `${distro_codename}` → `noble`, `jammy`, `bookworm`, etc.

### Format 2: Simple Origin:Suite

**Syntax**: `"Origin Name:suite"`

**Use case**: Third-party repositories with clear origin names

**Examples**:
```
"Brave Software:stable";     # Brave Browser
"Docker:noble";               # Docker for Ubuntu 24.04
"Google LLC:stable";          # Google Chrome/Earth
"code stable:stable";         # VS Code
"edge stable:stable";         # Microsoft Edge
```

**Note**: Origin names can contain spaces and special characters.

### Format 3: Explicit Key=Value (Allowed-Origins)

**Syntax**: `"origin=Name,suite=suite"`

**Use case**: Explicit matching when you want clarity

**Examples**:
```
"origin=Ubuntu,suite=noble-security";
"origin=Debian,suite=stable";
```

**Note**: This is more verbose but clearer than the colon-separated format.

### Format 4: Origins-Pattern (Multi-field Matching)

**Syntax**: `"field=value,field=value[,...]"`

**Use case**: Complex matching, repositories without standard metadata

**Examples**:
```
# Match by origin and site
"origin=Tailscale,site=pkgs.tailscale.com";

# Match by site only (for repos without origin)
"site=download.opensuse.org";

# Match with codename
"origin=Oracle Corporation,codename=noble";

# Multiple conditions (ALL must match)
"origin=Google LLC,suite=stable,component=main";
```

**Important**: All specified fields must match. Omitted fields act as wildcards.

### Format 5: Wildcard Patterns

**Syntax**: `"field=*"` or partial wildcards

**Use case**: Match all repositories or broad categories

**Examples**:
```
# Match ALL repositories (use with caution!)
"origin=*";

# These wildcards work in command-line tools but NOT in config files:
"*-security"          # CLI only: all security repos
"Ubuntu:*"            # CLI only: all Ubuntu repos
```

**Warning**: `"origin=*"` will update packages from ALL configured repositories, including potentially unstable sources. Use carefully.

## Matching Fields Reference

These fields come from the repository's `Release` file metadata. You can view them with `apt-cache policy`:

| Field | Aliases | Description | Example Values |
|-------|---------|-------------|----------------|
| `origin` | `o` | Repository origin/provider | `Ubuntu`, `Debian`, `Google LLC`, `Brave Software` |
| `suite` | `a`, `archive` | Release suite/archive | `stable`, `noble-security`, `jammy-updates` |
| `codename` | `n` | Distribution codename | `noble`, `jammy`, `bookworm`, `bullseye` |
| `label` | `l` | Repository label | `Ubuntu`, `Debian-Security` |
| `component` | `c` | Repository component | `main`, `universe`, `contrib`, `non-free` |
| `site` | - | Repository hostname | `pkgs.tailscale.com`, `download.docker.com` |

### Viewing Repository Metadata

To see what fields are available for a repository:

```bash
apt-cache policy
```

Example output:
```
500 http://archive.ubuntu.com/ubuntu noble/main amd64 Packages
     release v=24.04,o=Ubuntu,a=noble,n=noble,l=Ubuntu,c=main,b=amd64
```

Field mapping:
- `o=Ubuntu` → origin
- `a=noble` → suite/archive
- `n=noble` → codename
- `l=Ubuntu` → label
- `c=main` → component

### Understanding Missing Metadata

**Important**: If a field is missing from `apt-cache policy` output, the repository doesn't provide that metadata in its Release file.

**Example - Tailscale repository**:
```
500 https://pkgs.tailscale.com/stable/ubuntu noble/main amd64 Packages
     release o=Tailscale,n=noble,l=Tailscale,c=main,b=amd64
     origin pkgs.tailscale.com
```

Notice: **No `a=` (archive/suite) field!** This means:
- ✗ Cannot use: `"Tailscale:stable"` (no suite available)
- ✓ Must use: `"origin=Tailscale,site=pkgs.tailscale.com"` or `"origin=Tailscale,codename=noble"`

**When fields are missing**, use the `site` field as a fallback:
- The `origin` line (second line above) shows the hostname: `pkgs.tailscale.com`
- Match by site when standard fields are incomplete: `"site=pkgs.tailscale.com"`

**Why this happens**:
- Some repositories don't follow Debian package repository standards completely
- Third-party repos may have minimal or non-standard Release file metadata
- This is especially common with:
  - Self-hosted repositories
  - Build system repositories (OpenSUSE Build Service, PPAs)
  - Small vendor repositories

**How to handle it**:

1. **Use `apt-uu-config origin suggest`** - automatically detects missing metadata and suggests the best pattern
2. **Use `Origins-Pattern` section** with multi-field matching:
   ```
   Unattended-Upgrade::Origins-Pattern {
       "origin=Tailscale,site=pkgs.tailscale.com";  # More specific
       "site=download.opensuse.org";                 # Site-only fallback
   };
   ```
3. **Avoid using simple `"origin:suite"` format** when suite is missing or unclear (empty, ".", or otherwise meaningless)

## Common Scenarios

### Scenario 1: Security Updates Only

**Goal**: Only install security updates, nothing else

**Configuration**:
```
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};
```

### Scenario 2: Security + Stable Updates

**Goal**: Security updates plus tested stable updates

**Configuration**:
```
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}:${distro_codename}-updates";
};
```

### Scenario 3: Include Third-Party Applications

**Goal**: Auto-update browsers and applications from official sources

**Configuration**:
```
Unattended-Upgrade::Allowed-Origins {
    # System security
    "${distro_id}:${distro_codename}-security";

    # Third-party applications
    "Brave Software:stable";
    "Google LLC:stable";
    "code stable:stable";
    "Docker:noble";
};
```

### Scenario 4: Everything Including Backports

**Goal**: Keep system cutting-edge with backported packages

**Configuration**:
```
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}:${distro_codename}-updates";
    "${distro_id}:${distro_codename}-backports";
};
```

### Scenario 5: Complex Third-Party Repos

**Goal**: Handle repos with non-standard metadata

**Configuration**:
```
Unattended-Upgrade::Origins-Pattern {
    # Match by site (for repos without proper Origin field)
    "site=pkgs.tailscale.com";
    "site=download.opensuse.org";

    # Match with multiple conditions
    "origin=Oracle Corporation,codename=noble";
};
```

### Scenario 6: Conservative Auto-Updates

**Goal**: Only critical security updates, manual control for everything else

**Configuration**:
```
Unattended-Upgrade::Allowed-Origins {
    # Only security updates
    "${distro_id}:${distro_codename}-security";
};

# Also add to config:
Unattended-Upgrade::Remove-Unused-Dependencies "false";
Unattended-Upgrade::Automatic-Reboot "false";
```

## Variable Substitution

### Available Variables

| Variable | Resolves To | Example |
|----------|-------------|---------|
| `${distro_id}` | Distribution name | `Ubuntu`, `Debian` |
| `${distro_codename}` | Release codename | `noble`, `jammy`, `bookworm` |

### Special Distribution Identifiers

Ubuntu Extended Security Maintenance (ESM) uses special origin identifiers:

```
"${distro_id}ESMApps:${distro_codename}-apps-security";   # ESM Apps
"${distro_id}ESM:${distro_codename}-infra-security";      # ESM Infrastructure
```

These resolve to:
- `UbuntuESMApps:noble-apps-security`
- `UbuntuESM:noble-infra-security`

### Multi-Distribution Configs

Variables make configs portable across distributions and releases:

```
Unattended-Upgrade::Allowed-Origins {
    # Works on Ubuntu 22.04, 24.04, Debian 11, 12, etc.
    "${distro_id}:${distro_codename}-security";
};
```

## Troubleshooting

### Issue: Repository Not Being Updated

**Step 1**: Check repository metadata
```bash
apt-cache policy | grep -A1 "your-repo-name"
```

**Step 2**: Verify the pattern matches the metadata

Example metadata:
```
release o=Brave Software,a=stable,n=stable,l=Brave
```

This will match:
- ✓ `"Brave Software:stable"`
- ✓ `"origin=Brave Software,suite=stable"`
- ✗ `"Brave:stable"` (wrong origin name)

**Step 3**: Check pattern syntax
- Ensure proper quoting: `"origin:suite"` not `origin:suite`
- Verify semicolons at end of each line
- Check for typos in origin/suite names
- Ensure closing `};` bracket

### Issue: Repository Shows as DISABLED in Status

**Possible causes**:

1. **Pattern mismatch**: The configured pattern doesn't match repository metadata
   - Solution: Use `apt-cache policy` to find correct origin/suite values

2. **Wrong pattern format**: Using Allowed-Origins syntax in Origins-Pattern or vice versa
   - Solution: Keep `"origin:suite"` in Allowed-Origins, `"key=value"` in Origins-Pattern

3. **Case sensitivity**: Origin names are case-sensitive
   - Solution: Match exact case from `apt-cache policy`

### Issue: Unknown Repository Fields

If `apt-cache policy` doesn't show origin/suite for a repository:

**Solution**: Use `Origins-Pattern` with `site` field:
```
Unattended-Upgrade::Origins-Pattern {
    "site=example.com";
};
```

### Testing Configuration

After making changes:

```bash
# Test the configuration (dry run)
sudo unattended-upgrade --dry-run --debug

# Check which packages would be upgraded
sudo unattended-upgrade --dry-run -d

# Verify syntax
sudo apt-config dump | grep Unattended-Upgrade::
```

### Debugging Tips

1. **Enable debug logging**:
   ```
   Unattended-Upgrade::Debug "true";
   ```

2. **Check the log**:
   ```bash
   sudo tail -f /var/log/unattended-upgrades/unattended-upgrades.log
   ```

3. **Verify pattern matching manually**:
   ```bash
   # List all available origins
   apt-cache policy | grep -Po 'o=[^,]+' | sort -u

   # List all available suites
   apt-cache policy | grep -Po 'a=[^,]+' | sort -u
   ```

## Best Practices

1. **Start conservative**: Begin with security updates only, expand gradually
2. **Test in dry-run**: Always test new patterns with `--dry-run` first
3. **Use variables**: Prefer `${distro_id}` over hardcoded distribution names
4. **Document custom patterns**: Add comments explaining why non-standard repos are included
5. **Review logs regularly**: Check `/var/log/unattended-upgrades/` for issues
6. **Backup before changes**: Tool creates `.bak` files automatically, but verify they exist

## Additional Resources

- [Debian UnattendedUpgrades Wiki](https://wiki.debian.org/UnattendedUpgrades)
- [Ubuntu AutomaticSecurityUpdates](https://help.ubuntu.com/community/AutomaticSecurityUpdates)
- [unattended-upgrades README](https://github.com/mvo5/unattended-upgrades/blob/master/README.md)
- Manual pages: `man unattended-upgrade`, `man apt.conf`

## Related Tool Commands

### Using apt-uu-config

Instead of manually editing config files, use this tool:

```bash
# View current configuration
sudo apt-uu-config status

# Enable auto-updates for a specific origin
sudo apt-uu-config origin enable "Brave Software:stable"

# Disable updates for a pattern
sudo apt-uu-config origin disable "ubuntu:*-backports"

# Enable all security repos
sudo apt-uu-config origin enable "*-security"
```

See [README.md](../README.md) for full tool documentation.