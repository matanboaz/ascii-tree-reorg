# Functional Specification

## 1. CLI Interface Definition

### Command Signature

```bash
python run.py \
  --tree-file <PATH> \
  --source-dir <PATH> \
  --output-root <PATH> \
  [--task-name <STR>] \
  [--indent-width <INT>] \
  [--move]
  ```  

### Argument Specification  

| **_Option Flag_** | **_Long Flag_**  | **_Required_** | **_Default_**               | **_Type_** | **_Description_**                                    |
|-------------------|------------------|----------------|-----------------------------|------------|------------------------------------------------------|
| `-t`              | `--tree-file`    | No             | `data/inputs/structure.txt` | Path       | Path to plaintext file containing ASCII tree schema  |
| `-s`              | `--source-dir`   | No             | `data/inputs/raw_archive`   | Path       | Path to folder containing unorganized files.         |
| `-o`              | `--output-root`  | No             | `data/outputs/              | Path       | Target folder where run directories are created.     |
| `-n`              | `--task-name`    | No             | `reorg_job`                 | str        | Logical label used in timestamped run folder naming. |
| `-w`              | `--indent-width` | No             | `4`                         | int        | Fallback indentation step width in characters.       |
| (none)            | `--move`         | No             | `False`                     | bool       | Flag: moves files instead of copying.                |  

---

## 2. GUI Interface Definition ( `run_ui.py` )  

The Tkinter desktop interface exposes:  

1. **Source Folder Picker:** Sets the path to the unorganized source files.  
2. **Destination Folder Picker:** Sets the target output root directory.  
3. **Execution Options:**  
    - _Move files_: Switches transfer from `shutil.copy2` to `shutil.move` .
    - _Overwrite existing files_: Overwrites duplicate files already existing at target.  
    - _Clean relocated / Orphan files_: Scans for and removes files that were moved or sit as orphans outside the designated root.  
    - _Indent Width_: Numeric spinbox configuring fallback indentation pitch.  
4. **ASCII Tree Editor:** Live scrollable text area supporting loading from disk, editing, and clearing.  
5. **Execution Progress & Console Output:** Thread-safe terminal display capturing live logs, node operations, warnings, and completion status.  

---

## 3. Core Operational Workflows  

### 3.1 Indentation Detection & Path Parsing Workflow  

```text
[Raw ASCII Line] 
       │
       ▼
[Strip Comments ('#') & Carriage Returns]
       │
       ▼
[Extract Glyph Prefix: `│`, `├`, `└`, `─`, ` `]
       │
       ├── Prefix Length == 0  ──> Root Level (Depth = 0)
       └── Prefix Length > 0   ──> Calculate Depth = Length // IndentationStep
       │
       ▼
[Clean Leaf Name & Classify: Dir if ends with '/', File otherwise]
       │
       ▼
[Update Stack by Popping Until Stack Depth < Current Depth]
       │
       ▼
[Resolve Relative Path: Stack[-1].Path / Cleaned Leaf Name]
```

### 3.2 Interactive Conflict Resolution Workflow  

When multiple files with the same name are discovered during source indexing:  

1. Automated file placement pauses for that specific node.  
2. System presents destination path: `Destination: <node.relative_path>` .
3. Displays candidate table:  
    - Candidate index ( `[1..N]` ).
    - Relative path from source root.  
    - Size in Kilobytes.
    - Last modified timestamp ( `YYYY-MM-DD HH:MM:SS` ).
4. User selects index or enters `'s'` to skip.
5. If moved, selected item is removed from candidate tracking.  

### 3.3 Orphan Purge Workflow  

Before placing nodes:  

1. Read the allowed top-level directory names from the parsed tree nodes ( `node.relative_path.parts[0]` ).
2. Scan the immediate children of `target_dir` .
3. If an item in `target_dir` is not in the set of allowed root names (and is not `.git` or `.gitkeep` ), purge it recursively.

---

## 4. Error Handling and Edge Cases  

- **Missing Files:** Files declared in the ASCII tree that do not exist in the source folder produce a `[MISSING]` warning in the log, allowing the remaining files to process normally.  
- **Malformed Indentation:** If the indentation character lengths cannot be factored by the detected GCD or configured step, execution halts with a descriptive `ValueError` before any filesystem changes occur.  
- **Case Sensitivity:** On Linux/macOS, path comparisons follow standard case sensitivity; on Windows, case-preserving matching applies.
