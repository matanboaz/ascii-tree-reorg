"""ASCII tree generator engine for scanning local directory structures"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set

@dataclass(frozen=True)
class GeneratorOptions:
    """Configuration options for ASCII tree generation."""

    include_files: bool = True
    max_depth: Optional[int] = None
    indent_step: int = 4
    ignore_patterns: Set[str] = None

    def __post_init__(self) -> None:
        if self.indent_step < 2:
            raise ValueError(
                f"indent_step must be at least 2, got {self.indent_step}."
            )

    def get_ignore_set(self) -> Set[str]:
        default_ignores = {
            ".git",
            ".github",
            "__pycache__",
            ".pytest_cache",
            ".venv",
            "venv",
            ".idea",
            ".vscode",
            ".DS_Store",
            "dist",
            "build",
            "*.egg-info",
        }
        if self.ignore_patterns:
            return default_ignores.union(self.ignore_patterns)
        return default_ignores

class DirectoryTreeGenerator:
    """Generates standard terminal-style ASCII/Unicode tree strings from a folder."""

    def __init__(self, root_dir: Path, options: Optional[GeneratorOptions] = None):
        self.root_dir = Path(root_dir).resolve()
        self.options = options or GeneratorOptions()
        self._ignores = self.options.get_ignore_set()

    def _should_ignore(self, entry_name: str) -> bool:
        if entry_name in self._ignores:
            return True
        for pattern in self._ignores:
            if pattern.startswith("*") and entry_name.endswith(pattern[1:]):
                return True
        return False

    def _connector(self, is_last: bool) -> str:
        """Entry connector padded to exactly one indent unit.

        Guides and connectors share the indent_step width so generated
        trees always satisfy the strict parser, at any indent_step.
        """
        step = self.options.indent_step
        dash_run = "─" * max(1, step - 2)
        return ("└" if is_last else "├") + dash_run.ljust(step - 1)

    def _build_tree(self, current_dir: Path, prefix: str = "", current_depth: int = 0) -> List[str]:
        if self.options.max_depth is not None and current_depth >= self.options.max_depth:
            return []

        try:
            raw_entries = [p for p in current_dir.iterdir() if not self._should_ignore(p.name)]
        except PermissionError:
            return [f"{prefix}{self._connector(is_last=True)}[Permission Denied]"]

        # Filter out files if configured
        if not self.options.include_files:
            raw_entries = [p for p in raw_entries if p.is_dir()]

        # Sort: directories first, then alphabetical (case-insensitive)
        entries = sorted(raw_entries, key=lambda x: (not x.is_dir(), x.name.lower()))

        lines: List[str] = []
        count = len(entries)

        for idx, entry in enumerate(entries):
            is_last = idx == (count - 1)
            connector = self._connector(is_last)
            display_name = f"{entry.name}/" if entry.is_dir() else entry.name

            lines.append(f"{prefix}{connector}{display_name}")

            if entry.is_dir():
                step = self.options.indent_step
                continuation = " " * step if is_last else "│" + " " * (step - 1)
                nested_lines = self._build_tree(
                    entry,
                    prefix=prefix + continuation,
                    current_depth=current_depth + 1,
                )
                lines.extend(nested_lines)

        return lines

    def generate(self) -> str:
        """Walks the folder and returns the full ASCII tree as a string."""
        if not self.root_dir.is_dir():
            raise NotADirectoryError(f"Directory not found: {self.root_dir}")

        root_label = f"{self.root_dir.name}/"
        body_lines = self._build_tree(self.root_dir, prefix="", current_depth=0)
        return "\n".join([root_label] + body_lines)
