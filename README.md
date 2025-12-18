# AIVerse PyPI Repository

A PEP-503 compliant Python package index hosted on GitHub Pages (private repository).

## Overview

This repository hosts Python wheels for AIVerse internal packages. The index is automatically regenerated when new releases are published.

**Index URL**: `https://drav-ai.github.io/pypi/simple/`

**Visibility**: Private repository (GitHub Team tier)

## Available Packages

| Package | Description |
|---------|-------------|
| aiverse-schemas | Pydantic schemas for API contracts and data models |
| aiverse-utils | Shared utilities (logging, telemetry, helpers) |
| aiverse-core | Core business logic and domain services |
| aiverse-db | Database models and migrations (SQLAlchemy) |
| aiverse-infra | Infrastructure clients (Redis, S3, messaging) |

## Authentication

Since this is a private repository, downloading wheels requires GitHub authentication.

### GitHub Token Setup

Create a Personal Access Token (PAT) with `read:packages` scope:
1. Go to https://github.com/settings/tokens/new
2. Select scopes: `read:packages`, `repo` (for private repo access)
3. Generate and save the token

### Environment Variable

Set the token as an environment variable:

```bash
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

## Usage

### pip install (with authentication)

```bash
pip install aiverse-schemas \
    --extra-index-url https://drav-ai.github.io/pypi/simple/ \
    --trusted-host drav-ai.github.io \
    --trusted-host github.com
```

For wheel downloads from private releases, configure pip with netrc:

```bash
# ~/.netrc (Linux/macOS) or %USERPROFILE%\_netrc (Windows)
machine github.com
    login oauth
    password ghp_xxxxxxxxxxxxxxxxxxxx
```

### requirements.txt

```
--extra-index-url https://drav-ai.github.io/pypi/simple/
--trusted-host drav-ai.github.io
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
trusted-host = 
    drav-ai.github.io
    github.com
```

### Dockerfile

```dockerfile
# Pass GITHUB_TOKEN as build arg
ARG GITHUB_TOKEN

# Configure netrc for GitHub authentication
RUN echo "machine github.com\n  login oauth\n  password ${GITHUB_TOKEN}" > ~/.netrc && \
    chmod 600 ~/.netrc

# Install packages
RUN pip install -r requirements.txt \
    --extra-index-url https://drav-ai.github.io/pypi/simple/ \
    --trusted-host drav-ai.github.io \
    --trusted-host github.com

# Remove netrc after install (security)
RUN rm -f ~/.netrc
```

Build with:
```bash
docker build --build-arg GITHUB_TOKEN=$GITHUB_TOKEN -t myimage .
```

### GitHub Actions CI

```yaml
- name: Install dependencies
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    echo "machine github.com" >> ~/.netrc
    echo "  login oauth" >> ~/.netrc
    echo "  password $GITHUB_TOKEN" >> ~/.netrc
    chmod 600 ~/.netrc
    pip install -r requirements.txt \
      --extra-index-url https://drav-ai.github.io/pypi/simple/
```

## How It Works

1. Wheels are uploaded as GitHub Release assets to this repository
2. A GitHub Action regenerates the PEP-503 compliant index
3. The index is committed to the `main` branch in `simple/`
4. GitHub Pages serves the index at `https://drav-ai.github.io/pypi/simple/`
5. Wheel downloads from releases require GitHub authentication

## Publishing Packages

Use `aiverse-build` to publish packages:

```bash
# Publish and wait for index to update
aiverse-build publish-wheel aiverse-schemas -v 0.0.12 --wait

# Fire-and-forget (index updates asynchronously)
aiverse-build publish-wheel aiverse-schemas -v 0.0.12 --no-wait
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
  tests/
    test_generate_index.py
  simple/                 # Generated PEP-503 index (served by GitHub Pages)
    index.html
    aiverse-schemas/
      index.html
    ...
  README.md
```

## Security Notes

- Never commit tokens to the repository
- Use short-lived tokens where possible
- In CI/CD, use `${{ secrets.GITHUB_TOKEN }}` which is automatically provided
- Remove `.netrc` files after pip install in Docker builds

## License

Apache-2.0
