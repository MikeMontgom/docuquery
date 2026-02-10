# Application Behaviors

**App:** DocuQuery RAG System
**URL:** https://docuquery.vercel.app (frontend) / https://web-production-1485e.up.railway.app (backend)
**Last Updated:** 2026-02-09
**Total Behaviors:** 78

---

## How to Read This Document

Each behavior follows this format:
- **ID**: Unique identifier (e.g., NAV-01, UPLOAD-03)
- **Category**: Grouping for related behaviors
- **Given/When/Then**: The behavior specification
- **Priority**: CRITICAL (app is broken without this), HIGH (core feature), MEDIUM (important but not blocking), LOW (nice-to-have)
- **Notes**: Implementation details, known issues, or context for the test runner

---

## NAVIGATION: Page Load & Layout

### NAV-01: App loads with sidebar and query area
- **Priority:** CRITICAL
- **Given:** User navigates to the app URL
- **When:** Page loads
- **Then:** A two-panel layout is displayed: a left sidebar with the DocuQuery logo, an upload area, and a document list; and a right main area with a chat/query interface
- **Notes:** Single-page app, no routing. Sidebar width is fixed. Main area contains the QueryInterface component. Font is Inter loaded from Google Fonts.

### NAV-02: App title is set
- **Priority:** LOW
- **Given:** User navigates to the app URL
- **When:** Page loads
- **Then:** Browser tab title reads "DocuQuery RAG"
- **Notes:** Set in frontend/index.html.

---

## DATA LOADING: Document List & Status Polling

### LOAD-01: Document list loads on app start
- **Priority:** CRITICAL
- **Given:** App has loaded
- **When:** The Sidebar component mounts
- **Then:** A GET request is made to /api/documents, and the document list is populated with all documents sorted by upload_date descending
- **Notes:** API call is in Sidebar's useEffect. Documents show name, status, page/chunk count.

### LOAD-02: Document list shows empty state
- **Priority:** HIGH
- **Given:** No documents have been uploaded
- **When:** The document list loads
- **Then:** An empty state message is shown (no document cards rendered), and the upload area is still visible
- **Notes:** Check that no error is shown — just an empty list.

### LOAD-03: Processing documents poll for status updates
- **Priority:** HIGH
- **Given:** A document has status "uploading" (processing in progress)
- **When:** The polling interval fires (every 3 seconds)
- **Then:** The document list is re-fetched, and when the document status changes to "ready" or "error", the card updates accordingly and polling stops for completed documents
- **Notes:** Polling is implemented via setInterval in Sidebar. Interval is 3000ms. Polls only while any document has status "uploading".

### LOAD-04: Ready documents show chunk and page counts
- **Priority:** MEDIUM
- **Given:** A document has status "ready"
- **When:** The document list is displayed
- **Then:** The document card shows the document name, total_pages, and total_chunks
- **Notes:** Fields come from the GET /api/documents response.

### LOAD-05: Error documents show error status
- **Priority:** MEDIUM
- **Given:** A document has status "error"
- **When:** The document list is displayed
- **Then:** The document card shows an error indicator/badge
- **Notes:** The error_message field is available in the API response but may not be displayed in the UI card.

---

## USER INPUT: File Upload

### INPUT-01: Upload valid PDF via file picker
- **Priority:** CRITICAL
- **Given:** User is on the app with the sidebar visible
- **When:** User clicks the upload area and selects a valid PDF file
- **Then:** The file is uploaded via POST /api/documents/upload as multipart/form-data, the document appears in the list with status "uploading", and background processing begins
- **Notes:** Upload area is in the Sidebar component. Accepts .pdf files only. The input element has accept=".pdf".

### INPUT-02: Upload valid PDF via drag-and-drop
- **Priority:** HIGH
- **Given:** User is on the app with the sidebar visible
- **When:** User drags a PDF file onto the upload drop zone
- **Then:** The drop zone highlights on dragover, and when dropped, the file is uploaded identically to file picker upload
- **Notes:** Drop zone has onDragOver, onDragLeave, onDrop handlers. Visual feedback on drag via state change (isDragging).

### INPUT-03: Upload non-PDF file is rejected
- **Priority:** HIGH
- **Given:** User is on the app with the sidebar visible
- **When:** User selects a non-PDF file (e.g., .txt, .docx, .exe)
- **Then:** The backend returns HTTP 400 with detail "Only PDF files are accepted" and an error message is shown to the user
- **Notes:** Validation is in routers/documents.py — checks filename ends with .pdf. Frontend also has accept=".pdf" on the file input.

