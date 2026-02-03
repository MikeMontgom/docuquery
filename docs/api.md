# API Contract

Base URL: `http://localhost:8000` (development) or Railway deployment URL

## CORS Configuration
- Allowed origins: `FRONTEND_URL` environment variable
- Allowed methods: GET, POST, PATCH, DELETE
- Allowed headers: Content-Type

---

## Document Management

### Upload Document

```
POST /api/documents/upload
Content-Type: multipart/form-data
```

**Request Body:**
- `file`: PDF file (required)

**Response:**
```json
{
  "doc_id": "1",
  "name": "document.pdf",
  "status": "uploading"
}
```

**Behavior:**
1. Saves PDF to GCS at `pdfs/{doc_id}/{filename}`
2. Creates Documents record in Airtable
3. Starts async processing pipeline
4. Returns immediately with `status: "uploading"`

---

### List Documents

```
GET /api/documents
```

**Response:**
```json
[
  {
    "doc_id": "1",
    "name": "document.pdf",
    "status": "ready",
    "total_chunks": 42,
    "total_pages": 15,
    "upload_date": "2024-01-15T10:30:00Z"
  }
]
```

**Behavior:**
- Returns all documents ordered by `upload_date` descending
- Status values: `uploading`, `ready`, `error`

---

### Rename Document

```
PATCH /api/documents/{doc_id}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "new-name.pdf"
}
```

**Response:**
```json
{
  "doc_id": "1",
  "name": "new-name.pdf",
  "status": "ready"
}
```

---

### Delete Document

```
DELETE /api/documents/{doc_id}
```

**Response:**
```json
{
  "success": true
}
```

**Behavior:**
1. Deletes document record from Airtable
2. Deletes all associated chunks from Airtable
3. Deletes PDF from GCS
4. Deletes all images from GCS

---

## Query

### Ask Question

```
POST /api/query
Content-Type: application/json
```

**Request Body:**
```json
{
  "question": "What is the main topic of chapter 3?",
  "conversation_history": [
    { "role": "user", "content": "Previous question" },
    { "role": "assistant", "content": "Previous answer" }
  ],
  "model": "gpt-4o"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | Yes | The user's question |
| `conversation_history` | array | Yes | Last 10 exchanges (can be empty) |
| `model` | string | No | Answering model. Default: `gpt-4o` |

**Supported Models:**
- `gpt-4o` (default)
- `gpt-4o-mini`
- `gemini-3`

**Response:**
```json
{
  "answer": "Chapter 3 discusses...",
  "sources": [
    {
      "doc_name": "document.pdf",
      "chunk_sequence": 15,
      "heading_path": "Chapter 3 > Overview"
    }
  ]
}
```

**Behavior:**
1. Routes question to relevant chunks (GPT-4o-mini)
2. Assembles context (raw for selected chunks, summary for others)
3. Generates answer using selected model
4. Returns answer with source attributions

---

## Health

### Health Check

```
GET /api/health
```

**Response:**
```json
{
  "status": "ok"
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error description"
}
```

**HTTP Status Codes:**
- `400` - Bad request (invalid input)
- `404` - Resource not found
- `500` - Internal server error
