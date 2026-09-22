import unittest.mock
from pathlib import Path
import pytest
from ascii_tree_reorg.core.auditor import StructureAuditor
from ascii_tree_reorg.core.models import TreeNode
from ascii_tree_reorg.core.parser import AsciiTreeParser
from ascii_tree_reorg.core.resolver import ConflictResolver
from ascii_tree_reorg.engine.reorganizer import DirectoryReorganizer


@pytest.fixture
def temp_workspace(tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    source.mkdir()
    dest.mkdir()
    (source / "data.csv").write_text("col1,col2\n1,2", encoding="utf-8")
    (source / "config.yaml").write_text("env: prod", encoding="utf-8")
    return source, dest


def test_tree_parser(tmp_path):
    tree_content = """my_project/
├── configs/
│   └── config.yaml
└── data.csv"""
    tree_file = tmp_path / "tree.txt"
    tree_file.write_text(tree_content.strip(), encoding="utf-8")

    parser = AsciiTreeParser(tree_file, fallback_width=4)
    nodes = parser.parse()

    assert len(nodes) == 4
    assert nodes[1].relative_path == Path("my_project/configs")
    assert nodes[1].is_directory is True
    assert nodes[2].relative_path == Path("my_project/configs/config.yaml")
    assert nodes[2].is_directory is False


def test_safe_copy_execution(temp_workspace):
    source, dest = temp_workspace
    nodes = [
        TreeNode("my_app", Path("my_app"), True, 0, 1),
        TreeNode("config.yaml", Path("my_app/config.yaml"), False, 1, 2),
    ]

    reorganizer = DirectoryReorganizer(source_dir=source, target_dir=dest, move_files=False)
    reorganizer.execute(nodes)

    assert (dest / "my_app" / "config.yaml").exists()
    assert (source / "config.yaml").exists()


def test_destructive_move_execution(temp_workspace):
    source, dest = temp_workspace
    nodes = [
        TreeNode("my_app", Path("my_app"), True, 0, 1),
        TreeNode("config.yaml", Path("my_app/config.yaml"), False, 1, 2),
    ]

    reorganizer = DirectoryReorganizer(source_dir=source, target_dir=dest, move_files=True)
    reorganizer.execute(nodes)

    assert (dest / "my_app" / "config.yaml").exists()
    assert not (source / "config.yaml").exists()


def test_structure_auditor_reports_no_crash(temp_workspace):
    source, dest = temp_workspace
    nodes = [
        TreeNode("my_app", Path("my_app"), True, 0, 1),
        TreeNode("config.yaml", Path("my_app/config.yaml"), False, 1, 2),
        TreeNode("config.yaml", Path("my_app/sub/config.yaml"), False, 2, 3),
    ]
    reorganizer = DirectoryReorganizer(source_dir=source, target_dir=dest)
    auditor = StructureAuditor(nodes, reorganizer.source_index)
    auditor.run_audit()


def test_conflict_resolver_interactive_pick(tmp_path):
    node = TreeNode("dup.txt", Path("target/dup.txt"), False, 1, 1)
    cand_a = tmp_path / "a/dup.txt"
    cand_b = tmp_path / "b/dup.txt"
    for c in [cand_a, cand_b]:
        c.parent.mkdir(parents=True, exist_ok=True)
        c.write_text("test", encoding="utf-8")

    with unittest.mock.patch("builtins.input", return_value="2"):
        chosen = ConflictResolver.prompt_selection(node, [cand_a, cand_b], tmp_path)
        assert chosen == cand_b


def test_conflict_resolver_interactive_skip(tmp_path):
    node = TreeNode("dup.txt", Path("target/dup.txt"), False, 1, 1)
    cand_a = tmp_path / "a/dup.txt"
    cand_b = tmp_path / "b/dup.txt"
    for c in [cand_a, cand_b]:
        c.parent.mkdir(parents=True, exist_ok=True)
        c.write_text("test", encoding="utf-8")

    with unittest.mock.patch("builtins.input", return_value="s"):
        chosen = ConflictResolver.prompt_selection(node, [cand_a, cand_b], tmp_path)
        assert chosen is None