"""
Pipeline Orchestrator

Coordinates the full document processing pipeline:
1. Extraction (Gemini)
2. Break scoring (GPT-4o)
3. Cleanup (deterministic)
4. Chunking (DP)
5. Image cropping (pdfplumber)
6. Write to Airtable
7. Summarization (GPT-4o)
8. Update document status
"""

from services import airtable, gcs
from pipeline import extract, breaks, cleanup, chunk, images, summarize


def process_document(doc_record_id: str) -> None:
    """
    Process a document through the full pipeline.

    Args:
        doc_record_id: Airtable record ID of the document
    """
    try:
        # Get document record
        doc = airtable.get_document(doc_record_id)
        if not doc:
            raise ValueError(f"Document not found: {doc_record_id}")

        # Download PDF from GCS
        pdf_url = doc["pdf_url"]
        if not pdf_url:
            raise ValueError("Document has no PDF URL")

        # Extract filename from URL
        # URL format: gs://bucket/pdfs/{doc_id}/{filename}
        filename = pdf_url.split("/")[-1]
        pdf_content = gcs.download_pdf(doc_record_id, filename)

        # Step 1: Extract text using Gemini
        extracted_text = extract.extract_pdf(pdf_content)

        # Step 2: Score breaks using GPT-4o
        text_with_breaks = breaks.score_breaks(extracted_text)

        # Step 3: Cleanup (deterministic)
        cleaned_text, page_mapping = cleanup.cleanup(text_with_breaks)

        # Step 4: Chunk using DP
        chunks = chunk.chunk_text(cleaned_text, page_mapping)

        if not chunks:
            raise ValueError("No chunks generated from document")

        # Step 5a: DISABLED - save_all_pages crashes pdfplumber on some PDFs
        # TODO: May remove entirely if PDF popup viewer is sufficient
        # images.save_all_pages(doc_record_id, pdf_content)

        # Step 5b: Crop images for graphic chunks
        image_urls = images.process_all_graphics(doc_record_id, pdf_content, chunks)

        # Step 6: Write chunks to Airtable
        doc_name = doc["name"]
        chunk_records = []
        for i, c in enumerate(chunks):
            content = c.content_raw
            # Add NEW DOCUMENT marker to first chunk for multi-doc clarity
            if i == 0:
                content = f"=== NEW DOCUMENT: {doc_name} ===\n\n{content}"

            record = {
                "doc_id": [doc_record_id],  # Linked record field
                "sequence_number": c.sequence_number,
                "chunk_type": c.chunk_type,
                "content_raw": content,
                "heading_path": c.heading_path,
                "token_count": c.token_count,
                "source_pages": c.source_pages,
            }
            # Add image URL if this is a graphic chunk
            if c.sequence_number in image_urls:
                record["image_url"] = image_urls[c.sequence_number]

            chunk_records.append(record)

        created_chunks = airtable.create_chunks(chunk_records)

        # Step 7: Summarize chunks
        summaries = summarize.summarize_all(chunks)

        # Update chunks with summaries
        # Map sequence_number to record_id
        seq_to_record = {c["sequence_number"]: c["record_id"] for c in created_chunks}

        for seq_num, summary in summaries.items():
            if seq_num in seq_to_record:
                record_id = seq_to_record[seq_num]
                # Update chunk with summary
                airtable._request(
                    "PATCH",
                    f"{airtable.config.AIRTABLE_CHUNKS_TABLE_ID}/{record_id}",
                    json={"fields": {"content_summary": summary}},
                )

        # Step 8: Update document status
        airtable.update_document(
            doc_record_id,
            {
                "status": "ready",
                "total_chunks": len(chunks),
            },
        )

    except Exception as e:
        # Mark document as error
        try:
            airtable.update_document(
                doc_record_id,
                {
                    "status": "error",
                    "error_message": str(e)[:1000],  # Truncate long errors
                },
            )
        except Exception:
            pass  # Best effort error recording

        raise
