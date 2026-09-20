# ASCII Tree Reorganizer & Generator (`ascii-tree-reorg`)

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](pyproject.toml)
[![Python](https://img.shields.io/badge/python-3.9+-brightgreen.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A modular, zero-external-dependency utility to bridge the gap between directory structures and text specifications. It provides bidirectional capability:  

1. **Reconstruction**: Takes a flat or disorganized collection of files and an ASCII/Unicode directory tree, parses parent-child relationships, audits collisions, and arranges files into their exact paths.
2. **Generation (New in v0.2.0)**: Scans any local directory and generates clean, customizable ASCII tree text matching the standard `tree` format with custom depth limits and file-filtering options.

Operates via a terminal CLI, scriptable Python API, or a dual-tab desktop GUI. Designed to run offline in air-gapped environments without third-party dependencies.

---

## Features

* **Bidirectional Workflow**: Reorganize flat files into a tree, or reverse-engineer any directory into an ASCII tree diagram.
* **Dual-Tab GUI**: Built-in Tkinter desktop interface with real-time logs, progress tracking, file-dialog pickers, and clipboard export.
* **Safe Non-Destructive Default**: Uses `shutil.copy2` by default to preserve file metadata and timestamps. File moves (`shutil.move`) are opt-in (`--move`).
* **Auto-Adaptive Indentation**: Infers indentation step size (e.g., 2-space vs. 4-space) using Greatest Common Divisor (GCD) logic, warning and adapting automatically.
* **Pre-Flight Structural Audit**: Identifies exact tree path collisions, duplicate basenames across branches, and duplicate source files before disk mutations.
* **Interactive Disambiguation**: In terminal mode, conflicts prompt for source candidate selection with size and timestamp metadata. In GUI mode, choices are logged and managed safely.
* **Zero Dependencies**: Relies exclusively on the Python standard library (`pathlib`, `shutil`, `argparse`, `dataclasses`, `tkinter`).

---

## Directory Structure

```text
ascii_tree_reorg/
├── configs/
│   └── default_config.json
├── data/
│   ├── inputs/
│   │   ├── raw_archive/           # Source files for reconstruction
│   │   └── structure.txt          # Input ASCII tree specification
│   └── outputs/                   # Auto-generated timestamped run folders
├── docs/
│   ├── ARCHITECTURE.md
│   ├── FUNCTIONAL_SPEC.md
│   ├── PRD.md
│   └── RUNBOOK.md
├── src/
│   └── ascii_tree_reorg/
│       ├── core/
│       │   ├── auditor.py
│       │   ├── generator.py       # (v0.2.0) Tree generation engine
│       │   ├── models.py
│       │   ├── parser.py
│       │   └── resolver.py
│       ├── engine/
│       │   └── reorganizer.py
│       ├── ui/
│       │   └── tkinter_app.py     # (v0.2.0) Dual-tab GUI
│       └── utils/
│           └── config_loader.py
├── tests/
│   └── test_reorganize.py
├── pyproject.toml
├── run.py                         # CLI entrypoint
└── run_ui.py                      # Desktop GUI entrypoint

```

---

## Quick Start

### 1. Run the Desktop GUI

```bash
python run_ui.py

```

* **Tab 1 ("Reconstruct from Tree")**: Select source folder, destination root, paste/load an ASCII tree, and click **Reconstruct Directory Structure**.
* **Tab 2 ("Generate Tree from Folder")**: Choose any existing directory, set max depth and file visibility options, and click **Scan and Generate ASCII**.

### 2. Run via Command Line Interface (CLI)

#### Reconstructing Files

```bash
# Safe copy mode (default)
python run.py -t data/inputs/structure.txt -s data/inputs/raw_archive --task-name experiment_1

# Destructive move mode
python run.py -t data/inputs/structure.txt -s data/inputs/raw_archive --task-name migration_job --move

```

#### Running the Test Suite

```bash
pytest tests/ -v

```

---

## Building Standalone Windows Executable (`.exe`)

PyInstaller can bundle the GUI into a standalone folder that runs without Python:

```powershell
# 1. Clean previous build artifacts
Remove-Item -Recurse -Force .\build, .\dist, .\*.spec -ErrorAction SilentlyContinue

# 2. Compile via PyInstaller
pyinstaller --noconfirm --onedir --windowed --name "AsciiTreeReorg" `
  --add-data "configs;configs" `
  --paths "src" `
  run_ui.py

```

The executable will be located at:
`dist/AsciiTreeReorg/AsciiTreeReorg.exe`

---