### INPUT-04: Upload empty file is rejected
- **Priority:** MEDIUM
- **Given:** User is on the app
- **When:** User uploads a 0-byte PDF file
- **Then:** The backend returns HTTP 400 with detail "File is empty" and an error is shown
- **Notes:** Checked in routers/documents.py after reading file content.

### INPUT-05: Upload corrupted PDF is rejected
- **Priority:** MEDIUM
- **Given:** User is on the app
- **When:** User uploads a file with .pdf extension but invalid PDF content
- **Then:** The backend returns HTTP 400 with detail about invalid PDF, and an error is shown
- **Notes:** pypdf.PdfReader throws an exception on invalid PDFs, caught in the upload endpoint.

### INPUT-06: Query text input accepts text
- **Priority:** CRITICAL
- **Given:** At least one document has status "ready"
- **When:** User types in the query textarea
- **Then:** The text appears in the textarea, and the send button becomes enabled when input is non-empty
- **Notes:** Textarea is in QueryInterface. Disabled when no documents are ready or when a query is in progress. Placeholder changes based on whether documents exist.

### INPUT-07: Query input disabled when no documents ready
- **Priority:** HIGH
- **Given:** No documents have status "ready" (either no documents, or all are uploading/error)
- **When:** User views the query interface
- **Then:** The textarea is disabled with placeholder "Upload a document to get started", the send button is disabled, and the cursor shows not-allowed
- **Notes:** Controlled by hasDocuments state derived from document list.

### INPUT-08: Model selector allows choosing answering model
- **Priority:** HIGH
- **Given:** User is in the query interface
- **When:** User clicks the model dropdown
- **Then:** Three options are available: GPT-4o, GPT-4o mini, Gemini 3. The selected model is sent with the query request.
- **Notes:** Model selector is inside the query input box, above the textarea. Default is GPT-4o. Values: "gpt-4o", "gpt-4o-mini", "gemini-3".

### INPUT-09: Query submits on Enter key
- **Priority:** MEDIUM
- **Given:** User has typed a question in the query textarea
- **When:** User presses Enter (without Shift)
- **Then:** The query is submitted (same as clicking the send button)
- **Notes:** Shift+Enter inserts a newline instead of submitting. Handled by onKeyDown in QueryInterface.

### INPUT-10: Query submits on send button click
- **Priority:** CRITICAL
- **Given:** User has typed a question in the query textarea
- **When:** User clicks the send button (arrow icon)
- **Then:** The question is sent via POST /api/query with the question, conversation_history, and selected model
- **Notes:** Button is disabled when input is empty, query is in progress, or no documents are ready.

---

## USER INPUT: Document Management

### INPUT-11: Rename document via inline edit
- **Priority:** MEDIUM
- **Given:** A document card is displayed in the sidebar
- **When:** User clicks the edit/rename button on the document card, changes the name, and confirms
- **Then:** A PATCH /api/documents/{doc_id} request is sent with the new name, and the card updates to show the new name
- **Notes:** The rename also updates the first chunk's content_raw to replace the "=== NEW DOCUMENT: {old_name} ===" marker with the new name.

---

## ACTIONS: Document Operations

### ACT-01: Delete document with confirmation
- **Priority:** HIGH
- **Given:** A document card is displayed in the sidebar
- **When:** User clicks the delete button on the document card
- **Then:** A confirmation dialog/prompt appears asking the user to confirm deletion
- **Notes:** Confirmation uses window.confirm() in the frontend.

### ACT-02: Confirmed delete removes document completely
- **Priority:** HIGH
- **Given:** User has clicked delete and the confirmation dialog is showing
- **When:** User confirms the deletion
- **Then:** A DELETE /api/documents/{doc_id} request is sent, the document is removed from the sidebar list, all chunks are deleted from Airtable, all files (PDF + images) are deleted from GCS, and the document record is deleted from Airtable
- **Notes:** Delete cascades: chunks first, then GCS files, then document record. The document list refreshes after deletion.

### ACT-03: Cancelled delete does nothing
- **Priority:** MEDIUM
- **Given:** User has clicked delete and the confirmation dialog is showing
- **When:** User cancels the deletion
- **Then:** Nothing happens — document remains in the list unchanged
- **Notes:** window.confirm() returns false on cancel.

