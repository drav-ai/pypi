"""Tests for PEP-503 index generation script."""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_index import (
    WheelInfo,
    generate_package_index,
    generate_root_index,
    group_wheels_by_package,
    normalize_package_name,
    parse_wheel_filename,
)


class TestNormalizePackageName:
    """Test PEP-503 package name normalization."""

    def test_underscore_to_hyphen(self) -> None:
        """Test underscores are converted to hyphens."""
        assert normalize_package_name("aiverse_schemas") == "aiverse-schemas"

    def test_period_to_hyphen(self) -> None:
        """Test periods are converted to hyphens."""
        assert normalize_package_name("aiverse.db") == "aiverse-db"

    def test_mixed_separators(self) -> None:
        """Test mixed separators are normalized to single hyphen."""
        assert normalize_package_name("My_Package.Name") == "my-package-name"

    def test_uppercase_to_lowercase(self) -> None:
        """Test uppercase is converted to lowercase."""
        assert normalize_package_name("AIVERSE_CORE") == "aiverse-core"

    def test_consecutive_separators(self) -> None:
        """Test consecutive separators are collapsed to single hyphen."""
        assert normalize_package_name("package__name..test") == "package-name-test"

    def test_hyphen_preserved(self) -> None:
        """Test existing hyphens are preserved."""
        assert normalize_package_name("aiverse-core") == "aiverse-core"


class TestParseWheelFilename:
    """Test wheel filename parsing."""

    def test_standard_wheel(self) -> None:
        """Test parsing standard wheel filename."""
        result = parse_wheel_filename("aiverse_schemas-0.0.12-py3-none-any.whl")

        assert result is not None
        package_name, version = result
        assert package_name == "aiverse-schemas"
        assert version == "0.0.12"

    def test_semver_preserved(self) -> None:
        """Test semantic version is fully preserved."""
        result = parse_wheel_filename("aiverse_core-1.2.3-py3-none-any.whl")

        assert result is not None
        _, version = result
        assert version == "1.2.3"

    def test_period_in_package_name(self) -> None:
        """Test package name with period is normalized."""
        result = parse_wheel_filename("aiverse.db-0.10.0-py3-none-any.whl")

        assert result is not None
        package_name, version = result
        assert package_name == "aiverse-db"
        assert version == "0.10.0"

    def test_complex_package_name(self) -> None:
        """Test complex package name normalization."""
        result = parse_wheel_filename("My_Package.Name-2.0.0-py3-none-any.whl")

        assert result is not None
        package_name, _ = result
        assert package_name == "my-package-name"

    def test_prerelease_version(self) -> None:
        """Test prerelease version parsing."""
        result = parse_wheel_filename("package-1.0.0a1-py3-none-any.whl")

        assert result is not None
        _, version = result
        assert version == "1.0.0a1"

    def test_postrelease_version(self) -> None:
        """Test post-release version parsing."""
        result = parse_wheel_filename("package-1.0.0.post1-py3-none-any.whl")

        assert result is not None
        _, version = result
        assert version == "1.0.0.post1"

    def test_dev_version(self) -> None:
        """Test dev version parsing."""
        result = parse_wheel_filename("package-1.0.0.dev5-py3-none-any.whl")

        assert result is not None
        _, version = result
        assert version == "1.0.0.dev5"

    def test_invalid_extension(self) -> None:
        """Test non-.whl files return None."""
        assert parse_wheel_filename("package-1.0.0.tar.gz") is None

    def test_too_few_parts(self) -> None:
        """Test filenames with too few parts return None."""
        assert parse_wheel_filename("package-1.0.0.whl") is None

    def test_no_extension(self) -> None:
        """Test filenames without extension return None."""
        assert parse_wheel_filename("package-1.0.0-py3-none-any") is None


