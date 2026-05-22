import { mkdirSync } from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

async function getPublishedRouteIds(request: { get: (url: string) => Promise<any> }) {
  const response = await request.get(
    "http://127.0.0.1:8000/rankings?window=all_day&metric=typical_trip_loss_minutes",
  );
  expect(response.ok()).toBeTruthy();
  const payload = (await response.json()) as {
    routes: Array<{ route_id: string }>;
  };
  return payload.routes.map((route) => route.route_id);
}

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

test("remaining public routes render from the live historical api", async ({ page, request }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  const routeIds = await getPublishedRouteIds(request);
  expect(routeIds.length).toBeGreaterThan(1);
  const primaryRouteId = routeIds[0];
  const secondaryRouteId = routeIds[1];

  await page.goto(`/routes/${encodeURIComponent(primaryRouteId)}`);
  await expect(page.getByText("Worst time window")).toBeVisible();

  await page.goto(
    `/compare?${new URLSearchParams({
      ids: `${primaryRouteId},${secondaryRouteId}`,
    }).toString()}`,
  );
  await expect(page.getByText(/Worst selected route/i)).toBeVisible();

  await page.goto("/map");
  await expect(page.getByText(/Highest published loss/i)).toBeVisible();

  await page.goto("/methodology");
  await expect(page.getByText(/Plain-English contract/i)).toBeVisible();
});