### ACT-04: Upload triggers async processing pipeline
- **Priority:** CRITICAL
- **Given:** A valid PDF has been uploaded successfully
- **When:** The upload endpoint returns
- **Then:** A background task is started running process_document(), the document status is "uploading" during processing, and it transitions to "ready" on success or "error" on failure
- **Notes:** Uses FastAPI BackgroundTasks. Pipeline runs: extract -> breaks -> cleanup -> chunk -> images -> write chunks -> summarize -> update status.

---

## ACTIONS: Query Operations

### ACT-05: Submit query and receive answer
- **Priority:** CRITICAL
- **Given:** User has typed a question and at least one document is ready
- **When:** User submits the query
- **Then:** A loading indicator appears (bouncing dots), the query is sent to POST /api/query, and when the response returns, the answer appears as an AI chat bubble with source citations below it
- **Notes:** The user's question appears immediately as a user bubble. The AI response appears after the API call completes. Chat auto-scrolls to bottom via chatEndRef.

### ACT-06: Citation click opens PDF viewer
- **Priority:** HIGH
- **Given:** An AI response with source citations is displayed
- **When:** User clicks a citation button (e.g., "[1] document.pdf p.5-7")
- **Then:** A PDF viewer modal opens showing the referenced document, navigated to the cited page number
- **Notes:** Citation buttons show index number, doc_name, and source_pages. The PdfViewer component opens as a modal overlay. Page number is parsed from source_pages (takes first number from "5-7" format).

### ACT-07: Conversation history is maintained
- **Priority:** HIGH
- **Given:** User has had previous exchanges in the current session
- **When:** User submits a new query
- **Then:** The last 10 exchanges (user + assistant messages) are included in the conversation_history field of the API request, enabling follow-up questions
- **Notes:** History is maintained in QueryInterface state. Each exchange is {role, content}. History is sent to both routing and answering prompts.

---

## DISPLAY: Chat Interface

### DISP-01: User messages appear as right-aligned bubbles
- **Priority:** HIGH
- **Given:** User has submitted a query
- **When:** The chat area renders
- **Then:** The user's message appears right-aligned with an indigo background, white text, a "U" avatar, and "You" label below
- **Notes:** ChatBubble component with isUser=true. Rounded corners with top-right corner flat (rounded-tr-none).

### DISP-02: AI messages appear as left-aligned bubbles
- **Priority:** HIGH
- **Given:** The AI has responded to a query
- **When:** The chat area renders
- **Then:** The AI's answer appears left-aligned with a white background, dark text, an "AI" avatar, and "Assistant" label below
- **Notes:** ChatBubble component with isUser=false. Rounded corners with top-left corner flat (rounded-tl-none).

### DISP-03: AI messages display source citations
- **Priority:** HIGH
- **Given:** The AI response includes sources
- **When:** The AI chat bubble renders
- **Then:** Below the answer text, a "Citations (click to view)" section shows clickable buttons for each source, each displaying an index number, document name (truncated to 120px), and page numbers
- **Notes:** Sources rendered in ChatBubble when message.sources exists and is non-empty. Each citation is a button with onClick handler.

### DISP-04: Loading indicator during query
- **Priority:** HIGH
- **Given:** A query has been submitted
- **When:** The API call is in progress
- **Then:** Three bouncing dots appear in the chat area as a loading indicator, and the textarea and send button are disabled
- **Notes:** isQuerying state controls the loading UI. Three gray dots with staggered animation delays (0ms, 200ms, 400ms).

### DISP-05: Welcome state before first query
- **Priority:** MEDIUM
- **Given:** No queries have been submitted yet in this session
- **When:** The query interface is displayed
- **Then:** A welcome/empty state is shown in the chat area (centered content with the app logo and a prompt to ask a question)
- **Notes:** Shown when messages array is empty and not currently querying.

### DISP-06: Document status badges
- **Priority:** MEDIUM
- **Given:** Documents are listed in the sidebar
- **When:** The sidebar renders
- **Then:** Each document card shows a colored status badge: "uploading" (with animation/spinner), "ready" (success indicator), or "error" (error indicator)
- **Notes:** Status values come from the document's status field. Visual treatment varies by status.

---

## DISPLAY: PDF Viewer Modal

