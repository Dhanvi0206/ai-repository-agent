from __future__ import annotations

import ast
import re
from pathlib import Path


def extract_code_structure(code_files: list[dict]) -> list[dict]:
    """Extract functions, classes, methods, and imports from code files."""
    structures: list[dict] = []

    for file_info in code_files:
        extension = file_info.get("extension", "")
        absolute_path = file_info.get("absolute_path")
        content = _read_file_text(absolute_path)

        structure = {
            "file": file_info["file_path"],
            "language": file_info.get("language"),
            "functions": [],
            "classes": [],
            "methods": [],
            "imports": [],
        }

        if extension == ".py":
            structure.update(_extract_python_structure(content))
        else:
            structure.update(_extract_generic_structure(content))

        structures.append(structure)

    return structures


def _extract_python_structure(content: str) -> dict:
    functions: list[str] = []
    classes: list[str] = []
    methods: list[str] = []
    imports: list[str] = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return {"functions": functions, "classes": classes, "methods": methods, "imports": imports}

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(f"{node.name}.{child.name}")
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    return {
        "functions": sorted(functions),
        "classes": sorted(classes),
        "methods": sorted(methods),
        "imports": sorted(set(imports)),
    }


def _extract_generic_structure(content: str) -> dict:
    function_matches = re.findall(
        r"(?:function|def|func|fn)\s+([A-Za-z_][A-Za-z0-9_]*)|\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{",
        content,
    )
    class_matches = re.findall(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)", content)
    import_matches = re.findall(
        r'import\s+.*?from\s+["\']([^"\']+)["\']|require\(["\']([^"\']+)["\']\)|#include\s+[<"]([^">]+)[">]',
        content,
    )

    functions = sorted({match[0] or match[1] for match in function_matches if any(match)})
    imports = sorted({value for match in import_matches for value in match if value})

    return {
        "functions": functions,
        "classes": sorted(set(class_matches)),
        "methods": [],
        "imports": imports,
    }


def _read_file_text(absolute_path: str | None) -> str:
    if not absolute_path:
        return ""
    try:
        return Path(absolute_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
