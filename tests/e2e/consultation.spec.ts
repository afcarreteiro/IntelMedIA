import { test, expect } from "@playwright/test";

test("clinician can create session, see transcript, and export soap", async ({ page }) => {
  await page.route("**/auth/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ access_token: "token-local", token_type: "bearer" }),
    });
  });

  await page.goto("http://localhost:5173");

  await expect(page.locator('input[type="password"]')).toBeVisible();
  await expect(page.locator('input[type="password"]')).toHaveValue("intelmedia");

  await expect(page.getByRole("button", { name: "Create session" })).toBeDisabled();
  await page.getByRole("button", { name: "Sign in" }).click();

  await page.getByRole("button", { name: "Create session" }).click();
  await expect(page.getByText("Session ACTIVE")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Draft transcript" })).toBeVisible();
  await expect(page.locator("li", { hasText: "Draft transcript" })).toHaveCount(1);

  await page.getByRole("button", { name: "Close session" }).click();
  await expect(page.getByText("Session CLOSED")).toBeVisible();
  await expect(page.getByRole("button", { name: "Create session" })).toBeEnabled();

  await page.getByRole("button", { name: "Export SOAP" }).click();
  await expect(page.getByText("SOAP note for session-local")).toBeVisible();
  await expect(page.getByText("intelmedia")).toHaveCount(0);
});
