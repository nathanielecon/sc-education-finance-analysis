from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


def load_config(root: Path) -> dict[str, Any]:
    """Load the repository configuration."""
    with (root / "config.toml").open("rb") as handle:
        return tomllib.load(handle)


def resolve_path(root: Path, value: str) -> Path:
    """Resolve a configured path below the repository root."""
    result = (root / value).resolve()
    if root.resolve() not in result.parents and result != root.resolve():
        raise ValueError(f"Configured path escapes the repository: {value}")
    return result
