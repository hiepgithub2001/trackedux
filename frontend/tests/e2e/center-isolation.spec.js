import { test, expect } from '@playwright/test';

/**
 * Verifies that a superadmin cannot access center-scoped operational pages —
 * any attempt to load `/students`, `/teachers`, etc. is redirected to
 * `/system/centers` by `ProtectedRoute`. Backend 403 from `get_center_id`
 * is also asserted at the API layer.
 */
test('superadmin is redirected from center-scoped pages to /system/centers', async ({ page, request }) => {
  const apiBase = 'http://localhost:8000/api/v1';
  const username = process.env.SUPERADMIN_USERNAME;
  const password = process.env.SUPERADMIN_PASSWORD;
  test.skip(!username || !password, 'SUPERADMIN_USERNAME / SUPERADMIN_PASSWORD env vars not provided');

  const loginResp = await request.post(`${apiBase}/auth/login`, {
    data: { username, password },
  });
  expect(loginResp.ok()).toBeTruthy();
  const { access_token, refresh_token, user } = await loginResp.json();
  expect(user.role).toBe('superadmin');

  // API guard: center-scoped endpoint must return 403 for superadmin.
  const studentsApi = await request.get(`${apiBase}/students`, {
    headers: { Authorization: `Bearer ${access_token}` },
  });
  expect(studentsApi.status()).toBe(403);

  // Seed localStorage so the SPA treats us as logged-in superadmin.
  await page.addInitScript(
    ({ access_token, refresh_token, user }) => {
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('user', JSON.stringify(user));
    },
    { access_token, refresh_token, user },
  );

  for (const path of ['/students', '/teachers', '/classes', '/schedule']) {
    await page.goto(path);
    await expect(page).toHaveURL(/\/system\/centers/);
  }
});
