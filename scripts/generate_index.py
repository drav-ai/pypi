#!/usr/bin/env python3
"""PEP-503 compliant PyPI index generator for GitHub Pages.

This script fetches all releases from the GitHub repository and generates
a static PEP-503 compliant simple repository index.

Usage:
    python generate_index.py [--output-dir simple] [--repo drav-ai/pypi]

Environment Variables:
    GITHUB_TOKEN: GitHub token for API access (optional for public repos)
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import NamedTuple

import requests
from packaging.version import Version

GITHUB_API_URL = "https://api.github.com"
DEFAULT_REPO = "drav-ai/pypi"
DEFAULT_OUTPUT_DIR = "simple"


class WheelInfo(NamedTuple):
    """Information about a wheel file."""

    name: str
    version: str
    filename: str
    download_url: str
    sha256: str


def normalize_package_name(name: str) -> str:
    """Normalize package name per PEP-503.

    - Lowercase
    - Replace runs of [-_.] with single hyphen
    """
    return re.sub(r"[-_.]+", "-", name.lower())


def parse_wheel_filename(filename: str) -> tuple[str, str] | None:
    """Parse package name and version from wheel filename.

    Wheel filename format: {distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl

    Returns:
        Tuple of (package_name, version) or None if parsing fails.
    """
    if not filename.endswith(".whl"):
        return None

    # Remove .whl extension and split by hyphen
    base = filename[:-4]
    parts = base.split("-")

    if len(parts) < 5:
        return None

    # First part is package name (may contain underscores), second is version
    # Normalize per PEP-503: lowercase, replace runs of [-_.] with hyphen
    package_name = normalize_package_name(parts[0])
    version = parts[1]

    return package_name, version


def fetch_releases(repo: str, token: str | None = None) -> list[dict]:
    """Fetch all releases from GitHub repository.

    Args:
        repo: Repository in format 'owner/repo'
        token: Optional GitHub token for authentication

    Returns:
        List of release objects from GitHub API
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    releases = []
    page = 1
    per_page = 100

    while True:
        url = f"{GITHUB_API_URL}/repos/{repo}/releases"
        params = {"page": page, "per_page": per_page}

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        page_releases = response.json()
        if not page_releases:
            break

        releases.extend(page_releases)
        page += 1

        # Safety limit
        if page > 100:
            break

    return releases


def extract_wheels_from_releases(releases: list[dict], repo: str) -> list[WheelInfo]:
    """Extract wheel information from GitHub releases.

    Args:
        releases: List of release objects from GitHub API
        repo: Repository in format 'owner/repo'

    Returns:
        List of WheelInfo objects
    """
    wheels = []

    for release in releases:
        tag_name = release.get("tag_name", "")
        assets = release.get("assets", [])

        for asset in assets:
            filename = asset.get("name", "")
            if not filename.endswith(".whl"):
                continue

            parsed = parse_wheel_filename(filename)
            if not parsed:
                print(f"Warning: Could not parse wheel filename: {filename}", file=sys.stderr)
                continue

            package_name, version = parsed

            # Download URL for release assets
            download_url = f"https://github.com/{repo}/releases/download/{tag_name}/{filename}"

            # Get SHA256 from asset label or compute placeholder
            # GitHub doesn't provide checksums, so we use a placeholder
            # The actual checksum should be computed when uploading
            sha256 = ""

            # Check if there's a corresponding .sha256 file or label
            sha256_asset_name = f"{filename}.sha256"
            for sha_asset in assets:
                if sha_asset.get("name") == sha256_asset_name:
                    # Fetch the SHA256 content
                    sha_url = sha_asset.get("browser_download_url", "")
                    if sha_url:
                        try:
                            sha_response = requests.get(sha_url, timeout=10)
                            if sha_response.status_code == 200:
                                sha256 = sha_response.text.strip().split()[0]
                        except requests.RequestException:
                            pass
                    break

            wheels.append(
                WheelInfo(
                    name=package_name,
                    version=version,
                    filename=filename,
                    download_url=download_url,
                    sha256=sha256,
                )
            )

    return wheels


def group_wheels_by_package(wheels: list[WheelInfo]) -> dict[str, list[WheelInfo]]:
    """Group wheels by normalized package name.

    Args:
        wheels: List of WheelInfo objects

    Returns:
        Dictionary mapping package names to lists of wheels
    """
    packages: dict[str, list[WheelInfo]] = {}

    for wheel in wheels:
        normalized_name = normalize_package_name(wheel.name)
        if normalized_name not in packages:
            packages[normalized_name] = []
        packages[normalized_name].append(wheel)

    # Sort wheels within each package by version (newest first)
    # Use packaging.version.Version for proper semantic version comparison
    for package_name in packages:
        packages[package_name].sort(key=lambda w: Version(w.version), reverse=True)

    return packages


def generate_root_index(packages: dict[str, list[WheelInfo]]) -> str:
    """Generate the root index.html listing all packages.

    Args:
        packages: Dictionary mapping package names to wheels

    Returns:
        HTML content for root index
    """
    html_parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        '  <meta charset="utf-8">',
        "  <title>AIVerse PyPI Simple Index</title>",
        "</head>",
        "<body>",
        "  <h1>AIVerse PyPI Simple Index</h1>",
    ]

    # Sort packages alphabetically
    for package_name in sorted(packages.keys()):
        html_parts.append(f'  <a href="{package_name}/">{package_name}</a><br>')

    html_parts.extend(
        [
            "</body>",
            "</html>",
        ]
    )

    return "\n".join(html_parts)


