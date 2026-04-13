import { test, expect } from "@playwright/test";

test("clinician can create session, see transcript, and export soap", async ({ page }) => {
  await page.goto("http://localhost:5173");

  await expect(page.getByRole("button", { name: "Create session" })).toBeDisabled();
  await page.getByRole("button", { name: "Sign in" }).click();

  await page.getByRole("button", { name: "Create session" }).click();
  await expect(page.getByText("Session ACTIVE")).toBeVisible();
  await expect(page.getByText("Draft transcript")).toBeVisible();

  await page.getByRole("button", { name: "Close session" }).click();
  await expect(page.getByText("Session CLOSED")).toBeVisible();
  await expect(page.getByRole("button", { name: "Create session" })).toBeEnabled();

  await page.getByRole("button", { name: "Export SOAP" }).click();
});
