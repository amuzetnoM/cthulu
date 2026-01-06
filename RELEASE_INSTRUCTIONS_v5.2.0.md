# Release Completion Instructions for v5.2.0

## Status

✅ **COMPLETED:**
- Version bumped to 5.2.0 in all files:
  - `pyproject.toml`
  - `cthulu/__main__.py`
  - `Dockerfile`
  - `.github/workflows/docker-publish.yml`
- Release notes created: `docs/Changelog/v5.2.0.md`
- CHANGELOG.md updated with v5.2.0 section
- Git tag `v5.2.0` created locally
- All changes committed to branch `copilot/review-commit-history`

⏳ **PENDING (Manual Steps Required):**

## Step 1: Push the v5.2.0 Tag

The tag has been created locally but needs to be pushed to GitHub to trigger the release workflow.

**Option A: Using the provided script**
```bash
./release_v5.2.0.sh
```

**Option B: Manual push**
```bash
git push origin v5.2.0
```

This will trigger the `docker-publish.yml` workflow automatically.

## Step 2: Monitor the Docker Build

Once the tag is pushed, GitHub Actions will automatically:

1. **Build Docker images** for `linux/amd64` and `linux/arm64` platforms
2. **Push to GHCR** (GitHub Container Registry):
   - `ghcr.io/amuzetnom/cthulu:v5.2.0`
   - `ghcr.io/amuzetnom/cthulu:5.2`
   - `ghcr.io/amuzetnom/cthulu:5` (semver major.minor)
3. **Create GitHub Release** automatically with the release notes from the workflow

**Monitor progress at:**
https://github.com/amuzetnoM/cthulu/actions/workflows/docker-publish.yml

The workflow typically takes 10-15 minutes to complete.

## Step 3: Verify the Release

Once the workflow completes:

### Verify Docker Image
```bash
# Pull the new image
docker pull ghcr.io/amuzetnom/cthulu:v5.2.0

# Verify version
docker run --rm ghcr.io/amuzetnom/cthulu:v5.2.0 python -c "from cthulu.__main__ import __version__; print(__version__)"
# Should output: 5.2.0
```

### Verify GitHub Release
Visit: https://github.com/amuzetnoM/cthulu/releases/tag/v5.2.0

The release should include:
- Title: "Cthulu v5.2.0 - Evolution"
- Release notes from the workflow
- Auto-generated release notes from GitHub
- Links to Docker images

## Step 4: Post-Release Tasks (Optional)

### Update Documentation Links
If you have external documentation or websites referencing the version:
- Update any "Current Version" badges
- Update Docker pull commands in README
- Update installation instructions if needed

### Announce the Release
Consider announcing on:
- Project discussion board
- Discord/Slack channels
- Social media
- Community forums

### Merge PR to Main
After verification, merge the PR `copilot/review-commit-history` to `main` branch to make v5.2.0 the official version.

## Troubleshooting

### If the workflow fails:
1. Check the Actions logs for specific errors
2. Common issues:
   - GHCR authentication (should use `secrets.GITHUB_TOKEN`)
   - Docker build failures (check Dockerfile syntax)
   - Missing permissions (workflow needs `packages: write`)

### If you need to re-run:
1. Delete the tag: `git tag -d v5.2.0 && git push origin :refs/tags/v5.2.0`
2. Fix any issues
3. Recreate and push the tag

### Manual release creation:
If automatic release creation fails, you can create it manually:
```bash
gh release create v5.2.0 \
  --title "Cthulu v5.2.0 - Evolution" \
  --notes-file docs/Changelog/v5.2.0.md \
  --latest
```

## Summary of Changes

**Version:** 5.1.0 → 5.2.0 (MINOR bump)  
**Commits:** 207 since v5.1.0  
**Major Features:** 60  
**Bug Fixes:** 38  

**Key Additions:**
- Web-based Backtesting UI
- Local LLM Integration (llama-cpp)
- Hektor Vector Studio
- Profit Scaler System
- Entry Confluence Filter
- Auto-tune Consolidation
- Advisory Mode
- GCP Deployment Infrastructure
- Security Hardening

**See:** `docs/Changelog/v5.2.0.md` for complete details.

---

**Next Step:** Run `./release_v5.2.0.sh` or `git push origin v5.2.0` to complete the release.
