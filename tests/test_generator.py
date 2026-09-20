import tempfile
from pathlib import Path
import pytest

from ascii_tree_reorg.core.generator import DirectoryTreeGenerator, GeneratorOptions


@pytest.fixture
def sample_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "sample_project"
        root.mkdir()
        
        # Structure
        (root / "configs").mkdir()
        (root / "configs" / "app.yaml").write_text("env: prod")
        (root / "data" / "raw").mkdir(parents=True)
        (root / "data" / "raw" / "dataset.csv").write_text("a,b,c")
        (root / "src").mkdir()
        (root / "src" / "main.py").write_text("print('hello')")
        (root / ".git").mkdir()  # Should be ignored
        
        yield root


def test_basic_tree_generation(sample_workspace):
    generator = DirectoryTreeGenerator(sample_workspace)
    tree_text = generator.generate()

    assert "sample_project/" in tree_text
    assert "configs/" in tree_text
    assert "app.yaml" in tree_text
    assert "data/" in tree_text
    assert "raw/" in tree_text
    assert "dataset.csv" in tree_text
    assert ".git" not in tree_text


def test_directories_only(sample_workspace):
    opts = GeneratorOptions(include_files=False)
    generator = DirectoryTreeGenerator(sample_workspace, options=opts)
    tree_text = generator.generate()

    assert "configs/" in tree_text
    assert "src/" in tree_text
    assert "app.yaml" not in tree_text
    assert "main.py" not in tree_text


def test_max_depth_clamping(sample_workspace):
    # Depth 1 allows root immediate children, but excludes data/raw
    opts = GeneratorOptions(max_depth=1)
    generator = DirectoryTreeGenerator(sample_workspace, options=opts)
    tree_text = generator.generate()

    assert "configs/" in tree_text
    assert "data/" in tree_text
    assert "raw/" not in tree_text