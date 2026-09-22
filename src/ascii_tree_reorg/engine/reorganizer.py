import collections
import shutil
from pathlib import Path
from typing import Dict, List, Set
from ..core.models import TreeNode
from ..core.resolver import ConflictResolver


class DirectoryReorganizer:
    """Handles directory instantiation, file transfer, overwrite safety, relocation cleanup, and orphan pruning.

    Safe-by-default contract:
    - ``overwrite`` and ``clean_relocated`` are opt-in. A default run only adds
      missing files and directories; it never deletes or replaces anything in
      the target.
    - Every destination is validated to stay inside ``target_dir`` before any
      write, so traversal segments, absolute paths, or hostile symlinks in the
      target cannot redirect writes outside it.
    - ``dry_run`` computes and prints the full plan without touching the
      filesystem.
    """

    def __init__(
        self,
        source_dir: Path,
        target_dir: Path,
        move_files: bool = False,
        overwrite: bool = False,
        clean_relocated: bool = False,
        dry_run: bool = False,
    ):
        self.source_dir = source_dir.resolve()
        self.target_dir = target_dir.resolve()
        self.move_files = move_files
        self.overwrite = overwrite
        self.clean_relocated = clean_relocated
        self.dry_run = dry_run
        self.source_index: Dict[str, List[Path]] = collections.defaultdict(list)
        self._index_source()

    def _index_source(self) -> None:
        if not self.source_dir.exists():
            return
        for path in self.source_dir.rglob("*"):
            if path.is_file() and not path.is_symlink():
                self.source_index[path.name].append(path)

    def _resolve_destination(self, node: TreeNode) -> Path:
        """Returns the destination path for a node, guaranteeing containment.

        Raises ValueError if the entry is absolute, contains '..', or resolves
        (through symlinks already present in the target) outside target_dir.
        """
        rel = node.relative_path
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(
                f"Unsafe tree entry rejected: '{rel}' (line {node.line_number}). "
                "Entries must stay inside the target directory."
            )
        dest = self.target_dir / rel
        try:
            resolved = dest.resolve()
            resolved.relative_to(self.target_dir)
        except (OSError, ValueError):
            raise ValueError(
                f"Unsafe destination rejected: '{rel}' (line {node.line_number}) "
                f"resolves outside target directory '{self.target_dir}'."
            )
        return dest

    def _purge_parent_orphans(self, desired_nodes: List[TreeNode]) -> None:
        """
        Purges any folders or files sitting directly inside target_dir that
        do not belong to the root level of the ASCII tree.
        Only runs when clean_relocated is explicitly enabled.
        """
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

            if item.name not in allowed_roots:
                if self.dry_run:
                    print(f"[DRY RUN] Would delete undeclared item from {self.target_dir.name}: {item.name}")
                    continue
                print(f"[ORPHAN PURGE] Deleting undeclared item from {self.target_dir.name}: {item.name}")
                try:
                    if item.is_dir() and not item.is_symlink():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except OSError as e:
                    print(f"[WARN] Failed to purge '{item.name}': {e}")

    def _cleanup_old_positions(self, desired_nodes: List[TreeNode]) -> None:
        """Removes duplicate or stale copies of files sitting in obsolete locations inside target_dir.

        Only runs when clean_relocated is explicitly enabled.
        """
        expected_paths_by_name: Dict[str, Set[Path]] = collections.defaultdict(set)
        for n in desired_nodes:
            if not n.is_directory:
                expected_paths_by_name[n.name].add(n.relative_path)

        if not self.target_dir.exists():
            return

        for existing_file in list(self.target_dir.rglob("*")):
            if not existing_file.is_file() or existing_file.is_symlink():
                continue

            fname = existing_file.name
            try:
                rel_pos = existing_file.relative_to(self.target_dir)
            except ValueError:
                continue

            if fname in expected_paths_by_name:
                if rel_pos not in expected_paths_by_name[fname]:
                    if self.dry_run:
                        print(f"[DRY RUN] Would remove stale copy: {rel_pos}")
                        continue
                    print(f"[CLEANUP] Removing stale copy: {rel_pos}")
                    try:
                        existing_file.unlink()
                    except OSError as e:
                        print(f"[WARN] Failed to delete stale copy '{existing_file}': {e}")

    def _place_single_node(self, node: TreeNode) -> None:
        action = "Moving" if self.move_files else "Copying"
        verb = "move" if self.move_files else "copy"
        dest_path = self._resolve_destination(node)

        if node.is_directory:
            if self.dry_run:
                if not dest_path.exists():
                    print(f"[DRY RUN] Would create directory: {node.relative_path}")
                return
            dest_path.mkdir(parents=True, exist_ok=True)
            return

        filename = node.name
        candidates = self.source_index.get(filename, [])
        if not candidates:
            if not dest_path.exists():
                print(f"[MISSING] File '{node.name}' for '{node.relative_path}' not found in source.")
            else:
                print(f"[KEEP] Existing file already in place: {node.relative_path}")
            return

        if len(candidates) > 1:
            if self.dry_run:
                print(
                    f"[DRY RUN] Would prompt to resolve {len(candidates)} conflicting "
                    f"sources for '{node.relative_path}'."
                )
                return
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
                print(f"[SKIP] Target already exists (use overwrite to replace): {node.relative_path}")
                return
            elif self.dry_run:
                print(f"[DRY RUN] Would overwrite: {selected_source.name} -> {node.relative_path}")
                return
            else:
                print(f"[OVERWRITE] {selected_source.name} -> {node.relative_path}")
        elif self.dry_run:
            print(f"[DRY RUN] Would {verb}: {selected_source.name} -> {node.relative_path}")
            return
        else:
            print(f"[{action.upper()}] {selected_source.name} -> {node.relative_path}")

        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
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
        # Validate every destination before any mutation, so a single hostile
        # entry aborts the run instead of failing halfway through.
        for node in nodes:
            self._resolve_destination(node)

        if self.dry_run:
            print("[DRY RUN] Planning only; no filesystem changes will be made.")
        if self.clean_relocated:
            self._purge_parent_orphans(nodes)
            self._cleanup_old_positions(nodes)
        for node in nodes:
            self._place_single_node(node)
        if self.dry_run:
            print("[DRY RUN] Plan complete; no filesystem changes were made.")