def generate_package_index(package_name: str, wheels: list[WheelInfo]) -> str:
    """Generate index.html for a specific package.

    Args:
        package_name: Normalized package name
        wheels: List of wheels for this package

    Returns:
        HTML content for package index
    """
    html_parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        '  <meta charset="utf-8">',
        f"  <title>Links for {package_name}</title>",
        "</head>",
        "<body>",
        f"  <h1>Links for {package_name}</h1>",
    ]

    for wheel in wheels:
        # Include SHA256 hash fragment if available (PEP-503)
        if wheel.sha256:
            href = f"{wheel.download_url}#sha256={wheel.sha256}"
        else:
            href = wheel.download_url

        html_parts.append(f'  <a href="{href}">{wheel.filename}</a><br>')

    html_parts.extend(
        [
            "</body>",
            "</html>",
        ]
    )

    return "\n".join(html_parts)


def write_index(output_dir: Path, packages: dict[str, list[WheelInfo]]) -> None:
    """Write all index files to the output directory.

    Args:
        output_dir: Path to output directory
        packages: Dictionary mapping package names to wheels
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write root index
    root_index = generate_root_index(packages)
    root_index_path = output_dir / "index.html"
    root_index_path.write_text(root_index)
    print(f"Generated: {root_index_path}")

    # Write package indices
    for package_name, wheels in packages.items():
        package_dir = output_dir / package_name
        package_dir.mkdir(parents=True, exist_ok=True)

        package_index = generate_package_index(package_name, wheels)
        package_index_path = package_dir / "index.html"
        package_index_path.write_text(package_index)
        print(f"Generated: {package_index_path}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate PEP-503 compliant PyPI index from GitHub releases")
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPO),
        help=f"GitHub repository (default: {DEFAULT_REPO})",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for index files (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token for API access (default: GITHUB_TOKEN env var)",
    )

    args = parser.parse_args()

    print(f"Fetching releases from {args.repo}...")
    try:
        releases = fetch_releases(args.repo, args.token)
    except requests.RequestException as e:
        print(f"Error fetching releases: {e}", file=sys.stderr)
        return 1

    print(f"Found {len(releases)} releases")

    wheels = extract_wheels_from_releases(releases, args.repo)
    print(f"Found {len(wheels)} wheel files")

    packages = group_wheels_by_package(wheels)
    print(f"Found {len(packages)} unique packages")

    output_dir = Path(args.output_dir)
    write_index(output_dir, packages)

    print("Index generation complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
