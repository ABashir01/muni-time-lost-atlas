import { mkdirSync } from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

test("homepage renders and a desktop review screenshot is captured", async ({ page }) => {
  const screenshotDir = path.join(process.cwd(), "..", "artifacts", "frontend");
  mkdirSync(screenshotDir, { recursive: true });

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await expect(page.getByText("Worst Published Routes")).toBeVisible();
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(screenshotDir, "b5-homepage-desktop.png") });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByText(/Historical\/static API snapshot/i)).toBeVisible();
});

test("remaining public routes render from the live historical api", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });

  await page.goto("/routes/14");
  await expect(page.getByText("Worst published stop wait")).toBeVisible();

  await page.goto("/compare?ids=14,49");
  await expect(page.getByText(/Worst selected route/i)).toBeVisible();

  await page.goto("/map");
  await expect(page.getByText(/Highest published loss/i)).toBeVisible();

  await page.goto("/methodology");
  await expect(page.getByText(/Plain-English contract/i)).toBeVisible();
});
