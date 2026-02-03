"""
Step 5: Dynamic programming chunking (no LLM).

Splits cleaned text into optimal chunks using break markers.
"""

import re
from dataclasses import dataclass

from pipeline.cleanup import PageMapping

# Constants
TARGET_CHUNK_TOKENS = 650
MIN_CHUNK_TOKENS = 200
MAX_CHUNK_TOKENS = 1200
TOKEN_ESTIMATE_FACTOR = 1.3

# DP cost weights
ALPHA = 1.0  # Size deviation penalty
BETA = 50.0  # Weak break penalty


@dataclass
class Chunk:
    """Represents a document chunk."""

    sequence_number: int
    chunk_type: str  # "text" or "graphic"
    content_raw: str
    token_count: int
    source_pages: str
    heading_path: str


def _estimate_tokens(text: str) -> int:
    """Estimate token count from text."""
    return int(len(text.split()) * TOKEN_ESTIMATE_FACTOR)


def _extract_graphics(text: str) -> list[tuple[int, int, str]]:
    """
    Extract GRAPHIC_INSERT blocks from text.
    Returns list of (start, end, content) tuples.
    """
    pattern = r"%%% GRAPHIC_INSERT %%%\s*(.*?)\s*%%% END_GRAPHIC_INSERT %%%"
    matches = []
    for match in re.finditer(pattern, text, re.DOTALL):
        matches.append((match.start(), match.end(), match.group(0)))
    return matches


def _extract_breaks(text: str) -> list[tuple[int, int, int]]:
    """
    Extract break markers from text.
    Returns list of (position, id, score) tuples.
    """
    pattern = r"\[BREAK id=(\d+) score=(\d+)\]"
    breaks = []
    for match in re.finditer(pattern, text):
        breaks.append((match.start(), int(match.group(1)), int(match.group(2))))
    return breaks


def _remove_break_markers(text: str) -> str:
    """Remove break markers from text."""
    return re.sub(r"\[BREAK id=\d+ score=\d+\]\n?", "", text)


def _find_heading_path(text: str, position: int) -> str:
    """
    Find the most recent heading path before a position.
    Looks for markdown-style headings (# Heading).
    """
    # Find all headings before position
    heading_pattern = r"^(#{1,6})\s+(.+)$"
    text_before = text[:position]
    headings = []

    for match in re.finditer(heading_pattern, text_before, re.MULTILINE):
        level = len(match.group(1))
        title = match.group(2).strip()
        headings.append((level, title))

    if not headings:
        return ""

    # Build path from most recent headings at each level
    path_parts = {}
    for level, title in headings:
        path_parts[level] = title
        # Clear deeper levels when we see a shallower heading
        for l in list(path_parts.keys()):
            if l > level:
                del path_parts[l]

    # Build path string
    return " > ".join(path_parts[l] for l in sorted(path_parts.keys()))


def chunk_text(text: str, page_mapping: PageMapping) -> list[Chunk]:
    """
    Split text into optimal chunks using dynamic programming.

    Args:
        text: Cleaned text with break markers
        page_mapping: Character position to page number mapping

    Returns:
        List of Chunk objects
    """
    chunks = []
    sequence = 0

    # First, extract and handle graphic blocks separately
    graphics = _extract_graphics(text)
    graphic_positions = set()
    for start, end, content in graphics:
        graphic_positions.update(range(start, end))

    # If there are graphics, process text segments and graphics separately
    if graphics:
        last_end = 0
        for g_start, g_end, g_content in sorted(graphics):
            # Process text before this graphic
            if g_start > last_end:
                text_segment = text[last_end:g_start]
                segment_chunks = _chunk_text_segment(
                    text_segment, page_mapping, last_end, sequence
                )
                chunks.extend(segment_chunks)
                sequence += len(segment_chunks)

            # Add graphic as its own chunk
            sequence += 1
            chunks.append(
                Chunk(
                    sequence_number=sequence,
                    chunk_type="graphic",
                    content_raw=g_content,
                    token_count=_estimate_tokens(g_content),
                    source_pages=page_mapping.get_pages_for_range(g_start, g_end),
                    heading_path=_find_heading_path(text, g_start),
                )
            )
            last_end = g_end

        # Process remaining text after last graphic
        if last_end < len(text):
            text_segment = text[last_end:]
            segment_chunks = _chunk_text_segment(
                text_segment, page_mapping, last_end, sequence
            )
            chunks.extend(segment_chunks)
    else:
        # No graphics, process entire text
        chunks = _chunk_text_segment(text, page_mapping, 0, 0)

    return chunks


