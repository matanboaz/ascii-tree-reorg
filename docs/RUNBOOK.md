# Runbook

## Python

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install ".[test]" build twine
python -m pytest -q
python -m build
python -m twine check dist/*
```

## Desktop

```bash
npm ci
npm run dev
npm run build:desktop
python -m pip install ".[desktop-build]"
python scripts/build_desktop_sidecar.py
npm run package:release
```

Build each desktop package on its target OS. Never copy a sidecar across operating systems or architectures.

## Release

1. Update `src/ascii_tree_reorg/__init__.py`; packaging reads that version dynamically.
2. Align `package.json` and current-version docs.
3. Run Python tests, desktop compilation, package build, and `twine check`.
4. Merge through review and publish a GitHub release tagged `vX.Y.Z`.

The release workflow rejects a tag that does not match the Python package version.
