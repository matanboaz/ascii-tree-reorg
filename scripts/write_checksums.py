"""Write a deterministic SHA-256 manifest for desktop release artifacts."""
import hashlib
import sys
from pathlib import Path
root = Path(sys.argv[1] if len(sys.argv) > 1 else "release")
output_name = sys.argv[2] if len(sys.argv) > 2 else "SHA256SUMS.txt"
allowed = {".zip", ".dmg", ".exe", ".AppImage", ".deb"}
artifacts = sorted(path for path in root.iterdir() if path.is_file() and path.name != output_name and path.suffix in allowed)
if not artifacts:
    raise SystemExit(f"No release artifacts in {root}")
lines=[]
for path in artifacts:
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    lines.append(f"{digest}  {path.name}")
(root/output_name).write_text("\n".join(lines)+"\n",encoding="utf-8")
print(f"Wrote checksums for {len(artifacts)} artifacts")
