# Implemented functional specification

## CLI reconstruction

Inputs are source folder, tree file, output root, task name, and indentation width. The CLI creates a timestamped run directory unless it is a dry run. Copy is default. Move, overwrite, cleanup, and dry run are explicit flags. Duplicate names are selected interactively. The parser and destination plan are validated before placement.

## Tree generation

The Python generator accepts a source folder, include-files setting, maximum depth, indentation width, and optional ignore names. It emits a Unicode tree that round-trips through the strict parser. Canopy currently generates with files included and default depth/indentation settings.

## Canopy desktop

Canopy supports safe copy-only reconstruction and tree generation. It provides native folder dialogs, editable tree text, progress, actual duplicate candidate choices, cancel, and success/error/partial-result messaging. It does not expose move, overwrite, cleanup, dry-run, generated-tree depth, generated-tree include-files, or indentation controls. Those remain CLI/API capabilities.

## Safety

Dry run never writes. Traversal, absolute paths, drive-relative paths, and symlink escapes are rejected. Cancellation is not transactional: already copied files remain. Missing or skipped files do not make a run atomic.
