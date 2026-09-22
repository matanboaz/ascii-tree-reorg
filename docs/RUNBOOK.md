# Contributor and release runbook

## Source setup and validation

```bash
python -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install ".[test,desktop-build]" build twine
npm ci
python -m pytest -q
npm run test:ui
npm run build:desktop
python -m build
python -m twine check dist/*
```

Build the frozen sidecar before desktop packaging:

```bash
python scripts/build_desktop_sidecar.py
npm run package          # unpacked native directory
npm run package:release  # configured native installers/archives
```

Build each platform on that target operating system and architecture. Never copy a sidecar between OSes or architectures.

## Local desktop development

`npm run dev` serves only the renderer. For Electron hot reload:

1. Run `npm run dev` and note the local URL.
2. In a second terminal, set `VITE_DEV_SERVER_URL` to that URL.
3. Run `npx electron .` after compiling Electron TypeScript, or use `npm run build:desktop` first.

For a simpler production-like local run, build the sidecar then run `npm run start:desktop`.

## Python release path

1. Update `src/ascii_tree_reorg/__init__.py`.
2. Align `package.json` and the README version badge.
3. Run all Python/UI tests, builds, `twine check`, and installed-wheel smoke.
4. Merge reviewed changes.
5. Publish a GitHub release tagged `vX.Y.Z`.

`.github/workflows/publish.yml` checks that the tag matches the Python version and publishes the sdist/wheel to PyPI with trusted publishing.

## Desktop release path

`.github/workflows/desktop-release.yml` builds on native runners:

| Runner | Architecture | Outputs |
| --- | --- | --- |
| Ubuntu | x64 | AppImage, DEB |
| macOS 14 | arm64 | DMG, ZIP |
| Windows | x64 | NSIS installer, ZIP |

Every leg runs Python and UI tests, freezes the platform sidecar, builds artifacts, smoke-tests the packaged sidecar, writes a platform SHA-256 manifest, and uploads artifacts. Published releases attach the artifacts to the GitHub Release.

Published desktop releases fail closed:

- macOS requires the configured certificate plus Apple ID/team credentials, then verifies `codesign` and the notarization staple.
- Windows requires a signing certificate and verifies a valid Authenticode signature on the installer.
- Release tag, desktop version, and Python version must agree.

Manual `workflow_dispatch` builds are useful for artifact testing, but without signing secrets they are not public-release candidates.

## Air-gapped use

The installed Canopy application and frozen sidecar make no required runtime network calls; fonts/assets are bundled and Electron denies navigation and permission requests. For an air-gapped transfer:

1. Build/sign on a controlled connected system or CI.
2. Transfer the installer/archive and matching SHA-256 manifest through the approved media process.
3. Verify the checksum and code signature before import.
4. Retain the exact artifact, manifest, source commit, and release tag for rollback.
5. Test the package on the same Windows/macOS/Linux architecture used inside the gap.

The source build itself is not offline by default: npm/pip/PyInstaller/electron-builder download dependencies. Preparing an offline build requires a pinned wheelhouse, npm cache or internal registry, Electron/electron-builder caches, and license/SBOM review.
