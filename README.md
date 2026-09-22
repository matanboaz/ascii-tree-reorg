# ASCII Tree Reorganizer & Generator

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](pyproject.toml) [![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/) [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Build real directory structures from ASCII trees, or scan a directory and generate a portable tree. The Python engine is safe by default and works through the CLI or the Canopy desktop app.

## Features

- Strict line-numbered parsing and exact filename preservation.
- Safe copy mode by default; move, overwrite, and cleanup are explicit.
- Destination containment checks, dry-run planning, and structured diagnostics.
- Electron + React + TypeScript desktop UI for reconstruction and generation.
- Native folder selection, progress, conflict choices, and clear completion states.

## CLI

```bash
python -m pip install .
ascii-tree-reorg --tree-file data/inputs/structure.txt \
  --source-dir data/inputs/raw_archive --output-root data/outputs
```

Use `--dry-run` to preview. Use `--move`, `--overwrite`, or `--clean-relocated` only when intended.

## Canopy desktop app

```bash
npm ci
npm run dev                 # development
npm run build:desktop       # production compile check
python -m pip install ".[desktop-build]"
python scripts/build_desktop_sidecar.py
npm run package:release
```

Build desktop packages on each target OS. Configured outputs are DMG/ZIP for macOS, NSIS/ZIP for Windows, and AppImage/DEB for Linux.

## Tests

```bash
python -m pip install ".[test]"
python -m pytest -q
npm ci && npm run build:desktop
```

## Layout

- `desktop/`: React UI and Electron main/preload
- `src/ascii_tree_reorg/core/`: parser, generator, models, events, audit, conflicts
- `src/ascii_tree_reorg/desktop/`: Python sidecar protocol
- `src/ascii_tree_reorg/engine/`: safe filesystem work
- `tests/`: engine, safety, packaging, and bridge tests

MIT licensed. See [LICENSE](LICENSE).
