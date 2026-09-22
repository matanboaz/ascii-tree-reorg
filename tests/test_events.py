from pathlib import Path

from ascii_tree_reorg.core.events import OperationEvent
from ascii_tree_reorg.core.models import TreeNode
from ascii_tree_reorg.engine.reorganizer import DirectoryReorganizer


def test_structured_events_report_file_progress_and_completion(tmp_path, capsys):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "note.txt").write_text("hello", encoding="utf-8")
    nodes = [
        TreeNode("project", Path("project"), True, 1, 0),
        TreeNode("note.txt", Path("project/note.txt"), False, 2, 1),
    ]
    events = []

    DirectoryReorganizer(source, target, event_callback=events.append).execute(nodes)

    assert (target / "project" / "note.txt").read_text(encoding="utf-8") == "hello"
    assert [(event.kind, event.current, event.total) for event in events] == [
        ("progress", 1, 2),
        ("file", 0, 0),
        ("progress", 2, 2),
    ]
    assert events[1].data["path"] == "project/note.txt"
    assert "[COPYING] note.txt -> project/note.txt" in capsys.readouterr().out


def test_conflict_callback_chooses_source_without_terminal_input(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    (source / "first").mkdir(parents=True)
    (source / "second").mkdir()
    (source / "first" / "same.txt").write_text("first", encoding="utf-8")
    (source / "second" / "same.txt").write_text("second", encoding="utf-8")
    node = TreeNode("same.txt", Path("same.txt"), False, 1, 0)
    events = []
    choices = []

    def choose(current_node, candidates, source_root):
        choices.append((current_node, candidates, source_root))
        return next(path for path in candidates if path.parent.name == "second")

    DirectoryReorganizer(
        source,
        target,
        event_callback=events.append,
        conflict_resolver=choose,
    ).execute([node])

    assert (target / "same.txt").read_text(encoding="utf-8") == "second"
    assert choices and choices[0][0] == node
    conflict = next(event for event in events if event.kind == "conflict")
    assert conflict.level == "warning"
    assert len(conflict.data["candidates"]) == 2


def test_dry_run_conflict_is_structured_and_never_calls_resolver(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    (source / "first").mkdir(parents=True)
    (source / "second").mkdir()
    (source / "first" / "same.txt").write_text("first", encoding="utf-8")
    (source / "second" / "same.txt").write_text("second", encoding="utf-8")
    events = []

    def must_not_run(*_args):
        raise AssertionError("dry runs must not ask for a conflict choice")

    DirectoryReorganizer(
        source,
        target,
        dry_run=True,
        event_callback=events.append,
        conflict_resolver=must_not_run,
    ).execute([TreeNode("same.txt", Path("same.txt"), False, 1, 0)])

    conflict = next(event for event in events if event.kind == "conflict")
    assert conflict.data["dry_run"] is True
    assert not target.exists()


def test_operation_event_has_isolated_data_dicts():
    first = OperationEvent("one", "one")
    second = OperationEvent("two", "two")

    first.data["value"] = 1

    assert second.data == {}
