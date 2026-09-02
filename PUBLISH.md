# Publishing Omarcharium

This document describes the workflow for publishing updates to Omarcharium and making new releases available via the Omarchy Plugin Marketplace and Git distribution.

## Prerequisites

- An up-to-date Omarchy environment with `quickshell`, `pw-cat`, and Python 3.11+.
- GitHub CLI (`gh`) authenticated with repository access, or configured SSH/HTTPS Git credentials.
- Clean working directory on the `main` branch.

## Release Process

### 1. Run local validation suite

Before preparing a release, ensure all automated checks and validations pass cleanly:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/aquarium.py
bash -n scripts/launch-aquarium scripts/idle-integration scripts/select-backdrop
omarchy plugin validate .
git diff --check
```

### 2. Bump version and update documentation

1. **`manifest.json`**: Update the `"version"` field (following [Semantic Versioning](https://semver.org/)):
   ```json
   "version": "1.0.10"
   ```

2. **`CHANGELOG.md`**: Add a new release section detailing added, changed, fixed, or security-related modifications:
   ```markdown
   ## [1.0.10] - YYYY-MM-DD

   ### Added
   - Description of new features...
   ```
   Update the comparison links at the bottom of `CHANGELOG.md`.

3. **User Documentation**: If configuration keys or behavior changed, update `docs/CONFIGURATION.md` and `README.md`.

### 3. Synchronize local installation and test

Sync the updated files to the local user plugin directory to test runtime behavior in the Omarchy shell:

```bash
PLUGIN_ID="dailen.omarcharium"
PLUGIN_DIR="$HOME/.config/omarchy/plugins/$PLUGIN_ID"
mkdir -p "$PLUGIN_DIR"
cp -a --no-preserve=ownership ./. "$PLUGIN_DIR/"
omarchy restart shell
```

Verify that:
- The control room opens cleanly and reflects any new settings.
- The screensaver launches without error.
- Audio diagnostics (`python3 scripts/aquarium.py --audio-test 8`) function as expected.

### 4. Commit and tag

Commit the release changes and create an annotated Git tag matching the version:

```bash
VERSION="1.0.10"
git add manifest.json CHANGELOG.md PUBLISH.md docs/ scripts/ Config.qml defaults.json tests/
git commit -m "chore(release): prepare v${VERSION}"
git tag -a "v${VERSION}" -m "Release v${VERSION}"
```

### 5. Push to GitHub

Push both the commits and the release tag to the remote repository:

```bash
git push origin main
git push origin --tags
```

### 6. Create GitHub release

Create the GitHub Release using `gh` CLI:

```bash
VERSION="1.0.10"
gh release create "v${VERSION}" \
  --title "v${VERSION}" \
  --notes "Release notes from CHANGELOG.md"
```

Or extract the notes directly from `CHANGELOG.md`:

```bash
gh release create "v${VERSION}" \
  --title "v${VERSION}" \
  --notes-file <(sed -n "/## \[${VERSION}\]/,/## \[/p" CHANGELOG.md | sed '$d')
```

### 7. Verify CI and Marketplace Availability

1. Check the GitHub Actions CI pipeline to ensure the build and tests pass:
   ```bash
   gh run watch
   ```
2. Once the tag and release are published on GitHub, users can install or update the plugin via:
   ```bash
   omarchy plugin update dailen.omarcharium
   ```
   Or install for the first time:
   ```bash
   omarchy plugin add https://github.com/DailenG/omarcharium
   ```
