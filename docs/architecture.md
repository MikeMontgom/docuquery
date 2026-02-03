# Architecture

## System Overview

DocuQuery is a document question-answering system that uses variable-resolution retrieval. Users upload PDFs, the system processes them into optimized chunks stored in Airtable, and users can ask natural-language questions answered using LLM-based routing.

## Components

### Frontend (React/Vite)
- **Deployment**: Vercel
- **Responsibilities**:
  - PDF upload interface
  - Document management (list, rename, delete)
  - Chat interface for queries
  - Model selection for answering
  - Conversation history (10 exchanges)

### Backend (Python/FastAPI)
- **Deployment**: Railway
- **Responsibilities**:
  - REST API endpoints
  - PDF processing pipeline
  - Query pipeline
  - External service orchestration

### Google Cloud Storage
- **Structure**:
  - `pdfs/{doc_id}/{filename}.pdf` - Original PDFs (private)
  - `images/{doc_id}/{graphic_id}.png` - Cropped images (public read)

### Airtable
- **Tables**: Documents, Chunks
- **Access**: REST API (no SDK)
- **Constraints**:
  - 5 requests/second rate limit
  - 10 records per batch write
  - 100,000 character limit per long text field

### LLM APIs
- **Gemini 3**: PDF extraction (OCR-optimized)
- **GPT-4o**: Break scoring, summarization, answering
- **GPT-4o-mini**: Routing

## Data Flow

### Upload Flow
```
User uploads PDF
    → Save to GCS
    → Create Documents record (status: uploading)
    → Async processing pipeline
    → Update status to ready/error
```

### Processing Pipeline
```
PDF → Split into 5-page batches
    → Gemini 3 extraction
    → GPT-4o break scoring
    → Deterministic cleanup
    → DP chunking
    → Image cropping (pdfplumber)
    → Write chunks to Airtable
    → GPT-4o summarization
```

### Query Flow
```
Question + History
    → Load all summaries
    → GPT-4o-mini routing (identify relevant chunks)
    → Assemble context (raw for selected, summary for rest)
    → Configurable model answering
    → Return answer + sources
```

## Technology Choices

| Choice | Rationale |
|--------|-----------|
| Airtable over Postgres | Rapid prototyping, built-in UI, simple schema |
| LLM routing over embeddings | Better semantic understanding, no vector DB needed |
| Gemini 3 for extraction | OCR-optimized, handles complex layouts |
| GPT-4o for break scoring | Better judgment on semantic boundaries |
| Variable-resolution retrieval | Provides full context while focusing on relevant sections |

## Constraints

- **No authentication**: Single user MVP
- **No embeddings**: LLM-based routing only
- **No additional databases**: Airtable only
- **Prompts are fixed**: Use exactly as documented
