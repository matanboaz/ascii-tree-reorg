# Product requirements and current status

## Goal

Turn directory trees into real workspaces and real workspaces into portable tree specifications without risking source files.

## Implemented workflows

1. Reconstruct a hierarchy from loose files and an ASCII tree.
2. Generate an ASCII tree from a folder.
3. Resolve duplicate source conflicts using actual candidate paths.
4. Preview CLI work with dry run and opt into move, overwrite, or cleanup.
5. Cancel desktop work with explicit partial-result messaging.

## Interfaces

- Python CLI for scripts, dry runs, and advanced filesystem actions.
- Canopy Electron desktop for cross-platform safe copy-only reconstruction and generation.

## Quality bars

Strict line-numbered errors; containment validation before mutation; structured progress; terminal error/cancel semantics; sandboxed renderer and validated IPC; Python-version and desktop-OS CI; clean wheel installation; native artifact smoke tests; checksums; and fail-closed desktop signing/notarization for published releases.

See [FUNCTIONAL_SPEC.md](FUNCTIONAL_SPEC.md) for implemented scope rather than treating future requirements as shipped behavior.
