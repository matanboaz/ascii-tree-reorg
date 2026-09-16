# ASCII Tree Directory Reorganizer (`ascii-tree-reorg`)

A deterministic, zero-dependency Python utility and desktop GUI that reconstructs folder hierarchies from ASCII/Unicode directory tree diagrams (like output from POSIX `tree`) and relocates loose files into their designated folders.

Designed for air-gapped data pipelines, clinical research drops, and batch data reorganization.

---

## Features

- **Automated Tree Parsing**: Supports UTF-8 tree glyphs (`├──`, `└──`, `│`), spaces, dashes, and tabs.
- **Auto Indentation Pitch Detection**: Uses Greatest Common Divisor (GCD) math to detect and adapt to 2-space, 4-space, or custom tree indentation automatically.
- **Interactive Disambiguation**: Intelligently detects identical basenames across multiple subfolders and prompts for manual selection with file metadata (size, timestamp).
- **Desktop GUI & Headless CLI**: Run via a Tkinter interface or automated bash/powershell scripts.
- **Orphan & Obsolete Cleaner**: Cleans previous faulty runs and removes files dumped outside the root hierarchy.
- **Zero Third-Party Dependencies**: Pure Python standard library (`pathlib`, `shutil`, `argparse`, `tkinter`). Runs fully offline.

---

## Project Structure

```text
ascii_tree_reorg/
├── configs/
│   └── default_config.json        # Default path configurations and pitches
├── data/
│   ├── inputs/
│   │   ├── raw_archive/           # Drop unorganized/unzipped source files here
│   │   └── structure.txt          # Target ASCII directory schema
│   └── outputs/                   # Destination output directory
├── docs/                          # In-depth architectural & operational docs
├── src/
│   └── ascii_tree_reorg/
│       ├── core/                  # Parsing, GCD pitch detection, conflict models
│       ├── engine/                # Reorganizer, file placement, and orphan cleanup
│       └── ui/                    # Tkinter desktop GUI
├── run.py                         # CLI entrypoint
├── run_ui.py                      # Desktop GUI entrypoint
└── pyproject.toml                 # Package specification

```

---

## Installation & Requirements  

### System Requirements  

- **Python:** 3.9 or higher (tested on Windows11, Windows Server, Linux, macOS).  

- **Core Dependencies:** None. Uses only standard library modules (`pathlib`, `shutil`, `argparse`, `dataclasses`, `re`, `math`, `collection`, `datetime`, `tkinter`).  

### Setup on Development Machine

Clone the repository:  

```Bash
git clone [https://github.com/](https://github.com/)<YOUR_GITHUB_USERNAME>/ascii-tree-reorg.git
cd ascii-tree-reorg
```  

Optional: Install in editable mode if you want the `ascii-reorg` command available globally in your virtual/conda environment:  

```Bash
pip install -e .
```

---

## Usage Examples  

### 1. Desktop Graphical User Interfacce (GUI)  

Launch the graphical interface:  

```bash
python run_ui.py
```

1. **Source Folder:** Select the folder holding the unorganized/unzipped files.  
2. **Destination::** Select the target root (`data/outputs` by default).  
3. **ASCII Structure:** Paste or load your schema text.  
4. **Options:**  
    - Check **Move files** to cut and paste instead of copy.
    - Check **Clean relocated / orphan files** to purge obsolete dumps from previous runs.  
5. Click 🚀 **Reconstruct Directory Structure**.  

### 2. Command Line Interface (CLI)

#### Safe Copy Run (Default)  

Places files into a fresh timestamped directory under `data/outputs/`:

```bash
python run.py --task-name clinical_nlp_drop
```

#### Move Files (Destructive Cut/Paste)

Saves disk space for large checkpoints and `.parqet` files:  

```bash
python run.py --task-name clinical_nlp_drop --move
```

#### Custom Tree, Source, and Indent Width

```bash
python run.py \
  --tree-file data/inputs/structure.txt \
  --source-dir "C:/Downloads/unzipped_bundle" \
  --output-root data/outputs \
  --task-name run_v1 \
  --indent-width 2
```  

