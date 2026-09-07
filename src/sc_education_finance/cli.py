from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .download import fetch_sources
from .pipeline import build, check, refresh


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="sc-education-finance")
    result.add_argument("command", choices=("fetch", "build", "refresh", "check"))
    result.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.root.resolve()
    if args.command == "fetch":
        fetch_sources(root, load_config(root))
    elif args.command == "build":
        build(root)
    elif args.command == "refresh":
        refresh(root)
    else:
        check(root)
    return 0
