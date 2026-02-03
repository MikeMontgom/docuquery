from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

from services import airtable
from query import router as query_router, assembler, answerer
import config

router = APIRouter(prefix="/api", tags=["query"])


def _load_all_chunks() -> list[dict]:
    """Load all chunks directly from Airtable (workaround for linked record filter issues)."""
    records = []
    offset = None
    url = f"https://api.airtable.com/v0/{config.AIRTABLE_BASE_ID}/{config.AIRTABLE_CHUNKS_TABLE_ID}"
    headers = {
        "Authorization": f"Bearer {config.AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }

    while True:
        params = {
            "sort[0][field]": "sequence_number",
            "sort[0][direction]": "asc",
        }
        if offset:
            params["offset"] = offset

        response = httpx.get(url, headers=headers, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        for r in data.get("records", []):
            fields = r.get("fields", {})
            records.append({
                "record_id": r["id"],
                "doc_id": fields.get("doc_id", []),
                "sequence_number": fields.get("sequence_number"),
                "chunk_type": fields.get("chunk_type"),
                "content_raw": fields.get("content_raw"),
                "content_summary": fields.get("content_summary"),
                "image_url": fields.get("image_url"),
                "heading_path": fields.get("heading_path"),
                "token_count": fields.get("token_count"),
                "source_pages": fields.get("source_pages"),
            })

        offset = data.get("offset")
        if not offset:
            break

    return records


class QueryRequest(BaseModel):
    question: str
    conversation_history: list[dict] = []
    model: str = "gpt-4o"


class Source(BaseModel):
    doc_name: str
    doc_id: str
    chunk_sequence: int
    heading_path: str | None = None
    source_pages: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Ask a question about the uploaded documents."""
    # Validate model
    if request.model not in ["gpt-4o", "gpt-4o-mini", "gemini-3"]:
        raise HTTPException(status_code=400, detail=f"Unsupported model: {request.model}")

    # Step Q1: Load all chunks from ready documents
    docs = airtable.list_documents()
    ready_docs = {d["record_id"]: d["name"] for d in docs if d.get("status") == "ready"}

    if not ready_docs:
        return QueryResponse(
            answer="No documents have been processed yet. Please upload a document first.",
            sources=[],
        )

    # Load all chunks directly (workaround for linked record filter issues)
    all_chunks = _load_all_chunks()

    if not all_chunks:
        return QueryResponse(
            answer="No content available in the processed documents.",
            sources=[],
        )

    # Step Q2: Route question to identify relevant chunks
    selected_ids = query_router.route_question(
        request.question,
        request.conversation_history,
        all_chunks,
    )

    # Step Q3: Assemble context
    context, sources = assembler.assemble_context(
        all_chunks,
        set(selected_ids),
        ready_docs,
    )

    # Step Q4: Generate answer
    answer = answerer.generate_answer(
        request.question,
        request.conversation_history,
        context,
        request.model,
    )

    return QueryResponse(
        answer=answer,
        sources=[Source(**s) for s in sources],
    )
