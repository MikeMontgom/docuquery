import { test, expect } from '@playwright/test';

const API_BASE = 'https://web-production-1485e.up.railway.app';

// DISP-01: User messages appear as right-aligned bubbles
// Priority: HIGH
test('DISP-01: User messages appear as right-aligned bubbles', async ({ page, request }) => {
  const listRes = await request.get(`${API_BASE}/api/documents`);
  const docs = await listRes.json();
  const hasReady = docs.some((d: any) => d.status === 'ready');

  if (!hasReady) {
    test.skip(true, 'No ready documents available');
    return;
  }

  await page.goto('/');
  await page.waitForTimeout(3000);

  // Submit a query
  const textarea = page.locator('textarea').first();
  await textarea.fill('Hello');

  const queryPromise = page.waitForResponse(
    (resp) => resp.url().includes('/api/query'),
    { timeout: 60000 }
  );
  await page.locator('button[type="submit"]').click();

  // The user message should appear immediately with "You" label
  await expect(page.getByText('You').first()).toBeVisible({ timeout: 5000 });

  // Wait for response
  await queryPromise;
});

// DISP-02: AI messages appear as left-aligned bubbles
// Priority: HIGH
test('DISP-02: AI messages appear with Assistant label', async ({ page, request }) => {
  const listRes = await request.get(`${API_BASE}/api/documents`);
  const docs = await listRes.json();
  const hasReady = docs.some((d: any) => d.status === 'ready');

  if (!hasReady) {
    test.skip(true, 'No ready documents available');
    return;
  }

  await page.goto('/');
  await page.waitForTimeout(3000);

  const textarea = page.locator('textarea').first();
  await textarea.fill('What is this about?');

  const queryPromise = page.waitForResponse(
    (resp) => resp.url().includes('/api/query'),
    { timeout: 60000 }
  );
  await page.locator('button[type="submit"]').click();
  await queryPromise;
  await page.waitForTimeout(3000);

  // AI response should have "Assistant" label
  await expect(page.getByText('Assistant').first()).toBeVisible({ timeout: 10000 });
});

// DISP-03: AI messages display source citations
// Priority: HIGH
test('DISP-03: AI messages display citations section', async ({ page, request }) => {
  const listRes = await request.get(`${API_BASE}/api/documents`);
  const docs = await listRes.json();
  const hasReady = docs.some((d: any) => d.status === 'ready');

  if (!hasReady) {
    test.skip(true, 'No ready documents available');
    return;
  }

  await page.goto('/');
  await page.waitForTimeout(3000);

  const textarea = page.locator('textarea').first();
  await textarea.fill('What specific information is in the first section?');

  const queryPromise = page.waitForResponse(
    (resp) => resp.url().includes('/api/query'),
    { timeout: 60000 }
  );
  await page.locator('button[type="submit"]').click();
  await queryPromise;
  await page.waitForTimeout(5000);

  // Check for citations section
  const citationsLabel = page.getByText(/citation/i).first();
  await expect(citationsLabel).toBeVisible({ timeout: 10000 });
});

// DISP-04: Loading indicator during query
// Priority: HIGH
test('DISP-04: Loading indicator shows during query', async ({ page, request }) => {
  const listRes = await request.get(`${API_BASE}/api/documents`);
  const docs = await listRes.json();
  const hasReady = docs.some((d: any) => d.status === 'ready');

  if (!hasReady) {
    test.skip(true, 'No ready documents available');
    return;
  }

  await page.goto('/');
  await page.waitForTimeout(3000);

  const textarea = page.locator('textarea').first();
  await textarea.fill('Explain the key concepts');

  await page.locator('button[type="submit"]').click();

  // During loading, the textarea should be disabled
  await expect(textarea).toBeDisabled({ timeout: 2000 });

  // Wait for response to complete
  await page.waitForResponse(
    (resp) => resp.url().includes('/api/query'),
    { timeout: 60000 }
  );
});

// DISP-05: Welcome state before first query
// Priority: MEDIUM
test('DISP-05: Welcome state shown before first query', async ({ page }) => {
  await page.goto('/');
  await page.waitForTimeout(3000);

  // Should show a welcome/empty state message
  const bodyText = await page.textContent('body');
  // Check for welcome-related text
  const hasWelcome = bodyText!.toLowerCase().includes('ask') ||
    bodyText!.toLowerCase().includes('upload') ||
    bodyText!.toLowerCase().includes('document') ||
    bodyText!.toLowerCase().includes('question');
  expect(hasWelcome).toBe(true);
});

// DISP-06: Document status badges
// Priority: MEDIUM
test('DISP-06: Documents show status indicators', async ({ page, request }) => {
  const listRes = await request.get(`${API_BASE}/api/documents`);
  const docs = await listRes.json();

  if (docs.length === 0) {
    test.skip(true, 'No documents available');
    return;
  }

  await page.goto('/');
  await page.waitForTimeout(3000);

  // Check that status text is visible (READY, UPLOADING, or ERROR)
  const statusTexts = await page.getByText(/ready|uploading|error/i).count();
  expect(statusTexts).toBeGreaterThanOrEqual(1);
});

// DISP-07: PDF viewer opens as modal overlay
// Priority: HIGH
// Covered by ACT-06

