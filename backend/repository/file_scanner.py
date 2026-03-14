from __future__ import annotations

from pathlib import Path


IGNORED_DIRECTORIES = {
    ".git",
    ".github",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "venv",
    ".venv",
    "target",
    "coverage",
    ".pytest_cache",
}


def scan_repository(repo_path: str | Path) -> list[dict]:
    """Recursively scan a repository and collect file metadata."""
    root = Path(repo_path)
    scanned_files: list[dict] = []

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if _should_ignore(file_path, root):
            continue

        scanned_files.append(_build_file_metadata(file_path, root))

    return scanned_files


def _should_ignore(file_path: Path, root: Path) -> bool:
    relative_parts = file_path.relative_to(root).parts
    return any(
        part.startswith(".") or part in IGNORED_DIRECTORIES for part in relative_parts[:-1]
    )


def _build_file_metadata(file_path: Path, root: Path) -> dict:
    line_count = _safe_line_count(file_path)
    file_size_kb = round(file_path.stat().st_size / 1024, 2)

    return {
        "file_path": str(file_path.relative_to(root)).replace("\\", "/"),
        "extension": file_path.suffix.lower(),
        "size_kb": file_size_kb,
        "lines": line_count,
        "absolute_path": str(file_path.resolve()),
    }


def _safe_line_count(file_path: Path) -> int:
    try:
        with file_path.open("r", encoding="utf-8", errors="ignore") as file_handle:
            return sum(1 for _ in file_handle)
    except OSError:
        return 0
