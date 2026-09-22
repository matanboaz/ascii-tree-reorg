"""Inspect a packaged Canopy ZIP and execute its bundled Python sidecar."""
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

archive = Path(sys.argv[1]).resolve()
if not archive.is_file() or archive.suffix.lower() != ".zip":
    raise SystemExit(f"Expected a desktop ZIP, got {archive}")
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    with zipfile.ZipFile(archive) as bundle:
        unsafe = [name for name in bundle.namelist() if Path(name).is_absolute() or ".." in Path(name).parts]
        if unsafe:
            raise SystemExit(f"Unsafe archive members: {unsafe[:3]}")
        bundle.extractall(root)
    expected = "ascii-tree-reorg-sidecar.exe" if sys.platform == "win32" else "ascii-tree-reorg-sidecar"
    matches = list(root.rglob(expected))
    if len(matches) != 1:
        raise SystemExit(f"Expected one {expected}, found {len(matches)}")
    sidecar = matches[0]
    if sys.platform != "win32":
        sidecar.chmod(sidecar.stat().st_mode | 0o111)
    request = json.dumps({"operation": "generate", "source": str(root), "include_files": False, "max_depth": 1}) + "\n"
    result = subprocess.run([str(sidecar)], input=request, text=True, capture_output=True, timeout=30, check=True)
    events = [json.loads(line) for line in result.stdout.splitlines()]
    if not events or events[-1].get("kind") != "complete":
        raise SystemExit(f"Sidecar did not complete: {events[-3:]}")
print(f"Archive smoke passed: {archive.name} ({archive.stat().st_size / 1024 / 1024:.1f} MB)")
