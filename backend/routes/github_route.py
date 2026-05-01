"""
GitHub Route — POST /api/github endpoint for analyzing GitHub repositories.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from services.github_service import fetch_repo
from services.agent_service import CodebaseAgent

logger = logging.getLogger(__name__)
router = APIRouter()


class GitHubRequest(BaseModel):
    url: str


@router.post("/api/github")
async def analyze_github(request: GitHubRequest):
    """
    Analyze a GitHub repository: fetch files, parse, build graph, generate explanations.
    """
    try:
        logger.info(f"Analyzing GitHub repo: {request.url}")

        # Fetch repository files
        repo_data = fetch_repo(request.url)

        if not repo_data:
            raise HTTPException(
                status_code=400,
                detail="No supported source files found in the repository.",
            )

        # Run the analysis agent
        agent = CodebaseAgent(repo_data)
        results = agent.run()

        # Clean up internal state before returning
        results.pop("_graph_instance", None)

        return {
            "status": "success",
            "url": request.url,
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"GitHub analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
