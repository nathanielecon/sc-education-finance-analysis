"""Apply deterministic structural prose checks to the public narrative."""

from __future__ import annotations

import re
import sys
from pathlib import Path

MAX_WORDS = 25
FORBIDDEN = {
    "agentic ai",
    "case study",
    "recruiter-facing",
    "recruiter facing",
    "resume",
    "résumé",
    "ats",
    "cutting-edge",
    "seamless",
}
SMALL_TITLE_WORDS = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "with"}


def _visible_text(line: str) -> str:
    text = re.sub(r"!\[([^]]*)\]\([^)]+\)", r"\1", line)
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    return re.sub(r"`[^`]+`", "term", text)


def _title_case_errors(line: str) -> list[str]:
    title = line.lstrip("#").strip()
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]*", title)
    errors: list[str] = []
    for index, word in enumerate(words):
        if word.upper() in {"NAEP", "RPP", "BLS", "ETL", "FY"}:
            continue
        if index and word.lower() in SMALL_TITLE_WORDS:
            continue
        if not word[0].isupper():
            errors.append(f"heading is not Title Case: {title}")
            break
    return errors


def lint(path: Path) -> list[str]:
    errors: list[str] = []
    in_code = False
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if raw_line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if raw_line.startswith("#"):
            errors.extend(
                f"{path}:{line_number}: {message}" for message in _title_case_errors(raw_line)
            )
        visible = _visible_text(raw_line)
        lowered = visible.lower()
        for phrase in FORBIDDEN:
            if re.search(rf"\b{re.escape(phrase)}\b", lowered):
                errors.append(f"{path}:{line_number}: forbidden promotional phrase: {phrase}")
        if ";" in visible:
            errors.append(f"{path}:{line_number}: semicolons are not permitted")
        if raw_line.startswith("|") or raw_line.startswith("!["):
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", visible):
            words = re.findall(r"\b[\w$%–-]+\b", sentence)
            if len(words) > MAX_WORDS:
                errors.append(
                    f"{path}:{line_number}: sentence has {len(words)} words; limit is {MAX_WORDS}"
                )
    return errors


def main(argv: list[str]) -> int:
    paths = [Path(value) for value in argv]
    if not paths:
        raise SystemExit("Provide one or more Markdown files.")
    errors = [error for path in paths for error in lint(path)]
    if errors:
        print("\n".join(errors))
        return 1
    print(f"STE structural checks passed for {len(paths)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
