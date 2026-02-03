"""
Step 4: Deterministic cleanup (no LLM).

- Records source page mapping
- Removes [PAGE X] markers
- Removes code block UI artifacts
- Resequences break IDs
"""

import re
from dataclasses import dataclass


@dataclass
class PageMapping:
    """Maps character ranges to source pages."""

    ranges: list[tuple[int, int, int]]  # (start_char, end_char, page_num)

    def get_pages_for_range(self, start: int, end: int) -> str:
        """Get page range string for a character range."""
        pages = set()
        for range_start, range_end, page in self.ranges:
            if range_start < end and range_end > start:
                pages.add(page)

        if not pages:
            return ""

        pages_list = sorted(pages)
        if len(pages_list) == 1:
            return str(pages_list[0])
        return f"{pages_list[0]}-{pages_list[-1]}"


def _build_page_mapping(text: str) -> PageMapping:
    """Build a mapping from character positions to page numbers."""
    ranges = []
    pattern = r"\[PAGE (\d+)\]"

    current_page = 1
    last_end = 0

    for match in re.finditer(pattern, text):
        page_num = int(match.group(1))
        marker_start = match.start()

        # Record range for previous page
        if marker_start > last_end:
            ranges.append((last_end, marker_start, current_page))

        current_page = page_num
        last_end = match.end()

    # Record final range
    if last_end < len(text):
        ranges.append((last_end, len(text), current_page))

    return PageMapping(ranges)


def _remove_page_markers(text: str) -> str:
    """Remove [PAGE X] markers."""
    return re.sub(r"\[PAGE \d+\]\n?", "", text)


def _remove_code_artifacts(text: str) -> str:
    """Remove UI artifacts that appear around code blocks."""
    artifacts = [
        "content_copy",
        "expand_less",
        "expand_more",
        "code ",
        "Python\n",
        "JavaScript\n",
    ]

    result = text
    for artifact in artifacts:
        # Remove artifacts that appear on lines adjacent to code fences
        # Pattern: artifact followed by optional whitespace and newline before ```
        result = re.sub(rf"{re.escape(artifact)}\s*\n```", "```", result)
        # Pattern: ``` followed by newline and artifact
        result = re.sub(rf"```\n{re.escape(artifact)}", "```", result)

    return result


def _resequence_breaks(text: str) -> str:
    """Renumber all break IDs sequentially from 1."""
    pattern = r"\[BREAK id=\d+ score=(\d+)\]"
    counter = [0]

    def replace_fn(match):
        counter[0] += 1
        score = match.group(1)
        return f"[BREAK id={counter[0]} score={score}]"

    return re.sub(pattern, replace_fn, text)


def cleanup(text: str) -> tuple[str, PageMapping]:
    """
    Apply deterministic cleanup to extracted text.

    Returns:
        Tuple of (cleaned_text, page_mapping)
    """
    # 1. Build page mapping before removing markers
    page_mapping = _build_page_mapping(text)

    # 2. Remove page markers
    text = _remove_page_markers(text)

    # 3. Remove code block artifacts
    text = _remove_code_artifacts(text)

    # 4. Resequence break IDs
    text = _resequence_breaks(text)

    return text, page_mapping
