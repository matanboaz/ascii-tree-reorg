import json
from pathlib import Path
from typing import Any, Dict


def load_configuration(config_path: Path) -> Dict[str, Any]:
    """Loads configuration JSON file if present; returns defaults otherwise."""
    defaults = {
        "indent_width": 4,
        "move_files": False,
        "default_input_tree": "data/inputs/structure.txt",
        "default_input_source": "data/inputs/raw_archive",
        "default_output_root": "data/outputs",
    }
    if config_path and config_path.is_file():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_conf = json.load(f)
                defaults.update(user_conf)
        except Exception as e:
            print(f"[WARN] Failed to read configuration from {config_path}: {e}")
    return defaults