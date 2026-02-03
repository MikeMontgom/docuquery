---
allowed-tools: mcp__claude-in-chrome__*, Read, Write, Edit, Bash
description: Set up API credentials for Airtable, GCS, Gemini, and OpenAI
---

# Credential Provisioner

Interactive Chrome-assisted skill for creating API credentials and provisioning environments for the DocuQuery RAG system. Requires Chrome extension connected.

## Services to Configure

This project requires exactly 4 services:

| Service | Credential Type | What We Need |
|---------|----------------|--------------|
| Airtable | Personal Access Token + Base ID | Token, Base ID, Table IDs (after schema setup) |
| Google Cloud Storage | Service Account JSON | Credentials file, Bucket name |
| Google AI Studio (Gemini) | API Key | API key for extraction |
| OpenAI | API Key | API key for GPT-4o/4o-mini |

## Workflow

### Step 1: Verify Chrome Connection

Check that the Chrome extension is connected. If not, instruct the user to ensure Claude Code is running with browser access.

### Step 2: Process Each Service

For each service:
1. Navigate to the credential creation page
2. **Pause at auth gates** — if login/2FA appears, tell the user to handle it
3. Walk through creation (click buttons, fill forms)
4. **NEVER enter passwords** — only the user handles authentication
5. Capture the credential when displayed
6. Confirm with user before storing

---

## Service Runbooks

### Airtable — Personal Access Token

**Console:** https://airtable.com/create/tokens

1. Navigate to token creation page
2. Handle auth gate if needed
3. Click "Create new token"
4. Set token name: `docuquery-rag`
5. Add scopes:
   - `data.records:read`
   - `data.records:write`
   - `schema.bases:read`
   - `schema.bases:write`
6. Under "Access", add the RAG_System workspace/base
7. Click "Create token"
8. **IMMEDIATELY** capture the token (starts with `pat`) — shown only once
9. Record: `AIRTABLE_API_KEY`

**Get Base ID:**
1. Navigate to the target base in Airtable
2. Extract `app...` from the URL (e.g., `https://airtable.com/appXXXXXXXXX/...`)
3. Record: `AIRTABLE_BASE_ID`

**Table IDs:** Will be captured after airtable-operations agent creates the schema.

---

### Google Cloud Platform — Service Account + Bucket

**Console:** https://console.cloud.google.com

#### Create/Select Project
1. Navigate to https://console.cloud.google.com/projectcreate (or use existing)
2. Handle auth gate if needed
3. Set project name: `docuquery-rag`
4. Click Create, wait for completion

#### Enable Cloud Storage API
1. Navigate to APIs & Services > Library
2. Search for "Cloud Storage API"
3. Click Enable

#### Create Service Account
1. Navigate to APIs & Services > Credentials
2. Click "Create Credentials" > "Service Account"
3. Set name: `docuquery-service`
4. Skip optional grant steps (click Done)
5. Click the created service account
6. Go to Keys tab > Add Key > Create new key > JSON
7. Download triggers automatically
8. Note the downloaded file path
9. Record: `GCS_CREDENTIALS_JSON` (path to JSON file)

#### Create Storage Bucket
1. Navigate to https://console.cloud.google.com/storage/browser
2. Click "Create Bucket"
3. Set name: `docuquery-rag-storage` (or similar unique name)
4. Choose region (user preference, default: us-central1)
5. Accept defaults for storage class
6. Click Create
7. Record: `GCS_BUCKET_NAME`

---

### Google AI Studio — Gemini API Key

**Console:** https://aistudio.google.com/apikey

1. Navigate to API key page
2. Handle auth gate if needed
3. Click "Create API Key"
4. Select the `docuquery-rag` Google Cloud project
5. Capture the key value
6. Record: `GEMINI_API_KEY`

---

### OpenAI — API Key

**Console:** https://platform.openai.com/api-keys

1. Navigate to API keys page
2. Handle auth gate if needed
3. Click "Create new secret key"
4. Set name: `docuquery-rag`
5. Set permissions: "All" (or user preference)
6. Capture the key (starts with `sk-proj-`) — shown only once
7. Record: `OPENAI_API_KEY`

---

## Step 3: Write .env File

After all credentials are captured, write to `/Users/mikemontgom/PycharmProjects/RAG_system/.env`:

```
# ===========================
# DocuQuery RAG System
# Generated: {date}
# ===========================

# --- LLM API Keys ---
GEMINI_API_KEY={captured}
OPENAI_API_KEY={captured}

# --- Google Cloud Storage ---
GCS_BUCKET_NAME={captured}
GCS_CREDENTIALS_JSON={path-to-json}

# --- Airtable ---
AIRTABLE_API_KEY={captured}
AIRTABLE_BASE_ID={captured}
AIRTABLE_DOCUMENTS_TABLE_ID=  # Set after schema creation
AIRTABLE_CHUNKS_TABLE_ID=     # Set after schema creation

# --- CORS ---
FRONTEND_URL=http://localhost:3000
```

Verify `.gitignore` includes `.env` and the service account JSON path.

---

## Step 4: Validate Credentials

Test each credential with a minimal API call:

| Service | Test |
|---------|------|
| Airtable | `curl -H "Authorization: Bearer $AIRTABLE_API_KEY" https://api.airtable.com/v0/meta/bases` |
| GCS | Verify JSON file exists and is valid JSON |
| Gemini | `curl "https://generativelanguage.googleapis.com/v1/models?key=$GEMINI_API_KEY"` |
| OpenAI | `curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models` |

Report: `[OK]` or `[FAIL]` for each.

---

## Step 5: Summary

Provide completion summary:

```
Credential Provisioning Complete
================================

Services Configured:
  [OK] Airtable — PAT created, Base ID captured
  [OK] Google Cloud — Service account + bucket created
  [OK] Gemini — API key created
  [OK] OpenAI — API key created

Files Written:
  .env — credentials populated
  .gitignore — verified

Next Steps:
  1. Run airtable schema setup to create Documents and Chunks tables
  2. Capture table IDs and add to .env
  3. Begin backend implementation (Step 1 of build order)
```

---

## Important Constraints

- **NEVER enter passwords or 2FA codes** — pause and ask the user
- **NEVER store credentials in git-tracked files**
- **Capture immediately** — keys are often shown only once
- **One service at a time** — complete each before moving on
- **Service account JSON** — store outside project or in .gitignore path