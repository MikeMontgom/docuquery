# Session Progress

## Last Updated
2025-02-02

## Current Task
End-to-end testing with second document

## Just Completed
- Added retry logic with exponential backoff to extract.py and breaks.py
  - extract.py: 3 retries, 10/20/30s backoff for Gemini rate limits
  - breaks.py: 3 retries, 10/20/30s backoff for GPT-4o rate limits
  - (summarize.py already had this)
- Image handling improvements:
  - Added full-page fallback when cropping fails (images.py)
  - Added save_all_pages() to save every page as image for citation previews
  - Added API endpoint GET /api/documents/{doc_id}/page/{page_num}/image
- Added "=== NEW DOCUMENT: {name} ===" marker to first chunk (orchestrator.py)
- First successful end-to-end test with 46-page PDF (Python-Tutorial-ML-DataScience.pdf)
  - 52 chunks created, querying works
- Items 1-13 of build order all complete:
  - Project skeleton (FastAPI, config, health endpoint)
  - Airtable service (CRUD for Documents/Chunks)
  - GCS service (upload/delete files)
  - Document upload endpoint
  - Gemini extraction (`pipeline/extract.py`)
  - Break scoring (`pipeline/breaks.py`)
  - Deterministic cleanup (`pipeline/cleanup.py`)
  - DP chunking (`pipeline/chunk.py`)
  - Image cropping (`pipeline/images.py`)
  - Pipeline orchestrator
  - Summarization (`pipeline/summarize.py`)
  - Query engine (router, assembler, answerer)
  - Document management endpoints (list, rename, delete)

## Next Steps
1. Set up testing infrastructure (pytest, fixtures)
2. Write end-to-end tests for document endpoints
3. Write end-to-end tests for query endpoint
4. Manual testing with real PDF

## Blockers / Decisions Made
- None currently

## Active Errors / Issues
- None known

## Key Context
- Backend: Python/FastAPI on Railway
- Frontend: React 19/Vite on Vercel
- Database: Airtable (REST API, not SDK)
- Storage: Google Cloud Storage
- LLMs: Gemini for extraction, GPT-4o for breaks/summarization/answering, GPT-4o-mini for routing
- No authentication (single user MVP)
- No embeddings (LLM-based routing instead)

## File Structure Reference
```
├── main.py                 # FastAPI app entry
├── config.py               # Environment config
├── routers/
│   ├── documents.py        # Upload, list, rename, delete
│   └── query.py            # Query endpoint
├── services/
│   ├── airtable.py         # Airtable CRUD
│   └── gcs.py              # GCS file ops
├── pipeline/
│   ├── extract.py          # Gemini PDF extraction
│   ├── breaks.py           # GPT-4o break scoring
│   ├── cleanup.py          # Deterministic cleanup
│   ├── chunk.py            # DP chunking algorithm
│   ├── images.py           # Image cropping
│   ├── summarize.py        # GPT-4o summarization
│   └── orchestrator.py     # Pipeline coordinator
├── query/
│   ├── router.py           # GPT-4o-mini chunk routing
│   ├── assembler.py        # Context assembly
│   └── answerer.py         # Answer generation
└── frontend/
    ├── App.tsx             # Main React app
    ├── components/         # UI components
    └── services/api.ts     # API client
```
