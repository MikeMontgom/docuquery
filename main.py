from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from routers import documents, query

app = FastAPI(title="DocuQuery RAG API")
app.include_router(documents.router)
app.include_router(query.router)

# Parse FRONTEND_URL - supports comma-separated values for multiple origins
_origins = [o.strip() for o in config.FRONTEND_URL.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
