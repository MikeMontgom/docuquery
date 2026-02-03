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

Build and test each step before moving on:

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
- [ ] 14. End-to-end testing

## Quick Reference

```bash
# Run backend
uvicorn main:app --reload

# Run frontend
cd frontend && npm run dev
```

## Documentation

- [Architecture Details](docs/architecture.md)
- [API Contract](docs/api.md)
- [Airtable Schema](docs/airtable-schema.md)
- [Processing Pipeline](docs/processing-pipeline.md)
- [Query Pipeline](docs/query-pipeline.md)
- [Prompts](docs/prompts/)

## Skills & Agent Context

### Skills (Slash Commands
- `/provision-credentials` — Interactive credential setup for Airtable, GCS, Gemini, OpenAI

### Task Agent Context
When spawning Task agents for specific domains, include relevant context from:
- [Airtable Operations](docs/agents/airtable-operations.md) — Schema setup, validation, batch writes

### Deferred (Post-MVP)
- [Quality Testing Framework](docs/future/quality-testing.md) — Automated QA for pipeline stages
