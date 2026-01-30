# Release Management Guide

Advanced guide for publishing SkillSpector releases. For basic usage, see [README.md](README.md#release-management).

## Quick Reference

### Setup Credentials (One-time)

```bash
# Recommended: Poetry auth.toml
poetry config http-basic.nv-shared <username> <token>

# Alternative: Environment variables
export TWINE_USERNAME="<username>"
export TWINE_PASSWORD="<token>"
```

Get token: [https://urm.nvidia.com](https://urm.nvidia.com) → Profile → Authentication Settings

### Release Commands

```bash
# Standard releases
make release VERSION=patch USER=user@nvidia.com   # 0.1.0 -> 0.1.1
make release VERSION=minor USER=user@nvidia.com   # 0.1.0 -> 0.2.0
make release VERSION=major USER=user@nvidia.com   # 0.1.0 -> 1.0.0

# Development versions
make release VERSION=dev USER=user@nvidia.com     # 0.1.0 -> 0.1.0-dev1

# Dry run (preview changes)
python release.py --version patch --user user@nvidia.com --dry-run
```

## Troubleshooting

### Authentication Issues
```bash
# Verify credentials are configured
cat ~/.config/pypoetry/auth.toml

# Test Artifactory access
curl -u "username:token" https://urm.nvidia.com/artifactory/api/pypi/nv-shared-pypi

# Regenerate token if expired
# Visit: https://urm.nvidia.com → Profile → Authentication Settings
```

### Git Issues
```bash
# Version already exists → Bump to next version
grep 'version =' pyproject.toml

# Tag already exists → Delete and recreate
git tag -d release/X.Y.Z

# Push failed → Pull latest first
git pull origin main
```

### Build Issues
```bash
# Clean and rebuild
make clean
make build

# Manual publish
python -m twine upload --repository-url https://urm.nvidia.com/artifactory/api/pypi/nv-shared-pypi dist/*
```

## CI/CD Integration

### GitLab CI Example
```yaml
release:
  stage: deploy
  script:
    - export TWINE_USERNAME="${ARTIFACTORY_USER}"
    - export TWINE_PASSWORD="${ARTIFACTORY_TOKEN}"
    - make release VERSION=patch USER=ci-bot@nvidia.com
  only:
    - main
  when: manual
```

### GitHub Actions Example
```yaml
- name: Publish Release
  env:
    TWINE_USERNAME: ${{ secrets.ARTIFACTORY_USER }}
    TWINE_PASSWORD: ${{ secrets.ARTIFACTORY_TOKEN }}
  run: make release VERSION=patch USER=ci-bot@nvidia.com
```

**Security:** Store credentials as masked CI/CD variables, rotate tokens every 90 days.

## Best Practices

1. Test before releasing: `make test && make lint`
2. Preview with dry-run: `python release.py --version patch --dry-run`
3. Use semantic versioning: MAJOR.MINOR.PATCH
4. Use dev versions for testing: `make release VERSION=dev`
5. Keep auth.toml permissions at 600
6. Never commit credentials to repository
