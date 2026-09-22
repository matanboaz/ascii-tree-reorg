import datetime
import sys
from pathlib import Path
from typing import Callable, List, Optional
from .models import TreeNode


ConflictChoice = Callable[[TreeNode, List[Path], Path], Optional[Path]]


class ConflictResolver:
    """Interactively prompts the user to select the intended source file candidate."""

    @staticmethod
    def prompt_selection(node: TreeNode, candidates: List[Path], source_root: Path) -> Optional[Path]:
        print(f"\n[CONFLICT] Multiple candidates for destination: '{node.relative_path}'")
        for idx, path in enumerate(candidates, start=1):
            try:
                stat = path.stat()
                size_kb = stat.st_size / 1024
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            except OSError:
                size_kb = 0.0
                mtime = "unknown"

            try:
                rel_to_src = path.relative_to(source_root)
            except ValueError:
                rel_to_src = path
            print(f"  [{idx}] {rel_to_src}  ({size_kb:.2f} KB, modified {mtime})")
        print("  [s] Skip this file")

        while True:
            try:
                choice = input(f"Select candidate [1-{len(candidates)}] or 's' to skip: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                # Fallback only when input() cannot read from stdin
                if not sys.stdin.isatty():
                    print("[INFO] Non-interactive stdin detected. Defaulting to candidate [1].")
                    return candidates[0]
                print(f"\n[ABORTED] Skipping '{node.relative_path}'.")
                return None

            if choice == "s":
                print(f"[SKIPPED] Skipped '{node.relative_path}'.")
                return None
            if choice.isdigit():
                val = int(choice)
                if 1 <= val <= len(candidates):
                    return candidates[val - 1]
            print(f"Invalid choice. Please enter a number between 1 and {len(candidates)}, or 's'.")