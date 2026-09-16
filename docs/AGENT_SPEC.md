# AI Agent Specification (`ascii-tree-reorg`)

This specification provides comprehensive guidance for autonomous coding agents (Claude Code, Cursor, Windsurf, Codex) modifying or extending this codebase.

---

## PART I: UNIFIED SYSTEM CONTEXT

`ascii-tree-reorg` is a zero-dependency, object-oriented Python 3.9+ application designed to reconstruct folder hierarchies from plaintext ASCII directory trees. The utility operates in both headless CLI and Tkinter GUI modes.

### Key Architectural Invariants

1. **Zero External Dependencies**: Standard library modules only. Never introduce `pip` requirements for core functionality.
2. **Safe by Default**: File movements default to `shutil.copy2`. Destructive moves (`shutil.move`) must require explicit user activation.
3. **Dynamic Indentation Detection**: Do not hardcode line indentation offsets. Always use `IndentationDetector.detect()` with GCD math.
4. **Separation of Concerns**: Parsing (`core/parser.py`), auditing (`core/auditor.py`), and file operations (`engine/reorganizer.py`) must remain decoupled.
5. **Thread Safety in UI**: Long-running filesystem operations in `ui/tkinter_app.py` must run inside daemon threads, updating UI state through `.after()` callbacks.

---

## PART II: MICRO-TASK SPECIFICATIONS

### Task 1: Tree Parsing & Model Construction

* **Target:** `src/ascii_tree_reorg/core/parser.py`
* **Rules:**
  * Clean line prefixes using regex `^([│\s├└─\-+|]*)`.
  * Calculate depth via integer division: `prefix_len // step_width`.
  * Strip inline comments starting with `#`.
  * Maintain parent path stack `List[Tuple[int, Path]]`.
  * Directories are identified by trailing slashes or presence of child nodes.

### Task 2: Indentation Pitch Detection

* **Target:** `src/ascii_tree_reorg/core/parser.py` -> `IndentationDetector`
* **Rules:**
  * Compute GCD across all non-zero prefix lengths using `math.gcd`.
  * If calculated GCD differs from default width, log warning and return calculated GCD.
  * If lines are uneven and indivisible, raise `ValueError`.

### Task 3: Directory Reorganization & Placement

* **Target:** `src/ascii_tree_reorg/engine/reorganizer.py`
* **Rules:**
  * Index source files recursively into a `defaultdict(list)`.
  * For directory nodes, create directory with `parents=True, exist_ok=True`.
  * For file nodes, retrieve source path from indexed map.
  * If multiple candidates exist, invoke `ConflictResolver.prompt_selection()`.
  * If moving, remove used candidate from index to prevent duplicate assignments.

### Task 4: Orphan & Parent Cleanup

* **Target:** `src/ascii_tree_reorg/engine/reorganizer.py` -> `_purge_parent_orphans`
* **Rules:**
  * Collect all valid root folder names from `desired_nodes[].relative_path.parts[0]`.
  * Iterate items in `target_dir`.
  * Delete any directory or file whose name is not in the set of allowed roots (ignoring `.git` and `.gitkeep`).

---

## PART III: ACCEPTANCE CRITERIA FOR MODIFICATIONS

1. All changes must pass `pytest tests/test_reorganize.py` with zero errors.
2. No external libraries added to `pyproject.toml` dependencies.
3. CLI (`run.py`) and GUI (`run_ui.py`) entrypoints must function identically regarding file placement.
4. Code must conform to PEP 8 standards with type hints on all function signatures.
