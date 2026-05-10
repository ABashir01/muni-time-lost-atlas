import { mkdirSync } from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

test("major public surfaces render and a desktop review screenshot is captured", async ({
  page,
}) => {
  const screenshotDir = path.join(process.cwd(), "..", "artifacts", "frontend");
  mkdirSync(screenshotDir, { recursive: true });

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Where Muni riders lose/i })).toBeVisible();
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(screenshotDir, "b5-homepage-desktop.png") });

  await page.goto("/routes/14");
  await expect(page.getByRole("heading", { name: /Mission/i })).toBeVisible();

  await page.goto("/compare?ids=14,49");
  await expect(page.getByRole("heading", { name: /Put the routes next to each other/i })).toBeVisible();

  await page.goto("/map");
  await expect(page.getByRole("heading", { name: /The citywide evidence surface/i })).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByText(/Updates every 60 seconds/i)).toBeVisible();

  await page.goto("/methodology");
  await expect(page.getByRole("heading", { name: /Typical trip: \+X.X min is the public promise/i })).toBeVisible();
});
