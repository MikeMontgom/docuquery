"""
Query Router - Step Q2

Uses GPT-4o-mini to identify relevant chunks from summaries.
"""

import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI

import config

_client = OpenAI(api_key=config.OPENAI_API_KEY)

_PROMPT_PATH = Path(__file__).parent.parent / "docs" / "prompts" / "routing.md"
_PROMPT_TEMPLATE = None

_MAX_TOKENS_PER_BATCH = 50000


def _load_prompt() -> str:
    """Load and cache the routing prompt."""
    global _PROMPT_TEMPLATE
    if _PROMPT_TEMPLATE is None:
        content = _PROMPT_PATH.read_text()
        parts = content.split("```")
        if len(parts) >= 2:
            _PROMPT_TEMPLATE = parts[1].strip()
        else:
            _PROMPT_TEMPLATE = content
    return _PROMPT_TEMPLATE


def _estimate_tokens(text: str) -> int:
    """Rough token estimate."""
    return int(len(text.split()) * 1.3)


def _format_history(history: list[dict]) -> str:
    """Format conversation history for prompt."""
    if not history:
        return "(No previous conversation)"

    lines = []
    for msg in history:
        role = msg.get("role", "user").upper()
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _format_summaries(chunks: list[dict]) -> str:
    """Format chunk summaries for routing prompt."""
    lines = []
    for c in chunks:
        chunk_id = c.get("record_id", c.get("chunk_id", ""))
        heading = c.get("heading_path", "")
        summary = c.get("content_summary", "")
        lines.append(f"[{chunk_id}] ({heading}) {summary}")
    return "\n".join(lines)


def _route_batch(
    question: str,
    history: list[dict],
    chunks: list[dict],
    prompt_template: str,
) -> list[str]:
    """Route a single batch of chunks."""
    history_formatted = _format_history(history)
    summaries_formatted = _format_summaries(chunks)

    prompt = prompt_template.replace("{conversation_history_formatted}", history_formatted)
    prompt = prompt.replace("{question}", question)
    prompt = prompt.replace("{all_summaries_formatted}", summaries_formatted)

    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
        temperature=0.1,
        max_tokens=1000,
    )

    result_text = response.choices[0].message.content.strip()

    # Parse JSON array from response
    try:
        # Handle potential markdown code fences
        if "```" in result_text:
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]

        chunk_ids = json.loads(result_text)
        return [str(cid) for cid in chunk_ids]
    except (json.JSONDecodeError, IndexError):
        # Fallback: try to extract IDs from bracket notation without quotes
        # e.g., [recABC123, recDEF456] -> ["recABC123", "recDEF456"]
        import re
        match = re.search(r'\[(.*?)\]', result_text, re.DOTALL)
        if match:
            ids_str = match.group(1)
            # Split by comma and clean up
            ids = [id.strip().strip('"\'') for id in ids_str.split(',')]
            return [id for id in ids if id and id.startswith('rec')]
        return []


def route_question(
    question: str,
    history: list[dict],
    chunks: list[dict],
) -> list[str]:
    """
    Route a question to identify relevant chunk IDs.

    Args:
        question: User's question
        history: Conversation history
        chunks: All available chunks with summaries

    Returns:
        List of chunk record IDs to retrieve at full resolution
    """
    prompt = _load_prompt()

    # Check if we need to batch
    summaries_text = _format_summaries(chunks)
    total_tokens = _estimate_tokens(summaries_text)

    if total_tokens <= _MAX_TOKENS_PER_BATCH:
        return _route_batch(question, history, chunks, prompt)

    # Split into batches and process in parallel
    batch_size = len(chunks) * _MAX_TOKENS_PER_BATCH // total_tokens
    batches = [chunks[i:i + batch_size] for i in range(0, len(chunks), batch_size)]

    all_ids = set()
    with ThreadPoolExecutor(max_workers=len(batches)) as executor:
        futures = [
            executor.submit(_route_batch, question, history, batch, prompt)
            for batch in batches
        ]
        for future in futures:
            all_ids.update(future.result())

    return list(all_ids)
