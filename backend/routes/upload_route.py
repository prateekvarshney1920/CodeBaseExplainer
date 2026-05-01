"""
Upload Route — POST /api/upload endpoint for analyzing uploaded ZIP files.
"""

import os
import io
import zipfile
import tempfile
import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from services.agent_service import CodebaseAgent
from services.github_service import ALLOWED_EXTENSIONS, SKIP_DIRS

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_FILE_SIZE = 100_000  # 100 KB per file


def _should_skip(path: str) -> bool:
    """Check if a file path should be skipped."""
    parts = path.replace("\\", "/").split("/")
    return any(part in SKIP_DIRS for part in parts)


def _has_allowed_extension(path: str) -> bool:
    """Check if a file has an allowed extension."""
    return any(path.endswith(ext) for ext in ALLOWED_EXTENSIONS)


def _extract_zip(content: bytes) -> dict:
    """
    Extract source files from a ZIP archive.

    Returns:
        Dictionary mapping filepath → content
    """
    files = {}

    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        for info in zf.infolist():
            # Skip directories
            if info.is_dir():
                continue

            path = info.filename.replace("\\", "/")

            # Remove leading directory (common in GitHub ZIPs)
            parts = path.split("/")
            if len(parts) > 1:
                # Strip the top-level directory if all files share one
                path = "/".join(parts[1:]) if parts[0] else path

            if not path:
                continue

            # Apply filters
            if _should_skip(path):
                continue
            if not _has_allowed_extension(path):
                continue
            if info.file_size > MAX_FILE_SIZE:
                logger.info(f"Skipping large file: {path} ({info.file_size} bytes)")
                continue

            try:
                content_bytes = zf.read(info.filename)
                files[path] = content_bytes.decode("utf-8", errors="replace")
            except Exception as e:
                logger.warning(f"Failed to read {path} from ZIP: {e}")
                continue

    return files


@router.post("/api/upload")
async def analyze_upload(file: UploadFile = File(...)):
    """
    Analyze an uploaded ZIP file: extract, parse, build graph, generate explanations.
    """
    try:
        # Validate file type
        if not file.filename or not file.filename.endswith(".zip"):
            raise HTTPException(
                status_code=400,
                detail="Only .zip files are accepted.",
            )

        # Read file content
        content = await file.read()

        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE // (1024*1024)} MB.",
            )

        logger.info(f"Processing uploaded file: {file.filename} ({len(content)} bytes)")

        # Extract files from ZIP
        repo_data = _extract_zip(content)

        if not repo_data:
            raise HTTPException(
                status_code=400,
                detail="No supported source files found in the ZIP archive.",
            )

        # Run the analysis agent
        agent = CodebaseAgent(repo_data)
        results = agent.run()

        # Clean up internal state
        results.pop("_graph_instance", None)

        return {
            "status": "success",
            "filename": file.filename,
            "file_count": len(repo_data),
            "files": {k: v[:200] + "..." if len(v) > 200 else v for k, v in repo_data.items()},
            "languages": results.get("languages", {}),
            "primary_language": results.get("primary_language", "unknown"),
            "graph": results.get("graph", {"nodes": [], "edges": []}),
            "summaries": results.get("summaries", {}),
            "architecture_overview": results.get("architecture_overview", ""),
            "entry_points": results.get("entry_points", []),
            "cycles": results.get("cycles", []),
        }

    except HTTPException:
        raise
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid or corrupted ZIP file.")
    except Exception as e:
        logger.error(f"Upload analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