class TestGroupWheelsByPackage:
    """Test grouping and sorting wheels by package."""

    def test_groups_by_normalized_name(self) -> None:
        """Test wheels are grouped by normalized package name."""
        wheels = [
            WheelInfo(
                "aiverse-schemas",
                "0.0.12",
                "aiverse_schemas-0.0.12-py3-none-any.whl",
                "https://example.com/0.0.12",
                "sha256:abc",
            ),
            WheelInfo(
                "aiverse-core",
                "0.1.0",
                "aiverse_core-0.1.0-py3-none-any.whl",
                "https://example.com/0.1.0",
                "sha256:def",
            ),
        ]

        packages = group_wheels_by_package(wheels)

        assert "aiverse-schemas" in packages
        assert "aiverse-core" in packages
        assert len(packages["aiverse-schemas"]) == 1
        assert len(packages["aiverse-core"]) == 1

    def test_sorts_by_semantic_version_descending(self) -> None:
        """Test wheels are sorted by semantic version, newest first."""
        wheels = [
            WheelInfo(
                "aiverse-core",
                "0.2.0",
                "aiverse_core-0.2.0-py3-none-any.whl",
                "https://example.com/0.2.0",
                "sha256:1",
            ),
            WheelInfo(
                "aiverse-core",
                "0.10.0",
                "aiverse_core-0.10.0-py3-none-any.whl",
                "https://example.com/0.10.0",
                "sha256:2",
            ),
            WheelInfo(
                "aiverse-core",
                "0.1.0",
                "aiverse_core-0.1.0-py3-none-any.whl",
                "https://example.com/0.1.0",
                "sha256:3",
            ),
            WheelInfo(
                "aiverse-core",
                "1.0.0",
                "aiverse_core-1.0.0-py3-none-any.whl",
                "https://example.com/1.0.0",
                "sha256:4",
            ),
            WheelInfo(
                "aiverse-core",
                "0.9.0",
                "aiverse_core-0.9.0-py3-none-any.whl",
                "https://example.com/0.9.0",
                "sha256:5",
            ),
        ]

        packages = group_wheels_by_package(wheels)
        versions = [w.version for w in packages["aiverse-core"]]

        # Should be sorted newest to oldest using semantic versioning
        expected = ["1.0.0", "0.10.0", "0.9.0", "0.2.0", "0.1.0"]
        assert versions == expected

    def test_handles_prerelease_versions(self) -> None:
        """Test prerelease versions sort correctly."""
        wheels = [
            WheelInfo(
                "pkg",
                "1.0.0",
                "pkg-1.0.0-py3-none-any.whl",
                "https://example.com/1.0.0",
                "sha256:1",
            ),
            WheelInfo(
                "pkg",
                "1.0.0a1",
                "pkg-1.0.0a1-py3-none-any.whl",
                "https://example.com/1.0.0a1",
                "sha256:2",
            ),
            WheelInfo(
                "pkg",
                "1.0.0b1",
                "pkg-1.0.0b1-py3-none-any.whl",
                "https://example.com/1.0.0b1",
                "sha256:3",
            ),
            WheelInfo(
                "pkg",
                "1.0.0rc1",
                "pkg-1.0.0rc1-py3-none-any.whl",
                "https://example.com/1.0.0rc1",
                "sha256:4",
            ),
        ]

        packages = group_wheels_by_package(wheels)
        versions = [w.version for w in packages["pkg"]]

        # Final release should be first, then rc, beta, alpha
        expected = ["1.0.0", "1.0.0rc1", "1.0.0b1", "1.0.0a1"]
        assert versions == expected


class TestGenerateRootIndex:
    """Test root index HTML generation."""

    def test_generates_valid_html(self) -> None:
        """Test root index generates valid HTML structure."""
        packages = {
            "aiverse-schemas": [],
            "aiverse-core": [],
        }

        html = generate_root_index(packages)

        assert "<!DOCTYPE html>" in html
        assert "<title>AIVerse PyPI Simple Index</title>" in html
        assert '<a href="aiverse-core/">aiverse-core</a>' in html
        assert '<a href="aiverse-schemas/">aiverse-schemas</a>' in html

    def test_packages_sorted_alphabetically(self) -> None:
        """Test packages are listed alphabetically."""
        packages = {
            "zebra": [],
            "alpha": [],
            "middle": [],
        }

        html = generate_root_index(packages)

        # Find positions of each package link
        alpha_pos = html.find("alpha/")
        middle_pos = html.find("middle/")
        zebra_pos = html.find("zebra/")

        assert alpha_pos < middle_pos < zebra_pos

    def test_empty_packages(self) -> None:
        """Test empty packages dict generates valid but empty index."""
        html = generate_root_index({})

        assert "<!DOCTYPE html>" in html
        assert "<h1>AIVerse PyPI Simple Index</h1>" in html


