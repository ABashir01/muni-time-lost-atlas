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

async function expectMapReady(page: { locator: (selector: string) => any }) {
  const map = page.locator('[data-map-engine="maplibre-gl-js"]').first();
  await expect(map).toHaveAttribute("data-map-loaded", "ready");
  return map;
}

test("homepage, route detail, and map page render with real map surfaces", async ({
  page,
  request,
}) => {
  const screenshotDir = path.join(process.cwd(), "..", "artifacts", "frontend");
  mkdirSync(screenshotDir, { recursive: true });
  const routeIds = await getPublishedRouteIds(request);
  expect(routeIds.length).toBeGreaterThan(0);

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await expect(page.getByText("Worst Published Routes")).toBeVisible();
  await expect(page.getByText("Worst routes highlighted")).toBeVisible();
  await expectMapReady(page);
  await page.screenshot({ path: path.join(screenshotDir, "b5-homepage-desktop.png") });

  await page.goto(`/routes/${encodeURIComponent(routeIds[0])}`);
  await expect(page.getByText("Worst time window")).toBeVisible();
  await expectMapReady(page);

  await page.goto("/map");
  await expect(page.getByText(/Highest published loss/i)).toBeVisible();
  await expectMapReady(page);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByText(/Historical\/static API snapshot/i)).toBeVisible();
  await expectMapReady(page);
});

test("MapLibre route layers load without runtime failure", async ({ page, request }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  const routeIds = await getPublishedRouteIds(request);
  expect(routeIds.length).toBeGreaterThan(1);
  const primaryRouteId = routeIds[0];
  const runtimeErrors: string[] = [];
  page.on("pageerror", (error) => {
    runtimeErrors.push(error.message);
  });

  await page.goto("/");
  const homepageMap = await expectMapReady(page);
  await expect(homepageMap).toHaveAttribute("data-route-count", /[1-9]/);
  await expect(homepageMap).toHaveAttribute("data-background-route-count", /^[0-9]+$/);

  await page.goto(`/routes/${encodeURIComponent(primaryRouteId)}`);
  await expect(page.getByText("Worst time window")).toBeVisible();
  const routeMap = await expectMapReady(page);
  await expect(routeMap).toHaveAttribute("data-segment-count", /[1-9]/);

  await page.goto("/map");
  await expect(page.getByText(/Highest published loss/i)).toBeVisible();
  const citywideMap = await expectMapReady(page);
  await expect(citywideMap).toHaveAttribute("data-route-count", /[1-9]/);

  expect(runtimeErrors).toEqual([]);
});
