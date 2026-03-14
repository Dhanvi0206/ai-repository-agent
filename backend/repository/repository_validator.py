from __future__ import annotations

import os
import subprocess


def repository_exists(repo_url: str, timeout_seconds: int = 10) -> bool:
    """Check public repository accessibility using git instead of the GitHub API."""
    try:
        subprocess.run(
            ["git", "ls-remote", repo_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=True,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        return True
    except Exception:
        return False
