# Architecture & Systems Design

## 1. Architectural Philosophy

The application follows object-oriented design and SOLID principles:

* **Single Responsibility**: Distinct modules handle indentation derivation, syntax parsing, pre-flight auditing, conflict resolution, directory instantiation, and UI presentation.
* **Zero Dependency Constraint**: Strictly standard library modules (`pathlib`, `shutil`, `argparse`, `dataclasses`, `re`, `math`, `collections`, `datetime`, `tkinter`).
* **Immutability**: Parsed tree nodes are represented as frozen dataclasses (`TreeNode`).

---

## 2. Component Class Diagram  

```
       +-------------------+
       |    Application    |
       +-------------------+
                 |
      +----------+----------+
      |          |          |
      ▼          ▼          ▼
+------------------+ +-------------+ +--------------------+
| AsciiTreeParser  | | Directory   | |  StructureAuditor  |
+------------------+ | Reorganizer | +--------------------+
          |          +-------------+           |
          ▼                 |                  |
+------------------+        |                  |
|  TreeNode        |<-------+------------------+
|  (Data Model)    |
+------------------+
          ^
          |
+---------------------+
| IndentationDetector |
+---------------------+
          |
          v
+---------------------+
|  ConflictResolver   |
+---------------------+
```

---

## 3. Module Responsibilities

### `core/models.py`

Defines `TreeNode`:

```python
@dataclass(frozen=True)
class TreeNode:
    name: str
    relative_path: Path
    is_directory: bool
    depth: int
    line_number: int  
```

### `core/parser.py`

Contains:  

* `IndentationDetector`: Analyzes line prefixes using `math.gcd` over all non-zero prefix lengths to determine structural pitch (2-space, 4-space, etc.).
* `AsciiTreeParser`: Tokenizes tree text, cleans Unicode box glyphs, maintains the hierarchy stack, and constructs `TreeNode` instances.  

### `core/auditor.py`  

Contains `StructureAuditor` :  

* Verifies whether duplicate paths were declared inside the tree schema.
* Detects when identical filenames exist across different folders.
* Scans the source directory for basename collisions before execution begins.  

### `core/resolver.py`

Contains `ConflictResolver` :  

* Manages terminal-based user disambiguation for duplicate source files.
* Gathers `os.stat_result` metadata and presents formatted candidate options.  

### `engine/reorganizer.py`

Contains `DirectoryReorganizer` :

* Recursively indexes source files into a hash map ( `Dict[str, List[Path]]` ).
* Provides `_purge_parent_orphans` to remove obsolete top-level entries from previous runs.
* Provides `_cleanup_old_positions` to prevent duplicate file copies when reorganizing in-place.
* Dispatches folder creation ( `mkdir` ) and file placement ( `shutil.copy2` or `shutil.move` ).

### `ui/tkinter_app.py`  

Provides `AsciiTreeReorgApp` :

* Threaded desktop UI preventing interface lockups during file copies.  
* Standard stream redirection ( `TextRedirector` ) to display live execution logs.  

---

## 4. Architecture Decision Records (ADRs)  

### ADR-001: Automatic Indentation Pitch Detection via GCD

* **Status:** Accepted

* **Context:** ASCII trees in documentation frequently mix 2-space, 4-space, or custom indentation widths.
* **Decision:** Calculate the Greatest Common Divisor of non-zero prefix lengths. Adapt automatically if the detected GCD differs from the configured default.
* **Consequence:** Handles arbitrary formatting without requiring manual configuration adjustments.  

### ADR-002: Default Non-Destructive Copy ( `shutil.copy2` )

* **Status:** Accepted

* **Context:** Operating on clinical research drops or irreplaceable model weights requires absolute protection against accidental data deletion.
* **Decision:** Default to copying while preserving file timestamps and modes. Require explicit user action ( `--move` or checkbox) for file moves.
* **Consequence:** Safe, repeatable execution with zero risk of source data loss.  

### ADR-003: Pure Standard Library Implementation

* **Status:** Accepted

* **Context:** Deployment environments include air-gapped hospital clusters, secure enclaves, and minimal Docker containers without internet access.
* **Decision:** Avoid all external dependencies ( `click`, `rich`, `pydantic` ). Use standard library only.

* **Consequence:** Zero dependency management overhead; functions out-of-the-box on any Python 3.9+ installation.
