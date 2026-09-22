import math
import re
from pathlib import Path
from typing import List, Tuple
from .models import TreeNode


class IndentationDetector:
    """Calculates and validates ASCII tree indentation steps using GCD."""

    @staticmethod
    def detect(lines: List[str], configured_width: int) -> int:
        prefix_lens = []
        for line in lines:
            line_content = line.split("#")[0]
            cleaned = re.sub(r"^[│\s├└─\-+|]+", "", line_content).strip()
            if not cleaned:
                continue

            match = re.match(r"^([│\s├└─\-+|]*)", line_content)
            if match:
                p_len = len(match.group(1))
                if p_len > 0:
                    prefix_lens.append(p_len)

        if not prefix_lens:
            return max(1, configured_width)

        observed_gcd = prefix_lens[0]
        for p in prefix_lens[1:]:
            observed_gcd = math.gcd(observed_gcd, p)

        if observed_gcd < 2:
            mismatches = [p for p in prefix_lens if p % configured_width != 0]
            if mismatches:
                raise ValueError(
                    f"Malformed indentation detected: {sorted(set(prefix_lens))} chars. "
                    f"Inconsistent with configured width ({configured_width})."
                )
            return max(1, configured_width)

        if observed_gcd != configured_width:
            print(
                f"[WARN] Indentation mismatch: Configured width was {configured_width}, "
                f"but detected pitch is {observed_gcd} chars. Auto-adapting to {observed_gcd}."
            )
            return observed_gcd

        return configured_width



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

class AsciiTreeParser:
    """Parses raw ASCII tree text into structured TreeNode objects."""

    def __init__(self, file_path: Path, fallback_width: int = 4):
        self.file_path = file_path
        self.fallback_width = fallback_width

import math
import re
from pathlib import Path
from typing import List, Tuple
from .models import TreeNode


class IndentationDetector:
    """Calculates and validates ASCII tree indentation steps using GCD."""

    @staticmethod
    def detect(lines: List[str], configured_width: int) -> int:
        prefix_lens = []
        for line in lines:
            line_content = line.split("#")[0]
            cleaned = re.sub(r"^[│\s├└─\-+|]+", "", line_content).strip()
            if not cleaned:
                continue

            match = re.match(r"^([│\s├└─\-+|]*)", line_content)
            if match:
                p_len = len(match.group(1))
                if p_len > 0:
                    prefix_lens.append(p_len)

        if not prefix_lens:
            return max(1, configured_width)

        observed_gcd = prefix_lens[0]
        for p in prefix_lens[1:]:
            observed_gcd = math.gcd(observed_gcd, p)

        if observed_gcd < 2:
            mismatches = [p for p in prefix_lens if p % configured_width != 0]
            if mismatches:
                raise ValueError(
                    f"Malformed indentation detected: {sorted(set(prefix_lens))} chars. "
                    f"Inconsistent with configured width ({configured_width})."
                )
            return max(1, configured_width)

        if observed_gcd != configured_width:
            print(
                f"[WARN] Indentation mismatch: Configured width was {configured_width}, "
                f"but detected pitch is {observed_gcd} chars. Auto-adapting to {observed_gcd}."
            )
            return observed_gcd

        return configured_width


class AsciiTreeParser:
    """Parses raw ASCII tree text into structured TreeNode objects."""

    def __init__(self, file_path: Path, fallback_width: int = 4):
        self.file_path = file_path
        self.fallback_width = fallback_width

    def parse(self, target_root_name: str = "") -> List[TreeNode]:
        with open(self.file_path, "r", encoding="utf-8") as f:
            raw_lines = [l.rstrip("\r\n") for l in f.readlines() if l.strip()]

        step_width = IndentationDetector.detect(raw_lines, self.fallback_width)

        # Detect if the first line is an enclosing root matching target_root_name
        first_clean_name = ""
        first_line_is_dir = False
        for line in raw_lines:
            c = re.sub(r"^[│\s├└─\-+|]+", "", line.split("#")[0]).strip()
            if c and c not in (".", "./"):
                first_clean_name = c.rstrip("/")
                first_line_is_dir = c.endswith("/") or True
                break

        strip_outer_root = False
        if (
            target_root_name
            and first_clean_name
            and first_clean_name.lower() == target_root_name.lower()
        ):
            strip_outer_root = True

        stack: List[Tuple[int, Path]] = []
        nodes: List[TreeNode] = []

        for line_no, line in enumerate(raw_lines, start=1):
            line_no_comment = line.split("#")[0]
            cleaned = re.sub(r"^[│\s├└─\-+|]+", "", line_no_comment).strip()
            if not cleaned or cleaned in (".", "./"):
                continue

            prefix_match = re.match(r"^([│\s├└─\-+|]*)", line_no_comment)
            prefix_len = len(prefix_match.group(1)) if prefix_match else 0
            raw_depth = prefix_len // step_width

            is_directory = cleaned.endswith("/") or (line_no == 1 and raw_depth == 0)
            name = cleaned.rstrip("/")

            if not name:
                continue

            _validate_entry_name(name, line_no)

            # If stripping outer root, skip the first entry and shift all child depths down by 1
            if strip_outer_root:
                if line_no == 1 and raw_depth == 0:
                    continue
                depth = max(0, raw_depth - 1)
            else:
                depth = raw_depth

            while stack and stack[-1][0] >= depth:
                stack.pop()

            parent_path = stack[-1][1] if stack else Path("")
            rel_path = parent_path / name if str(parent_path) else Path(name)

            node = TreeNode(
                name=name,
                relative_path=rel_path,
                is_directory=is_directory,
                depth=depth,
                line_number=line_no,
            )
            nodes.append(node)

            if is_directory:
                stack.append((depth, rel_path))

        return nodes