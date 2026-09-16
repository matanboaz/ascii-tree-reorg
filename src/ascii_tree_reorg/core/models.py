from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class TreeNode:
    """Represents a discrete node parsed from an ASCII tree."""
    name: str
    relative_path: Path
    is_directory: bool
    depth: int
    line_number: int