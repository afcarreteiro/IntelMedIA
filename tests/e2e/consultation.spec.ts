import { test, expect } from "@playwright/test";

test("clinician can manage session lifecycle and export soap", async ({ page }) => {
  await page.route("**/auth/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ access_token: "token-local", token_type: "bearer" }),
    });
  });

  await page.route("**/sessions", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ session_id: "session-e2e", status: "IDLE" }),
    });
  });

  await page.route("**/sessions/session-e2e/close", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ session_id: "session-e2e", status: "CLOSED" }),
    });
  });

  await page.route("**/sessions/session-e2e/soap", async (route) => {
    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ detail: "not found" }),
    });
  });

  await page.goto("/");

  await expect(page.locator('input[type="password"]')).toBeVisible();
  await expect(page.locator('input[type="password"]')).toHaveValue("intelmedia");

  await expect(page.getByRole("button", { name: "Create session" })).toBeDisabled();
  await page.getByRole("button", { name: "Sign in" }).click();

  await page.getByRole("button", { name: "Create session" }).click();
  await expect(page.getByText("Session IDLE")).toBeVisible();
  await expect(page.getByRole("button", { name: "Create session" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Close session" })).toBeEnabled();

  await page.getByRole("button", { name: "Close session" }).click();
  await expect(page.getByText("Session CLOSED")).toBeVisible();
  await expect(page.getByRole("button", { name: "Create session" })).toBeDisabled();

  await page.getByRole("button", { name: "Export SOAP" }).click();
  await expect(page.getByText("SOAP export unavailable: backend endpoint not implemented.")).toBeVisible();
  await expect(page.getByText("intelmedia")).toHaveCount(0);
});