### DISP-07: PDF viewer opens as modal overlay
- **Priority:** HIGH
- **Given:** User clicked a citation
- **When:** The PdfViewer component mounts
- **Then:** A full-screen modal overlay appears with a dark backdrop (bg-black/60 with backdrop-blur), containing a white card with header and PDF iframe
- **Notes:** Modal is 85vh height, max-w-5xl. Clicking the backdrop closes the modal.

### DISP-08: PDF viewer shows document name and page
- **Priority:** MEDIUM
- **Given:** The PDF viewer is open
- **When:** The header renders
- **Then:** The document name and initial page number are displayed in the header, along with a PDF icon
- **Notes:** Header includes doc name as h3, "Page N" as subtitle.

### DISP-09: PDF viewer has "Open in new tab" link
- **Priority:** MEDIUM
- **Given:** The PDF viewer is open and the signed URL has loaded
- **When:** User sees the header
- **Then:** An "Open in new tab" link is available that opens the PDF in a new browser tab
- **Notes:** Uses target="_blank" with rel="noopener noreferrer". Only shown after pdfUrl is loaded.

### DISP-10: PDF viewer closes on Escape key
- **Priority:** MEDIUM
- **Given:** The PDF viewer is open
- **When:** User presses the Escape key
- **Then:** The PDF viewer modal closes
- **Notes:** Escape key listener added in useEffect, cleaned up on unmount.

### DISP-11: PDF viewer closes on X button
- **Priority:** MEDIUM
- **Given:** The PDF viewer is open
- **When:** User clicks the X close button in the header
- **Then:** The PDF viewer modal closes
- **Notes:** Close button is in the top-right of the header.

### DISP-12: PDF viewer closes on backdrop click
- **Priority:** MEDIUM
- **Given:** The PDF viewer is open
- **When:** User clicks the dark backdrop outside the modal card
- **Then:** The PDF viewer modal closes
- **Notes:** onClick on the overlay div calls onClose. Inner card has e.stopPropagation() to prevent closing when clicking inside.

### DISP-13: PDF viewer shows loading spinner
- **Priority:** MEDIUM
- **Given:** The PDF viewer has just opened
- **When:** The signed URL is being fetched from the API
- **Then:** A spinning loading indicator is shown in the PDF content area
- **Notes:** Loading state is true until the GET /api/documents/{doc_id}/pdf call completes.

### DISP-14: PDF viewer shows error on failure
- **Priority:** MEDIUM
- **Given:** The PDF viewer is open
- **When:** The signed URL fetch fails
- **Then:** "Failed to load PDF" error text is displayed in red in the content area
- **Notes:** Error state set in catch block of fetchPdf.

---

## API: Backend Endpoints

### API-01: Health check returns OK
- **Priority:** CRITICAL
- **Given:** The backend is running
- **When:** GET /health is called
- **Then:** Response is HTTP 200 with body {"status": "ok"}
- **Notes:** Defined in main.py. No authentication required.

### API-02: Upload document endpoint
- **Priority:** CRITICAL
- **Given:** Backend is running
- **When:** POST /api/documents/upload is called with a PDF file as multipart/form-data
- **Then:** Response is HTTP 200 with {"doc_id": "recXXX", "name": "filename.pdf", "status": "uploading"}, the PDF is saved to GCS, a document record is created in Airtable, and background processing starts
- **Notes:** doc_id is the Airtable record_id. Name is the original filename. Status is always "uploading" on initial return.

### API-03: List documents endpoint
- **Priority:** CRITICAL
- **Given:** Backend is running
- **When:** GET /api/documents is called
- **Then:** Response is HTTP 200 with a JSON array of all documents, each with doc_id, name, status, total_chunks, total_pages, upload_date, ordered by upload_date descending
- **Notes:** Pagination handled internally by Airtable service. Returns all documents regardless of status.

### API-04: Rename document endpoint
- **Priority:** HIGH
- **Given:** A document with the given doc_id exists
- **When:** PATCH /api/documents/{doc_id} is called with {"name": "new_name"}
- **Then:** Response is HTTP 200 with the updated document object, the name is updated in Airtable, and the first chunk's NEW DOCUMENT marker is updated
- **Notes:** Returns 404 if doc_id not found. Returns 400 if name field is missing.

### API-05: Delete document endpoint
- **Priority:** HIGH
- **Given:** A document with the given doc_id exists
- **When:** DELETE /api/documents/{doc_id} is called
- **Then:** Response is HTTP 200 with {"success": true}, all chunks deleted from Airtable, all files deleted from GCS, document record deleted from Airtable
- **Notes:** Delete order: chunks, GCS files, document record. Returns 404 if doc_id not found.

