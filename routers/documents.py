from datetime import date
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks

from services import airtable, gcs
from pipeline.orchestrator import process_document

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload a PDF document for processing."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # Count pages using pypdf
    from io import BytesIO
    from pypdf import PdfReader

    try:
        reader = PdfReader(BytesIO(content))
        total_pages = len(reader.pages)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    # Create document record first to get record_id
    doc = airtable.create_document({
        "name": file.filename,
        "status": "uploading",
        "total_pages": total_pages,
        "upload_date": date.today().isoformat(),
    })

    # Upload PDF to GCS using record_id as doc_id
    pdf_url = gcs.upload_pdf(doc["record_id"], file.filename, content)

    # Update document with PDF URL
    doc = airtable.update_document(doc["record_id"], {"pdf_url": pdf_url})

    # Start async processing pipeline
    background_tasks.add_task(process_document, doc["record_id"])

    return {
        "doc_id": doc["record_id"],
        "name": doc["name"],
        "status": doc["status"],
    }


@router.get("")
async def list_documents():
    """List all documents."""
    docs = airtable.list_documents()
    return [
        {
            "doc_id": d["record_id"],
            "name": d["name"],
            "status": d["status"],
            "total_chunks": d["total_chunks"],
            "total_pages": d["total_pages"],
            "upload_date": d["upload_date"],
        }
        for d in docs
    ]


@router.patch("/{doc_id}")
async def rename_document(doc_id: str, body: dict):
    """Rename a document and update NEW DOCUMENT marker in first chunk."""
    if "name" not in body:
        raise HTTPException(status_code=400, detail="Missing 'name' field")

    doc = airtable.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    old_name = doc["name"]
    new_name = body["name"]

    # Update document record
    updated = airtable.update_document(doc_id, {"name": new_name})

    # Update NEW DOCUMENT marker in first chunk if it exists
    chunks = airtable.get_chunks_by_document(doc_id)
    if chunks:
        first_chunk = min(chunks, key=lambda c: c["sequence_number"])
        content = first_chunk.get("content_raw", "")
        old_marker = f"=== NEW DOCUMENT: {old_name} ==="
        new_marker = f"=== NEW DOCUMENT: {new_name} ==="
        if old_marker in content:
            new_content = content.replace(old_marker, new_marker, 1)
            airtable._request(
                "PATCH",
                f"{airtable.config.AIRTABLE_CHUNKS_TABLE_ID}/{first_chunk['record_id']}",
                json={"fields": {"content_raw": new_content}},
            )

    return {
        "doc_id": updated["record_id"],
        "name": updated["name"],
        "status": updated["status"],
    }


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and all associated data."""
    doc = airtable.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete chunks from Airtable
    airtable.delete_chunks_by_document(doc_id)

    # Delete files from GCS
    gcs.delete_document_files(doc_id)

    # Delete document record
    airtable.delete_document(doc_id)

    return {"success": True}


@router.get("/{doc_id}/pdf")
async def get_pdf(doc_id: str):
    """Get a signed URL for the document PDF."""
    doc = airtable.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    url = gcs.get_pdf_url(doc_id)
    if not url:
        raise HTTPException(status_code=404, detail="PDF not found")

    return {"url": url, "name": doc["name"], "total_pages": doc["total_pages"]}


@router.get("/{doc_id}/page/{page_num}/image")
async def get_page_image(doc_id: str, page_num: int):
    """Get a signed URL for a page image preview."""
    doc = airtable.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    url = gcs.get_page_image_url(doc_id, page_num)
    if not url:
        raise HTTPException(status_code=404, detail="Page image not found")

    return {"url": url}
