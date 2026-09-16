# Product Requirements Document (PRD)

## 1. Document Overview
* **Product Name:** ASCII Tree Directory Reorganizer (`ascii-tree-reorg`)
* **Status:** Approved / Production Ready
* **Target Platforms:** Cross-platform (Windows 10/11, Windows Server, Linux, macOS)
* **Execution Environment:** Python 3.9+ runtime, zero external pip dependencies.

---

## 2. Executive Summary & Problem Statement
Engineers, data scientists, and researchers frequently receive project deliverables, model weights, and clinical datasets as flat archives or flattened zip bundles. These drops are typically accompanied by a textual ASCII directory tree diagram in a `README.md` or specification document showing where each file should live.

Manually recreating complex nested folders and moving files one by one is error-prone, labor-intensive, and risks file loss or name collisions.

`ascii-tree-reorg` provides an automated, idempotent, and deterministic utility (via CLI and desktop GUI) to parse plaintext ASCII/Unicode directory tree structures, validate directory syntax, audit potential collisions, and place files into their exact target destinations.

---

## 3. Goals & Objectives
* **Automation:** Fully eliminate manual directory creation and file movement.
* **Safety First:** Default to non-destructive copying (`shutil.copy2`); require explicit opt-in for destructive moves (`--move`).
* **Deterministic Layout Parsing:** Automatically parse variations of terminal trees (`├──`, `└──`, `│`, standard indents) while detecting indentation pitch via Greatest Common Divisor (GCD) math.
* **Collision Transparency:** Audit duplicate filenames and provide interactive disambiguation when multiple source files share the same name across different folders.
* **Orphan Cleanup:** Automatically purge obsolete, relocated files and top-level directory debris left over from previous faulty executions.
* **Air-Gapped Ready:** Strict reliance on Python's built-in standard library with zero third-party dependencies.

---

## 4. User Personas
* **Data Scientist / NLP Researcher:** Receives model checkpoints (`.pkl`), feature stores (`.parquet`), and tabular data (`.csv`) in flat archives and needs to map them to reproducible pipelines inside secure hospital or enterprise networks.
* **DevOps / Systems Engineer:** Automates project boilerplate setup and restores standard structures across air-gapped environments without package management (`pip`) access.

---

## 5. Scope & Requirements Matrix

### 5.1 In-Scope
* Parsing plaintext tree structures (UTF-8) containing directory indicators (`/`) and file basenames.
* Dynamic detection of indentation width using prefix GCD analysis.
* Non-destructive copy as system default, preserving file metadata (`mtime`, `mode`).
* Destructive move behind explicit user flag/toggle.
* Interactive disambiguation with candidate file metadata (path, size, timestamp) when collisions occur.
* Pre-flight structural and ambiguity auditing.
* Top-level orphan folder and file cleanup (`_purge_parent_orphans`).
* Desktop GUI built with Tkinter.

### 5.2 Out-of-Scope
* Modifying or extracting directly inside compressed archives (`.zip`, `.tar.gz`) without prior extraction.
* Automatic fuzzy matching for misspelled filenames.
* Web-based multi-user server interface.

---

## 6. Functional Requirements Matrix

| Requirement ID | Type | Description | Priority |
| :--- | :--- | :--- | :--- |
| **REQ-PRD-01** | Core | Read ASCII tree structure from file or interactive GUI editor. | P0 |
| **REQ-PRD-02** | Core | Parse directories vs. files via trailing slash conventions or hierarchical depth. | P0 |
| **REQ-PRD-03** | Core | Copy files preserving file metadata (`mtime`, `mode`) by default. | P0 |
| **REQ-PRD-04** | Core | Support moving files in-place using `--move` CLI flag or GUI checkbox. | P0 |
| **REQ-PRD-05** | Usability | Detect indentation step dynamically using prefix character analysis. | P1 |
| **REQ-PRD-06** | Safety | Audit duplicate paths in the tree and ambiguous names before execution. | P1 |
| **REQ-PRD-07** | Safety | Provide interactive prompt displaying size/mtime when identical source files exist. | P1 |
| **REQ-PRD-08** | Reliability | Clean obsolete/orphan files sitting outside the root tree hierarchy. | P1 |