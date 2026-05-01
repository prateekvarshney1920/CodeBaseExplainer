"""
Explain Route — Endpoints for file explanations and prompt management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

from services.llm_service import (
    summarize_file,
    explain_simple,
    load_prompts,
    save_prompts,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class ExplainRequest(BaseModel):
    filename: str
    content: str
    simple: bool = False


class PromptUpdate(BaseModel):
    value: str


@router.post("/api/explain")
async def explain_file(request: ExplainRequest):
    """
    Generate an AI explanation for a single file.
    Use simple=true for beginner-friendly explanations.
    """
    try:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="File content cannot be empty.")

        # Truncate very large files
        content = request.content[:8000] if len(request.content) > 8000 else request.content

        if request.simple:
            explanation = explain_simple(request.filename, content)
        else:
            explanation = summarize_file(request.filename, content)

        return {
            "status": "success",
            "filename": request.filename,
            "explanation": explanation,
            "mode": "simple" if request.simple else "detailed",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Explanation failed for {request.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")


@router.get("/api/prompts")
async def get_prompts():
    """Return all configured LLM prompts."""
    try:
        prompts = load_prompts()
        return {"status": "success", "prompts": prompts}
    except Exception as e:
        logger.error(f"Failed to load prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/prompts/{key}")
async def update_prompt(key: str, update: PromptUpdate):
    """Update a specific prompt by key."""
    try:
        prompts = load_prompts()

        if key not in prompts:
            raise HTTPException(
                status_code=404,
                detail=f"Prompt key '{key}' not found. Available keys: {list(prompts.keys())}",
            )

        if not update.value.strip():
            raise HTTPException(status_code=400, detail="Prompt value cannot be empty.")

        prompts[key] = update.value
        save_prompts(prompts)

        return {
            "status": "success",
            "key": key,
            "value": update.value,
            "message": f"Prompt '{key}' updated successfully.",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update prompt '{key}': {e}")
        raise HTTPException(status_code=500, detail=str(e))
