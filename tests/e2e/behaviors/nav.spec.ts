import { test, expect } from '@playwright/test';

// NAV-01: App loads with sidebar and query area
// Priority: CRITICAL
test('NAV-01: App loads with sidebar and query area', async ({ page }) => {
  // GIVEN: User navigates to the app URL
  await page.goto('/');

  // THEN: A two-panel layout is displayed
  // Check sidebar is present (has upload area and document list)
  await expect(page.getByText(/upload/i).first()).toBeVisible({ timeout: 10000 });

  // Check query area is present
  await expect(page.getByText(/query|ask|assistant/i).first()).toBeVisible();
});

// NAV-02: App title is set
// Priority: LOW
test('NAV-02: App title is set', async ({ page }) => {
  // GIVEN: User navigates to the app URL
  await page.goto('/');

  // THEN: Browser tab title reads "DocuQuery RAG"
  await expect(page).toHaveTitle(/DocuQuery/i);
});
