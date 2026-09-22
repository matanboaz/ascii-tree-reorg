import json
from importlib.resources import files

import ascii_tree_reorg


def test_version_has_single_expected_source():
    assert ascii_tree_reorg.__version__ == "0.3.0"


def test_packaged_default_configuration_is_available():
    resource = files("ascii_tree_reorg.resources").joinpath("default_config.json")
    config = json.loads(resource.read_text(encoding="utf-8"))
    assert config["indent_width"] == 4
    assert config["move_files"] is False
