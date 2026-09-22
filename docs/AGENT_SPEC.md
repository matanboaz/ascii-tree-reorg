# AI Agent Specification: `ascii-tree-reorg` v0.3.0

## System Prompt Context  

You are working on `ascii-tree-reorg`, an offline, zero-external-dependency Python package designed for bidirectional ASCII directory tree operations: reconstruction from text trees, and tree diagram generation from existing directories.

## Architecture Boundaries  

1. **Dependencies**: Pure Python standard library only (`pathlib`, `shutil`, `argparse`, `dataclasses`, `re`, `math`, `collections`, `datetime`, `tkinter`). No external packages are permitted in core or UI code.
2. **Path Handling**: All filesystem paths must use `pathlib.Path`. Explicit `.resolve()` must be used when anchoring root trees.
3. **Encoding**: File read/write operations must default to `utf-8` with fallback to `latin-1` where necessary.
4. **Data Isolation**: Generated file trees and reconstructed outputs must always target timestamped subfolders under `data/outputs/` to avoid overwriting inputs.

## Micro-Task Validation Checklist for AI Agents  

* When modifying `parser.py`: Verify that `IndentationDetector.detect` never returns a pitch less than 1 (guard against zero-division).
* When modifying `generator.py`: Verify that directory sorting places folders before files when `sort_dirs_first=True` and respects `max_depth`.
* When modifying `tkinter_app.py`:
  * Ensure both `launch_gui` and `run_gui` exist as callable module-level exports.
  * Ensure long-running disk operations are delegated to `threading.Thread(daemon=True)`.
  * Ensure UI state updates pass through `widget.after(0, ...)`.
* When running tests: Ensure all fixtures in `tests/test_reorganize.py` use `tmp_path` to prevent residue on disk.
