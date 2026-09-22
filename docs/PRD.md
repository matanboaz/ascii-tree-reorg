# Product requirements

## Goal

Turn directory trees into real workspaces and real workspaces into portable tree specifications without risking source files.

## Workflows

1. Reconstruct a hierarchy from loose files and an ASCII tree.
2. Generate an ASCII tree from a folder.
3. Resolve duplicate source conflicts with path and metadata context.
4. Preview destructive work before enabling move, overwrite, or cleanup.

## Interfaces

- Python CLI for scripts and terminal use.
- Canopy Electron desktop client for cross-platform use.

## Quality bars

Strict errors, safe containment, structured progress, five explicit desktop states, Python-version CI, clean package installation, and guarded release publishing.
