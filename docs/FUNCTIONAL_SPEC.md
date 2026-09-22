# Functional specification

## Reconstruction

Input: source, destination, ASCII tree, and optional move/overwrite/cleanup/dry-run settings. The parser validates the tree and the engine validates all destinations before placement. Duplicate source names become structured conflicts.

## Generation

Input: source folder, include-files setting, maximum depth, and indentation width. Output is a Unicode tree that round-trips through the strict parser.

## Desktop

Canopy provides reconstruction and generation. Native dialogs and the Python worker stay in Electron's main process. The renderer shows idle, running, conflict, success, and error states through a narrow preload API.

## Safety

Copy is default. Move, overwrite, and cleanup are explicit. Dry run never writes. Traversal, absolute paths, drive-relative paths, and symlink escapes are rejected.
