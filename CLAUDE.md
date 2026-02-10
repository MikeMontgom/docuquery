# DocuQuery RAG System

PDF document question-answering system using variable-resolution retrieval.

## Tech Stack
- **Backend**: Python 3.12+ / FastAPI (Railway)
- **Frontend**: React 19 / Vite (Vercel)
- **Database**: Airtable (REST API)
- **Storage**: Google Cloud Storage
- **LLMs**: Gemini 3, GPT-4o, GPT-4o-mini

## Architecture

```
┌─────────────────┐     REST API      ┌─────────────────┐
│  React/Vite UI  │◄────────────────►│  FastAPI Backend │
│    (Vercel)     │                   │    (Railway)     │
└─────────────────┘                   └────────┬────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
            ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
            │     GCS      │          │   Airtable   │          │   LLM APIs   │
            │  PDFs/Images │          │ Chunks/Docs  │          │ Gemini/GPT   │
            └──────────────┘          └──────────────┘          └──────────────┘
```

## Key Conventions

- **MVP focus**: No over-engineering. Single user, no auth.
- **Prompts**: Stored in `docs/prompts/` - use exactly as written.
- **Airtable**: Use REST API directly, not SDK. Batch writes (10 records max).
- **No embeddings**: Routing is LLM-based, not vector-based.

## Model Assignments

| Task | Model | Notes |
|------|-------|-------|
| Extraction (OCR) | Gemini 3 | 5-page batches |
| Break Scoring | GPT-4o | Full document |
| Summarization | GPT-4o | 10 concurrent |
| Routing | GPT-4o-mini | All summaries |
| Answering | Configurable | Default: GPT-4o |

## Build Order

All MVP features complete and deployed:

- [x] 1. Project skeleton (FastAPI, config, health endpoint)
- [x] 2. Airtable service (CRUD for Documents/Chunks)
- [x] 3. GCS service (upload/delete files)
- [x] 4. Document upload endpoint
- [x] 5. Gemini extraction (`pipeline/extract.py`)
- [x] 6. Break scoring (`pipeline/breaks.py`)
- [x] 7. Deterministic cleanup (`pipeline/cleanup.py`)
- [x] 8. DP chunking (`pipeline/chunk.py`)
- [x] 9. Image cropping (`pipeline/images.py`)
- [x] 10. Pipeline orchestrator
- [x] 11. Summarization (`pipeline/summarize.py`)
- [x] 12. Query engine (router, assembler, answerer)
- [x] 13. Document management endpoints (list, rename, delete)
- [x] 14. PDF viewer feature (citation click → opens PDF at page)
- [x] 15. Deployment (Railway backend, Vercel frontend)
- [x] 16. E2E behavior test suite (61 Playwright tests, 60/61 passing)

## Quick Reference

```bash
# Run backend
uvicorn main:app --reload

# Run frontend
cd frontend && npm run dev

# Run E2E tests (against production)
npx playwright test

# Run specific test category
npx playwright test tests/e2e/behaviors/api.spec.ts
```

## Documentation

- [Architecture Details](docs/architecture.md)
- [API Contract](docs/api.md)
- [Airtable Schema](docs/airtable-schema.md)
- [Processing Pipeline](docs/processing-pipeline.md)
- [Query Pipeline](docs/query-pipeline.md)
- [Behavior Specs](docs/BEHAVIORS.md)
- [Prompts](docs/prompts/)

## Skills & Agent Context

### Skills (Slash Commands
- `/provision-credentials` — Interactive credential setup for Airtable, GCS, Gemini, OpenAI

### Task Agent Context
When spawning Task agents for specific domains, include relevant context from:
- [Airtable Operations](docs/agents/airtable-operations.md) — Schema setup, validation, batch writes

### Deferred (Post-MVP)
- [Quality Testing Framework](docs/future/quality-testing.md) — Automated QA for pipeline stages
- SQLite migration (replace Airtable as data store)

## Deployment Status

**Status: ✅ LIVE AND VERIFIED (2026-02-09)**

### GitHub
- **Repo**: MikeMontgom/docuquery

### Railway (Backend)
- **Project**: extraordinary-unity
- **Service**: web
- **URL**: https://web-production-1485e.up.railway.app
- **Status**: ✅ DEPLOYED AND RUNNING
- **CORS**: `FRONTEND_URL` = `https://docuquery-six.vercel.app`
- Health check: `curl https://web-production-1485e.up.railway.app/health` → `{"status":"ok"}`

### Vercel (Frontend)
- **URL**: https://docuquery-six.vercel.app
- **Status**: ✅ DEPLOYED AND CONNECTED
- **Env**: `VITE_API_URL` = `https://web-production-1485e.up.railway.app`

### E2E Test Results
- **60/61 passing** (1 skipped: no error-status documents to test)
- 0 failures, 0 flaky
- Full coverage: API, deployment, navigation, input, actions, display, errors, edge cases
- Run with: `npx playwright test`

### Railway Project Cleanup (2026-02-09)
- **extraordinary-unity**: DocuQuery backend (ACTIVE)
- ~~miraculous-victory~~: Deleted (was empty, no services)
- ~~joyful-youth~~: Deleted (was crashed duplicate, missing GEMINI_API_KEY)

## Known Issues / Suspended Features

### PDF Page Extraction (DISABLED)
- `images.save_all_pages()` in `pipeline/orchestrator.py` is disabled (commented out)
- **Reason**: pdfplumber causes Python SIGTRAP crash on some PDFs
- **Impact**: Individual page images are NOT saved to GCS
- **Workaround**: PDF viewer popup uses signed URL to full PDF (works fine)
- **Decision needed**: May remove entirely if PDF popup viewer is sufficient

### Airtable Linked Record Filtering
- `get_chunks_by_document()` cannot use Airtable formula for linked records
- Workaround: Fetches all chunks and filters in Python (works but less efficient)
- Will be resolved when migrating to SQLite
