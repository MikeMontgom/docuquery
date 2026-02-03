# DocuQuery RAG System

A document question-answering system that uses variable-resolution retrieval to answer questions about uploaded PDFs.

## Features

- **PDF Upload & Processing**: Upload PDFs and automatically extract, chunk, and index content
- **Smart Retrieval**: LLM-based routing identifies relevant sections without embeddings
- **Variable Resolution**: Full text for relevant chunks, summaries for context
- **Multi-Model Support**: Choose between GPT-4o, GPT-4o-mini, or Gemini 3 for answering
- **Conversation Memory**: Maintains context across 10 exchanges

## Architecture

```
Frontend (React/Vite) ◄──► Backend (FastAPI) ◄──► GCS / Airtable / LLMs
```

See [docs/architecture.md](docs/architecture.md) for details.

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Google Cloud Storage bucket
- Airtable base with Documents and Chunks tables
- API keys for Gemini and OpenAI

### Backend Setup

```bash
# Clone and navigate
cd RAG_system

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run server
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/documents/upload | Upload a PDF |
| GET | /api/documents | List all documents |
| PATCH | /api/documents/{id} | Rename document |
| DELETE | /api/documents/{id} | Delete document |
| POST | /api/query | Ask a question |
| GET | /api/health | Health check |

See [docs/api.md](docs/api.md) for full API documentation.

## Documentation

- [Architecture](docs/architecture.md)
- [API Contract](docs/api.md)
- [Airtable Schema](docs/airtable-schema.md)
- [Processing Pipeline](docs/processing-pipeline.md)
- [Query Pipeline](docs/query-pipeline.md)
- [Prompts](docs/prompts/)

## Development

See [CLAUDE.md](CLAUDE.md) for build order and development context.

## License

Private - All rights reserved