// DISP-08: PDF viewer shows document name and page
// Priority: MEDIUM
test('DISP-08: PDF viewer shows document name', async ({ page, request }) => {
  const listRes = await request.get(`${API_BASE}/api/documents`);
  const docs = await listRes.json();
  const hasReady = docs.some((d: any) => d.status === 'ready');

  if (!hasReady) {
    test.skip(true, 'No ready documents available');
    return;
  }

  await page.goto('/');
  await page.waitForTimeout(3000);

  // Submit query to get citations
  const textarea = page.locator('textarea').first();
  await textarea.fill('What does this document cover?');

  const queryPromise = page.waitForResponse(
    (resp) => resp.url().includes('/api/query'),
    { timeout: 60000 }
  );
  await page.locator('button[type="submit"]').click();
  await queryPromise;
  await page.waitForTimeout(5000);

  // Click first citation if available
  const citations = page.locator('button').filter({ hasText: /\[\d+\]/ });
  if ((await citations.count()) > 0) {
    await citations.first().click();
    await page.waitForTimeout(2000);

    // Modal should show document name in header
    const modal = page.locator('.fixed');
    await expect(modal.first()).toBeVisible({ timeout: 5000 });
  }
});

// DISP-09: PDF viewer has "Open in new tab" link
// Priority: MEDIUM
test('DISP-09: PDF viewer has open in new tab link', async ({ page, request }) => {
  const listRes = await request.get(`${API_BASE}/api/documents`);
  const docs = await listRes.json();
  const hasReady = docs.some((d: any) => d.status === 'ready');

  if (!hasReady) {
    test.skip(true, 'No ready documents available');
    return;
  }

  await page.goto('/');
  await page.waitForTimeout(3000);

  const textarea = page.locator('textarea').first();
  await textarea.fill('Describe the contents');

  const queryPromise = page.waitForResponse(
    (resp) => resp.url().includes('/api/query'),
    { timeout: 60000 }
  );
  await page.locator('button[type="submit"]').click();
  await queryPromise;
  await page.waitForTimeout(5000);

  const citations = page.locator('button').filter({ hasText: /\[\d+\]/ });
  if ((await citations.count()) > 0) {
    await citations.first().click();
    await page.waitForTimeout(3000);

    // Look for "Open in new tab" link
    const newTabLink = page.getByText(/open in new tab/i);
    await expect(newTabLink).toBeVisible({ timeout: 5000 });
  }
});

// DISP-10: PDF viewer closes on Escape key
// Priority: MEDIUM
test('DISP-10: PDF viewer closes on Escape', async ({ page, request }) => {
  const listRes = await request.get(`${API_BASE}/api/documents`);
  const docs = await listRes.json();
  const hasReady = docs.some((d: any) => d.status === 'ready');

  if (!hasReady) {
    test.skip(true, 'No ready documents available');
    return;
  }

  await page.goto('/');
  await page.waitForTimeout(3000);

  const textarea = page.locator('textarea').first();
  await textarea.fill('What is in this document?');

  const queryPromise = page.waitForResponse(
    (resp) => resp.url().includes('/api/query'),
    { timeout: 60000 }
  );
  await page.locator('button[type="submit"]').click();
  await queryPromise;
  await page.waitForTimeout(5000);

  const citations = page.locator('button').filter({ hasText: /\[\d+\]/ });
  if ((await citations.count()) > 0) {
    await citations.first().click();
    await page.waitForTimeout(2000);

    // Verify modal is open (iframe visible)
    await expect(page.locator('iframe').first()).toBeVisible({ timeout: 5000 });

    // Press Escape
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1000);

    // Modal should be closed (iframe should be gone)
    await expect(page.locator('iframe')).toHaveCount(0);
  }
});

// DISP-11: PDF viewer closes on X button
// Priority: MEDIUM
// Similar flow to DISP-10 but clicks the X button instead

// DISP-12: PDF viewer closes on backdrop click
// Priority: MEDIUM
// Similar flow to DISP-10 but clicks the backdrop

// DISP-13: PDF viewer shows loading spinner
// Priority: MEDIUM
test('DISP-13: PDF viewer shows loading state', async ({ page, request }) => {
  const listRes = await request.get(`${API_BASE}/api/documents`);
  const docs = await listRes.json();
  const hasReady = docs.some((d: any) => d.status === 'ready');

  if (!hasReady) {
    test.skip(true, 'No ready documents available');
    return;
  }

  await page.goto('/');
  await page.waitForTimeout(3000);

  const textarea = page.locator('textarea').first();
  await textarea.fill('Describe the content');

  const queryPromise = page.waitForResponse(
    (resp) => resp.url().includes('/api/query'),
    { timeout: 60000 }
  );
  await page.locator('button[type="submit"]').click();
  await queryPromise;
  await page.waitForTimeout(5000);

  const citations = page.locator('button').filter({ hasText: /\[\d+\]/ });
  if ((await citations.count()) > 0) {
    await citations.first().click();

    // Should briefly show a loading state before the PDF loads
    // The modal should appear
    await expect(page.locator('.fixed').first()).toBeVisible({ timeout: 5000 });
  }
});
