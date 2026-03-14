from __future__ import annotations


def build_repository_knowledge_graph(
    repository_metadata: dict,
    dependency_graph: dict[str, list[str]],
    code_structures: list[dict],
) -> dict:
    """Combine metadata, dependencies, and code structure into a queryable graph."""
    repository_id = f"repository:{repository_metadata['owner']}/{repository_metadata['repo_name']}"
    nodes: list[dict] = [
        {
            "id": repository_id,
            "type": "Repository",
            "attributes": repository_metadata,
        }
    ]
    edges: list[dict] = []

    structure_lookup = {structure["file"]: structure for structure in code_structures}

    for file_path, structure in structure_lookup.items():
        file_node_id = f"file:{file_path}"
        nodes.append(
            {
                "id": file_node_id,
                "type": "File",
                "attributes": {
                    "path": file_path,
                    "language": structure.get("language"),
                },
            }
        )
        edges.append({"source": repository_id, "target": file_node_id, "relationship": "contains"})

        for function_name in structure.get("functions", []):
            function_id = f"function:{file_path}:{function_name}"
            nodes.append(
                {
                    "id": function_id,
                    "type": "Function",
                    "attributes": {"name": function_name, "file": file_path},
                }
            )
            edges.append({"source": file_node_id, "target": function_id, "relationship": "defines"})

        for class_name in structure.get("classes", []):
            class_id = f"class:{file_path}:{class_name}"
            nodes.append(
                {
                    "id": class_id,
                    "type": "Class",
                    "attributes": {"name": class_name, "file": file_path},
                }
            )
            edges.append({"source": file_node_id, "target": class_id, "relationship": "defines"})

    for source_file, target_files in dependency_graph.items():
        for target_file in target_files:
            edges.append(
                {
                    "source": f"file:{source_file}",
                    "target": f"file:{target_file}",
                    "relationship": "depends_on",
                }
            )

    return {
        "nodes": nodes,
        "edges": edges,
        "query_hints": {
            "find_files_using_module": "Follow depends_on edges targeting a file node.",
            "find_functions_in_file": "Follow defines edges from a file node to Function nodes.",
        },
    }
