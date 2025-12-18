# AIVerse PyPI Repository

A PEP-503 compliant Python package index hosted on GitHub Pages.

## Overview

This repository hosts Python wheels for AIVerse internal packages. The index is automatically regenerated when new releases are published.

**Index URL**: `https://drav-ai.github.io/pypi/simple/`

## Available Packages

| Package | Description |
|---------|-------------|
| aiverse-schemas | Pydantic schemas for API contracts and data models |
| aiverse-utils | Shared utilities (logging, telemetry, helpers) |
| aiverse-core | Core business logic and domain services |
| aiverse-db | Database models and migrations (SQLAlchemy) |
| aiverse-infra | Infrastructure clients (Redis, S3, messaging) |

## Usage

### pip install

```bash
pip install aiverse-schemas --extra-index-url https://drav-ai.github.io/pypi/simple/
```

### requirements.txt

```
--extra-index-url https://drav-ai.github.io/pypi/simple/
aiverse-schemas>=0.0.12
aiverse-utils>=0.0.11
aiverse-core>=0.0.11
aiverse-db>=0.0.16
aiverse-infra>=0.0.14
```

### pip.conf

For development machines, add to `~/.pip/pip.conf` (Linux/macOS) or `%APPDATA%\pip\pip.ini` (Windows):

```ini
[global]
extra-index-url = https://drav-ai.github.io/pypi/simple/
trusted-host = drav-ai.github.io
```

### Dockerfile

```dockerfile
RUN pip install -r requirements.txt \
    --extra-index-url https://drav-ai.github.io/pypi/simple/
```

## How It Works

1. Wheels are uploaded as GitHub Release assets to this repository
2. A GitHub Action regenerates the PEP-503 compliant index
3. The index is pushed to the `gh-pages` branch
4. GitHub Pages serves the index at `https://drav-ai.github.io/pypi/simple/`

## Publishing Packages

Use `aiverse-build` to publish packages:

```bash
# Publish and wait for index to update
aiverse-build publish-wheel aiverse-schemas --version 0.0.12 --wait

# Fire-and-forget (index updates asynchronously)
aiverse-build publish-wheel aiverse-schemas --version 0.0.12
```

## Manual Index Regeneration

Trigger the GitHub Action manually:

```bash
gh workflow run update-index.yml --repo drav-ai/pypi
```

## PEP-503 Compliance

This repository implements the [PEP 503 - Simple Repository API](https://peps.python.org/pep-0503/):

- Package names are normalized (lowercase, hyphens)
- Links include SHA256 hash fragments for integrity verification
- Content-Type headers are set correctly by GitHub Pages

## Repository Structure

```
pypi/
  .github/
    workflows/
      update-index.yml    # Regenerates index on release/dispatch
  scripts/
    generate_index.py     # PEP-503 index generator
  simple/                 # Generated index (on gh-pages branch)
    index.html
    aiverse-schemas/
      index.html
    ...
  README.md
```

## License

Apache-2.0