---

## Example Input & Expected Output  

### Input ASCII Tree (`data/inputs/structure.txt`)

```text
SMART_AI_NLP/
├── src/
│   ├── configs/
│   │   └── config.yaml
│   └── pipeline/
│       └── load_data.py
├── data/
│   └── raw/
│       └── cohort.csv
└── main.py
```  

### Execution Output Log  

```text
================= DIAGNOSTIC RUN =================
[DEBUG] Source Directory      : C:\Users\...\raw_archive
[DEBUG] Destination Directory : C:\Users\...\data\outputs
[DEBUG] Total Parsed Nodes    : 6
   -> [DIR]  SMART_AI_NLP/
   -> [DIR]  src
   -> [DIR]  configs
   -> [FILE] config.yaml
   -> [DIR]  pipeline
   -> [FILE] load_data.py
   -> [DIR]  data/raw
   -> [FILE] cohort.csv
   -> [FILE] main.py

---------------- EXECUTION LOG ----------------
[COPYING] config.yaml -> SMART_AI_NLP\src\configs\config.yaml
[COPYING] load_data.py -> SMART_AI_NLP\src\pipeline\load_data.py
[COPYING] cohort.csv -> SMART_AI_NLP\data\raw\cohort.csv
[COPYING] main.py -> SMART_AI_NLP\main.py
[ORPHAN PURGE] Deleting obsolete item from outputs: old_stale_folder
[DONE] Execution finished successfully.
```

---

## Compile to Standalone `.exe` for Windows Server  

To run this tool on an air-gapped Windows Server without installing Python, compile it into an executable using PyInstaller on your development laptop.  

### Step 1: Build on Development Machine (Connected to the internet)  

1. Install PyInstaller: (`PowerShell`)  

```powershell
pip install pyinstaller
```

1. Build the directory package: (`PowerShell`)  

    ```powershell
    cd "C:\Users\SZMC\projects_and_apps\ascii_tree_reorg"
    pyinstaller --noconfirm --onedir --windowed --name "AsciiTreeReorg" `
    --add-data "configs;configs" `
    --paths "src" `
    run_ui.py
    ```  

    *(Note:* ``--onedir`` *is used instead of * `--onfile` *to ensure instant startup and prevent enterprise endpoint security locks on** `%TEMP%`*)*  

2. Output binary directory is generated at:  

    ```text
    dist/AsciiTreeReorg/
    ```

### Step 2: Transfer & Run on Air-Gapped Windows Server  

1. Archive `dist/AsciiTreeReorg/` into a `.zip` archive.  
2. Transfer the archive to the sercure server following standard data ingress protocol (e.g., approved USB or cross-domain share).  
3. Unzip anywhere (e.g., `D:\tools\AsciiTreeReorg` ).
4. Launch `AsciiTreeReorg.exe` . No Python runtimes or external libraries are required on the host.  

---

## Environment Matrix

| ***Component***    | ***Dev Environment***                           | ***Air-Gapped Windows Server***                     |
|--------------------|-------------------------------------------------|-----------------------------------------------------|
| ***Python***       | Python 3.9+ installed                           | **Not required (if using standalone `.exe`)**       |
| ***Git***          | Installed (to push/pull remote repo)            | Not required                                        |
| ***Dependencies*** | Standard library + `pyinstaller` (for building) | None (zero dependencies)                            |
| ***Permissions***  | Normal User                                     | Read on source directory, Write on output directory |
| ***Network***      | Internet access (for GitHub)                    | Air-gapped / Offline                                |

---

## Documentation Index  

For detailed engineering references, see the files in `docs/` :  

- `docs/PRD.md` : Product Requirements Document and problem statement.  
- `docs/FUNCTIONAL_SPEC.md` : Full CLI and operational functional specifications.  
- `docs/ARCHITECTURE.md` : Architecture design, class breakdown, and Architecture Decision Records (ADRs).  
- `docs/RUNBOOK.md` : Deployment, operational guidelines, and incident recovery playbooks.  
- `docs/AGENT_SPEC.md` : Decomposed specifications for AI coding agents.
