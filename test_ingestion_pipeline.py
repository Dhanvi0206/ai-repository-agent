from backend.repository.repo_fetcher import (
    RepositoryFetchError,
    prepare_repository_for_analysis,
)


def main() -> None:
    repo_url = "https://github.com/pallets/flask"

    try:
        result = prepare_repository_for_analysis(repo_url)

        print("Repository:", result["repository"])
        print("Branch:", result["branch"])
        print("Repository path:", result["local_path"])
        print("Files scanned:", result["files_scanned"])
        print("Code files:", result["code_files"])
        print("Total chunks:", result["chunks_generated"])
        print("Languages:", result["metadata"]["languages_used"])
        print("Top ranked file:", result["ranked_contexts"][0]["file"] if result["ranked_contexts"] else "n/a")
        print("Entry point:", result["summary"]["entry_point"])
    except RepositoryFetchError as exc:
        print("Repository ingestion failed:")
        print(exc.to_dict())


if __name__ == "__main__":
    main()
