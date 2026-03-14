from __future__ import annotations

from pathlib import Path


DEFAULT_CHUNK_SIZE = 200
MAX_CHUNK_CHARACTERS = 12000


def chunk_code_files(
    filtered_files: list[dict],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> list[dict]:
    """Split code files into line-based chunks for downstream LLM analysis."""
    chunks: list[dict] = []

    for file_info in filtered_files:
        absolute_path = file_info.get("absolute_path")
        if not absolute_path:
            continue

        try:
            lines = Path(absolute_path).read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue

        if not lines:
            continue

        chunk_id = 1
        start_index = 0
        while start_index < len(lines):
            end_index = min(start_index + chunk_size, len(lines))
            chunk_lines = lines[start_index:end_index]

            # Keep chunk payloads within a conservative character budget.
            while len("\n".join(chunk_lines)) > MAX_CHUNK_CHARACTERS and len(chunk_lines) > 1:
                chunk_lines = chunk_lines[:-1]
                end_index -= 1

            content = "\n".join(chunk_lines)
            if not content.strip():
                start_index = end_index
                continue

            chunks.append(
                {
                    "file_path": file_info["file_path"],
                    "language": file_info.get("language"),
                    "chunk_id": chunk_id,
                    "start_line": start_index + 1,
                    "end_line": end_index,
                    "content": content,
                    "metadata": {
                        "extension": file_info.get("extension"),
                        "size_kb": file_info.get("size_kb"),
                        "lines": file_info.get("lines"),
                    },
                }
            )

            chunk_id += 1
            start_index = end_index

    return chunks
