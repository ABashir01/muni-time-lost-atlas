import { mkdirSync } from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

test("homepage mobile header and layout hold together", async ({ page }) => {
  const screenshotDir = path.join(process.cwd(), "..", "artifacts", "frontend");
  mkdirSync(screenshotDir, { recursive: true });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");

  await expect(page.getByLabel("Open navigation menu")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: /Where Muni Riders Lose The Most Time/i }),
  ).toBeVisible();
  await expect(page.getByText("Compare routes or corridors.")).toBeVisible();

  await page.screenshot({
    path: path.join(screenshotDir, "homepage-mobile-closed.png"),
    fullPage: true,
  });

  await page.getByLabel("Open navigation menu").click();
  await expect(page.getByRole("link", { name: "Explore the map" })).toBeVisible();

  await page.screenshot({
    path: path.join(screenshotDir, "homepage-mobile-menu-open.png"),
    fullPage: true,
  });
});
