from __future__ import annotations

import re
from pathlib import Path


IMPORT_PATTERNS = [
    re.compile(r"^\s*import\s+([a-zA-Z0-9_\. ,]+)", re.MULTILINE),
    re.compile(r"^\s*from\s+([a-zA-Z0-9_\.]+)\s+import\s+", re.MULTILINE),
    re.compile(r'require\(["\']([^"\']+)["\']\)'),
    re.compile(r'import\s+.*?from\s+["\']([^"\']+)["\']'),
    re.compile(r'#include\s+[<"]([^">]+)[">]'),
]


def build_dependency_graph(code_files: list[dict]) -> dict[str, list[str]]:
    """Build a lightweight dependency graph from import-style statements."""
    module_lookup = _build_module_lookup(code_files)
    dependency_graph: dict[str, list[str]] = {}

    for file_info in code_files:
        file_path = file_info["file_path"]
        content = _read_file_text(file_info.get("absolute_path"))
        imports = _extract_imports(content)

        resolved_dependencies = sorted(
            {
                _resolve_dependency(import_name, module_lookup)
                for import_name in imports
                if _resolve_dependency(import_name, module_lookup) is not None
            }
        )
        dependency_graph[file_path] = resolved_dependencies

    return dependency_graph


def _build_module_lookup(code_files: list[dict]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for file_info in code_files:
        file_path = file_info["file_path"]
        file_without_extension = Path(file_path).with_suffix("")
        dotted_module = ".".join(file_without_extension.parts)
        slash_module = str(file_without_extension).replace("\\", "/")
        lookup[dotted_module] = file_path
        lookup[slash_module] = file_path
        lookup[file_without_extension.name] = file_path
    return lookup


def _extract_imports(content: str) -> list[str]:
    imports: set[str] = set()
    for pattern in IMPORT_PATTERNS:
        for match in pattern.findall(content):
            if isinstance(match, tuple):
                imports.update(part.strip() for part in match if part.strip())
            else:
                imports.update(_split_import_match(match))
    return sorted(imports)


def _split_import_match(match: str) -> list[str]:
    if "," in match:
        return [part.strip().split(" as ")[0] for part in match.split(",") if part.strip()]
    return [match.strip().split(" as ")[0]]


def _resolve_dependency(import_name: str, module_lookup: dict[str, str]) -> str | None:
    normalized = import_name.strip().lstrip(".")
    if not normalized:
        return None

    candidates = [
        normalized,
        normalized.replace("/", "."),
        normalized.replace(".", "/"),
        normalized.split(".")[0],
    ]

    for candidate in candidates:
        if candidate in module_lookup:
            return module_lookup[candidate]
    return None


def _read_file_text(absolute_path: str | None) -> str:
    if not absolute_path:
        return ""
    try:
        return Path(absolute_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
