# Airtable Operations — Task Agent Context

Reference documentation for Task agents handling Airtable schema setup, validation, and data operations.

## When to Use

Provide this context to a Task agent (via `subagent_type: general-purpose`) when:
- Creating or modifying Airtable tables
- Validating schema matches spec
- Batch writing records
- Debugging Airtable API issues
- Verifying data integrity after pipeline writes

## API Fundamentals

```
Base URL: https://api.airtable.com/v0/{base_id}/{table_name_or_id}
Auth: Bearer token in Authorization header
Rate limit: 5 requests/second — MUST enforce this
Batch limit: 10 records per create/update request
Long text limit: 100,000 characters per field
```

### Standard Headers
```python
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
```

### Environment Variables
```
AIRTABLE_API_KEY          — Personal access token (pat...)
AIRTABLE_BASE_ID          — Base ID (app...)
AIRTABLE_DOCUMENTS_TABLE_ID  — Documents table ID (tbl...)
AIRTABLE_CHUNKS_TABLE_ID     — Chunks table ID (tbl...)
```

Read from `config.py` or `.env`. Never hardcode.

---

## Project Schema

### Table: Documents

| Field | Type | Description | Notes |
|-------|------|-------------|-------|
| doc_id | Auto Number | Primary key | Auto-generated, read-only |
| name | Single Line Text | Display name | Initially filename without extension |
| status | Single Select | Processing state | Options: uploading, ready, error |
| pdf_url | URL | GCS link to original PDF | |
| total_chunks | Number | Chunk count after processing | Set on completion |
| total_pages | Number | Page count of PDF | Set on upload |
| upload_date | Date | When uploaded | |
| error_message | Long Text | Error details | Only when status=error |

### Table: Chunks

| Field | Type | Description | Notes |
|-------|------|-------------|-------|
| chunk_id | Auto Number | Primary key | Auto-generated, read-only |
| doc_id | Link to Documents | Parent document | Linked record field |
| sequence_number | Number | 1-indexed order | Within parent document |
| chunk_type | Single Select | Content type | Options: text, graphic |
| content_raw | Long Text | Raw content | Text or GRAPHIC_INSERT JSON |
| content_summary | Long Text | Functional summary | For routing |
| image_url | URL | GCS cropped image URL | Graphic chunks only |
| heading_path | Single Line Text | Section breadcrumb | e.g. "Ch 9 > 9.2 > Linear Regression" |
| token_count | Number | Approximate tokens | word_count * 1.3 |
| source_pages | Single Line Text | PDF page range | e.g. "21-23" |

---

## Operations

### 1. Schema Setup

Create tables matching the spec above. For each table:
- Verify it doesn't already exist before creating
- Create fields with correct types and options
- For Single Select fields, pre-populate option values
- For Link fields, verify the target table exists first

### 2. Schema Validation

Compare existing tables against the spec:
- List all fields and their types
- Flag missing fields, wrong types, missing select options
- Report extra fields (noted, not necessarily wrong)
- Verify linked record relationships

Validation output format:
```
TABLE: {name}
  [OK] field_name (type) — matches spec
  [MISSING] field_name
  [WRONG TYPE] field_name — expected {X}, got {Y}
  [EXTRA] field_name (type) — not in spec
```

### 3. Batch Write Operations

Always batch in groups of 10:
```python
for i in range(0, len(records), 10):
    batch = records[i:i+10]
    payload = {"records": [{"fields": r} for r in batch]}
    response = requests.post(url, headers=headers, json=payload)
    time.sleep(0.2)  # Rate limiting: 5 req/sec
```

Report progress:
```
Writing chunks: batch 1/12 (records 1-10)... OK
Writing chunks: batch 2/12 (records 11-20)... OK
```

### 4. Data Integrity Checks

After pipeline writes, verify:
- All chunks for a document have sequential sequence_numbers (1 to N, no gaps)
- Every chunk has non-empty content_raw
- Every chunk has non-empty content_summary (after summarization)
- Graphic chunks have image_url populated
- Token counts are within expected range (200-1200)
- Document total_chunks matches actual chunk count
- Document status is "ready" (not stuck on "uploading")

### 5. Cleanup Operations

When a document is deleted:
- Delete all chunks where doc_id matches
- Delete the document record
- NOTE: GCS file deletion is NOT handled here — flag for main agent

When cleaning up failed processing:
- Find documents with status "error" or "uploading" older than 1 hour
- List their chunk counts (may have partial data)
- Report but do not delete without explicit approval

---

## Rate Limiting

CRITICAL: Airtable enforces 5 requests/second.

```python
import time

class AirtableRateLimiter:
    def __init__(self, requests_per_second=5):
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0

    def wait(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()
```

---

## Error Handling

| Status | Meaning | Action |
|--------|---------|--------|
| 401 | Invalid API key | Check AIRTABLE_API_KEY env var |
| 403 | No access to base | Check AIRTABLE_BASE_ID, verify token scopes |
| 404 | Table/record not found | Verify table ID, check for typos |
| 422 | Invalid request | Check field names, types, select option values |
| 429 | Rate limited | Back off 30 seconds, retry with slower rate |
| 500+ | Airtable server error | Retry after 5 seconds, max 3 attempts |

For 422 errors, read the full error message:
```json
{
  "error": {
    "type": "INVALID_REQUEST_UNKNOWN",
    "message": "Field 'status' has value 'processing' which is not an allowed option"
  }
}
```

---

## Linked Record Fields

The doc_id field in Chunks is a linked record field. When creating chunks:
```python
# doc_id must be an array of Airtable record IDs (not the auto-number)
fields = {
    "doc_id": ["recABC123"],  # Array of record IDs
    "sequence_number": 1,
    "chunk_type": "text",
    # ...
}
```

To get the record ID of a document, query the Documents table and use the `id` field from the response (not `doc_id` which is auto-number).

---

## Scope Boundaries

This context covers:
- Schema setup and validation
- Data operations (CRUD)
- Integrity checks

This context does NOT cover:
- Writing pipeline processing code
- Modifying the application's airtable.py service module
- Deployment
- GCS operations
- Schema design decisions (implement as specified, flag concerns)

If the schema spec seems wrong, report clearly:
> "Potential issue: {field} is typed as {X} but the pipeline writes {Y} to it. This may cause {Z}. Recommend changing to {type}."