### API-06: Get PDF URL endpoint
- **Priority:** HIGH
- **Given:** A document with the given doc_id exists and has a PDF in GCS
- **When:** GET /api/documents/{doc_id}/pdf is called
- **Then:** Response is HTTP 200 with {"url": "https://signed-url...", "name": "filename", "total_pages": N}
- **Notes:** URL is a signed GCS URL valid for 1 hour. Returns 404 if document or PDF not found.

### API-07: Get page image endpoint
- **Priority:** LOW
- **Given:** A document with the given doc_id exists
- **When:** GET /api/documents/{doc_id}/page/{page_num}/image is called
- **Then:** Response is HTTP 200 with {"url": "https://signed-url..."} if the page image exists, or 404 if not
- **Notes:** Page images are only available if save_all_pages was run (currently DISABLED). This endpoint will likely return 404 for all requests.

### API-08: Query endpoint
- **Priority:** CRITICAL
- **Given:** Backend is running and at least one document has status "ready"
- **When:** POST /api/query is called with {"question": "...", "conversation_history": [...], "model": "gpt-4o"}
- **Then:** Response is HTTP 200 with {"answer": "...", "sources": [{"doc_name": "...", "doc_id": "...", "chunk_sequence": N, "heading_path": "...", "source_pages": "..."}]}
- **Notes:** Synchronous endpoint. Model must be one of: gpt-4o, gpt-4o-mini, gemini-3. Returns 400 for invalid model.

### API-09: Query with no ready documents
- **Priority:** HIGH
- **Given:** No documents have status "ready"
- **When:** POST /api/query is called
- **Then:** Response is HTTP 200 with answer text saying "No documents have been processed yet..." and empty sources
- **Notes:** Does not return an error — returns a helpful message as the answer.

### API-10: Query with invalid model
- **Priority:** MEDIUM
- **Given:** Backend is running
- **When:** POST /api/query is called with an unsupported model value
- **Then:** Response is HTTP 400 with error detail about invalid model
- **Notes:** Validation in routers/query.py checks model against allowed list.

### API-11: CORS allows frontend origin
- **Priority:** CRITICAL
- **Given:** Frontend is making requests from its deployed URL
- **When:** Any API request is made from the frontend
- **Then:** CORS headers allow the request (Access-Control-Allow-Origin matches the frontend URL)
- **Notes:** CORS configured in main.py using FRONTEND_URL env var. Allows credentials, all methods, all headers.

---

## DATA PIPELINE: Document Processing

### PIPE-01: Extraction produces text from PDF pages
- **Priority:** CRITICAL
- **Given:** A PDF has been uploaded and processing has started
- **When:** The extraction step runs
- **Then:** The PDF is split into 5-page batches, each batch is sent to Gemini with the extraction prompt, and the results are concatenated into a master text string with [PAGE X] markers preserved
- **Notes:** Model: gemini-2.0-flash. Sequential batch processing. Temperature: 0.1. Max output: 32,000 tokens. Retry: 3 attempts with exponential backoff.

### PIPE-02: Break scoring inserts semantic break markers
- **Priority:** CRITICAL
- **Given:** Extracted text is available from step 1
- **When:** The break scoring step runs
- **Then:** GPT-4o inserts [BREAK id=X score=Y] markers throughout the text at semantic boundaries, with scores from 25 (weak) to 100 (strong structural boundary)
- **Notes:** Model: GPT-4o. Single call for docs under 12k tokens; segmented with 2k overlap for larger docs. Temperature: 0.1.

### PIPE-03: Cleanup removes markers and resequences breaks
- **Priority:** HIGH
- **Given:** Text with break markers and page markers is available
- **When:** The cleanup step runs
- **Then:** Page mapping is recorded (character ranges to page numbers), [PAGE X] markers are removed, code UI artifacts are removed (content_copy, expand_less, etc.), and break IDs are resequenced from 1
- **Notes:** Deterministic — no LLM call. Returns (cleaned_text, PageMapping).

