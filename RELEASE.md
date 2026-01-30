# Release Management Guide

This guide explains how to publish new versions of SkillSpector to the nv-shared-pypi Artifactory repository.

## Prerequisites

### 1. Install Development Dependencies

```bash
make install-dev
```

This installs all required tools including `build`, `twine`, and `poetry`.

### 2. Configure Authentication (One-time Setup)

The release script supports multiple authentication methods (checked in order):

#### Option 1: Poetry auth.toml (Recommended for Local Releases)

Configure Poetry with your Artifactory credentials:

```bash
poetry config http-basic.nv-shared <your-nvidia-username> <your-artifactory-token>
```

This creates/updates `~/.config/pypoetry/auth.toml` with your credentials:

```toml
[http-basic.nv-shared]
username = "your-nvidia-username"
password = "your-artifactory-token"
```

**Benefits:**
- Secure file with restrictive permissions (600)
- Single source of truth for all projects using Poetry
- No need to set environment variables

**Get your Artifactory token:**
1. Go to [https://urm.nvidia.com](https://urm.nvidia.com)
2. Click your profile → "Edit Profile" → "Authentication Settings"
3. Generate or copy your API token

#### Option 2: Environment Variables (For CI/CD)

```bash
export TWINE_USERNAME="your-nvidia-username"
export TWINE_PASSWORD="your-artifactory-token"
```

#### Option 3: ARTIFACTORY_PASSWORD (Legacy)

```bash
export ARTIFACTORY_PASSWORD="your-artifactory-token"
# Must provide --user flag when running release
```

#### Option 4: Interactive Prompt (Fallback)

If no credentials are configured, you'll be prompted to enter your password/token.

## Releasing a New Version

### Using Make (Recommended)

```bash
# Patch release (0.1.0 -> 0.1.1)
make release VERSION=patch USER=your-email@nvidia.com

# Minor release (0.1.0 -> 0.2.0)
make release VERSION=minor USER=your-email@nvidia.com

# Major release (0.1.0 -> 1.0.0)
make release VERSION=major USER=your-email@nvidia.com

# Development version (0.1.0 -> 0.1.0-dev1)
make release VERSION=dev USER=your-email@nvidia.com
```

### Using Python Script Directly

```bash
# Patch release
python release.py --version patch --user your-email@nvidia.com

# Minor release
python release.py --version minor --user your-email@nvidia.com

# Major release
python release.py --version major --user your-email@nvidia.com

# Specific version
python release.py --version 1.2.3 --user your-email@nvidia.com

# Development version
python release.py --version dev --user your-email@nvidia.com

# Dry run (see what would happen without making changes)
python release.py --version patch --user your-email@nvidia.com --dry-run
```

## Release Process

When you run a release, the following steps are executed automatically:

1. **Version Bump**: Updates version in:
   - `pyproject.toml`
   - `src/skillspector/__init__.py`

2. **Git Commit**: Commits the version change with message:
   ```
   chore: bump version to X.Y.Z
   ```

3. **Build Package**: Creates distribution files in `dist/`:
   - Source distribution (`.tar.gz`)
   - Wheel file (`.whl`)

4. **Publish**: Uploads to nv-shared-pypi Artifactory:
   - URL: `https://urm.nvidia.com/artifactory/api/pypi/nv-shared-pypi`
   - Uses credentials from auth.toml or environment variables

5. **Git Tag**: Creates and pushes a tag:
   - Release: `release/X.Y.Z`
   - Development: `dev/X.Y.Z-devN`

6. **Push to Remote**: Pushes both commit and tag to origin/main

## Version Numbering

SkillSpector follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking API changes
- **MINOR** (0.X.0): New features, backward compatible
- **PATCH** (0.0.X): Bug fixes, backward compatible
- **DEV** (0.0.0-devN): Development/pre-release versions

### Development Versions

Development versions are useful for testing before official releases:

```bash
# Create first dev version from current release (0.1.0 -> 0.1.0-dev1)
make release VERSION=dev USER=your-email@nvidia.com

# Increment dev version (0.1.0-dev1 -> 0.1.0-dev2)
make release VERSION=dev USER=your-email@nvidia.com

# Create dev version of next minor (0.1.0 -> 0.2.0-dev1)
python release.py --version minor --dev --user your-email@nvidia.com
```

## Manual Build and Publish

If you need more control, you can build and publish separately:

```bash
# Build only
make build

# Publish only (after building)
make publish

# Clean build artifacts
make clean
```

## Troubleshooting

### Authentication Failed

If you see authentication errors:

1. **Check credentials are configured**:
   ```bash
   cat ~/.config/pypoetry/auth.toml
   ```

2. **Verify Artifactory token is valid**:
   - Log in to [https://urm.nvidia.com](https://urm.nvidia.com)
   - Regenerate your API token if expired

3. **Test with curl**:
   ```bash
   curl -u "username:token" https://urm.nvidia.com/artifactory/api/pypi/nv-shared-pypi
   ```

### Git Push Failed

If the git push fails:

1. **Check you're on main branch**:
   ```bash
   git branch
   ```

2. **Check you have push access**:
   ```bash
   git remote -v
   ```

3. **Pull latest changes first**:
   ```bash
   git pull origin main
   ```

### Version Already Exists

If the version already exists in Artifactory:

1. **Check current version**:
   ```bash
   grep 'version =' pyproject.toml
   ```

2. **Check what versions exist**:
   - Browse [Artifactory](https://urm.nvidia.com/artifactory/nv-shared-pypi/skillspector/)

3. **Bump to a higher version** or use development versions

### Tag Already Exists

If a git tag already exists locally:

```bash
# Delete local tag
git tag -d release/X.Y.Z

# Delete remote tag (careful!)
git push origin :refs/tags/release/X.Y.Z
```

## Best Practices

1. **Always test before releasing**:
   ```bash
   make test
   make lint
   ```

2. **Use dry-run first** to preview changes:
   ```bash
   python release.py --version patch --user your-email@nvidia.com --dry-run
   ```

3. **Write good commit messages** before releasing:
   - Document what changed since last release
   - Update CHANGELOG if you have one

4. **Tag important releases** with descriptive messages:
   ```bash
   git tag -a release/1.0.0 -m "First stable release"
   ```

5. **Keep main branch clean**:
   - Don't commit directly to main
   - Use feature branches and merge requests

## Security Notes

- **Never commit credentials** to the repository
- **Use Artifactory tokens** instead of passwords
- **Rotate tokens regularly** (every 90 days recommended)
- **auth.toml permissions** should be 600 (user read/write only)
- **Don't share tokens** - each developer should have their own

## CI/CD Integration

For automated releases in CI/CD pipelines, use environment variables:

```yaml
# Example GitLab CI
release:
  stage: deploy
  script:
    - export TWINE_USERNAME="${ARTIFACTORY_USER}"
    - export TWINE_PASSWORD="${ARTIFACTORY_TOKEN}"
    - make release VERSION=patch USER=ci-bot@nvidia.com
  only:
    - main
```

Store `ARTIFACTORY_USER` and `ARTIFACTORY_TOKEN` as CI/CD variables (masked).
