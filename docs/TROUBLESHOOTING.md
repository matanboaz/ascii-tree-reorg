# Troubleshooting

## CLI cannot find its default inputs

Defaults are resolved relative to the current working directory. Pass explicit `--tree-file`, `--source-dir`, and `--output-root` paths for installed use.

## Parsing or indentation error

Keep one connector width throughout the tree. The default form is `├── ` / `└── ` with four-character ancestor units (`│   ` or four spaces). Directories should end in `/`, especially empty ones. Use indentation, not `/` or `\`, to express nested paths.

## A file is missing or ambiguous

The engine searches source files recursively by base name. A missing name produces a warning. Duplicate base names produce candidate paths; choose the intended source or skip it. Use unique file names when unattended behavior is required.

## Existing or unexpected destination content

Copy mode keeps existing files by default. `--overwrite` replaces matching targets. `--clean-relocated` can delete undeclared or stale target content and should always be preceded by `--dry-run`. Check that `--output-root` and the generated timestamped run directory are the paths you intended.

## Cancellation left files behind

This is expected. Cancellation stops the worker but does not roll back completed copies. Review or remove the partial destination before retrying.

## Canopy worker will not start

Packaged builds require the matching frozen sidecar under application resources. Source runs require `python3` on macOS/Linux or `ASCII_TREE_REORG_PYTHON` pointing to an executable Python with this package installed. Run the sidecar protocol smoke from the release workflow when diagnosing packaging.

## macOS Gatekeeper or Windows SmartScreen warning

Public releases must be signed, and macOS artifacts must be notarized. Verify the code signature and SHA-256 manifest. Do not tell users to bypass operating-system warnings for an unsigned development artifact; use a signed release or build from reviewed source.

## Linux AppImage does not launch

Ensure the file is executable (`chmod +x Canopy-*.AppImage`). Some distributions require FUSE support. The DEB is the alternative for Debian-based systems.

## Where are logs?

The sidecar sends diagnostics to stderr and operation state to the app through NDJSON. Canopy does not yet expose a persistent activity log. Reproduce from a terminal during development for diagnostic output; avoid putting private file contents into bug reports.
