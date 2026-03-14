from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


class InvalidGitHubUrlError(ValueError):
    """Raised when the provided repository URL is not a valid GitHub URL."""


@dataclass(frozen=True)
class ParsedGitHubUrl:
    owner: str
    repo: str
    branch: str = "main"

    def to_dict(self) -> dict[str, str]:
        return {"owner": self.owner, "repo": self.repo, "branch": self.branch}


def parse_github_url(repo_url: str) -> dict[str, str]:
    """Parse GitHub URLs and extract repository owner, name, and branch.

    Supported formats:
    - https://github.com/user/repository
    - https://github.com/user/repository.git
    - https://github.com/user/repository/tree/main
    """
    parsed = urlparse(repo_url.strip())

    if parsed.scheme not in {"http", "https"}:
        raise InvalidGitHubUrlError(
            "Invalid repository URL. GitHub URL must start with http:// or https://."
        )

    if parsed.netloc.lower() != "github.com":
        raise InvalidGitHubUrlError(
            "Invalid repository URL. Only github.com repositories are supported."
        )

    path_parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(path_parts) < 2:
        raise InvalidGitHubUrlError(
            "Invalid GitHub repository URL. Expected format: "
            "https://github.com/<owner>/<repository>"
        )

    owner, repo = path_parts[0], path_parts[1]
    repo = repo.removesuffix(".git")
    if not owner or not repo:
        raise InvalidGitHubUrlError(
            "Invalid GitHub repository URL. Owner and repository name are required."
        )

    branch = "main"
    if len(path_parts) >= 4 and path_parts[2] == "tree":
        branch = path_parts[3]

    return ParsedGitHubUrl(owner=owner, repo=repo, branch=branch).to_dict()