### PIPE-04: DP chunking splits text optimally
- **Priority:** CRITICAL
- **Given:** Cleaned text with break markers and page mapping are available
- **When:** The chunking step runs
- **Then:** Text is split into chunks using dynamic programming that minimizes cost(chunk) = alpha*(tokens-650)^2 + beta*(100-break_score), with GRAPHIC_INSERT blocks as standalone chunks, respecting MIN_CHUNK_TOKENS=200 and MAX_CHUNK_TOKENS=1200
- **Notes:** No LLM call. Chunks only split at break markers, never mid-sentence. Graphic chunks have chunk_type "graphic", others have "text".

### PIPE-05: Image cropping extracts graphics from PDF
- **Priority:** HIGH
- **Given:** Graphic chunks with GRAPHIC_INSERT JSON exist
- **When:** The image processing step runs
- **Then:** For each graphic chunk, the specified page is rendered at 300 DPI, the image is cropped at the specified coordinates, saved as PNG, uploaded to GCS at images/{doc_id}/{graphic_id}.png, and the signed URL is stored
- **Notes:** Coordinate conversion: multiply PDF points (72 DPI) by 300/72. Fallback: full page render if cropping fails. Parallel: ThreadPoolExecutor with 5 workers.

### PIPE-06: Chunks are written to Airtable in batches
- **Priority:** CRITICAL
- **Given:** Chunks and image URLs are available
- **When:** The Airtable write step runs
- **Then:** All chunks are written to the Chunks table in batches of 10, with fields: doc_id (linked), sequence_number, chunk_type, content_raw, heading_path, token_count, source_pages, and image_url (for graphics). The first chunk gets a "=== NEW DOCUMENT: {name} ===" prefix.
- **Notes:** Airtable rate limit: 0.2s between requests. Linked field doc_id is passed as array [record_id].

### PIPE-07: Summarization generates functional summaries
- **Priority:** CRITICAL
- **Given:** Chunks have been written to Airtable
- **When:** The summarization step runs
- **Then:** Each text chunk is summarized by GPT-4o using the summarization prompt (telegraphic style, 80-90% shorter than original). Graphic chunks get "[title] description" format from their GRAPHIC_INSERT JSON. Each chunk record is updated with content_summary.
- **Notes:** Model: GPT-4o. Parallel: 3 workers with 0.5s delay between calls. Temperature: 0.2. Max tokens: 500. Retry: 3 attempts.

### PIPE-08: Pipeline success updates document status to ready
- **Priority:** CRITICAL
- **Given:** All pipeline steps have completed successfully
- **When:** The orchestrator finishes
- **Then:** The document record is updated with status="ready" and total_chunks set to the number of chunks created
- **Notes:** This triggers the frontend polling to show the document as ready.

### PIPE-09: Pipeline failure updates document status to error
- **Priority:** HIGH
- **Given:** Any pipeline step throws an exception
- **When:** The orchestrator catches the error
- **Then:** The document record is updated with status="error" and error_message set to the exception message (truncated to 1000 chars)
- **Notes:** The exception is re-raised after updating status for background task logging.

---

## AI/LLM: Query Engine

### AI-01: Router identifies relevant chunks
- **Priority:** CRITICAL
- **Given:** A question and all chunk summaries are available
- **When:** The routing step runs
- **Then:** GPT-4o-mini analyzes all summaries and returns a JSON array of chunk IDs that are relevant to the question, typically 5-15 chunks for a normal question
- **Notes:** Model: GPT-4o-mini. Temperature: 0.1. Batched if total summary tokens exceed 50k (batches processed in parallel). Fallback JSON parsing with regex if strict parse fails.

### AI-02: Context assembler uses variable resolution
- **Priority:** CRITICAL
- **Given:** Router has selected relevant chunk IDs
- **When:** Context assembly runs
- **Then:** Selected chunks include full content_raw, unselected chunks include only [SUMMARY] content_summary. Chunks are grouped by document and ordered by sequence_number. Graphic chunks with images get [IMAGE AVAILABLE: url] appended.
- **Notes:** This is the key architectural feature — variable-resolution retrieval provides full document context while focusing detail on relevant sections.

### AI-03: Answerer generates response with citations
- **Priority:** CRITICAL
- **Given:** Assembled context, question, and conversation history are available
- **When:** The answering step runs
- **Then:** The selected model generates an answer based only on the provided context, citing sources in "(Source: doc_name, heading_path)" format, and acknowledging when information might be in summary-only sections
- **Notes:** Default model: GPT-4o. Temperature: 0.3. Max tokens: 2,000. Gemini answering uses gemini-2.0-flash internally.

