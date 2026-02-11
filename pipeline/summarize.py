"""
Step 8: Summarization using GPT-4o.

Generates functional summaries for text chunks.
Graphic chunks use their description field directly.
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import OpenAI

import config
from pipeline.chunk import Chunk

# Initialize OpenAI client
_client = OpenAI(api_key=config.OPENAI_API_KEY)

# Load summarization prompt
_PROMPT_PATH = Path(__file__).parent.parent / "docs" / "prompts" / "summarization.md"
_PROMPT_TEMPLATE = None


def _load_prompt() -> str:
    """Load and cache the summarization prompt."""
    global _PROMPT_TEMPLATE
    if _PROMPT_TEMPLATE is None:
        content = _PROMPT_PATH.read_text()
        # Extract just the prompt between the code fence
        parts = content.split("```")
        if len(parts) >= 2:
            _PROMPT_TEMPLATE = parts[1].strip()
        else:
            _PROMPT_TEMPLATE = content
    return _PROMPT_TEMPLATE


def _extract_graphic_summary(content: str) -> str | None:
    """Extract title and description from GRAPHIC_INSERT JSON, formatted for routing."""
    pattern = r"%%% GRAPHIC_INSERT %%%\s*(\{.*?\})\s*%%% END_GRAPHIC_INSERT %%%"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return None

    try:
        data = json.loads(match.group(1))
        title = data.get("title", "")
        description = data.get("description", "")
        # Format as "[title] description" for searchability
        if title:
            return f"[{title}] {description}"
        return description
    except json.JSONDecodeError:
        return None


def _summarize_text(text: str, prompt: str, max_retries: int = 5) -> str:
    """Generate summary for a text chunk using GPT-4o with retry logic."""
    import time

    for attempt in range(max_retries):
        try:
            response = _client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.2,
                max_tokens=500,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            err_msg = str(e).lower()
            is_rate_limit = any(
                s in err_msg
                for s in ["rate", "resource", "exhausted", "429", "quota", "limit"]
            )
            if is_rate_limit and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10  # 10s, 20s, 30s, 40s
                time.sleep(wait_time)
            else:
                raise


def summarize_chunk(chunk: Chunk) -> str:
    """
    Generate summary for a single chunk.

    For graphic chunks, returns "[title] description" for searchability.
    For text chunks, uses GPT-4o summarization.
    """
    if chunk.chunk_type == "graphic":
        summary = _extract_graphic_summary(chunk.content_raw)
        return summary or "Graphic element"

    prompt = _load_prompt()
    return _summarize_text(chunk.content_raw, prompt)


def summarize_all(chunks: list[Chunk], max_workers: int = 3) -> dict[int, str]:
    """
    Generate summaries for all chunks with limited concurrency.

    Args:
        chunks: List of Chunk objects
        max_workers: Maximum concurrent summarization requests (default 3 to avoid rate limits)

    Returns:
        Dict mapping sequence_number to summary
    """
    import time

    prompt = _load_prompt()

    def summarize_one(chunk: Chunk) -> tuple[int, str]:
        if chunk.chunk_type == "graphic":
            summary = _extract_graphic_summary(chunk.content_raw)
            return chunk.sequence_number, summary or "Graphic element"
        else:
            summary = _summarize_text(chunk.content_raw, prompt)
            # Small delay between API calls to help with rate limiting
            time.sleep(0.5)
            return chunk.sequence_number, summary

    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for seq_num, summary in executor.map(summarize_one, chunks):
            results[seq_num] = summary

    return results
