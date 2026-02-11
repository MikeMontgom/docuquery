"""
Step 2: PDF text extraction using Gemini.

Extracts text from PDF in 5-page batches, sequentially.
Returns a master text string with [PAGE X] markers.
"""

import logging
import time
from io import BytesIO
from pathlib import Path

import google.generativeai as genai
from pypdf import PdfReader, PdfWriter

import config

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=config.GEMINI_API_KEY)

# Load extraction prompt template
_PROMPT_PATH = Path(__file__).parent.parent / "docs" / "prompts" / "extraction.md"
_PROMPT_TEMPLATE = None


def _load_prompt() -> str:
    """Load and cache the extraction prompt template."""
    global _PROMPT_TEMPLATE
    if _PROMPT_TEMPLATE is None:
        content = _PROMPT_PATH.read_text()
        # Extract just the prompt between the code fence
        lines = content.split("```")[1].strip()
        # Remove the first line if it's just a language identifier
        if lines.startswith("\n"):
            lines = lines[1:]
        _PROMPT_TEMPLATE = lines
    return _PROMPT_TEMPLATE


def _create_batch_pdf(reader: PdfReader, start_idx: int, end_idx: int) -> bytes:
    """Extract pages from a PDF and return as bytes."""
    writer = PdfWriter()
    for i in range(start_idx, min(end_idx, len(reader.pages))):
        writer.add_page(reader.pages[i])

    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def extract_pdf(pdf_content: bytes, batch_size: int = 5) -> str:
    """
    Extract text from PDF using Gemini.

    Args:
        pdf_content: Raw PDF bytes
        batch_size: Pages per batch (default 5)

    Returns:
        Master text string with all extracted content
    """
    reader = PdfReader(BytesIO(pdf_content))
    total_pages = len(reader.pages)

    # Use Gemini 2.0 Flash (current best model with PDF support)
    model = genai.GenerativeModel("gemini-2.0-flash")

    master_text_parts = []
    prompt_template = _load_prompt()

    # Process in batches
    total_batches = (total_pages + batch_size - 1) // batch_size
    for batch_idx, batch_start in enumerate(range(0, total_pages, batch_size)):
        batch_end = min(batch_start + batch_size, total_pages)
        batch_label = f"batch {batch_idx + 1}/{total_batches} (pages {batch_start + 1}-{batch_end})"

        # Rate-limit: pause between batches to avoid Gemini 429s
        if batch_idx > 0:
            time.sleep(4)

        # Create batch PDF
        batch_pdf = _create_batch_pdf(reader, batch_start, batch_end)

        # Format prompt with page numbers (1-indexed for display)
        prompt = prompt_template.replace("{start_page}", str(batch_start + 1))
        prompt = prompt.replace("{end_page}", str(batch_end))

        # Upload PDF to Gemini
        pdf_file = genai.upload_file(
            BytesIO(batch_pdf),
            mime_type="application/pdf",
            display_name=f"batch_{batch_start + 1}_{batch_end}.pdf",
        )

        # Generate extraction with retry logic for rate limits
        max_retries = 5
        extracted = None

        try:
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(
                        [prompt, pdf_file],
                        generation_config=genai.GenerationConfig(
                            temperature=0.1,
                            max_output_tokens=32000,
                        ),
                    )
                    extracted = response.text
                    logger.info(f"Extracted {batch_label}")
                    break
                except Exception as e:
                    err_msg = str(e).lower()
                    is_rate_limit = any(
                        s in err_msg
                        for s in ["rate", "resource", "exhausted", "429", "quota"]
                    )
                    if is_rate_limit and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 15  # 15s, 30s, 45s, 60s
                        logger.warning(
                            f"Rate limited on {batch_label}, "
                            f"attempt {attempt + 1}/{max_retries}, "
                            f"waiting {wait_time}s"
                        )
                        time.sleep(wait_time)
                    else:
                        raise

            if extracted is None:
                raise RuntimeError(f"Failed to extract {batch_label}")

            # Strip batch markers if present
            if "==START OF EXTRACTION BATCH==" in extracted:
                extracted = extracted.split("==START OF EXTRACTION BATCH==")[1]
            if "==END OF EXTRACTION BATCH==" in extracted:
                extracted = extracted.split("==END OF EXTRACTION BATCH==")[0]

            master_text_parts.append(extracted.strip())

        finally:
            # Clean up uploaded file
            try:
                genai.delete_file(pdf_file.name)
            except Exception:
                pass  # Best effort cleanup

    return "\n\n".join(master_text_parts)
