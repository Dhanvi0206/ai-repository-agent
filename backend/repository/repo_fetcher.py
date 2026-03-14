from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import requests
from git import InvalidGitRepositoryError, Repo

from backend.models.response_models import RepositoryMetadata
from backend.repository.chunker import chunk_code_files
from backend.repository.code_filter import filter_code_files
from backend.repository.code_structure_extractor import extract_code_structure
from backend.repository.context_builder import build_repository_contexts
from backend.repository.dependency_graph import build_dependency_graph
from backend.repository.file_scanner import scan_repository
from backend.repository.chunk_ranker import rank_chunks
from backend.repository.knowledge_graph import build_repository_knowledge_graph
from backend.repository.metadata_extractor import extract_repository_metadata
from backend.repository.repo_parser import InvalidGitHubUrlError, parse_github_url
from backend.repository.repo_summary import generate_repository_summary


MAX_REPO_SIZE_MB = int(os.getenv("MAX_REPO_SIZE_MB", "200"))
GIT_CLONE_TIMEOUT_SECONDS = int(os.getenv("GIT_CLONE_TIMEOUT_SECONDS", "120"))
WORKSPACE_ROOT = Path("workspace") / "repos"


class RepositoryFetchError(Exception):
    """Structured repository fetch failure for orchestrator-safe handling."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        repo_url: str | None = None,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.repo_url = repo_url
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "repo_url": self.repo_url,
            "details": self.details,
        }


class RepositoryFetcher:
    """Downloads and caches GitHub repositories for later file scanning."""

    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = workspace_root or WORKSPACE_ROOT
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def prepare_repository_metadata(self, repo_url: str) -> RepositoryMetadata:
        parsed = parse_github_url(repo_url)
        local_path, cache_hit = self.fetch_repository(repo_url)

        return RepositoryMetadata(
            repo_url=repo_url,
            source="github",
            clone_status="cached" if cache_hit else "cloned",
            owner=parsed["owner"],
            repository_name=parsed["repo"],
            branch=parsed["branch"],
            local_path=str(local_path),
            cache_hit=cache_hit,
        )

    def fetch_repository(self, repo_url: str) -> tuple[Path, bool]:
        parsed = parse_github_url(repo_url)
        owner = parsed["owner"]
        repo = parsed["repo"]
        branch = parsed["branch"]

        local_repo_path = self._build_local_repo_path(owner, repo, branch)
        if self._is_cached_repository(local_repo_path):
            return local_repo_path, True

        self._validate_repository_size(owner, repo, repo_url)

        clone_url = f"https://github.com/{owner}/{repo}.git"
        self._clone_repository(clone_url, local_repo_path, branch, repo_url)
        return local_repo_path, False

    def prepare_repository_for_analysis(self, repo_url: str) -> dict:
        """Run the full ingestion and intelligence pipeline for agent analysis."""
        parsed = parse_github_url(repo_url)
        local_repo_path, _ = self.fetch_repository(repo_url)
        scanned_files = scan_repository(local_repo_path)
        code_files = filter_code_files(scanned_files)
        chunks = chunk_code_files(code_files)
        metadata = extract_repository_metadata(repo_url, local_repo_path, scanned_files, code_files)
        dependency_graph = build_dependency_graph(code_files)
        code_structure = extract_code_structure(code_files)
        knowledge_graph = build_repository_knowledge_graph(
            metadata,
            dependency_graph,
            code_structure,
        )
        contexts = build_repository_contexts(
            chunks,
            code_structure,
            dependency_graph,
            metadata,
        )
        ranked_contexts = rank_chunks(contexts)
        summary = generate_repository_summary(metadata, code_structure, dependency_graph)

        return {
            "repository": f"{parsed['owner']}/{parsed['repo']}",
            "branch": parsed["branch"],
            "local_path": str(local_repo_path),
            "files_scanned": len(scanned_files),
            "code_files": len(code_files),
            "chunks_generated": len(chunks),
            "chunks": chunks,
            "metadata": metadata,
            "dependency_graph": dependency_graph,
            "code_structure": code_structure,
            "knowledge_graph": knowledge_graph,
            "contexts": contexts,
            "ranked_contexts": ranked_contexts,
            "summary": summary,
        }

    def _build_local_repo_path(self, owner: str, repo: str, branch: str) -> Path:
        repo_folder = f"{owner}_{repo}"
        if branch != "main":
            repo_folder = f"{repo_folder}_{branch}"
        sanitized_folder = repo_folder.replace("/", "_").replace("\\", "_")
        return self.workspace_root / sanitized_folder

    def _is_cached_repository(self, local_repo_path: Path) -> bool:
        if not local_repo_path.exists():
            return False

        try:
            Repo(local_repo_path)
            return True
        except InvalidGitRepositoryError:
            shutil.rmtree(local_repo_path, ignore_errors=True)
            return False

    def _validate_repository_size(self, owner: str, repo: str, repo_url: str) -> None:
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            response = requests.get(api_url, timeout=10)
        except requests.RequestException as exc:
            raise RepositoryFetchError(
                "network_error",
                "Failed to contact GitHub while validating repository size.",
                repo_url=repo_url,
                details={"error": str(exc)},
            ) from exc

        if response.status_code == 404:
            raise RepositoryFetchError(
                "repository_not_found",
                "Repository does not exist or is not publicly accessible.",
                repo_url=repo_url,
            )
        if response.status_code == 403:
            raise RepositoryFetchError(
                "access_denied",
                "GitHub denied access while validating the repository.",
                repo_url=repo_url,
            )
        if not response.ok:
            raise RepositoryFetchError(
                "github_api_error",
                "GitHub repository validation failed.",
                repo_url=repo_url,
                details={"status_code": response.status_code},
            )

        repo_size_kb = response.json().get("size", 0)
        repo_size_mb = repo_size_kb / 1024
        if repo_size_mb > MAX_REPO_SIZE_MB:
            raise RepositoryFetchError(
                "repository_too_large",
                (
                    f"Repository size {repo_size_mb:.2f} MB exceeds the configured "
                    f"limit of {MAX_REPO_SIZE_MB} MB."
                ),
                repo_url=repo_url,
                details={
                    "repo_size_mb": round(repo_size_mb, 2),
                    "max_repo_size_mb": MAX_REPO_SIZE_MB,
                },
            )

    def _clone_repository(
        self,
        clone_url: str,
        local_repo_path: Path,
        branch: str,
        repo_url: str,
    ) -> None:
        shutil.rmtree(local_repo_path, ignore_errors=True)
        local_repo_path.parent.mkdir(parents=True, exist_ok=True)

        clone_command = [
            "git",
            "clone",
            "--branch",
            branch,
            "--depth",
            "1",
            "--single-branch",
            "--filter=blob:none",
            clone_url,
            str(local_repo_path),
        ]

        try:
            subprocess.run(
                clone_command,
                check=True,
                capture_output=True,
                text=True,
                timeout=GIT_CLONE_TIMEOUT_SECONDS,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
            Repo(local_repo_path)
        except subprocess.TimeoutExpired as exc:
            shutil.rmtree(local_repo_path, ignore_errors=True)
            raise RepositoryFetchError(
                "clone_timeout",
                "Repository cloning timed out.",
                repo_url=repo_url,
                details={"timeout_seconds": GIT_CLONE_TIMEOUT_SECONDS},
            ) from exc
        except subprocess.CalledProcessError as exc:
            message = (exc.stderr or exc.stdout or str(exc)).strip()
            if "Remote branch" in message and "not found" in message:
                error_code = "branch_not_found"
                error_message = f"Branch '{branch}' does not exist in the repository."
            elif "Authentication failed" in message or "could not read Username" in message:
                error_code = "private_repository"
                error_message = "Repository appears to be private or requires authentication."
            else:
                error_code = "clone_failed"
                error_message = "Failed to clone repository from GitHub."

            shutil.rmtree(local_repo_path, ignore_errors=True)
            raise RepositoryFetchError(
                error_code,
                error_message,
                repo_url=repo_url,
                details={"error": message},
            ) from exc
        except Exception as exc:
            shutil.rmtree(local_repo_path, ignore_errors=True)
            raise RepositoryFetchError(
                "clone_timeout",
                "Repository cloning timed out or failed unexpectedly.",
                repo_url=repo_url,
                details={"error": str(exc)},
            ) from exc


def fetch_repository(repo_url: str) -> Path:
    """Convenience helper for simple script-based repository ingestion tests."""
    fetcher = RepositoryFetcher()
    local_repo_path, _ = fetcher.fetch_repository(repo_url)
    return local_repo_path


def prepare_repository_for_analysis(repo_url: str) -> dict:
    """Convenience helper for end-to-end repository ingestion."""
    fetcher = RepositoryFetcher()
    return fetcher.prepare_repository_for_analysis(repo_url)
