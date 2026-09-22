"""Defensive tests for path containment, safe defaults, and dry-run behavior."""
from pathlib import Path

import pytest

from ascii_tree_reorg.core.models import TreeNode
from ascii_tree_reorg.core.parser import AsciiTreeParser
from ascii_tree_reorg.engine.reorganizer import DirectoryReorganizer


def _write_tree(tmp_path, content: str) -> Path:
    tree_file = tmp_path / "tree.txt"
    tree_file.write_text(content.strip(), encoding="utf-8")
    return tree_file


@pytest.fixture
def workspace(tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    (source / "config.yaml").write_text("env: new", encoding="utf-8")
    return source, dest


# --- Parser rejection of unsafe entries -------------------------------------

def test_parser_rejects_parent_traversal(tmp_path):
    tree = _write_tree(tmp_path, "root/\n└── ..")
    with pytest.raises(ValueError, match="not allowed"):
        AsciiTreeParser(tree).parse()


def test_parser_rejects_absolute_path(tmp_path):
    tree = _write_tree(tmp_path, "root/\n└── /etc/passwd")
    with pytest.raises(ValueError, match="path separator"):
        AsciiTreeParser(tree).parse()


def test_parser_rejects_embedded_separator(tmp_path):
    tree = _write_tree(tmp_path, "root/\n└── sub/evil.txt")
    with pytest.raises(ValueError, match="path separator"):
        AsciiTreeParser(tree).parse()


def test_parser_rejects_backslash_path(tmp_path):
    tree = _write_tree(tmp_path, "root/\n└── ..\\evil.txt")
    with pytest.raises(ValueError):
        AsciiTreeParser(tree).parse()


def test_parser_rejects_drive_relative_path(tmp_path):
    tree = _write_tree(tmp_path, "root/\n└── C:evil.txt")
    with pytest.raises(ValueError, match="drive-relative"):
        AsciiTreeParser(tree).parse()


def test_parser_accepts_normal_tree(tmp_path):
    tree = _write_tree(tmp_path, "root/\n├── sub/\n│   └── file.txt\n└── data.csv")
    nodes = AsciiTreeParser(tree).parse()
    assert len(nodes) == 4


# --- Reorganizer containment (defense in depth) ------------------------------

def test_reorganizer_rejects_traversal_node(workspace):
    source, dest = workspace
    node = TreeNode("evil.txt", Path("../evil.txt"), False, 1, 1)
    reorganizer = DirectoryReorganizer(source_dir=source, target_dir=dest)
    with pytest.raises(ValueError, match="Unsafe"):
        reorganizer.execute([node])


def test_reorganizer_blocks_symlink_escape(workspace):
    source, dest = workspace
    outside = dest.parent / "outside"
    outside.mkdir()
    link = dest / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Symlinks not supported on this platform")
    node = TreeNode("config.yaml", Path("link/config.yaml"), False, 1, 1)
    reorganizer = DirectoryReorganizer(source_dir=source, target_dir=dest)
    with pytest.raises(ValueError, match="outside target"):
        reorganizer.execute([node])
    assert not (outside / "config.yaml").exists()


# --- Safe-by-default deletion behavior ---------------------------------------

def test_default_preserves_undeclared_target_items(workspace):
    source, dest = workspace
    keep = dest / "keep.txt"
    keep.write_text("precious", encoding="utf-8")
    nodes = [TreeNode("my_app", Path("my_app"), True, 0, 1)]
    DirectoryReorganizer(source_dir=source, target_dir=dest).execute(nodes)
    assert keep.exists()


def test_clean_relocated_opt_in_purges(workspace):
    source, dest = workspace
    orphan = dest / "orphan.txt"
    orphan.write_text("old", encoding="utf-8")
    gitkeep = dest / ".gitkeep"
    gitkeep.write_text("", encoding="utf-8")
    nodes = [TreeNode("my_app", Path("my_app"), True, 0, 1)]
    DirectoryReorganizer(
        source_dir=source, target_dir=dest, clean_relocated=True
    ).execute(nodes)
    assert not orphan.exists()
    assert gitkeep.exists()  # protected metadata survives opt-in cleanup


def test_default_does_not_overwrite(workspace):
    source, dest = workspace
    existing = dest / "my_app" / "config.yaml"
    existing.parent.mkdir(parents=True)
    existing.write_text("env: old", encoding="utf-8")
    nodes = [
        TreeNode("my_app", Path("my_app"), True, 0, 1),
        TreeNode("config.yaml", Path("my_app/config.yaml"), False, 1, 2),
    ]
    DirectoryReorganizer(source_dir=source, target_dir=dest).execute(nodes)
    assert existing.read_text(encoding="utf-8") == "env: old"


def test_overwrite_opt_in_replaces(workspace):
    source, dest = workspace
    existing = dest / "my_app" / "config.yaml"
    existing.parent.mkdir(parents=True)
    existing.write_text("env: old", encoding="utf-8")
    nodes = [
        TreeNode("my_app", Path("my_app"), True, 0, 1),
        TreeNode("config.yaml", Path("my_app/config.yaml"), False, 1, 2),
    ]
    DirectoryReorganizer(
        source_dir=source, target_dir=dest, overwrite=True
    ).execute(nodes)
    assert existing.read_text(encoding="utf-8") == "env: new"


# --- Dry run ------------------------------------------------------------------

def test_dry_run_makes_no_changes(workspace, capsys):
    source, dest = workspace
    orphan = dest / "orphan.txt"
    orphan.write_text("old", encoding="utf-8")
    nodes = [
        TreeNode("my_app", Path("my_app"), True, 0, 1),
        TreeNode("config.yaml", Path("my_app/config.yaml"), False, 1, 2),
    ]
    DirectoryReorganizer(
        source_dir=source,
        target_dir=dest,
        overwrite=True,
        clean_relocated=True,
        dry_run=True,
    ).execute(nodes)
    out = capsys.readouterr().out
    assert "[DRY RUN]" in out
    assert orphan.exists()                      # purge only planned
    assert not (dest / "my_app").exists()       # mkdir only planned
    assert (source / "config.yaml").exists()    # source untouched


def test_dry_run_skips_conflict_prompt(workspace, capsys):
    source, dest = workspace
    (source / "a").mkdir()
    (source / "a" / "config.yaml").write_text("a", encoding="utf-8")
    nodes = [TreeNode("config.yaml", Path("config.yaml"), False, 0, 1)]
    reorganizer = DirectoryReorganizer(
        source_dir=source, target_dir=dest, dry_run=True
    )
    assert len(reorganizer.source_index["config.yaml"]) == 2
    reorganizer.execute(nodes)  # must not call input()
    assert "Would prompt" in capsys.readouterr().out
    assert not (dest / "config.yaml").exists()
