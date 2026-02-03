# Query Pipeline

When a user asks a question, the backend runs this pipeline synchronously.

---

## Step Q1: Load All Summaries

Load all chunks from Airtable where the parent document status is "ready".

**Fields to load:**
- `chunk_id`
- `doc_id`
- `sequence_number`
- `chunk_type`
- `content_summary`
- `heading_path`
- `token_count`

**Caching:** This data should be cached in memory and refreshed only when documents are added or removed.

---

## Step Q2: Route (GPT-4o-mini)

Send ALL summaries to GPT-4o-mini to identify which chunks need raw content.

- Prompt: [`docs/prompts/routing.md`](prompts/routing.md)
- Returns array of chunk IDs that should be retrieved at full resolution

**Large Corpus Handling:**
- If total summary tokens exceed 80k, split into batches of ~50k tokens
- Process batches **in parallel**
- Merge results (union of all returned chunk IDs)

---

## Step Q3: Assemble Context

Build the context window for the answering model using variable-resolution retrieval.

### Resolution Strategy

| Chunk Type | Condition | Content Used |
|------------|-----------|--------------|
| Selected by router | Any | `content_raw` (full text) |
| Not selected | Any | `content_summary` (summary only) |

### Assembly Format

```
=== DOCUMENT: {doc_name} ===

[Chunk {seq}] ({heading_path})
{content_raw OR content_summary}

[Chunk {seq+1}] ({heading_path})
...
```

### Markers

- **Raw chunks**: Include content as-is
- **Summary chunks**: Prefix with `[SUMMARY] `
- **Graphic chunks with images**: Append `[IMAGE AVAILABLE: {image_url}]`

### Ordering

1. Group by document
2. Within each document, order by `sequence_number`

---

## Step Q4: Answer (Configurable Model)

Generate the final answer using the selected model.

- Prompt: [`docs/prompts/answering.md`](prompts/answering.md)
- Default model: GPT-4o
- Supported models: `gpt-4o`, `gpt-4o-mini`, `gemini-3`

The model receives:
- Conversation history (last 10 exchanges)
- Current question
- Assembled context (mixed raw + summary)

---

## Step Q5: Return Response

Return answer and source attributions to the frontend.

**Response Format:**
```json
{
  "answer": "Based on the documents...",
  "sources": [
    {
      "doc_name": "document.pdf",
      "chunk_sequence": 15,
      "heading_path": "Chapter 3 > Overview"
    }
  ]
}
```

---

## Session Memory

The frontend maintains `conversation_history` as an array:

```typescript
interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
```

- **Last 10 exchanges** are passed to the backend with each query
- History is included in both **routing** and **answering** prompts
- Enables follow-up questions and contextual understanding

---

## Variable-Resolution Retrieval

The key insight of this system is that it provides **full document context** while focusing detail where it matters:

1. **Router sees summaries of everything** - Can identify relevant sections across entire corpus
2. **Selected chunks get full text** - Detailed information for answering
3. **Other chunks remain as summaries** - Answering model knows what topics exist elsewhere
4. **Model can indicate gaps** - If answer is in a summary-only section, model says so

This avoids the "lost in the middle" problem of traditional RAG while maintaining awareness of the full document structure.
