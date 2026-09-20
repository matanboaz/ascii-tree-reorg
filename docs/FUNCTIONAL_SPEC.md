
# Functional Specification: `ascii-tree-reorg` v0.2.0

## 1. Subsystem Decomposition

```ascii-tree-reorg (v0.2.0)
├── Core Engine
│   ├── IndentationDetector   (Pitch calculation via GCD)
│   ├── AsciiTreeParser       (Tree text -> List[TreeNode])
│   ├── StructureAuditor      (Static analysis of collisions)
│   ├── ConflictResolver      (Disambiguation & Candidate metadata)
│   └── DirectoryTreeGenerator (Folder -> ASCII text) [New in v0.2.0]
├── Execution Engine
│   └── DirectoryReorganizer  (Filesystem placement, copy/move, cleanup)
├── Interfaces
│   ├── CLI                   (run.py / Application)
│   └── Desktop UI (Tkinter)  (run_ui.py / AsciiTreeReorgApp) [Dual-Tab in v0.2.0]
└── Utilities
└── ConfigLoader          (JSON configuration manager)
```

## 2. API & Component Contracts

### 2.1 `DirectoryTreeGenerator` (`src/ascii_tree_reorg/core/generator.py`)  

Generates ASCII tree representations of local directories.

```python
@dataclass
class GeneratorOptions:
    include_files: bool = True
    max_depth: Optional[int] = None
    indent_step: int = 4
    sort_dirs_first: bool = True

class DirectoryTreeGenerator:
    def __init__(self, root_dir: Path, options: Optional[GeneratorOptions] = None): ...
    def generate(self) -> str: ...

```

### 2.2 `AsciiTreeParser` (`src/ascii_tree_reorg/core/parser.py`)

Parses tree text files into structured nodes.

```python
class AsciiTreeParser:
    def __init__(self, file_path: Path, fallback_width: int = 4): ...
    def parse(self) -> List[TreeNode]: ...

```

### 2.3 `DirectoryReorganizer` (`src/ascii_tree_reorg/engine/reorganizer.py`)

Executes disk operations with support for progress observation.

```python
class DirectoryReorganizer:
    def __init__(
        self,
        source_dir: Path,
        target_dir: Path,
        move_files: bool = False,
        overwrite: bool = True,
        clean_relocated: bool = False
    ): ...
    def execute(self, nodes: List[TreeNode]) -> None: ...
    def _place_single_node(self, node: TreeNode) -> None: ...
    def _cleanup_old_positions(self, nodes: List[TreeNode]) -> None: ...

```

## 3. UI Specifications (`src/ascii_tree_reorg/ui/tkinter_app.py`)

* **Window Title**: `ASCII Tree Reorganizer & Generator v0.2.0`  

* **Tab 1: Reconstruct from Tree**:  

* Source path entry with browse dialog.
* Destination root path entry with browse dialog.
* Checkboxes: `Move files`, `Overwrite existing`, `Clean relocated`.
* Indentation pitch spinbox.
* Tree text editor with `Load Tree File...` and `Clear` buttons.
* Real-time progress bar + dynamic status string.
* Threaded worker execution to prevent UI freezing.
* Color-coded console output (redirected `stdout`).

* **Tab 2: Generate Tree from Folder**:  

* Target folder entry with browse dialog.
* `Include files` toggle.
* `Max Depth` spinbox (`0` = unlimited).
* `Scan and Generate ASCII` action button.
* Readout text widget with `Copy to Clipboard` and `Save to .txt File...` actions.
