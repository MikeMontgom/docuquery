"""
Context Assembler - Step Q3

Builds the context window using variable-resolution retrieval.
"""

from services import airtable


def assemble_context(
    all_chunks: list[dict],
    selected_ids: set[str],
    doc_names: dict[str, str],
) -> tuple[str, list[dict]]:
    """
    Assemble context from chunks using variable resolution.

    Args:
        all_chunks: All chunks with summaries and content
        selected_ids: Set of chunk record IDs selected by router
        doc_names: Dict mapping doc record_id to document name

    Returns:
        Tuple of (assembled_context_string, sources_list)
    """
    # Group chunks by document
    by_doc = {}
    for chunk in all_chunks:
        doc_id = chunk.get("doc_id", [])
        if isinstance(doc_id, list) and doc_id:
            doc_id = doc_id[0]  # Linked record field returns array
        if not doc_id:
            continue

        if doc_id not in by_doc:
            by_doc[doc_id] = []
        by_doc[doc_id].append(chunk)

    # Sort chunks within each document by sequence number
    for doc_id in by_doc:
        by_doc[doc_id].sort(key=lambda c: c.get("sequence_number", 0))

    # Build context string
    context_parts = []
    sources = []

    for doc_id, chunks in by_doc.items():
        doc_name = doc_names.get(doc_id, "Unknown Document")
        context_parts.append(f"=== DOCUMENT: {doc_name} ===\n")

        for chunk in chunks:
            record_id = chunk.get("record_id", "")
            seq_num = chunk.get("sequence_number", 0)
            heading = chunk.get("heading_path", "")
            chunk_type = chunk.get("chunk_type", "text")
            is_selected = record_id in selected_ids

            # Choose content based on selection
            if is_selected:
                content = chunk.get("content_raw", "")
                # Track as source
                sources.append({
                    "doc_name": doc_name,
                    "doc_id": doc_id,
                    "chunk_sequence": seq_num,
                    "heading_path": heading,
                    "source_pages": chunk.get("source_pages"),
                })
            else:
                content = f"[SUMMARY] {chunk.get('content_summary', '')}"

            # Format chunk
            chunk_header = f"[Chunk {seq_num}]"
            if heading:
                chunk_header += f" ({heading})"

            context_parts.append(chunk_header)
            context_parts.append(content)

            # Add image marker for graphic chunks
            if chunk_type == "graphic" and chunk.get("image_url"):
                context_parts.append(f"[IMAGE AVAILABLE: {chunk['image_url']}]")

            context_parts.append("")  # Blank line between chunks

    return "\n".join(context_parts), sources


def load_all_chunks_with_content(selected_ids: set[str]) -> list[dict]:
    """
    Load all chunks, fetching full content for selected ones.

    This is an optimization - we only fetch content_raw for selected chunks.
    """
    # For MVP, just load all chunks with all fields
    # In production, you'd want to optimize this query
    docs = airtable.list_documents()
    ready_docs = [d for d in docs if d.get("status") == "ready"]

    all_chunks = []
    for doc in ready_docs:
        chunks = airtable.get_chunks_by_document(doc["record_id"])
        all_chunks.extend(chunks)

    return all_chunks
