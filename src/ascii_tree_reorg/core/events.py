"""Structured runtime events shared by command-line and graphical clients."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class OperationEvent:
    """One machine-readable update emitted during an operation."""

    kind: str
    message: str
    level: str = "info"
    current: int = 0
    total: int = 0
    data: Dict[str, Any] = field(default_factory=dict)
