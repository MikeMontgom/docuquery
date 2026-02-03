# Airtable Schema

## Access Configuration

- **Base URL**: `https://api.airtable.com/v0/{base_id}/{table_name}`
- **Authentication**: Bearer token via `AIRTABLE_API_KEY`
- **Rate Limit**: 5 requests per second
- **Batch Size**: Maximum 10 records per create/update request

---

## Table: Documents

Stores metadata for each uploaded PDF.

| Field | Type | Description |
|-------|------|-------------|
| `doc_id` | Auto Number | Primary key |
| `name` | Single Line Text | Display name (initially filename without extension) |
| `status` | Single Select | Processing status |
| `pdf_url` | URL | GCS link to original PDF |
| `total_chunks` | Number | Total chunk count after processing |
| `total_pages` | Number | Page count of original PDF |
| `upload_date` | Date | When uploaded |
| `error_message` | Long Text | Error description if status=error |

**Status Options:**
- `uploading` - Processing in progress
- `ready` - Successfully processed
- `error` - Processing failed

---

## Table: Chunks

Stores processed content chunks with summaries.

| Field | Type | Description |
|-------|------|-------------|
| `chunk_id` | Auto Number | Primary key |
| `doc_id` | Link to Documents | Parent document reference |
| `sequence_number` | Number | 1-indexed order within document |
| `chunk_type` | Single Select | Content type |
| `content_raw` | Long Text | Full extracted content |
| `content_summary` | Long Text | Functional summary for routing |
| `image_url` | URL | GCS link for graphic chunks |
| `heading_path` | Single Line Text | Section breadcrumb |
| `token_count` | Number | Approximate token count |
| `source_pages` | Single Line Text | Original PDF page range |

**Chunk Type Options:**
- `text` - Text content
- `graphic` - Image/chart/diagram (includes GRAPHIC_INSERT JSON)

**Heading Path Example:**
```
"Chapter 9 > 9.2 > Linear Regression"
```

**Source Pages Example:**
```
"21-23"
```

---

## Relationships

```
Documents (1) ──────── (N) Chunks
    │                       │
    └── doc_id ◄──────────── doc_id (Link field)
```

---

## Field Constraints

| Constraint | Value |
|------------|-------|
| Long Text max length | 100,000 characters |
| Single Line Text max length | Unlimited (practical: ~100 chars) |
| Link field | References Documents table |

---

## API Usage Examples

### Create Document Record
```bash
curl -X POST "https://api.airtable.com/v0/{base_id}/Documents" \
  -H "Authorization: Bearer {api_key}" \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {
      "name": "document.pdf",
      "status": "uploading",
      "pdf_url": "https://storage.googleapis.com/...",
      "total_pages": 15,
      "upload_date": "2024-01-15"
    }
  }'
```

### Batch Create Chunks
```bash
curl -X POST "https://api.airtable.com/v0/{base_id}/Chunks" \
  -H "Authorization: Bearer {api_key}" \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {
        "fields": {
          "doc_id": ["rec123"],
          "sequence_number": 1,
          "chunk_type": "text",
          "content_raw": "...",
          "content_summary": "...",
          "heading_path": "Chapter 1",
          "token_count": 650,
          "source_pages": "1-3"
        }
      }
    ]
  }'
```

### Query Chunks by Document
```bash
curl "https://api.airtable.com/v0/{base_id}/Chunks?filterByFormula={doc_id}='rec123'" \
  -H "Authorization: Bearer {api_key}"
```
