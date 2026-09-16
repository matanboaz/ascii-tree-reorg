#!/usr/bin/env python3
"""Launcher for the native Desktop GUI (Tkinter)."""
import sys
from pathlib import Path

# Add src to sys.path so packages import cleanly
repo_root = Path(__file__).resolve().parent
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from ascii_tree_reorg.ui.tkinter_app import launch_gui as run_gui

if __name__ == "__main__":
    run_gui()