### AI-04: Conversation history enables follow-up questions
- **Priority:** HIGH
- **Given:** User has had previous exchanges in the session
- **When:** A new query is submitted
- **Then:** The last 10 exchanges are included in both the routing prompt and the answering prompt, allowing the model to understand context from prior questions (e.g., "Tell me more about that" works)
- **Notes:** History is formatted as "ROLE: content" strings joined by newlines. Maintained in frontend state, reset on page reload.

---

## ERROR HANDLING: Network & Validation

### ERR-01: Network error on document list fetch
- **Priority:** HIGH
- **Given:** The backend is unreachable or returns a server error
- **When:** The frontend tries to load the document list
- **Then:** An error state is shown in the sidebar (not a blank page or infinite spinner)
- **Notes:** Fetch error caught in Sidebar's loadDocuments function.

### ERR-02: Network error on query submission
- **Priority:** HIGH
- **Given:** The backend is unreachable or returns a server error
- **When:** The frontend submits a query
- **Then:** An error message is shown to the user (not an infinite loading state), and the query input becomes re-enabled
- **Notes:** Error caught in QueryInterface's handleSubmit. The isQuerying state should be reset to false.

### ERR-03: Upload error shows feedback
- **Priority:** HIGH
- **Given:** A file upload fails (network error or validation error)
- **When:** The upload API call returns an error
- **Then:** An error message is displayed to the user with the error detail, and the upload area remains functional for retry
- **Notes:** Error messages come from the API's "detail" field in the error response.

### ERR-04: Pipeline extraction retry on failure
- **Priority:** MEDIUM
- **Given:** A Gemini extraction batch fails
- **When:** The extraction step encounters an API error
- **Then:** The batch is retried up to 3 times with exponential backoff (10s, 20s, 30s). If all retries fail, the document is marked as error.
- **Notes:** Retry logic is per-batch in extract.py.

### ERR-05: Pipeline break scoring retry on failure
- **Priority:** MEDIUM
- **Given:** The GPT-4o break scoring call fails
- **When:** The break scoring step encounters an API error
- **Then:** The call is retried up to 3 times with exponential backoff. If all retries fail, the document is marked as error.
- **Notes:** Retry logic in breaks.py _process_segment function.

### ERR-06: Pipeline summarization retry on failure
- **Priority:** MEDIUM
- **Given:** A GPT-4o summarization call fails for a chunk
- **When:** The summarization step encounters an API error
- **Then:** The call is retried up to 3 times with exponential backoff (5s, 10s, 15s). If all retries fail, the error propagates and the document is marked as error.
- **Notes:** Retry logic in summarize.py summarize_all function.

### ERR-07: Routing JSON parse fallback
- **Priority:** MEDIUM
- **Given:** The routing model returns malformed JSON
- **When:** The router tries to parse the response
- **Then:** Fallback parsing handles markdown fences around JSON, missing quotes, and regex-based ID extraction. If all parsing fails, an empty selection is returned.
- **Notes:** Implemented in query/router.py _route_batch function.

---

## EDGE CASES: Boundary Conditions

### EDGE-01: First document upload (fresh system)
- **Priority:** HIGH
- **Given:** No documents exist in the system
- **When:** User uploads their first PDF
- **Then:** The document appears in the previously empty list, processing starts, and when complete the query interface becomes enabled
- **Notes:** Tests the transition from empty state to functional state.

### EDGE-02: Query with single-page PDF
- **Priority:** MEDIUM
- **Given:** A single-page PDF has been processed
- **When:** User asks a question
- **Then:** The system handles the minimal case correctly — extraction produces 1 batch, chunking produces at least 1 chunk, routing and answering work normally
- **Notes:** Ensure source_pages is "1" not "1-1".

### EDGE-03: Multiple documents queried together
- **Priority:** HIGH
- **Given:** Multiple documents with status "ready" exist
- **When:** User asks a question
- **Then:** The router sees summaries from ALL ready documents, and the answer may cite sources from multiple documents. Context is grouped by document with "=== DOCUMENT: name ===" headers.
- **Notes:** This is the multi-document RAG scenario.

### EDGE-04: Very long answer does not break UI
- **Priority:** MEDIUM
- **Given:** The answering model generates a very long response
- **When:** The chat bubble renders
- **Then:** The response is fully visible with proper scrolling, text wrapping works correctly, and the chat area scrolls to show the full response
- **Notes:** Chat area should auto-scroll to bottom. The AI bubble has max-w-[85%] constraint.

