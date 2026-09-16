#!/usr/bin/env python3
"""Convenience root runner for local CLI execution."""
import sys
from pathlib import Path

# Add src to sys.path so it runs directly without pip installation
src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from ascii_tree_reorg.app import main

if __name__ == "__main__":
    main()