def _chunk_text_segment(
    text: str, page_mapping: PageMapping, offset: int, start_sequence: int
) -> list[Chunk]:
    """
    Chunk a text segment (no graphics) using DP.
    """
    breaks = _extract_breaks(text)

    if not breaks:
        # No breaks, treat as single chunk
        content = _remove_break_markers(text).strip()
        if not content:
            return []

        return [
            Chunk(
                sequence_number=start_sequence + 1,
                chunk_type="text",
                content_raw=content,
                token_count=_estimate_tokens(content),
                source_pages=page_mapping.get_pages_for_range(offset, offset + len(text)),
                heading_path=_find_heading_path(text, 0),
            )
        ]

    # Build segments between breaks
    segments = []
    last_pos = 0
    for pos, break_id, score in breaks:
        if pos > last_pos:
            segment_text = text[last_pos:pos]
            segments.append(
                {
                    "text": segment_text,
                    "start": last_pos + offset,
                    "end": pos + offset,
                    "entry_score": score if segments else 100,  # First segment has implicit 100
                }
            )
        last_pos = pos + len(f"[BREAK id={break_id} score={score}]") + 1  # +1 for newline

    # Don't forget text after last break
    if last_pos < len(text):
        remaining = text[last_pos:].strip()
        if remaining:
            segments.append(
                {
                    "text": remaining,
                    "start": last_pos + offset,
                    "end": len(text) + offset,
                    "entry_score": 100,
                }
            )

    if not segments:
        return []

    # DP to find optimal chunking
    n = len(segments)

    # dp[i] = (min_cost, prev_index) to reach segment i
    INF = float("inf")
    dp = [(INF, -1)] * (n + 1)
    dp[0] = (0, -1)

    for i in range(n):
        if dp[i][0] == INF:
            continue

        # Try ending a chunk at each position j > i
        accumulated_text = ""
        accumulated_tokens = 0

        for j in range(i, n):
            segment = segments[j]
            accumulated_text += segment["text"]
            accumulated_tokens = _estimate_tokens(_remove_break_markers(accumulated_text))

            if accumulated_tokens < MIN_CHUNK_TOKENS and j < n - 1:
                continue

            if accumulated_tokens > MAX_CHUNK_TOKENS:
                break

            # Calculate cost
            entry_score = segments[i]["entry_score"]
            size_cost = ALPHA * (accumulated_tokens - TARGET_CHUNK_TOKENS) ** 2
            break_cost = BETA * (100 - entry_score)
            total_cost = dp[i][0] + size_cost + break_cost

            if total_cost < dp[j + 1][0]:
                dp[j + 1] = (total_cost, i)

    # Backtrack to find chunk boundaries
    chunk_ends = []
    pos = n
    while pos > 0:
        chunk_ends.append(pos)
        pos = dp[pos][1]

    chunk_ends.reverse()

    # Build chunks
    chunks = []
    prev_end = 0
    for end_idx in chunk_ends:
        chunk_segments = segments[prev_end:end_idx]
        if not chunk_segments:
            continue

        combined_text = "".join(s["text"] for s in chunk_segments)
        content = _remove_break_markers(combined_text).strip()
        if not content:
            prev_end = end_idx
            continue

        chunks.append(
            Chunk(
                sequence_number=start_sequence + len(chunks) + 1,
                chunk_type="text",
                content_raw=content,
                token_count=_estimate_tokens(content),
                source_pages=page_mapping.get_pages_for_range(
                    chunk_segments[0]["start"], chunk_segments[-1]["end"]
                ),
                heading_path=_find_heading_path(text, chunk_segments[0]["start"] - offset),
            )
        )
        prev_end = end_idx

    return chunks
