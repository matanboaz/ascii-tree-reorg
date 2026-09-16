import collections
from pathlib import Path
from typing import Dict, List
from .models import TreeNode


class StructureAuditor:
    """Inspects parsed nodes and source files for name collisions and duplicates."""

    def __init__(self, nodes: List[TreeNode], source_index: Dict[str, List[Path]]):
        self.nodes = nodes
        self.source_index = source_index

    def run_audit(self) -> None:
        path_counts = collections.defaultdict(list)
        name_counts = collections.defaultdict(list)

        for node in self.nodes:
            path_counts[node.relative_path].append(node)
            name_counts[node.name].append(node)

        # 1. Collision: Exact same relative path defined multiple times in ASCII tree
        for path, items in path_counts.items():
            if len(items) > 1:
                lines = [str(i.line_number) for i in items]
                print(
                    f"[WARN: COLLISION] Path '{path}' defined {len(items)} times "
                    f"in tree (Lines: {', '.join(lines)})"
                )

        # 2. Ambiguity: Same file or directory name appears across different folders
        for name, items in name_counts.items():
            if len(items) > 1:
                details = [
                    f"'{i.relative_path}' (Line {i.line_number}, {'dir' if i.is_directory else 'file'})"
                    for i in items
                ]
                print(
                    f"[WARN: DUPLICATE NAME IN TREE] '{name}' appears {len(items)} times:\n"
                    + "\n".join(f"    - {d}" for d in details)
                )

        # 3. Source directory collisions: Same filename present multiple times in source
        for name, paths in self.source_index.items():
            if len(paths) > 1:
                src_list = "\n".join(f"    - {p}" for p in paths)
                print(
                    f"[INFO: SOURCE CONFLICT] Multiple source files found for '{name}':\n"
                    f"{src_list}\n"
                    f"    -> Interactive resolution will prompt during placement."
                )