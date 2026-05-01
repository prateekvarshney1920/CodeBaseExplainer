"""
GitHub Service — Fetch repository contents via the GitHub REST API.
"""

import os
import re
import base64
import logging
from typing import Dict, Optional

import requests

logger = logging.getLogger(__name__)

# Extensions we care about
ALLOWED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".go", ".cpp", ".c", ".cs",
    ".rb", ".rs", ".h", ".hpp",
}

# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", "dist", "build",
    "__pycache__", ".next", ".venv", "venv",
    "env", ".tox", ".mypy_cache", ".pytest_cache",
    "vendor", "target", "bin", "obj",
}

# Max file size to fetch (100 KB) — skip huge generated files
MAX_FILE_SIZE = 100_000


def _parse_github_url(url: str) -> tuple:
    """
    Parse owner and repo from a GitHub URL.
    Supports formats:
      - https://github.com/owner/repo
      - https://github.com/owner/repo.git
      - https://github.com/owner/repo/tree/branch
    """
    url = url.strip().rstrip("/")
    # Remove .git suffix
    if url.endswith(".git"):
        url = url[:-4]

    pattern = r"github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, url)
    if not match:
        raise ValueError(f"Invalid GitHub URL: {url}")

    owner = match.group(1)
    repo = match.group(2)

    # Try to extract branch from /tree/branch
    branch = "main"
    tree_pattern = r"github\.com/[^/]+/[^/]+/tree/([^/]+)"
    tree_match = re.search(tree_pattern, url)
    if tree_match:
        branch = tree_match.group(1)

    return owner, repo, branch


def _get_headers() -> dict:
    """Build request headers, optionally with GitHub token."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token and token != "your_github_token_here_optional":
        headers["Authorization"] = f"token {token}"
    return headers


def _should_skip(path: str) -> bool:
    """Check if a file path should be skipped based on directory rules."""
    parts = path.split("/")
    return any(part in SKIP_DIRS for part in parts)


def _has_allowed_extension(path: str) -> bool:
    """Check if a file has an allowed extension."""
    return any(path.endswith(ext) for ext in ALLOWED_EXTENSIONS)


def fetch_repo(github_url: str) -> Dict[str, str]:
    """
    Fetch all relevant source files from a GitHub repository.

    Args:
        github_url: Full GitHub URL to the repository.

    Returns:
        Dictionary mapping filepath to file content.
    """
    owner, repo, branch = _parse_github_url(github_url)
    headers = _get_headers()

    # Try the specified branch first, fall back to "master"
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    response = requests.get(tree_url, headers=headers, timeout=30)

    if response.status_code == 404 and branch == "main":
        branch = "master"
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        response = requests.get(tree_url, headers=headers, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(
            f"GitHub API error ({response.status_code}): {response.json().get('message', 'Unknown error')}"
        )

    tree_data = response.json()
    files: Dict[str, str] = {}

    for item in tree_data.get("tree", []):
        path = item.get("path", "")
        item_type = item.get("type", "")
        size = item.get("size", 0)

        # Only process files (blobs)
        if item_type != "blob":
            continue

        # Skip unwanted directories
        if _should_skip(path):
            continue

        # Only include files with allowed extensions
        if not _has_allowed_extension(path):
            continue

        # Skip very large files
        if size and size > MAX_FILE_SIZE:
            logger.info(f"Skipping large file: {path} ({size} bytes)")
            continue

        # Fetch file content
        try:
            content = _fetch_file_content(owner, repo, path, branch, headers)
            if content is not None:
                files[path] = content
        except Exception as e:
            logger.warning(f"Failed to fetch {path}: {e}")
            continue

    logger.info(f"Fetched {len(files)} files from {owner}/{repo}")
    return files


def _fetch_file_content(
    owner: str, repo: str, path: str, branch: str, headers: dict
) -> Optional[str]:
    """Fetch and decode a single file's content from GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code != 200:
        return None

    data = response.json()
    content_b64 = data.get("content", "")
    encoding = data.get("encoding", "")

    if encoding == "base64" and content_b64:
        try:
            return base64.b64decode(content_b64).decode("utf-8", errors="replace")
        except Exception:
            return None

    return None
