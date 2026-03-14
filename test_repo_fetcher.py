from backend.repository.repo_fetcher import RepositoryFetchError, fetch_repository


def main() -> None:
    repo = "https://github.com/pallets/flask"

    try:
        path = fetch_repository(repo)
        print("Repository downloaded at:", path)
    except RepositoryFetchError as exc:
        print("Repository fetch failed:")
        print(exc.to_dict())


if __name__ == "__main__":
    main()
