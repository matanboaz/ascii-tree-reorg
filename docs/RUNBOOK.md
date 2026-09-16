# Operations & Deployment Runbook

## 1. Host Environment Requirements

* **Operating System:** Windows 10/11, Windows Server 2016+, Linux (Ubuntu, RHEL), macOS.
* **Python Runtime:** Python 3.9 or higher.
* **Permissions:** Read access to source folder; Write access to destination folder.
* **Encoding:** UTF-8 supported terminal / console.

---

## 2. Standard Operating Procedures (SOP)

### SOP-01: Standard Ingest & Restructure (Air-Gapped Server)

1. Extract incoming flat archive into:  

    ```text
    data/inputs/raw_archive/
    ```

2. Copy the ASCII tree specification into:  

    ```text
    data/inputs/structure.txt
    ```

3. Run the CLI tool in safe copy mode: (Bash)  

    ```bash
    python run.py --task-name clinical_ingest_v1
    ```

4. Verify the structured output in:  

    ```text
    data/outputs/run_clinical_ingest_v1_<TIMESTAMP>/
    ```

### SOP-02: Desktop GUI Execution  

1. Launch interface: (Bash)_  

    ```bash
    python run_ui.py
    ```

2. Confirm source directory points to the unorganized files.  
3. Confirm destination directory points to the target folder.
4. Paste the ASCII tree into the editor.
5. Click Reconstruct Directory Structure.
6. When complete, click Open Destination Folder to inspect output.

---

## 3. Incident Response & Troubleshooting Playbook

### Incident: Malformed Indentation Error  

- **Symptom:** `Indentation/Parsing Error: Malformed indentation detected...`
* **Root Cause:** Inconsistent indentation steps (e.g., mixing tabs, 3-space, and 5-space indents on different lines).
* **Resolution:**
    1. Open `structure.txt` in an editor.
    2. Normalize indentations to uniform 2 or 4 spaces.
    3. Or pass an explicit pitch via `-w <width>` .

### Incident: Missing Files in Output  

- **Symptom:** `[MISSING]` Tree entry `'<path>'` not found in source.
* **Root Cause:** Filename in tree does not match source file basename (case sensitivity or typos).
* **Resolution:**
    1. Check the console log to identify missing files.
    2. Compare basenames between source and tree specification.
    3. Correct discrepancies in `structure.txt` and re-run.  

### Incident: Obsolete Folders from Previous Runs Persist

- **Symptom:** Unwanted folders from an earlier failed run remain in `data/outputs` .
* **Root Cause:** Orphan cleaning was disabled or destination path pointed to the parent output folder.
* **Resolution:**
    1. Ensure Clean relocated / orphan files is checked in the GUI.
    2. Run the cleanup command directly in PowerShell:  

    ```powershell
    Get-ChildItem "data\outputs" | Where-Object { $_.Name -notin @("SMART_AI_NLP", ".gitkeep") } | Remove-Item -Recurse -Force
    ```  

---

## 4. Compilation & Deployment to Offline Servers

### Building the Standalone Executable (on connected laptop)  

```powershell
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --name "AsciiTreeReorg" `
  --add-data "configs;configs" `
  --paths "src" `
  run_ui.py
```

### Deploying to Offline Server  

1. Compress `dist/AsciiTreeReorg/` to a zip archive.
2. Transfer via approved ingress media to the target server.
3. Extract to desired location (e.g., `D:\tools\AsciiTreeReorg` ).
4. Execute `AsciiTreeReorg.exe` directly (no Python installation required).
