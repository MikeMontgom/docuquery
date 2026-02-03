"""
Step 6: Image cropping using pdfplumber.

Crops graphics from PDF pages based on GRAPHIC_INSERT coordinates.
"""

import json
import re
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor

import pdfplumber
from PIL import Image

from services import gcs

# Coordinate conversion: PDF points (72 DPI) to 300 DPI render
DPI_SCALE = 300 / 72


def _parse_graphic_insert(content: str) -> dict | None:
    """Extract JSON from GRAPHIC_INSERT block."""
    pattern = r"%%% GRAPHIC_INSERT %%%\s*(\{.*?\})\s*%%% END_GRAPHIC_INSERT %%%"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def render_full_page(pdf_content: bytes, page_num: int) -> bytes:
    """
    Render a full PDF page as PNG.

    Args:
        pdf_content: Raw PDF bytes
        page_num: 1-indexed page number

    Returns:
        PNG image bytes
    """
    with pdfplumber.open(BytesIO(pdf_content)) as pdf:
        if page_num < 1 or page_num > len(pdf.pages):
            raise ValueError(f"Invalid page number: {page_num}")

        page = pdf.pages[page_num - 1]
        img = page.to_image(resolution=150)  # Lower res for full pages

        buffer = BytesIO()
        img.original.save(buffer, format="PNG")
        return buffer.getvalue()


def crop_image(
    pdf_content: bytes, page_num: int, coords: list[float], graphic_id: str
) -> bytes:
    """
    Crop a region from a PDF page.

    Args:
        pdf_content: Raw PDF bytes
        page_num: 1-indexed page number
        coords: [x0, y0, x1, y1] in PDF points (72 DPI)
        graphic_id: Unique identifier for the graphic

    Returns:
        PNG image bytes
    """
    with pdfplumber.open(BytesIO(pdf_content)) as pdf:
        if page_num < 1 or page_num > len(pdf.pages):
            raise ValueError(f"Invalid page number: {page_num}")

        page = pdf.pages[page_num - 1]

        # Render page at 300 DPI
        img = page.to_image(resolution=300)

        # Convert coordinates from PDF points to pixels
        x0 = int(coords[0] * DPI_SCALE)
        y0 = int(coords[1] * DPI_SCALE)
        x1 = int(coords[2] * DPI_SCALE)
        y1 = int(coords[3] * DPI_SCALE)

        # Crop the image
        cropped = img.original.crop((x0, y0, x1, y1))

        # Convert to PNG bytes
        buffer = BytesIO()
        cropped.save(buffer, format="PNG")
        return buffer.getvalue()


def process_graphic_chunk(
    doc_id: str, pdf_content: bytes, chunk_content: str
) -> str | None:
    """
    Process a graphic chunk: crop image and upload to GCS.
    Falls back to full page if cropping fails.

    Args:
        doc_id: Document record ID
        pdf_content: Raw PDF bytes
        chunk_content: Raw chunk content (GRAPHIC_INSERT block)

    Returns:
        Public GCS URL for the cropped image, or None if processing fails
    """
    graphic_data = _parse_graphic_insert(chunk_content)
    if not graphic_data:
        return None

    page_num = graphic_data.get("page")
    coords = graphic_data.get("coordinates")
    graphic_id = graphic_data.get("graphic_id", "unknown")

    if not page_num:
        return None

    image_bytes = None

    # Try cropping first
    if coords:
        try:
            image_bytes = crop_image(pdf_content, page_num, coords, graphic_id)
        except Exception as e:
            print(f"Crop failed for {graphic_id}, falling back to full page: {e}")

    # Fallback to full page
    if image_bytes is None:
        try:
            image_bytes = render_full_page(pdf_content, page_num)
            graphic_id = f"page_{page_num}_fallback"
        except Exception as e:
            print(f"Full page render also failed for {graphic_id}: {e}")
            return None

    # Upload to GCS
    try:
        url = gcs.upload_image(doc_id, graphic_id, image_bytes)
        return url
    except Exception as e:
        print(f"GCS upload failed for {graphic_id}: {e}")
        return None


def process_all_graphics(
    doc_id: str, pdf_content: bytes, chunks: list
) -> dict[int, str]:
    """
    Process all graphic chunks in parallel.

    Args:
        doc_id: Document record ID
        pdf_content: Raw PDF bytes
        chunks: List of Chunk objects

    Returns:
        Dict mapping sequence_number to image URL for graphic chunks
    """
    graphic_chunks = [(c.sequence_number, c.content_raw) for c in chunks if c.chunk_type == "graphic"]

    if not graphic_chunks:
        return {}

    def process_one(item):
        seq_num, content = item
        url = process_graphic_chunk(doc_id, pdf_content, content)
        return seq_num, url

    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        for seq_num, url in executor.map(process_one, graphic_chunks):
            if url:
                results[seq_num] = url

    return results


def save_all_pages(doc_id: str, pdf_content: bytes) -> dict[int, str]:
    """
    Save all PDF pages as images for citation previews.

    Args:
        doc_id: Document record ID
        pdf_content: Raw PDF bytes

    Returns:
        Dict mapping page number (1-indexed) to GCS URL
    """
    with pdfplumber.open(BytesIO(pdf_content)) as pdf:
        total_pages = len(pdf.pages)

    def render_and_upload(page_num: int) -> tuple[int, str | None]:
        try:
            image_bytes = render_full_page(pdf_content, page_num)
            url = gcs.upload_image(doc_id, f"page_{page_num}", image_bytes)
            return page_num, url
        except Exception as e:
            print(f"Failed to save page {page_num}: {e}")
            return page_num, None

    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        for page_num, url in executor.map(render_and_upload, range(1, total_pages + 1)):
            if url:
                results[page_num] = url

    return results
