import time
from typing import Any
import httpx

import config

BASE_URL = f"https://api.airtable.com/v0/{config.AIRTABLE_BASE_ID}"
HEADERS = {
    "Authorization": f"Bearer {config.AIRTABLE_API_KEY}",
    "Content-Type": "application/json",
}

# Rate limiter: 5 requests/second
_last_request_time = 0.0
_MIN_INTERVAL = 0.2  # 1/5 second


def _rate_limit():
    """Enforce rate limit before each request."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request_time = time.time()


def _request(method: str, endpoint: str, **kwargs) -> dict:
    """Make rate-limited request to Airtable API."""
    _rate_limit()
    url = f"{BASE_URL}/{endpoint}"
    response = httpx.request(method, url, headers=HEADERS, timeout=30.0, **kwargs)
    response.raise_for_status()
    return response.json() if response.content else {}


# --- Documents ---


def list_documents() -> list[dict]:
    """List all documents, ordered by upload_date descending."""
    records = []
    offset = None

    while True:
        params = {"sort[0][field]": "upload_date", "sort[0][direction]": "desc"}
        if offset:
            params["offset"] = offset

        data = _request("GET", config.AIRTABLE_DOCUMENTS_TABLE_ID, params=params)
        records.extend(data.get("records", []))

        offset = data.get("offset")
        if not offset:
            break

    return [_format_document(r) for r in records]


def get_document(record_id: str) -> dict | None:
    """Get a document by Airtable record ID."""
    try:
        data = _request("GET", f"{config.AIRTABLE_DOCUMENTS_TABLE_ID}/{record_id}")
        return _format_document(data)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise


def create_document(fields: dict) -> dict:
    """Create a new document record. Returns the created document."""
    data = _request(
        "POST",
        config.AIRTABLE_DOCUMENTS_TABLE_ID,
        json={"fields": fields},
    )
    return _format_document(data)


def update_document(record_id: str, fields: dict) -> dict:
    """Update a document record. Returns the updated document."""
    data = _request(
        "PATCH",
        f"{config.AIRTABLE_DOCUMENTS_TABLE_ID}/{record_id}",
        json={"fields": fields},
    )
    return _format_document(data)


def delete_document(record_id: str) -> None:
    """Delete a document record."""
    _request("DELETE", f"{config.AIRTABLE_DOCUMENTS_TABLE_ID}/{record_id}")


def _format_document(record: dict) -> dict:
    """Convert Airtable record to API response format."""
    fields = record.get("fields", {})
    return {
        "record_id": record["id"],
        "doc_id": fields.get("doc_id"),  # Auto-number from Airtable
        "name": fields.get("name"),
        "status": fields.get("status"),
        "pdf_url": fields.get("pdf_url"),
        "total_chunks": fields.get("total_chunks"),
        "total_pages": fields.get("total_pages"),
        "upload_date": fields.get("upload_date"),
        "error_message": fields.get("error_message"),
    }


# --- Chunks ---


def get_chunks_by_document(doc_record_id: str) -> list[dict]:
    """Get all chunks for a document, ordered by sequence_number."""
    records = []
    offset = None

    # Fetch all chunks and filter by doc_id in Python
    # (Airtable linked record formulas are complex)
    while True:
        params = {
            "sort[0][field]": "sequence_number",
            "sort[0][direction]": "asc",
        }
        if offset:
            params["offset"] = offset

        data = _request("GET", config.AIRTABLE_CHUNKS_TABLE_ID, params=params)
        for r in data.get("records", []):
            # doc_id is a linked record array like ['recXXX']
            if doc_record_id in r.get("fields", {}).get("doc_id", []):
                records.append(r)

        offset = data.get("offset")
        if not offset:
            break

    return [_format_chunk(r) for r in records]


def create_chunks(chunks: list[dict]) -> list[dict]:
    """Create chunks in batches of 10. Returns created chunks."""
    created = []

    for i in range(0, len(chunks), 10):
        batch = chunks[i : i + 10]
        payload = {"records": [{"fields": c} for c in batch]}
        data = _request("POST", config.AIRTABLE_CHUNKS_TABLE_ID, json=payload)
        created.extend([_format_chunk(r) for r in data.get("records", [])])

    return created


def delete_chunks_by_document(doc_record_id: str) -> int:
    """Delete all chunks for a document. Returns count deleted."""
    # First get all chunk record IDs
    chunks = get_chunks_by_document(doc_record_id)
    record_ids = [c["record_id"] for c in chunks]

    # Delete in batches of 10
    for i in range(0, len(record_ids), 10):
        batch = record_ids[i : i + 10]
        params = "&".join([f"records[]={rid}" for rid in batch])
        _request("DELETE", f"{config.AIRTABLE_CHUNKS_TABLE_ID}?{params}")

    return len(record_ids)


def _format_chunk(record: dict) -> dict:
    """Convert Airtable record to API response format."""
    fields = record.get("fields", {})
    return {
        "record_id": record["id"],
        "chunk_id": fields.get("chunk_id"),  # If using auto-number
        "doc_id": fields.get("doc_id", []),  # Linked record IDs
        "sequence_number": fields.get("sequence_number"),
        "chunk_type": fields.get("chunk_type"),
        "content_raw": fields.get("content_raw"),
        "content_summary": fields.get("content_summary"),
        "image_url": fields.get("image_url"),
        "heading_path": fields.get("heading_path"),
        "token_count": fields.get("token_count"),
        "source_pages": fields.get("source_pages"),
    }
