# Migration from legacy interfaces

Version 0.3 retired the duplicate Streamlit applications, Tkinter shell/runner, and the old GUI console entry. The supported interfaces are now:

- `ascii-tree-reorg` for CLI reconstruction and advanced/destructive flags
- Canopy for safe copy-only reconstruction and tree generation

There is no in-place migration of legacy UI state. Preserve tree text and source/output paths, install the current CLI or a signed Canopy artifact, and rerun with a dry run when moving a workflow to the CLI. Scripts that called the removed GUI entry must call `ascii-tree-reorg` with explicit paths. Streamlit/Tkinter dependencies are no longer installed.

The filesystem/tree format remains compatible subject to the stricter parser: mixed/ragged connectors, traversal names, path separators inside entry names, and ambiguous malformed indentation now fail with line-numbered errors instead of being guessed.
