#!/usr/bin/env python3
"""
Release script for skillspector package.
"""

import argparse
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


def parse_version(version_string: str) -> tuple[int, int, int, str | None]:
    """Parse version string into major, minor, patch, and optional dev suffix components."""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-dev(\d+))?$", version_string)
    if not match:
        raise ValueError(
            f"Invalid version format: {version_string}. Expected format: X.Y.Z or X.Y.Z-devN"
        )

    major, minor, patch, dev_num = match.groups()
    dev_suffix = f"dev{dev_num}" if dev_num else None
    return int(major), int(minor), int(patch), dev_suffix


def bump_version(current_version: str, bump_type: str) -> str:
    """Bump version according to semantic versioning rules."""
    major, minor, patch, _ = parse_version(current_version)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    if bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    if bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Invalid bump type: {bump_type}. Must be major, minor, or patch")


def bump_dev_version(current_version: str, bump_type: str) -> str:
    """Create or bump a development version."""
    major, minor, patch, dev_suffix = parse_version(current_version)

    if bump_type == "dev":
        # If already a dev version, increment the dev number
        if dev_suffix:
            dev_num = int(dev_suffix[3:])  # Extract number from "devN"
            return f"{major}.{minor}.{patch}-dev{dev_num + 1}"
        # Create first dev version from current release
        return f"{major}.{minor}.{patch}-dev1"

    # For major/minor/patch with dev flag, create dev version of the bumped version
    if bump_type == "major":
        return f"{major + 1}.0.0-dev1"
    if bump_type == "minor":
        return f"{major}.{minor + 1}.0-dev1"
    if bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}-dev1"

    raise ValueError(f"Invalid bump type: {bump_type}. Must be major, minor, patch, or dev")


def update_pyproject_version(version: str, dry_run: bool = False) -> None:
    """Update version in pyproject.toml file."""
    pyproject_path = Path("pyproject.toml")

    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found in current directory")

    if dry_run:
        logger.info(f"🔍 DRY RUN: Would update version to {version} in pyproject.toml")
        return

    # Read current content
    with pyproject_path.open(encoding="utf-8") as f:
        content = f.read()

    # Update version line
    pattern = r'^version = "([^"]+)"'
    replacement = f'version = "{version}"'

    if re.search(pattern, content, re.MULTILINE):
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    else:
        raise ValueError("Could not find version line in pyproject.toml")

    # Write updated content
    with pyproject_path.open("w", encoding="utf-8") as f:
        f.write(new_content)

    logger.info(f"✅ Updated version to {version} in pyproject.toml")


def update_init_version(version: str, dry_run: bool = False) -> None:
    """Update version in src/skillspector/__init__.py file."""
    init_path = Path("src/skillspector/__init__.py")

    if not init_path.exists():
        raise FileNotFoundError("src/skillspector/__init__.py not found")

    if dry_run:
        logger.info(f"🔍 DRY RUN: Would update version to {version} in __init__.py")
        return

    # Read current content
    with init_path.open(encoding="utf-8") as f:
        content = f.read()

    # Update version line
    pattern = r'^__version__ = "([^"]+)"'
    replacement = f'__version__ = "{version}"'

    if re.search(pattern, content, re.MULTILINE):
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    else:
        raise ValueError("Could not find __version__ line in __init__.py")

    # Write updated content
    with init_path.open("w", encoding="utf-8") as f:
        f.write(new_content)

    logger.info(f"✅ Updated version to {version} in __init__.py")


