# Product Requirements Document (PRD): `ascii-tree-reorg`

## Version: 0.3.0

### 1. Executive Summary  

`ascii-tree-reorg` bridges the gap between system documentation and disk state. Originally developed to solve the ingestion and sorting of unorganized archives matching an ASCII specification, version 0.2.0 adds bidirectional capability: users can generate compliant ASCII tree documentation directly from any folder, as well as reconstruct folder structures from ASCII trees.

### 2. Core Personas & Use Cases  

* **Data Scientists / Researchers**: Ingesting messy zip archives containing models (`.pkl`), metrics (`.parquet`, `.csv`), and code (`.py`, `.json`), matching them to documented benchmark topologies.
* **Systems & DevOps Engineers**: Generating structure documentation for code repositories and validating deployment layouts in air-gapped environments.
* **Technical Authors**: Producing standardized ASCII folder trees for software documentation and verification.

### 3. Functional Requirements

#### FR-1: ASCII Tree Parsing & Indentation Normalization  

* Must support Unicode (`├──`, `└──`, `│`) and ASCII (`|--`, `\--`) branch notations.
* Must compute indentation depth automatically using GCD across prefix offsets, adapting between 2-space, 3-space, and 4-space formats.
* Must reject structurally irregular indentation patterns prior to disk execution.

#### FR-2: Structural Auditing & Pre-flight Conflict Checks  

* Must detect duplicate relative paths defined within the same tree file.
* Must identify instances where the same filename appears in multiple subdirectories across the desired tree.
* Must index the source directory to locate missing files and duplicate source basenames.

#### FR-3: Safe Filesystem Execution  

* Default file operation is non-destructive copy (`shutil.copy2`), maintaining timestamps and file attributes.
* Move mode (`shutil.move`) is strictly opt-in via `--move` or GUI checkbox.
* Target outputs are written to isolated, timestamped subdirectories inside the output root.

#### FR-4: Interactive Conflict Resolution  

* When multiple source files match a single target file node, the resolver prompts the operator with full metadata (relative path, size in KB, last modified timestamp).
* Includes a non-interactive headless fallback for CI/CD and batch pipelines.

#### FR-5: Directory Tree Generation (v0.2.0)  

* Must scan arbitrary directories and output standard tree representations.
* Must allow limiting traversal depth (`max_depth`).
* Must allow toggling file visibility (directories only vs. full files and folders).
* Must provide UI options to copy generated text directly to the clipboard or export to `.txt`.

### 4. Non-Functional Requirements  

* **Zero External Runtime Dependencies**: Standard library only (`pathlib`, `shutil`, `argparse`, `tkinter`, etc.).
* **Air-Gapped Operation**: Completely offline execution capability with no network calls or telemetry.
* **Platform Support**: Linux, macOS, and Windows (10/11, Server).
