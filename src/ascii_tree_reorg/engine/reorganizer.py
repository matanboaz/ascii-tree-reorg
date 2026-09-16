import collections
import os
import shutil
from pathlib import Path
from typing import Dict, List, Set
from ..core.models import TreeNode
from ..core.resolver import ConflictResolver


class DirectoryReorganizer:
    """Handles directory instantiation, file transfer, overwrite safety, relocation cleanup, and orphan pruning."""

    def __init__(
        self,
        source_dir: Path,
        target_dir: Path,
        move_files: bool = False,
        overwrite: bool = True,
        clean_relocated: bool = True,
    ):
        self.source_dir = source_dir.resolve()
        self.target_dir = target_dir.resolve()
        self.move_files = move_files
        self.overwrite = overwrite
        self.clean_relocated = clean_relocated
        self.source_index: Dict[str, List[Path]] = collections.defaultdict(list)
        self._index_source()

    def _index_source(self) -> None:
        if not self.source_dir.exists():
            return
        for path in self.source_dir.rglob("*"):
            if path.is_file() and not path.is_symlink():
                self.source_index[path.name].append(path)

    def _purge_parent_orphans(self, desired_nodes: List[TreeNode]) -> None:
            """
            Purges any folders or files sitting directly inside target_dir that
            do not belong to the root level of the ASCII tree.
            """
            # Determine the root names allowed directly inside target_dir
            # If tree has a single top wrapper like 'SMART_AI_NLP', allowed_roots = {'SMART_AI_NLP'}
            allowed_roots: Set[str] = set()
            for n in desired_nodes:
                if n.relative_path.parts:
                    allowed_roots.add(n.relative_path.parts[0])

            if not self.target_dir.exists():
                return

            for item in list(self.target_dir.iterdir()):
                # Keep git metadata or required project root files
                if item.name in (".git", ".gitkeep"):
                    continue

                # If an item sitting in outputs is NOT one of the declared root tree items
                if item.name not in allowed_roots:
                    print(f"[ORPHAN PURGE] Deleting obsolete item from {self.target_dir.name}: {item.name}")
                    try:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                    except OSError as e:
                        print(f"[WARN] Failed to purge '{item.name}': {e}")

    def _cleanup_old_positions(self, desired_nodes: List[TreeNode]) -> None:
        """Removes duplicate or stale copies of files sitting in obsolete locations inside target_dir."""
        expected_paths_by_name: Dict[str, Set[Path]] = collections.defaultdict(set)
        for n in desired_nodes:
            if not n.is_directory:
                expected_paths_by_name[n.name].add(n.relative_path)

        if not self.target_dir.exists():
            return

        for existing_file in list(self.target_dir.rglob("*")):
            if not existing_file.is_file():
                continue

            fname = existing_file.name
            try:
                rel_pos = existing_file.relative_to(self.target_dir)
            except ValueError:
                continue

            if fname in expected_paths_by_name:
                if rel_pos not in expected_paths_by_name[fname]:
                    print(f"[CLEANUP] Removing obsolete copy: {rel_pos}")
                    try:
                        existing_file.unlink()
                    except OSError as e:
                        print(f"[WARN] Failed to delete obsolete copy '{existing_file}': {e}")

    def _place_single_node(self, node: TreeNode) -> None:
        action = "Moving" if self.move_files else "Copying"
        dest_path = self.target_dir / node.relative_path

        if node.is_directory:
            dest_path.mkdir(parents=True, exist_ok=True)
            return

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        filename = node.name

        candidates = self.source_index.get(filename, [])
        if not candidates:
            if not dest_path.exists():
                print(f"[MISSING] File '{node.name}' for '{node.relative_path}' not found in source.")
            else:
                print(f"[KEEP] Existing file already in place: {node.relative_path}")
            return

        if len(candidates) > 1:
            selected_source = ConflictResolver.prompt_selection(node, candidates, self.source_dir)
            if selected_source is None:
                return
        else:
            selected_source = candidates[0]

        try:
            if dest_path.exists() and selected_source.resolve().samefile(dest_path.resolve()):
                print(f"[ALREADY IN PLACE] {node.relative_path}")
                return
        except OSError:
            pass

        if dest_path.exists():
            if not self.overwrite:
                print(f"[SKIP] Target already exists: {node.relative_path}")
                return
            else:
                print(f"[OVERWRITE] {selected_source.name} -> {node.relative_path}")
        else:
            print(f"[{action.upper()}] {selected_source.name} -> {node.relative_path}")

        try:
            if self.move_files:
                shutil.move(str(selected_source), str(dest_path))
                candidates.remove(selected_source)
                if not candidates:
                    del self.source_index[filename]
            else:
                shutil.copy2(str(selected_source), str(dest_path))
        except OSError as err:
            print(f"[ERROR] Failed to write '{dest_path}': {err}")

    def execute(self, nodes: List[TreeNode]) -> None:
        if self.clean_relocated:
            self._purge_parent_orphans(nodes)
            self._cleanup_old_positions(nodes)
        for node in nodes:
            self._place_single_node(node)