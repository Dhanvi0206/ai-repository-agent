from __future__ import annotations

from pathlib import Path


def generate_repository_summary(
    repository_metadata: dict,
    code_structures: list[dict],
    dependency_graph: dict[str, list[str]],
) -> dict:
    """Generate a lightweight repository-level summary for agent planning."""
    languages = repository_metadata.get("languages_used", [])
    main_modules = _derive_main_modules(code_structures, dependency_graph)
    entry_point = _detect_entry_point(code_structures)

    return {
        "project_type": _detect_project_type(repository_metadata, languages),
        "languages": languages,
        "main_modules": main_modules,
        "entry_point": entry_point,
    }


def _detect_project_type(repository_metadata: dict, languages: list[str]) -> str:
    config_files = {Path(path).name.lower() for path in repository_metadata.get("configuration_files", [])}
    if "package.json" in config_files:
        return "javascript_application"
    if "dockerfile" in config_files:
        return "containerized_application"
    if "python" in languages:
        return "python_application"
    if languages:
        return f"{languages[0]}_application"
    return "software_project"


def _derive_main_modules(code_structures: list[dict], dependency_graph: dict[str, list[str]]) -> list[str]:
    scores: dict[str, int] = {}
    for structure in code_structures:
        file_path = structure["file"]
        module_name = Path(file_path).stem
        scores[module_name] = scores.get(module_name, 0) + len(dependency_graph.get(file_path, []))
        scores[module_name] += len(structure.get("functions", []))
        scores[module_name] += len(structure.get("classes", []))

    return [name for name, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:5]]


def _detect_entry_point(code_structures: list[dict]) -> str | None:
    preferred_names = {"app.py", "main.py", "server.py", "manage.py", "index.js"}
    for structure in code_structures:
        if Path(structure["file"]).name in preferred_names:
            return structure["file"]
    return code_structures[0]["file"] if code_structures else None
