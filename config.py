import os
import json
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def _require(key: str) -> str:
    """Get required environment variable or raise."""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


# LLM API Keys
GEMINI_API_KEY = _require("GEMINI_API_KEY")
OPENAI_API_KEY = _require("OPENAI_API_KEY")

# Google Cloud Storage
GCS_BUCKET_NAME = _require("GCS_BUCKET_NAME")
_gcs_creds_raw = _require("GCS_CREDENTIALS_JSON")

# Handle GCS credentials: can be a file path OR a JSON string (for cloud deployment)
if _gcs_creds_raw.strip().startswith("{"):
    # It's a JSON string - write to temp file for google-cloud-storage
    _creds_dict = json.loads(_gcs_creds_raw)
    _temp_creds = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(_creds_dict, _temp_creds)
    _temp_creds.close()
    GCS_CREDENTIALS_JSON = _temp_creds.name
else:
    # It's a file path
    GCS_CREDENTIALS_JSON = _gcs_creds_raw
    _gcs_path = Path(GCS_CREDENTIALS_JSON)
    if not _gcs_path.is_absolute():
        GCS_CREDENTIALS_JSON = str(Path(__file__).parent / GCS_CREDENTIALS_JSON)

# Airtable
AIRTABLE_API_KEY = _require("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = _require("AIRTABLE_BASE_ID")
AIRTABLE_DOCUMENTS_TABLE_ID = _require("AIRTABLE_DOCUMENTS_TABLE_ID")
AIRTABLE_CHUNKS_TABLE_ID = _require("AIRTABLE_CHUNKS_TABLE_ID")

# CORS
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
