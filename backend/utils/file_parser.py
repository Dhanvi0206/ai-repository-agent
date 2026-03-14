from pathlib import Path


class FileParser:
    """Provides file parsing helpers for future repository analysis."""

    def read_text_file(self, file_path: str) -> str:
        return Path(file_path).read_text(encoding="utf-8")
