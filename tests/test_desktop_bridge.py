import json
import os
import subprocess
import sys
from pathlib import Path


def run_bridge(request, root: Path):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).parents[1] / "src")
    result = subprocess.run(
        [sys.executable, "-m", "ascii_tree_reorg.desktop.bridge"],
        input=json.dumps(request) + "\n",
        capture_output=True,
        text=True,
        cwd=root,
        env=environment,
        check=True,
    )
    return [json.loads(line) for line in result.stdout.splitlines()], result.stderr


def test_bridge_reconstructs_with_clean_json_stdout(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    (source / "note.txt").write_text("hello", encoding="utf-8")

    events, diagnostics = run_bridge(
        {
            "operation": "reconstruct",
            "source": str(source),
            "destination": str(destination),
            "tree": "note.txt",
        },
        tmp_path,
    )

    assert (destination / "note.txt").read_text(encoding="utf-8") == "hello"
    assert [event["kind"] for event in events] == ["file", "progress", "complete"]
    assert "[COPYING]" in diagnostics


def test_bridge_generates_tree(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "note.txt").write_text("hello", encoding="utf-8")

    events, _ = run_bridge(
        {"operation": "generate", "source": str(source), "include_files": True},
        tmp_path,
    )

    assert [event["kind"] for event in events] == ["generated", "complete"]
    assert "note.txt" in events[0]["data"]["tree"]


def test_bridge_reports_errors_as_events(tmp_path):
    events, _ = run_bridge(
        {
            "operation": "reconstruct",
            "source": str(tmp_path / "missing"),
            "destination": str(tmp_path / "destination"),
            "tree": "note.txt",
        },
        tmp_path,
    )

    assert events[-1]["kind"] == "complete"
    assert any(event["kind"] == "missing" for event in events)