### EDGE-05: Special characters in document name
- **Priority:** LOW
- **Given:** A PDF with special characters in its filename is uploaded (e.g., spaces, parentheses, unicode)
- **When:** The document is processed and displayed
- **Then:** The filename is preserved correctly in the document list and in source citations
- **Notes:** Test with filenames like "Report (Final v2).pdf" and "resum\u00e9.pdf".

### EDGE-06: Rapid consecutive queries
- **Priority:** LOW
- **Given:** User has received an answer
- **When:** User immediately submits another question without waiting
- **Then:** The system handles the request correctly — the second query includes the first exchange in conversation_history, and no race conditions occur
- **Notes:** The textarea is disabled during query execution (isQuerying=true), preventing true simultaneous queries from the UI.

### EDGE-07: Document deleted while being queried
- **Priority:** LOW
- **Given:** A query is in progress using chunks from a document
- **When:** The document is deleted (e.g., from another browser tab)
- **Then:** The in-progress query should still complete with whatever data it already loaded, but subsequent queries will not include the deleted document's chunks
- **Notes:** No explicit handling for this race condition. The query reads chunks at the start and works with that snapshot.

### EDGE-08: Large PDF processing (many pages)
- **Priority:** MEDIUM
- **Given:** A large PDF (100+ pages) is uploaded
- **When:** Processing runs
- **Then:** Extraction processes in 5-page batches sequentially, break scoring may segment into 80k-token chunks with overlap, chunking handles the full text, and the document eventually reaches "ready" status (may take several minutes)
- **Notes:** Processing time scales with page count. The 3-second polling interval will show status updates.

---

## DEPLOYMENT: Infrastructure

### DEPLOY-01: Backend health check is accessible
- **Priority:** CRITICAL
- **Given:** The backend is deployed to Railway
- **When:** GET https://web-production-1485e.up.railway.app/health is called
- **Then:** Response is HTTP 200 with {"status": "ok"}
- **Notes:** This is the primary deployment verification check.

### DEPLOY-02: Frontend is accessible
- **Priority:** CRITICAL
- **Given:** The frontend is deployed to Vercel
- **When:** User navigates to https://docuquery.vercel.app
- **Then:** The application loads and renders the two-panel layout
- **Notes:** Requires VITE_API_URL env var set in Vercel pointing to the Railway backend URL.

### DEPLOY-03: Frontend connects to backend
- **Priority:** CRITICAL
- **Given:** Both frontend and backend are deployed
- **When:** The frontend makes its first API call (GET /api/documents on load)
- **Then:** The request succeeds, CORS headers are correct, and the document list loads
- **Notes:** Requires FRONTEND_URL env var set in Railway matching the Vercel URL. CORS misconfiguration will cause all API calls to fail.

### DEPLOY-04: Environment variables are configured
- **Priority:** CRITICAL
- **Given:** The backend is deployed
- **When:** Any API endpoint is called
- **Then:** All required environment variables are present: GEMINI_API_KEY, OPENAI_API_KEY, GCS_BUCKET_NAME, GCS_CREDENTIALS_JSON, AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_DOCUMENTS_TABLE_ID, AIRTABLE_CHUNKS_TABLE_ID, FRONTEND_URL
- **Notes:** Missing env vars will cause runtime errors on first use. The health endpoint works without them, but all other endpoints depend on them.

### DEPLOY-05: GCS signed URLs are valid and accessible
- **Priority:** HIGH
- **Given:** A PDF has been uploaded to GCS
- **When:** The frontend requests a signed URL via GET /api/documents/{doc_id}/pdf
- **Then:** The returned signed URL is accessible (HTTP 200) and serves the correct PDF content
- **Notes:** Signed URLs for PDFs are valid for 1 hour. Image signed URLs are valid for 7 days. Expired URLs return 403.

### DEPLOY-06: Airtable rate limiting prevents throttle errors
- **Priority:** MEDIUM
- **Given:** Multiple Airtable operations are happening (e.g., writing chunks in batches)
- **When:** Requests are sent to the Airtable API
- **Then:** The 0.2s minimum interval between requests prevents HTTP 429 rate limit errors from Airtable
- **Notes:** Rate limiting is enforced globally in services/airtable.py via _rate_limit() function. Airtable limit is 5 req/s.
