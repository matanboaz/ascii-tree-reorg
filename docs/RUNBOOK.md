# Operations & Packaging Runbook

## 1. Environment & Setup

### Requirements  

* Python 3.9+ (standard library only).
* UTF-8 compatible terminal or console.
* PyInstaller (only required if compiling to `.exe`).

---

## 2. Standard Maintenance Workflows

### Running Locally  

```powershell
# Run the Desktop Application
python run_ui.py

# Run CLI Task
python run.py --task-name baseline_run

```

### Running Unit & Integration Tests

```powershell
pytest tests/ -v

```

---

## 3. PyInstaller Windows `.exe` Build Procedure

To compile a clean, standalone executable for distribution:

### Step 1: Clean Artifacts

```powershell
Remove-Item -Recurse -Force .\build, .\dist, .\*.spec -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Include __pycache__, .pytest_cache -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

```

### Step 2: Compile Executable

```powershell
pyinstaller --noconfirm --onedir --windowed --name "AsciiTreeReorg" `
  --add-data "configs;configs" `
  --paths "src" `
  run_ui.py

```

### Step 3: Verify Output

Launch `dist\AsciiTreeReorg\AsciiTreeReorg.exe` and confirm:

1. Window title displays `ASCII Tree Reorganizer & Generator v0.3.0`.
2. Both tabs load cleanly.
3. Test a quick tree generation on a local directory.

---

## 4. Git Release & Version Bumping Checklist

When releasing a new version:

1. Update `version = "X.Y.Z"` in `pyproject.toml`.
2. Update `__version__ = "X.Y.Z"` in `src/ascii_tree_reorg/__init__.py`.
3. Update the window title in `src/ascii_tree_reorg/ui/tkinter_app.py`.
4. Stage only source and documentation files (do NOT stage `dist/`, `build/`, or `.exe` files):  

    ```powershell
    git status
    git add src/ docs/ README.md pyproject.toml run.py run_ui.py tests/
    git commit -m "chore(release): bump version to vX.Y.Z"
    git tag "vX.Y.Z"
    git push origin main --tags
    ```
  
5. *(Optional)* Compress `dist/AsciiTreeReorg/` into a `.zip` archive and attach it to the GitHub Release page as a pre-built binary.  
