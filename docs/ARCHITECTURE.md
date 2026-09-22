# Architecture

- **Core domain**: parser, generator, models, audit, structured events, and conflict resolution.
- **Filesystem engine**: validates containment before writes and emits typed operation events.
- **CLI adapter**: parses terminal options and drives the engine.
- **Desktop sidecar**: accepts newline-delimited JSON requests and emits JSON events. Human diagnostics go to stderr.
- **Electron main process**: owns native dialogs and the Python child process.
- **React renderer**: renders reconstruction, generation, progress, conflict, success, and error states through a context-isolated preload API.

## Decisions

Parsing uses one explicit indentation unit and fails with line numbers instead of guessing. Copying is the default; move, overwrite, and cleanup are opt-in. Every destination is validated before mutation.

Graphical clients consume `OperationEvent` records and provide conflict callbacks rather than parsing print output or invoking terminal input. Python remains the source of truth.

The duplicated Streamlit implementations and Tkinter shell were retired after Canopy reached feature parity. Keeping three UIs caused behavior drift and left unsafe worker-thread widget updates in the legacy path.
