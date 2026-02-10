import { test, expect } from '@playwright/test';

const API_BASE = 'https://web-production-1485e.up.railway.app';
const FRONTEND_URL = 'https://docuquery-six.vercel.app';

// DEPLOY-01: Backend health check is accessible
// Priority: CRITICAL
test('DEPLOY-01: Backend health check returns OK', async ({ request }) => {
  const response = await request.get(`${API_BASE}/health`);
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(body.status).toBe('ok');
});

// DEPLOY-02: Frontend is accessible
// Priority: CRITICAL
test('DEPLOY-02: Frontend loads successfully', async ({ page }) => {
  const response = await page.goto(FRONTEND_URL);
  expect(response!.status()).toBe(200);

  // Page should render content
  await page.waitForTimeout(2000);
  const bodyText = await page.textContent('body');
  expect(bodyText).toBeTruthy();
  expect(bodyText!.length).toBeGreaterThan(20);
});

// DEPLOY-03: Frontend connects to backend
// Priority: CRITICAL
test('DEPLOY-03: Frontend makes successful API call to backend', async ({ page }) => {
  const responsePromise = page.waitForResponse(
    (resp) => resp.url().includes('/api/documents') && resp.status() === 200,
    { timeout: 15000 }
  );

  await page.goto(FRONTEND_URL);

  const response = await responsePromise;
  expect(response.status()).toBe(200);
});

// DEPLOY-04: Environment variables are configured
// Priority: CRITICAL
// Note: We verify this indirectly by checking that endpoints work
test('DEPLOY-04: Backend endpoints are functional (env vars configured)', async ({ request }) => {
  // Health check works
  const healthRes = await request.get(`${API_BASE}/health`);
  expect(healthRes.status()).toBe(200);

  // Documents endpoint works (requires Airtable env vars)
  const docsRes = await request.get(`${API_BASE}/api/documents`);
  expect(docsRes.status()).toBe(200);
});

// DEPLOY-05: GCS signed URLs are valid and accessible
// Priority: HIGH
test('DEPLOY-05: GCS signed URLs are accessible', async ({ request }) => {
  const listRes = await request.get(`${API_BASE}/api/documents`);
  const docs = await listRes.json();
  const readyDoc = docs.find((d: any) => d.status === 'ready');

  if (!readyDoc) {
    test.skip(true, 'No ready documents to test signed URLs');
    return;
  }

  const pdfRes = await request.get(`${API_BASE}/api/documents/${readyDoc.doc_id}/pdf`);
  expect(pdfRes.status()).toBe(200);
  const pdfData = await pdfRes.json();

  // Verify the signed URL is accessible
  const signedUrlRes = await request.get(pdfData.url);
  expect(signedUrlRes.status()).toBe(200);
});

// DEPLOY-06: Airtable rate limiting prevents throttle errors
// Priority: MEDIUM
test('DEPLOY-06: Multiple rapid API calls succeed', async ({ request }) => {
  // Make 5 rapid requests to test rate limiting handles them
  const promises = Array.from({ length: 5 }, () =>
    request.get(`${API_BASE}/api/documents`)
  );

  const responses = await Promise.all(promises);
  for (const resp of responses) {
    expect(resp.status()).toBe(200);
  }
});
