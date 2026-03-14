from __future__ import annotations


def build_repository_contexts(
    chunks: list[dict],
    code_structures: list[dict],
    dependency_graph: dict[str, list[str]],
    repository_metadata: dict,
) -> list[dict]:
    """Attach structural and dependency context to each code chunk."""
    structure_lookup = {structure["file"]: structure for structure in code_structures}
    contexts: list[dict] = []

    for chunk in chunks:
        file_path = chunk["file_path"]
        structure = structure_lookup.get(file_path, {})

        contexts.append(
            {
                "file": file_path,
                "language": chunk.get("language"),
                "imports": dependency_graph.get(file_path, []),
                "functions": structure.get("functions", []),
                "classes": structure.get("classes", []),
                "methods": structure.get("methods", []),
                "chunk": chunk["content"],
                "chunk_id": chunk["chunk_id"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "repository": {
                    "name": repository_metadata["repo_name"],
                    "owner": repository_metadata["owner"],
                    "default_branch": repository_metadata["default_branch"],
                },
            }
        )

    return contexts
