# Processing Pipeline

When a PDF is uploaded, the backend runs this pipeline asynchronously. The document status is `uploading` during processing, then `ready` on success or `error` on failure.

---

## Step 1: PDF Upload and Split

1. Save the uploaded PDF to GCS at `pdfs/{doc_id}/{filename}`
2. Use pypdf to count total pages
3. Split into batches of 5 pages each (final batch may be shorter)

---

## Step 2: Extraction (Gemini 3)

For each 5-page batch, send the PDF pages to Gemini 3 with the extraction prompt.

- Prompt: [`docs/prompts/extraction.md`](prompts/extraction.md)
- Process batches **sequentially** (each batch waits for previous)
- Append all batch results into a single master text string
- Preserve `[PAGE X]` markers

**Important:** The extraction prompt deliberately omits break markers. Breaks are handled in Step 3.

---

## Step 3: Break Scoring (GPT-4o)

Send the full master text to GPT-4o for break marker insertion.

- Prompt: [`docs/prompts/break-scoring.md`](prompts/break-scoring.md)
- GPT-4o receives **text only** (not the PDF)
- Single call for documents under 100k tokens
- For larger documents: split into ~80k token segments with 5k overlap
  - Process segments sequentially
  - On overlapping regions, prefer breaks from the segment with the region in its middle

---

## Step 4: Deterministic Cleanup (No LLM)

Apply these operations to the master text, in order:

1. **Record source page mapping** - Before removing markers, record which character ranges correspond to which pages (for `source_pages` field)

2. **Remove `[PAGE X]` markers** - Regex: `\[PAGE \d+\]`

3. **Remove code block UI artifacts** - Exact string removal:
   - `content_copy`
   - `expand_less`
   - `expand_more`
   - `code `
   - `Python\n`
   - `JavaScript\n`

   (When they appear on the line immediately before or after a code fence)

4. **Resequence break IDs** - Parse all `[BREAK id=X score=Y]`, renumber sequentially from 1 while preserving scores

**Do NOT:**
- Remove or modify headers/footers (too risky)
- Fix encoding (may mangle valid Unicode)
- Modify any text content

---

## Step 5: Dynamic Programming Chunking (No LLM)

Split the cleaned master text into chunks using dynamic programming.

### Constants

```python
TARGET_CHUNK_TOKENS = 650   # Target chunk size
MIN_CHUNK_TOKENS = 200      # Never create chunks smaller than this
MAX_CHUNK_TOKENS = 1200     # Never create chunks larger than this
TOKEN_ESTIMATE_FACTOR = 1.3 # Multiply word count by this for token estimate
```

### Rules (Priority Order)

1. **GRAPHIC_INSERT blocks are always their own chunk**
   - Parse `%%% GRAPHIC_INSERT %%% ... %%% END_GRAPHIC_INSERT %%%` as complete units
   - These become `chunk_type: "graphic"`

2. **TABLE_START blocks are their own chunk** if they would make the containing chunk exceed MAX_CHUNK_TOKENS

3. **All remaining text splits at break markers only**
   - Never split mid-sentence or at arbitrary positions

### DP Objective

Minimize total cost across all chunks:

```
cost(chunk) = α × (token_count - TARGET)² + β × (100 - entry_break_score)
```

- `α = 1.0` (penalize deviation from target size)
- `β = 50.0` (penalize splitting at weak breaks)
- `entry_break_score` = score of break marker at START of chunk

### Output

Ordered list of chunks, each with:
- Text content
- `chunk_type` ("text" or "graphic")
- Sequence number (1-indexed)
- Approximate token count
- Source page range

---

## Step 6: Image Cropping (pdfplumber)

For each graphic chunk:

1. Parse the GRAPHIC_INSERT JSON from chunk content
2. Open original PDF with pdfplumber
3. Navigate to specified page
4. Crop at specified coordinates (render at 300 DPI)
5. Save as PNG
6. Upload to GCS at `images/{doc_id}/{graphic_id}.png`
7. Store GCS URL in chunk's `image_url` field

**Coordinate Conversion:**
- Extraction uses 72 DPI coordinates (PDF points)
- pdfplumber uses same coordinate system
- When rendering to 300 DPI: multiply coordinates by `300/72 = 4.167`

---

## Step 7: Write Chunks to Airtable

Write all chunks to the Chunks table:

| Field | Source |
|-------|--------|
| `content_raw` | Text content (stripped of break markers) or full GRAPHIC_INSERT JSON |
| `chunk_type` | "text" or "graphic" |
| `sequence_number` | 1-indexed order |
| `token_count` | `word_count × 1.3` |
| `source_pages` | From page mapping in Step 4 |
| `heading_path` | Most recent section headings before this chunk |
| `image_url` | GCS URL for graphic chunks |

---

## Step 8: Summarization (GPT-4o)

Generate functional summaries for each chunk.

- Prompt: [`docs/prompts/summarization.md`](prompts/summarization.md)
- **Graphic chunks**: Copy `description` field from GRAPHIC_INSERT JSON directly (no LLM call)
- **Text chunks**: Send to GPT-4o with summarization prompt
- Process **10 concurrent requests**

---

## Step 9: Update Document Status

After all chunks are written and summarized:

**Success:**
```python
document.status = "ready"
document.total_chunks = len(chunks)
```

**Failure:**
```python
document.status = "error"
document.error_message = str(exception)
```

---

## Error Handling

- **Gemini extraction fails**: Retry once. If fails again, mark document as error and stop.
- **Malformed LLM output**: Retry once with same prompt.
- **Any unhandled error**: Set document `status` to "error" with exception message.

---

## Performance Notes

| Step | Concurrency |
|------|-------------|
| Gemini extraction | Sequential (5-page batches) |
| Break scoring | Single call (or sequential segments) |
| Summarization | 10 concurrent |
| Image cropping | 5 concurrent |
