from __future__ import annotations


ALLOWED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
}

IGNORED_PATH_KEYWORDS = {
    "/node_modules/",
    "/dist/",
    "/build/",
    "/venv/",
    "/.venv/",
}


def filter_code_files(file_list: list[dict]) -> list[dict]:
    """Keep only relevant code files and attach language metadata."""
    filtered_files: list[dict] = []

    for file_info in file_list:
        normalized_path = f"/{file_info['file_path'].replace(chr(92), '/')}/"
        extension = file_info.get("extension", "").lower()

        if extension not in ALLOWED_EXTENSIONS:
            continue
        if any(keyword in normalized_path for keyword in IGNORED_PATH_KEYWORDS):
            continue

        enriched_file = dict(file_info)
        enriched_file["language"] = ALLOWED_EXTENSIONS[extension]
        filtered_files.append(enriched_file)

    return filtered_files
