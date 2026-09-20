
# Software Architecture Document & Decision Records

## 1. System Architecture

The package follows a clean Layered / Hexagonal Architecture:  

* **Domain Models (`core.models`)**: Pure immutable dataclasses (`TreeNode`).
* **Core Logic (`core.*`)**: Stateless parsing, AST-like hierarchy construction, directory tree serialization, and auditing.
* **Infrastructure / Engine (`engine.*`)**: Stateful filesystem adapters wrapping Python's `shutil` and `os` primitives.
* **Application Adapters (`app.py`, `ui.tkinter_app`)**: CLI entrypoints and GUI controllers that drive the domain and infrastructure layers.

---

## 2. Architecture Decision Records (ADRs)

### ADR-001: Dynamic GCD Indentation Detection  

* **Status**: Accepted
* **Context**: ASCII trees use varying indentations (2 spaces, 4 spaces, tabs). Hardcoding width causes silent hierarchy flattens or crashes.
* **Decision**: Compute the Greatest Common Divisor of all prefix indentation lengths across non-empty lines. If mismatch occurs against user preferences, auto-adapt and log a warning.

### ADR-002: Default Non-Destructive Copying  

* **Status**: Accepted
* **Context**: Machine learning datasets (`.parquet`, `.pkl`) and source code archives cannot be recovered easily if lost during an interrupted move.
* **Decision**: Standardize on `shutil.copy2` by default. Gate `shutil.move` strictly behind user flags.

### ADR-003: Bidirectional Functionality in a Single Package (v0.2.0)  

* **Status**: Accepted
* **Context**: Operators restructuring archives often need to inspect an existing reference project, export its ASCII layout, and feed that layout into reconstruction jobs elsewhere.
* **Decision**: Introduce `DirectoryTreeGenerator` and expose both Reconstruction and Generation capabilities within a unified dual-tab GUI and modular API.

### ADR-004: Threaded Execution in Desktop GUI  

* **Status**: Accepted
* **Context**: Transferring large datasets or thousands of small files blocks the Tkinter main event loop, causing "Not Responding" window states.
* **Decision**: Isolate the reorganization worker inside a background `threading.Thread(daemon=True)`. Progress bar state and log streams dispatch back to the Tkinter UI thread via `after(0, ...)`.  
