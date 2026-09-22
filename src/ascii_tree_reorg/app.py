import argparse
import datetime
import sys
from importlib.resources import as_file, files
from pathlib import Path
from .core.auditor import StructureAuditor
from .core.parser import AsciiTreeParser
from .engine.reorganizer import DirectoryReorganizer
from .utils.config_loader import load_configuration


def build_output_directory(output_root: Path, task_name: str, create: bool = True) -> Path:
    """Builds a dedicated task-named and timestamped directory path in data/outputs.

    With create=False (dry runs) the path is returned without touching disk.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_task = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in task_name)
    run_dir = output_root / f"run_{sanitized_task}_{timestamp}"
    if create:
        run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def main():
    repo_root = Path.cwd()
    config_resource = files("ascii_tree_reorg.resources").joinpath("default_config.json")
    with as_file(config_resource) as default_config_file:
        conf = load_configuration(default_config_file)

    parser = argparse.ArgumentParser(
        description="Reorganize loose files into a structured hierarchy defined by an ASCII tree."
    )
    parser.add_argument(
        "--tree-file", "-t",
        type=Path,
        default=repo_root / conf["default_input_tree"],
        help="Path to ASCII directory tree file."
    )
    parser.add_argument(
        "--source-dir", "-s",
        type=Path,
        default=repo_root / conf["default_input_source"],
        help="Directory containing unorganized files."
    )
    parser.add_argument(
        "--output-root", "-o",
        type=Path,
        default=repo_root / conf["default_output_root"],
        help="Root directory where timestamped task outputs are stored."
    )
    parser.add_argument(
        "--task-name", "-n",
        type=str,
        default="reorg_job",
        help="Logical label/name for the task run folder."
    )
    parser.add_argument(
        "--indent-width", "-w",
        type=int,
        default=conf["indent_width"],
        help="Indentation character pitch (default: 4)."
    )
    parser.add_argument(
        "--move",
        action="store_true",
        default=conf["move_files"],
        help="Move files instead of copying them."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Replace files that already exist in the target. Off by default."
    )
    parser.add_argument(
        "--clean-relocated",
        action="store_true",
        default=False,
        help="Delete undeclared or stale items from the target before placement. Off by default."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print the planned actions without modifying the filesystem."
    )

    args = parser.parse_args()

    if not args.tree_file.is_file():
        sys.exit(f"Error: ASCII tree file '{args.tree_file}' does not exist.")
    if not args.source_dir.is_dir():
        sys.exit(f"Error: Source directory '{args.source_dir}' does not exist.")

    parser_obj = AsciiTreeParser(args.tree_file, args.indent_width)
    try:
        nodes = parser_obj.parse()
    except ValueError as e:
        sys.exit(f"Indentation/Parsing Error: {e}")

    if not nodes:
        sys.exit("[WARN] No valid nodes found in tree file. Exiting.")

    target_destination = build_output_directory(args.output_root, args.task_name, create=not args.dry_run)
    if args.dry_run:
        print(f"[INIT] Dry run: target directory would be {target_destination}")
    else:
        print(f"[INIT] Target directory created: {target_destination}")

    reorganizer = DirectoryReorganizer(
        source_dir=args.source_dir,
        target_dir=target_destination,
        move_files=args.move,
        overwrite=args.overwrite,
        clean_relocated=args.clean_relocated,
        dry_run=args.dry_run,
    )

    print("\n--- Running Structure & Name Audit ---")
    auditor = StructureAuditor(nodes, reorganizer.source_index)
    auditor.run_audit()
    print("--------------------------------------\n")

    reorganizer.execute(nodes)
    print(f"\n[DONE] Execution completed successfully.")
    print(f"[RESULT] Reorganized directory structure saved at:\n       {target_destination}")


if __name__ == "__main__":
    main()