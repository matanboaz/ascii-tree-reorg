"""Build the Python desktop bridge for the current OS before Electron packaging."""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "desktop-sidecar"
OUTPUT.mkdir(exist_ok=True)
name = "ascii-tree-reorg-sidecar.exe" if sys.platform == "win32" else "ascii-tree-reorg-sidecar"
subprocess.run(
    [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--onefile",
        "--name",
        name,
        "--distpath",
        str(OUTPUT),
        str(ROOT / "src" / "ascii_tree_reorg" / "desktop" / "bridge.py"),
    ],
    check=True,
    cwd=ROOT,
)
for spec in ROOT.glob("*.spec"):
    spec.unlink()
shutil.rmtree(ROOT / "build", ignore_errors=True)
print(OUTPUT / name)