class TestGeneratePackageIndex:
    """Test package index HTML generation."""

    def test_generates_valid_html(self) -> None:
        """Test package index generates valid HTML structure."""
        wheels = [
            WheelInfo(
                "aiverse-schemas",
                "0.0.12",
                "aiverse_schemas-0.0.12-py3-none-any.whl",
                "https://github.com/drav-ai/pypi/releases/download/aiverse-schemas-0.0.12/aiverse_schemas-0.0.12-py3-none-any.whl",
                "abc123def456",
            ),
        ]

        html = generate_package_index("aiverse-schemas", wheels)

        assert "<!DOCTYPE html>" in html
        assert "<title>Links for aiverse-schemas</title>" in html
        assert "<h1>Links for aiverse-schemas</h1>" in html

    def test_includes_sha256_hash(self) -> None:
        """Test wheel links include sha256 hash fragment."""
        wheels = [
            WheelInfo(
                "pkg",
                "1.0.0",
                "pkg-1.0.0-py3-none-any.whl",
                "https://example.com/pkg-1.0.0-py3-none-any.whl",
                "abc123def456789",
            ),
        ]

        html = generate_package_index("pkg", wheels)

        assert "#sha256=abc123def456789" in html

    def test_link_format(self) -> None:
        """Test wheel link format is correct."""
        wheels = [
            WheelInfo(
                "pkg",
                "1.0.0",
                "pkg-1.0.0-py3-none-any.whl",
                "https://example.com/pkg-1.0.0-py3-none-any.whl",
                "sha256hash",
            ),
        ]

        html = generate_package_index("pkg", wheels)

        expected_link = (
            '<a href="https://example.com/pkg-1.0.0-py3-none-any.whl#sha256=sha256hash">pkg-1.0.0-py3-none-any.whl</a>'
        )
        assert expected_link in html

    def test_multiple_wheels(self) -> None:
        """Test multiple wheels are listed."""
        wheels = [
            WheelInfo(
                "pkg",
                "1.0.0",
                "pkg-1.0.0-py3-none-any.whl",
                "https://example.com/1.0.0",
                "hash1",
            ),
            WheelInfo(
                "pkg",
                "0.9.0",
                "pkg-0.9.0-py3-none-any.whl",
                "https://example.com/0.9.0",
                "hash2",
            ),
        ]

        html = generate_package_index("pkg", wheels)

        assert "pkg-1.0.0-py3-none-any.whl" in html
        assert "pkg-0.9.0-py3-none-any.whl" in html


class TestWheelInfo:
    """Test WheelInfo dataclass."""

    def test_creation(self) -> None:
        """Test WheelInfo can be created with all fields."""
        wheel = WheelInfo(
            name="aiverse-schemas",
            version="0.0.12",
            filename="aiverse_schemas-0.0.12-py3-none-any.whl",
            download_url="https://example.com/wheel.whl",
            sha256="abc123",
        )

        assert wheel.name == "aiverse-schemas"
        assert wheel.version == "0.0.12"
        assert wheel.filename == "aiverse_schemas-0.0.12-py3-none-any.whl"
        assert wheel.download_url == "https://example.com/wheel.whl"
        assert wheel.sha256 == "abc123"

    def test_equality(self) -> None:
        """Test WheelInfo equality comparison."""
        wheel1 = WheelInfo("pkg", "1.0.0", "f.whl", "url", "hash")
        wheel2 = WheelInfo("pkg", "1.0.0", "f.whl", "url", "hash")

        assert wheel1 == wheel2
