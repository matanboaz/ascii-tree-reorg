"""Newline-delimited JSON bridge between Electron and the Python engine."""

import dataclasses
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from typing import Optional

from ascii_tree_reorg.core.events import OperationEvent
from ascii_tree_reorg.core.generator import DirectoryTreeGenerator, GeneratorOptions
from ascii_tree_reorg.core.parser import AsciiTreeParser
from ascii_tree_reorg.engine.reorganizer import DirectoryReorganizer


def send(event: OperationEvent) -> None:
    print(json.dumps(dataclasses.asdict(event)), file=sys.__stdout__, flush=True)


def read_choice() -> Optional[str]:
    line = sys.stdin.readline()
    if not line:
        return None
    response = json.loads(line)
    if response.get("type") != "resolve_conflict":
        raise ValueError("Expected resolve_conflict response")
    return response.get("choice")


def main() -> None:
    request_line = sys.stdin.readline()
    if not request_line:
        return
    try:
        request = json.loads(request_line)
        if request.get("operation") == "generate":
            options = GeneratorOptions(
                include_files=bool(request.get("include_files", True)),
                max_depth=request.get("max_depth") or None,
                indent_step=int(request.get("indent_width", 4)),
            )
            tree = DirectoryTreeGenerator(Path(request["source"]), options).generate()
            send(OperationEvent("generated", "Tree generated.", data={"tree": tree}))
            send(OperationEvent("complete", "Tree is ready."))
            return

        source = Path(request["source"])
        destination = Path(request["destination"])
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tree_file:
            tree_file.write(request["tree"])
            tree_path = Path(tree_file.name)
        try:
            nodes = AsciiTreeParser(tree_path, fallback_width=int(request.get("indent_width", 4))).parse()
        finally:
            tree_path.unlink(missing_ok=True)

        def resolve(_node, candidates, _source_root):
            choice = read_choice()
            if choice is None:
                return None
            chosen = Path(choice).resolve()
            return next((candidate for candidate in candidates if candidate.resolve() == chosen), None)

        reorganizer = DirectoryReorganizer(
            source,
            destination,
            move_files=bool(request.get("move_files", False)),
            overwrite=bool(request.get("overwrite", False)),
            clean_relocated=bool(request.get("clean_relocated", False)),
            dry_run=bool(request.get("dry_run", False)),
            event_callback=send,
            conflict_resolver=resolve,
        )
        # Existing CLI text remains useful for diagnostics but stdout is reserved
        # for the JSON protocol in sidecar mode.
        with redirect_stdout(sys.stderr):
            reorganizer.execute(nodes)
        send(OperationEvent("complete", "Workspace is ready."))
    except Exception as error:
        send(OperationEvent("error", str(error), level="error"))


if __name__ == "__main__":
    main()
