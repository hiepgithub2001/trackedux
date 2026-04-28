import { test, expect } from '@playwright/test';

test('homepage renders the React root', async ({ page }) => {
  await page.goto('/');
  const root = page.locator('#root');
  await expect(root).toBeAttached();
});
