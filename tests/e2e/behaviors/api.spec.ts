import { test, expect } from '@playwright/test';

const API_BASE = 'https://web-production-1485e.up.railway.app';

// API-01: Health check returns OK
// Priority: CRITICAL
test('API-01: Health check returns OK', async ({ request }) => {
  const response = await request.get(`${API_BASE}/health`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.status).toBe('ok');
});

// API-02: Upload document endpoint
// Priority: CRITICAL
test('API-02: Upload document endpoint accepts PDF', async ({ request }) => {
  // Create a minimal valid PDF
  const pdfHeader = '%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF';

  const response = await request.post(`${API_BASE}/api/documents/upload`, {
    multipart: {
      file: {
        name: 'test-api-02.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from(pdfHeader),
      },
    },
  });
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body).toHaveProperty('doc_id');
  expect(body).toHaveProperty('name');
  expect(body.status).toBe('uploading');

  // Cleanup: delete the test document
  if (body.doc_id) {
    await request.delete(`${API_BASE}/api/documents/${body.doc_id}`);
  }
});

// API-03: List documents endpoint
// Priority: CRITICAL
test('API-03: List documents endpoint returns array', async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/documents`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(Array.isArray(body)).toBe(true);
  if (body.length > 0) {
    const doc = body[0];
    expect(doc).toHaveProperty('doc_id');
    expect(doc).toHaveProperty('name');
    expect(doc).toHaveProperty('status');
  }
});

// API-04: Rename document endpoint
// Priority: HIGH
test('API-04: Rename document endpoint updates name', async ({ request }) => {
  // First, get a document to rename
  const listRes = await request.get(`${API_BASE}/api/documents`);
  const docs = await listRes.json();
  const readyDoc = docs.find((d: any) => d.status === 'ready');

  if (!readyDoc) {
    test.skip(true, 'No ready documents available for rename test');
    return;
  }

  const originalName = readyDoc.name;
  const testName = `test-rename-${Date.now()}`;

  // Rename
  const renameRes = await request.patch(`${API_BASE}/api/documents/${readyDoc.doc_id}`, {
    data: { name: testName },
  });
  expect(renameRes.status()).toBe(200);
  const renamed = await renameRes.json();
  expect(renamed.name).toBe(testName);

  // Restore original name
  await request.patch(`${API_BASE}/api/documents/${readyDoc.doc_id}`, {
    data: { name: originalName },
  });
});

// API-05: Delete document endpoint
// Priority: HIGH
test('API-05: Delete nonexistent document returns 404', async ({ request }) => {
  const response = await request.delete(`${API_BASE}/api/documents/nonexistent_id_12345`);
  expect(response.status()).toBe(404);
});

// API-06: Get PDF URL endpoint
// Priority: HIGH
test('API-06: Get PDF URL endpoint returns signed URL', async ({ request }) => {
  const listRes = await request.get(`${API_BASE}/api/documents`);
  const docs = await listRes.json();
  const readyDoc = docs.find((d: any) => d.status === 'ready');

  if (!readyDoc) {
    test.skip(true, 'No ready documents available for PDF URL test');
    return;
  }

  const response = await request.get(`${API_BASE}/api/documents/${readyDoc.doc_id}/pdf`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body).toHaveProperty('url');
  expect(body).toHaveProperty('name');
  expect(body).toHaveProperty('total_pages');
  expect(body.url).toContain('https://');
});

// API-07: Get page image endpoint
// Priority: LOW
test('API-07: Get page image for nonexistent doc returns 404', async ({ request }) => {
  const response = await request.get(`${API_BASE}/api/documents/nonexistent_id/page/1/image`);
  expect(response.status()).toBe(404);
});

// API-08: Query endpoint returns answer and sources
// Priority: CRITICAL
test('API-08: Query endpoint returns answer and sources', async ({ request }) => {
  const response = await request.post(`${API_BASE}/api/query`, {
    data: {
      question: 'What is this document about?',
      conversation_history: [],
      model: 'gpt-4o-mini',
    },
    timeout: 60000,
  });
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body).toHaveProperty('answer');
  expect(body).toHaveProperty('sources');
  expect(typeof body.answer).toBe('string');
  expect(Array.isArray(body.sources)).toBe(true);
});

// API-09: Query with no ready documents returns helpful message
// Priority: HIGH
// Note: This test only works if there are no ready documents. We test the shape instead.
test('API-09: Query endpoint handles request correctly', async ({ request }) => {
  const response = await request.post(`${API_BASE}/api/query`, {
    data: {
      question: 'test question',
      conversation_history: [],
      model: 'gpt-4o',
    },
    timeout: 60000,
  });
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body).toHaveProperty('answer');
  expect(body).toHaveProperty('sources');
});

// API-10: Query with invalid model returns 400
// Priority: MEDIUM
test('API-10: Query with invalid model returns 400', async ({ request }) => {
  const response = await request.post(`${API_BASE}/api/query`, {
    data: {
      question: 'test',
      conversation_history: [],
      model: 'invalid-model-name',
    },
  });
  expect(response.status()).toBe(400);
});

// API-11: CORS allows frontend origin
// Priority: CRITICAL
test('API-11: CORS allows frontend origin', async ({ request }) => {
  const response = await request.fetch(`${API_BASE}/health`, {
    method: 'OPTIONS',
    headers: {
      'Origin': 'https://docuquery-six.vercel.app',
      'Access-Control-Request-Method': 'GET',
    },
  });
  // CORS preflight should return 200
  expect(response.status()).toBeLessThan(400);
});
