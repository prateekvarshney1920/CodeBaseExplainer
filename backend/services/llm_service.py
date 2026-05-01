"""
LLM Service — Groq API integration for code explanations.
Uses the OpenAI-compatible API at https://api.groq.com/openai/v1.
Loads prompts from config/prompts.json, never hardcodes prompt strings.
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

# ── Prompt loader ──────────────────────────────────────────────────────────────

PROMPTS_PATH = Path(__file__).parent.parent / "config" / "prompts.json"


def load_prompts() -> dict:
    """Load all prompts from the prompts.json config file."""
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_prompts(prompts: dict) -> None:
    """Persist updated prompts back to the config file."""
    with open(PROMPTS_PATH, "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)


def get_prompt(key: str) -> str:
    """Get a single prompt template by key."""
    prompts = load_prompts()
    if key not in prompts:
        raise KeyError(f"Prompt key '{key}' not found in prompts.json")
    return prompts[key]


# ── Groq client ───────────────────────────────────────────────────────────────

_client: Optional[OpenAI] = None


def _get_client() -> Optional[OpenAI]:
    """Get or create the Groq OpenAI-compatible client."""
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_api_key_here":
        logger.warning("GROQ_API_KEY not set or is placeholder — LLM calls will fail")
        return None

    _client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    return _client


def _call_llm(prompt_text: str, max_retries: int = 3) -> str:
    """
    Call Groq API via OpenAI-compatible endpoint with exponential backoff retry.
    Returns the generated text or a fallback message on failure.
    """
    client = _get_client()
    if client is None:
        return "[LLM unavailable — GROQ_API_KEY not configured]"

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert code analyst. Provide clear, concise, and accurate explanations.",
                    },
                    {
                        "role": "user",
                        "content": prompt_text,
                    },
                ],
                temperature=0.4,
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except Exception as e:
            wait_time = (2 ** attempt) + 1
            logger.warning(
                f"Groq API call failed (attempt {attempt + 1}/{max_retries}): {e}. "
                f"Retrying in {wait_time}s..."
            )
            if attempt < max_retries - 1:
                time.sleep(wait_time)
            else:
                logger.error(f"Groq API call failed after {max_retries} attempts: {e}")
                return f"[LLM error after {max_retries} retries: {str(e)}]"


# ── Public API ─────────────────────────────────────────────────────────────────

def summarize_file(
    filename: str,
    content: str,
    prompt_key: str = "file_summary",
) -> str:
    """
    Generate a plain-English summary of a single file using the LLM.
    """
    template = get_prompt(prompt_key)
    prompt_text = template.format(filename=filename, content=content)
    return _call_llm(prompt_text)


def explain_architecture(
    file_tree: str,
    deps: str,
    entry_points: str = "",
    prompt_key: str = "architecture_overview",
) -> str:
    """
    Generate an architecture overview of the entire codebase.
    """
    template = get_prompt(prompt_key)
    prompt_text = template.format(
        file_tree=file_tree,
        dependencies=deps,
        entry_points=entry_points,
    )
    return _call_llm(prompt_text)


def explain_dependency(
    source: str,
    target: str,
    source_content: str,
    target_content: str,
    prompt_key: str = "dependency_explanation",
) -> str:
    """
    Explain why one file depends on another.
    """
    template = get_prompt(prompt_key)
    prompt_text = template.format(
        source=source,
        target=target,
        source_content=source_content,
        target_content=target_content,
    )
    return _call_llm(prompt_text)


def explain_simple(
    filename: str,
    content: str,
    prompt_key: str = "simple_explanation",
) -> str:
    """
    Explain a file in the simplest possible terms for complete beginners.
    """
    template = get_prompt(prompt_key)
    prompt_text = template.format(filename=filename, content=content)
    return _call_llm(prompt_text)
