"""Strict ASCII tree parsing.

Explicit rules replace the old regex/GCD heuristics:

* A comment line starts with '#' followed by a space or end of line.
  '#' anywhere else is part of the entry name, so "report#1.txt"
  survives intact.
* Box-drawing prefixes are tokenized into fixed-width units: ancestor
  guides ("│   " or plain spaces) and a final connector ("├── " /
  "└── ", any dash count). Every unit in a file must share one width;
  mixed or ragged indentation fails with a line-numbered error instead
  of a GCD guess.
* Directories are explicit: a trailing "/" marks one, and an entry with
  children must be one. A lone entry with neither is a file, so a
  single-file root is no longer misread as a directory.
* Entry names must be plain portable names: path separators, ".."
  segments, and absolute or drive-relative paths are rejected so a
  crafted tree can never escape the chosen target directory.
"""

from pathlib import Path
from typing import List, NamedTuple, Optional

from .models import TreeNode

_GUIDE = "│"
_CONNECTOR_STARTS = ("├", "└")
_DASH = "─"


class _Entry(NamedTuple):
    """One parsed tree line before hierarchy is attached."""

    line_number: int
    depth: int
    name: str
    dir_marker: bool  # trailing "/" in the source


def _validate_entry_name(name: str, line_number: int) -> None:
    """Rejects entry names that are not plain portable file names.

    Tree entries must be single names. Path separators, traversal segments,
    and absolute paths are rejected so a crafted tree can never make the
    reorganizer write outside the chosen target directory.
    """
    if name in (".", ".."):
        raise ValueError(
            f"Line {line_number}: entry '{name}' is not allowed. "
            "Tree entries must be plain file or directory names."
        )
    if "/" in name or "\\" in name:
        raise ValueError(
            f"Line {line_number}: entry '{name}' contains a path separator. "
            "Nested paths, '..' segments, and absolute paths are not allowed; "
            "use indentation to express hierarchy."
        )
    if len(name) >= 2 and name[1] == ":":
        raise ValueError(
            f"Line {line_number}: entry '{name}' looks like an absolute or "
            "drive-relative path, which is not allowed."
        )


def _is_comment(line: str) -> bool:
    """A comment is '#' followed by a space or end of line.

    '#anchor.txt' or 'report#1.txt' are names, not comments.
    """
    stripped = line.lstrip(" ")
    return stripped == "#" or stripped.startswith("# ")


def _split_line(line: str, line_no: int) -> tuple:
    """Splits one content line into (kind, prefix_len, connector_width, text).

    kind is "connector" for box-drawing entries and "plain" otherwise.
    Raises ValueError with the line number on malformed prefixes.
    """
    i = 0
    n = len(line)
    while i < n and (line[i] == _GUIDE or line[i] == " "):
        i += 1

    if i < n and line[i] in _CONNECTOR_STARTS:
        j = i + 1
        while j < n and line[j] == _DASH:
            j += 1
        if j == i + 1:
            raise ValueError(
                f"Line {line_no}: connector '{line[i]}' must be followed by at "
                f"least one '{_DASH}'."
            )
        k = j
        while k < n and line[k] == " ":
            k += 1
        text = line[k:]
        if not text:
            raise ValueError(f"Line {line_no}: connector without an entry name.")
        width = k - i
        if i % width != 0:
            raise ValueError(
                f"Line {line_no}: indentation before the connector is {i} chars, "
                f"not a multiple of this line's indent unit ({width}). Ancestor "
                "guides and connectors must share one width."
            )
        for start in range(0, i, width):
            unit = line[start:start + width]
            if unit != " " * width and unit != _GUIDE + " " * (width - 1):
                raise ValueError(
                    f"Line {line_no}: malformed ancestor guide {unit!r}; expected "
                    f"'{_GUIDE}' plus spaces or spaces only."
                )
        return ("connector", i, width, text)

    if _GUIDE in line[:i]:
        raise ValueError(
            f"Line {line_no}: '{_GUIDE}' guide without a connector."
        )
    return ("plain", i, None, line[i:])


