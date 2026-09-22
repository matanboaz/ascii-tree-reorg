from pathlib import Path


def test_legacy_ui_entrypoints_are_retired():
    root = Path(__file__).parents[1]
    assert not (root / "app_ui.py").exists()
    assert not (root / "run_ui.py").exists()
    assert not (root / "src/ascii_tree_reorg/ui").exists()
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8").lower()
    assert "streamlit" not in pyproject
    assert "tkinter" not in pyproject
