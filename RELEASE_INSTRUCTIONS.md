# Instructions for Creating v5.0.1 Release

## Tag Already Created
The tag `v5.0.1` has been created locally on commit `15b5534`.

## To Push the Tag
```bash
git push origin v5.0.1
```

## To Create GitHub Release

### Option 1: Using GitHub CLI
```bash
gh release create v5.0.1 \
  --title "v5.0.1 - Cthulu Rebranding" \
  --notes-file docs/release_notes/v5.0.1.md \
  --draft \
  --target copilot/update-branding-to-cthulu
```

### Option 2: Using GitHub Web Interface
1. Go to: https://github.com/amuzetnoM/herald/releases/new
2. Tag version: `v5.0.1`
3. Target branch: `copilot/update-branding-to-cthulu`
4. Release title: `v5.0.1 - Cthulu Rebranding`
5. Copy content from `docs/release_notes/v5.0.1.md` into the description
6. Check "Set as a pre-release" or "Create a draft release"
7. Click "Publish release" or "Save draft"

## Release Notes
The full release notes are available in: `docs/release_notes/v5.0.1.md`

## Key Changes in v5.0.1
- Complete rebranding from Herald to Cthulu
- 150+ files updated with ~978 references changed
- All 156 unit tests passing
- Added GitHub Actions CI/CD workflow
- No functional changes, branding only

## CI/CD Status
The GitHub Actions workflow will automatically run when the PR is merged or the tag is pushed:
- Multi-OS testing (Ubuntu, Windows)
- Multi-Python version (3.10, 3.11, 3.12)
- Code linting and formatting checks
- Test coverage reporting

## Verification Steps
Before releasing, verify:
- [ ] All unit tests pass: `python -m pytest tests/unit/ -v`
- [ ] Package installs correctly: `pip install -e .`
- [ ] Imports work: `python -c "from cthulu import __version__; print(__version__)"`
- [ ] CLI works: `python -m Cthulu --help`