class AsciiTreeParser:
    """Parses raw ASCII tree text into structured TreeNode objects."""

    def __init__(self, file_path: Path, fallback_width: int = 4):
        self.file_path = file_path
        self.fallback_width = max(1, fallback_width)

    def _read_content_lines(self) -> List[tuple]:
        with open(self.file_path, "r", encoding="utf-8") as f:
            raw_lines = [l.rstrip("\r\n") for l in f.readlines()]
        return [
            (line_no, line)
            for line_no, line in enumerate(raw_lines, start=1)
            if line.strip() and not _is_comment(line)
        ]

    def _unit_width(self, parts: List[tuple]) -> int:
        """Resolves the single indent unit for the file.

        Connector lines fix the width exactly. A file with only plain
        space indentation uses the smallest observed indent, and every
        other indent must be a multiple of it.
        """
        widths = {width for _, kind, _, width, _ in parts if kind == "connector"}
        if widths:
            if len(widths) > 1:
                first = next(p for p in parts if p[1] == "connector")
                raise ValueError(
                    f"Inconsistent connector widths {sorted(widths)}; e.g. line "
                    f"{first[0]} uses {first[3]}. A tree must use one indent width."
                )
            return widths.pop()
        indents = [prefix for _, kind, prefix, _, _ in parts if kind == "plain" and prefix > 0]
        return min(indents) if indents else self.fallback_width

    def _to_entries(self, content_lines: List[tuple]) -> List[_Entry]:
        parts = []
        for line_no, line in content_lines:
            kind, prefix, width, text = _split_line(line, line_no)
            parts.append((line_no, kind, prefix, width, text))

        unit = self._unit_width(parts)
        entries: List[_Entry] = []
        for line_no, kind, prefix, width, text in parts:
            if kind == "connector":
                depth = prefix // width + 1
            else:
                if prefix == 0:
                    depth = 0
                else:
                    if prefix % unit != 0:
                        raise ValueError(
                            f"Line {line_no}: indentation of {prefix} spaces is not "
                            f"a multiple of the indent unit ({unit})."
                        )
                    depth = prefix // unit

            dir_marker = text.endswith("/")
            name = text.rstrip("/")
            if name in (".", "./"):
                continue
            if not name:
                raise ValueError(f"Line {line_no}: empty entry name.")
            _validate_entry_name(name, line_no)
            entries.append(_Entry(line_no, depth, name, dir_marker))

        prev: Optional[_Entry] = None
        for entry in entries:
            if prev is not None and entry.depth > prev.depth + 1:
                raise ValueError(
                    f"Line {entry.line_number}: indentation jumps from depth "
                    f"{prev.depth} to {entry.depth}; a parent level is missing."
                )
            prev = entry
        return entries

    @staticmethod
    def _classify(entries: List[_Entry]) -> List[_Entry]:
        """Marks directories explicitly.

        A trailing "/" marks a directory; an entry with children must be
        one. Anything else is a file, including a lone root entry.
        """
        classified = []
        for idx, entry in enumerate(entries):
            has_children = (
                idx + 1 < len(entries) and entries[idx + 1].depth > entry.depth
            )
            classified.append(
                entry._replace(dir_marker=entry.dir_marker or has_children)
            )
        return classified

    def parse(self, target_root_name: str = "") -> List[TreeNode]:
        content_lines = self._read_content_lines()
        entries = self._classify(self._to_entries(content_lines))

        # An enclosing root directory that matches the target name is
        # stripped and its children shift up one level.
        if (
            target_root_name
            and entries
            and entries[0].depth == 0
            and entries[0].dir_marker
            and entries[0].name.lower() == target_root_name.lower()
        ):
            entries = [
                e._replace(depth=e.depth - 1) for e in entries[1:]
            ]

        stack: List[tuple] = []
        nodes: List[TreeNode] = []
        for entry in entries:
            while stack and stack[-1][0] >= entry.depth:
                stack.pop()
            parent_path = stack[-1][1] if stack else Path("")
            rel_path = parent_path / entry.name if str(parent_path) else Path(entry.name)
            nodes.append(
                TreeNode(
                    name=entry.name,
                    relative_path=rel_path,
                    is_directory=entry.dir_marker,
                    depth=entry.depth,
                    line_number=entry.line_number,
                )
            )
            if entry.dir_marker:
                stack.append((entry.depth, rel_path))
        return nodes
