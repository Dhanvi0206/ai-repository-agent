from __future__ import annotations

from pathlib import Path

from backend.repository.repo_parser import parse_github_url


README_FILENAMES = {"readme", "readme.md", "readme.rst", "readme.txt"}
LICENSE_FILENAMES = {"license", "license.md", "license.txt", "copying"}
CONFIG_FILENAMES = {
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "dockerfile",
    "docker-compose.yml",
    ".env.example",
    "setup.py",
    "tox.ini",
    "Makefile",
}


def extract_repository_metadata(
    repo_url: str,
    repo_path: str | Path,
    scanned_files: list[dict],
    code_files: list[dict],
) -> dict:
    """Extract high-level repository metadata for agent context."""
    parsed = parse_github_url(repo_url)
    root = Path(repo_path)
    all_files = scanned_files or []
    code_file_list = code_files or []

    languages = sorted({file_info.get("language") for file_info in code_file_list if file_info.get("language")})
    repository_size_kb = round(sum(file_info.get("size_kb", 0) for file_info in all_files), 2)
    normalized_names = {Path(file_info["file_path"]).name.lower() for file_info in all_files}

    return {
        "repo_name": parsed["repo"],
        "owner": parsed["owner"],
        "default_branch": parsed["branch"],
        "total_files": len(all_files),
        "total_code_files": len(code_file_list),
        "languages_used": languages,
        "repository_size_kb": repository_size_kb,
        "repository_size_mb": round(repository_size_kb / 1024, 2),
        "has_readme": any(name in README_FILENAMES for name in normalized_names),
        "has_license": any(name in LICENSE_FILENAMES for name in normalized_names),
        "configuration_files": sorted(
            file_info["file_path"]
            for file_info in all_files
            if Path(file_info["file_path"]).name in CONFIG_FILENAMES
            or Path(file_info["file_path"]).name.lower() in {name.lower() for name in CONFIG_FILENAMES}
        ),
        "workspace_path": str(root),
    }
