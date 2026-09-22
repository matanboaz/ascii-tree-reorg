"""Regression tests for the strict tokenizer and explicit root rules."""
from pathlib import Path

import pytest

from ascii_tree_reorg.core.generator import DirectoryTreeGenerator
from ascii_tree_reorg.core.parser import AsciiTreeParser


def _parse(tmp_path, content: str, **kwargs):
    tree_file = tmp_path / "tree.txt"
    tree_file.write_text(content.strip("\n"), encoding="utf-8")
    return AsciiTreeParser(tree_file, **kwargs).parse()


# --- Names survive tokenization ----------------------------------------------

def test_hash_inside_name_is_preserved(tmp_path):
    nodes = _parse(tmp_path, "root/\n└── report#1.txt")
    assert nodes[1].name == "report#1.txt"


def test_full_line_comments_are_skipped(tmp_path):
    nodes = _parse(
        tmp_path,
        "# header comment\n#\nroot/\n├── a.txt\n   # indented comment\n└── b.txt",
    )
    assert [n.name for n in nodes] == ["root", "a.txt", "b.txt"]


def test_hash_name_without_space_is_not_a_comment(tmp_path):
    nodes = _parse(tmp_path, "root/\n└── #anchor.txt")
    assert nodes[1].name == "#anchor.txt"


def test_leading_punctuation_is_preserved(tmp_path):
    nodes = _parse(tmp_path, "root/\n├── -draft.txt\n└── +add.txt")
    assert [n.name for n in nodes] == ["root", "-draft.txt", "+add.txt"]


# --- Explicit root classification --------------------------------------------

def test_single_file_root_is_a_file(tmp_path):
    nodes = _parse(tmp_path, "README.md")
    assert len(nodes) == 1
    assert nodes[0].is_directory is False
    assert nodes[0].depth == 0


def test_single_dir_root_with_slash(tmp_path):
    nodes = _parse(tmp_path, "my_project/")
    assert nodes[0].is_directory is True


def test_root_without_slash_but_with_children_is_a_dir(tmp_path):
    nodes = _parse(tmp_path, "my_project\n└── main.py")
    assert nodes[0].is_directory is True
    assert nodes[1].is_directory is False
    assert nodes[1].relative_path == Path("my_project/main.py")


def test_dot_root_is_skipped(tmp_path):
    nodes = _parse(tmp_path, ".\n├── dir/\n└── file.txt")
    assert [n.name for n in nodes] == ["dir", "file.txt"]
    assert nodes[0].is_directory is True


def test_target_root_strip_requires_directory(tmp_path):
    tree = tmp_path / "tree.txt"
    tree.write_text("my_project/\n└── main.py", encoding="utf-8")
    nodes = AsciiTreeParser(tree).parse(target_root_name="my_project")
    assert [n.name for n in nodes] == ["main.py"]
    assert nodes[0].depth == 0


# --- Strict indentation -------------------------------------------------------

def test_standard_tree_output_parses(tmp_path):
    nodes = _parse(
        tmp_path,
        "my_project/\n├── configs/\n│   └── config.yaml\n└── data.csv",
    )
    assert [n.depth for n in nodes] == [0, 1, 2, 1]
    assert nodes[2].relative_path == Path("my_project/configs/config.yaml")


def test_windows_style_wide_connector_parses(tmp_path):
    nodes = _parse(tmp_path, "root/\n├─── a.txt\n└─── sub/\n     └─── b.txt")
    assert [n.name for n in nodes] == ["root", "a.txt", "sub", "b.txt"]
    assert [n.depth for n in nodes] == [0, 1, 1, 2]


def test_mixed_guide_and_connector_widths_rejected(tmp_path):
    with pytest.raises(ValueError, match="not a multiple"):
        _parse(tmp_path, "root/\n├── sub1/\n│ └── file1.txt")


def test_ragged_prefix_rejected(tmp_path):
    with pytest.raises(ValueError, match="not a multiple"):
        _parse(tmp_path, "root/\n   ├── sub1/")


def test_inconsistent_connector_widths_rejected(tmp_path):
    with pytest.raises(ValueError, match="Inconsistent connector widths"):
        _parse(tmp_path, "root/\n├── a.txt\n├─── b.txt")


def test_indentation_jump_rejected(tmp_path):
    with pytest.raises(ValueError, match="jumps from depth"):
        _parse(tmp_path, "root/\n        └── deep.txt")


def test_depth_skipping_level_rejected(tmp_path):
    with pytest.raises(ValueError, match="jumps from depth"):
        _parse(tmp_path, "root/\n└── a/\n        └── deep.txt")


def test_plain_space_tree_uses_detected_unit(tmp_path):
    nodes = _parse(tmp_path, "root/\n  sub/\n    file.txt")
    assert [n.depth for n in nodes] == [0, 1, 2]
    assert nodes[2].relative_path == Path("root/sub/file.txt")


def test_plain_space_tree_uneven_indent_rejected(tmp_path):
    with pytest.raises(ValueError, match="not a multiple"):
        _parse(tmp_path, "root/\n    sub/\n      file.txt")


# --- Round trip with the generator -------------------------------------------

def test_generator_output_round_trips(tmp_path):
    root = tmp_path / "sample"
    (root / "configs").mkdir(parents=True)
    (root / "configs" / "app.yaml").write_text("env: prod", encoding="utf-8")
    (root / "data.csv").write_text("a,b", encoding="utf-8")

    tree_text = DirectoryTreeGenerator(root).generate()
    tree_file = tmp_path / "tree.txt"
    tree_file.write_text(tree_text, encoding="utf-8")

    nodes = AsciiTreeParser(tree_file).parse()
    by_path = {str(n.relative_path): n for n in nodes}
    assert by_path["sample"].is_directory is True
    assert by_path["sample/configs"].is_directory is True
    assert by_path["sample/configs/app.yaml"].is_directory is False
    assert by_path["sample/data.csv"].is_directory is False


# --- Non-default generator indent round trips --------------------------------

def _nested_sample(root: Path) -> None:
    (root / "configs" / "app.yaml").parent.mkdir(parents=True)
    (root / "configs" / "app.yaml").write_text("env: prod", encoding="utf-8")
    (root / "data" / "raw").mkdir(parents=True)
    (root / "data" / "raw" / "dataset.csv").write_text("a,b", encoding="utf-8")
    (root / "README.md").write_text("hi", encoding="utf-8")


@pytest.mark.parametrize("step", [2, 3, 4, 5, 8])
def test_generator_round_trip_at_indent_step(tmp_path, step):
    from ascii_tree_reorg.core.generator import GeneratorOptions

    root = tmp_path / "sample"
    root.mkdir()
    _nested_sample(root)

    tree_text = DirectoryTreeGenerator(
        root, options=GeneratorOptions(indent_step=step)
    ).generate()
    tree_file = tmp_path / "tree.txt"
    tree_file.write_text(tree_text, encoding="utf-8")

    nodes = AsciiTreeParser(tree_file).parse()
    by_path = {str(n.relative_path): n for n in nodes}
    assert by_path["sample"].is_directory is True
    assert by_path["sample/configs/app.yaml"].is_directory is False
    assert by_path["sample/data/raw"].is_directory is True
    assert by_path["sample/data/raw/dataset.csv"].depth == 3
    assert by_path["sample/README.md"].is_directory is False


def test_generator_rejects_too_small_indent_step(tmp_path):
    from ascii_tree_reorg.core.generator import GeneratorOptions

    with pytest.raises(ValueError, match="indent_step"):
        GeneratorOptions(indent_step=1)