def run_command(
    command: list[str], check: bool = True, capture_output: bool = False
) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    logger.info(f"🔄 Running: {' '.join(command)}")

    try:
        return subprocess.run(command, check=check, capture_output=capture_output, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Command failed: {' '.join(command)}")
        logger.error(f"Exit code: {e.returncode}")
        if e.stdout:
            logger.error(f"stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"stderr: {e.stderr}")
        raise


def build_and_publish(user: str, dry_run: bool = False) -> None:
    """Build and publish the package using build and twine.

    Authentication can be provided via (in order of precedence):
    1. Poetry auth.toml file (~/.config/pypoetry/auth.toml) - recommended for local releases
    2. TWINE_USERNAME and TWINE_PASSWORD environment variables - recommended for CI/CD
    3. ARTIFACTORY_PASSWORD environment variable with --user flag
    4. Interactive password prompt (if none of the above are configured)
    """
    if dry_run:
        logger.info("🔍 DRY RUN: Would run build and publish commands")
        return

    # Clean and build the package
    logger.info("🔨 Building package...")
    
    # Clean dist directory if it exists
    dist_dir = Path("dist")
    if dist_dir.exists():
        import shutil
        shutil.rmtree(dist_dir)
        logger.info("   Cleaned dist directory")
    
    # Build using python -m build
    run_command([sys.executable, "-m", "build"])

    # Publish to nv-shared-pypi repository
    logger.info("📦 Publishing to nv-shared-pypi repository...")

    # Check for authentication methods
    auth_toml = Path.home() / ".config" / "pypoetry" / "auth.toml"
    twine_username = os.environ.get("TWINE_USERNAME")
    twine_password = os.environ.get("TWINE_PASSWORD")
    password = os.environ.get("ARTIFACTORY_PASSWORD")

    # Repository URL
    repo_url = "https://urm.nvidia.com/artifactory/api/pypi/nv-shared-pypi"

    # Build publish command
    publish_cmd = [
        sys.executable, 
        "-m", 
        "twine", 
        "upload", 
        "--repository-url", 
        repo_url,
        "dist/*"
    ]

    # Try to read credentials from Poetry's auth.toml first
    poetry_username = None
    poetry_password = None
    
    if auth_toml.exists():
        try:
            # Use tomllib for Python 3.11+, tomli for older versions
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib  # type: ignore
            
            with auth_toml.open("rb") as f:
                auth_data = tomllib.load(f)
                if "http-basic" in auth_data and "nv-shared" in auth_data["http-basic"]:
                    poetry_username = auth_data["http-basic"]["nv-shared"].get("username")
                    poetry_password = auth_data["http-basic"]["nv-shared"].get("password")
        except Exception as e:
            logger.warning(f"⚠️  Could not read Poetry auth.toml: {e}")

    if poetry_username and poetry_password:
        logger.info(f"🔑 Using credentials from Poetry auth.toml: {auth_toml}")
        publish_cmd.extend(["-u", poetry_username, "-p", poetry_password])
    elif twine_username and twine_password:
        logger.info("🔑 Using credentials from TWINE_USERNAME/TWINE_PASSWORD environment variables")
        publish_cmd.extend(["-u", twine_username, "-p", twine_password])
    elif password:
        logger.info("🔑 Using password from ARTIFACTORY_PASSWORD environment variable")
        publish_cmd.extend(["-u", user, "-p", password])
    else:
        logger.info("💡 You will be prompted for your Artifactory password/token")
        logger.info(f"💡 Tip: Configure credentials in {auth_toml} using:")
        logger.info("    poetry config http-basic.nv-shared <username> <password>")
        logger.info("    or set TWINE_USERNAME and TWINE_PASSWORD environment variables")
        publish_cmd.extend(["-u", user])

    run_command(publish_cmd)

    logger.info("✅ Package published successfully!")


def create_git_tag(version: str, dry_run: bool = False) -> None:
    """Create and push a Git tag for the release."""
    # Use different tag format for development versions
    tag_name = f"dev/{version}" if "-dev" in version else f"release/{version}"

    if dry_run:
        logger.info(f"🔍 DRY RUN: Would create and push tag: {tag_name}")
        return

    # Check if we're in a git repository
    try:
        run_command(["git", "status"], capture_output=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            "Not in a git repository. Please run this script from the project root."
        ) from e

    # Check if tag already exists
    try:
        result = run_command(["git", "tag", "-l", tag_name], check=False, capture_output=True)
        if tag_name in result.stdout:
            logger.info(f"⚠️  Tag {tag_name} already exists. Skipping tag creation.")
            return
    except subprocess.CalledProcessError:
        pass

    # Create tag
    logger.info(f"🏷️  Creating tag: {tag_name}")
    run_command(["git", "tag", tag_name])

    # Push tag to remote
    logger.info("📤 Pushing tag to remote...")
    run_command(["git", "push", "origin", tag_name])

    logger.info(f"✅ Tag {tag_name} created and pushed successfully!")


def commit_version_change(version: str, dry_run: bool = False) -> None:
    """Commit the version change to git."""
    if dry_run:
        logger.info("🔍 DRY RUN: Would commit version change")
        return

    # Add the modified files
    run_command(["git", "add", "pyproject.toml", "src/skillspector/__init__.py"])

    # Commit with descriptive message
    commit_message = f"chore: bump version to {version}"
    run_command(["git", "commit", "-m", commit_message])

    # Push the commit
    run_command(["git", "push", "origin", "main"])

    logger.info("✅ Version change committed and pushed")


def main():
    """Main function to handle the release process."""
    parser = argparse.ArgumentParser(
        description="Release script for skillspector package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard releases (publishes to nv-shared-pypi artifactory)
  python release.py --version major --user nraghavan@nvidia.com
  python release.py --version minor --user nraghavan@nvidia.com
  python release.py --version patch --user nraghavan@nvidia.com
  python release.py --version 1.2.3 --user nraghavan@nvidia.com
  
  # Development versions
  python release.py --version dev --user nraghavan@nvidia.com          # 0.1.0 -> 0.1.0-dev1
  python release.py --version minor --dev --user nraghavan@nvidia.com  # 0.1.0 -> 0.2.0-dev1
  python release.py --version 0.2.0-dev2 --user nraghavan@nvidia.com  # Set specific dev version
  
  # Dry run (shows what would happen without making changes)
  python release.py --version minor --user nraghavan@nvidia.com --dry-run
        """,
    )

    parser.add_argument(
        "--version",
        "-v",
        required=True,
        help="Version bump type (major|minor|patch|dev) or specific version (X.Y.Z or X.Y.Z-devN)",
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="Create a development version (can be combined with major/minor/patch)",
    )

    parser.add_argument(
        "--user", "-u", required=True, help="User email for publishing (e.g., nraghavan@nvidia.com)"
    )

    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Show what would be done without actually doing it",
    )

    args = parser.parse_args()

    try:
        # Read current version from pyproject.toml
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.exists():
            raise FileNotFoundError("pyproject.toml not found in current directory")

        with pyproject_path.open(encoding="utf-8") as f:
            content = f.read()

        version_match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
        if not version_match:
            raise ValueError("Could not find version in pyproject.toml")

        current_version = version_match.group(1)

        # Determine the new version
        if args.version in ["major", "minor", "patch", "dev"]:
            # Check if --dev flag is used with major/minor/patch
            if args.dev and args.version != "dev":
                new_version = bump_dev_version(current_version, args.version)
                logger.info(
                    f"🔄 Creating development version from {current_version} to {new_version}"
                )
            elif args.version == "dev" or args.dev:
                new_version = bump_dev_version(current_version, "dev")
                logger.info(
                    f"🔄 Bumping development version from {current_version} to {new_version}"
                )
            else:
                new_version = bump_version(current_version, args.version)
                logger.info(f"🔄 Bumping version from {current_version} to {new_version}")
        else:
            # Specific version provided - validate format first
            try:
                parse_version(args.version)
                new_version = args.version
                logger.info(f"🎯 Setting version to {new_version}")
            except ValueError as e:
                raise ValueError(f"Invalid version format: {args.version}. {e}") from e

        # Update version in both files
        update_pyproject_version(new_version, args.dry_run)
        update_init_version(new_version, args.dry_run)

        # Commit the version change
        commit_version_change(new_version, args.dry_run)

        # Build and publish
        build_and_publish(args.user, args.dry_run)

        # Create git tag
        create_git_tag(new_version, args.dry_run)

        logger.info(f"\n🎉 Release {new_version} completed successfully!")
        if args.dry_run:
            logger.info("🔍 This was a dry run - no actual changes were made.")

    except Exception as e:
        logger.error(f"\n❌ Release failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
