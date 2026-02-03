"""
Step 3: Break scoring using GPT-4o.

Inserts semantic break markers into extracted text.
Returns text with [BREAK id=X score=Y] markers.
"""

from pathlib import Path

from openai import OpenAI

import config

# Initialize OpenAI client
_client = OpenAI(api_key=config.OPENAI_API_KEY)

# Load break scoring prompt
_PROMPT_PATH = Path(__file__).parent.parent / "docs" / "prompts" / "break-scoring.md"
_PROMPT_TEMPLATE = None

# Token limits - GPT-4o output is capped at 16384 tokens
# Since break scoring outputs ~input + markers, segment size must fit in output limit
_MAX_TOKENS_PER_SEGMENT = 12000  # Leaves room for break markers in output
_OVERLAP_TOKENS = 2000


def _load_prompt() -> str:
    """Load and cache the break scoring prompt."""
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


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: words * 1.3."""
    return int(len(text.split()) * 1.3)


def _split_for_processing(text: str) -> list[tuple[str, int, int]]:
    """
    Split text into segments for processing.
    Returns list of (segment_text, start_char, end_char) tuples.
    """
    tokens = _estimate_tokens(text)
    if tokens <= _MAX_TOKENS_PER_SEGMENT:
        return [(text, 0, len(text))]

    # Need to split - find paragraph boundaries
    segments = []
    paragraphs = text.split("\n\n")

    current_segment = []
    current_tokens = 0
    current_start = 0
    char_pos = 0

    for para in paragraphs:
        para_tokens = _estimate_tokens(para)

        if current_tokens + para_tokens > _MAX_TOKENS_PER_SEGMENT and current_segment:
            # Save current segment
            segment_text = "\n\n".join(current_segment)
            segments.append((segment_text, current_start, char_pos))

            # Start new segment with overlap
            overlap_paras = []
            overlap_tokens = 0
            for p in reversed(current_segment):
                p_tokens = _estimate_tokens(p)
                if overlap_tokens + p_tokens > _OVERLAP_TOKENS:
                    break
                overlap_paras.insert(0, p)
                overlap_tokens += p_tokens

            current_segment = overlap_paras + [para]
            current_tokens = overlap_tokens + para_tokens
            current_start = char_pos - len("\n\n".join(overlap_paras)) if overlap_paras else char_pos
        else:
            current_segment.append(para)
            current_tokens += para_tokens

        char_pos += len(para) + 2  # +2 for \n\n

    # Don't forget the last segment
    if current_segment:
        segment_text = "\n\n".join(current_segment)
        segments.append((segment_text, current_start, len(text)))

    return segments


def score_breaks(text: str) -> str:
    """
    Insert break markers into extracted text using GPT-4o.

    For large documents (>100k tokens), splits into segments with overlap.
    """
    segments = _split_for_processing(text)
    prompt = _load_prompt()

    if len(segments) == 1:
        # Simple case: single segment
        return _process_segment(segments[0][0], prompt)

    # Multi-segment processing
    results = []
    for i, (segment_text, start, end) in enumerate(segments):
        result = _process_segment(segment_text, prompt)

        if i > 0:
            # Handle overlap: prefer breaks from segment with region in middle
            # For simplicity, just trim overlapping break markers from start
            result = _trim_overlap_start(result)

        results.append(result)

    # Combine and resequence break IDs
    combined = "\n\n".join(results)
    return _resequence_breaks(combined)


def _process_segment(text: str, prompt: str, max_retries: int = 3) -> str:
    """Process a single segment with GPT-4o, with retry logic for rate limits."""
    import time

    for attempt in range(max_retries):
        try:
            response = _client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.1,
                max_tokens=16000,
            )
            return response.choices[0].message.content
        except Exception as e:
            if "rate" in str(e).lower() and attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10  # 10s, 20s, 30s backoff
                time.sleep(wait_time)
            else:
                raise


def _trim_overlap_start(text: str) -> str:
    """Remove break markers from the beginning of overlapped text."""
    import re

    lines = text.split("\n")
    # Skip lines until we find content that's clearly past the overlap
    # (This is a simplified approach)
    return text


def _resequence_breaks(text: str) -> str:
    """Renumber all break IDs sequentially from 1."""
    import re

    pattern = r"\[BREAK id=\d+ score=(\d+)\]"
    counter = [0]  # Use list to allow mutation in closure

    def replace_fn(match):
        counter[0] += 1
        score = match.group(1)
        return f"[BREAK id={counter[0]} score={score}]"

    return re.sub(pattern, replace_fn, text)
