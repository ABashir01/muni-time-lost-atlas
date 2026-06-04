import { readFileSync } from "node:fs";
import path from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import ComparePage from "@/app/compare/page";
import HomePage from "@/app/page";
import RankingsPage from "@/app/rankings/page";
import RouteDetailPage from "@/app/routes/[routeId]/page";
import MapPage from "@/app/map/page";
import MethodologyPage from "@/app/methodology/page";

vi.mock("next/navigation", async () => {
  const actual = await vi.importActual<typeof import("next/navigation")>("next/navigation");

  return {
    ...actual,
    useRouter: () => ({
      push: vi.fn(),
    }),
  };
});

const fixtureDir = path.join(process.cwd(), "..", "fixtures", "api");
const rankingsPayload = loadFixture("rankings_all_day_typical_trip_loss_minutes_routes.json");
const route14SummaryPayload = loadFixture("route_14_summary_all_day.json");
const route14SegmentsPayload = loadFixture("route_14_segments_direction_1_all_day.json");
const route14StopWaitPayload = loadFixture("route_14_stops_wait_direction_1_all_day.json");
const comparePayload = loadFixture("routes_compare_14_49_all_day.json");
const mapPayload = loadFixture("map_routes_all_day_typical_trip_loss_minutes.json");
const route49SummaryPayload = {
  ...rankingsPayload.routes.find((route: { route_id: string }) => route.route_id === "49"),
};

function loadFixture(fileName: string) {
  return JSON.parse(readFileSync(path.join(fixtureDir, fileName), "utf8"));
}

function jsonResponse(payload: unknown, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(payload), {
      headers: {
        "Content-Type": "application/json",
      },
      status,
    }),
  );
}

function notFoundResponse(detail: string) {
  return jsonResponse({ detail }, 404);
}

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: string | URL | Request) => {
      const url =
        input instanceof URL
          ? input
          : new URL(typeof input === "string" ? input : input.url);
      const routeId = url.pathname.match(/^\/routes\/([^/]+)\//)?.[1];

      if (url.pathname === "/rankings") {
        return jsonResponse(rankingsPayload);
      }

      if (url.pathname === "/map/routes") {
        return jsonResponse(mapPayload);
      }

      if (url.pathname === "/routes/compare") {
        const ids = (url.searchParams.get("ids") ?? "").split(",").filter(Boolean);
        const routes = ids
          .map((id) =>
            id === "14"
              ? route14SummaryPayload
              : id === "49"
                ? route49SummaryPayload
                : null,
          )
          .filter(Boolean);

        return jsonResponse({
          ...comparePayload,
          route_ids: ids,
          routes,
        });
      }

      if (url.pathname === "/routes/14/summary") {
        return jsonResponse(route14SummaryPayload);
      }

      if (url.pathname === "/routes/49/summary") {
        return jsonResponse(route49SummaryPayload);
      }

      if (url.pathname === "/routes/14/segments" && url.searchParams.get("direction") === "1") {
        return jsonResponse(route14SegmentsPayload);
      }

      if (url.pathname === "/routes/14/stops/wait" && url.searchParams.get("direction") === "1") {
        return jsonResponse(route14StopWaitPayload);
      }

      if (routeId === "49" && url.pathname.endsWith("/segments")) {
        return notFoundResponse("No segments found for route_id=49 and direction=1");
      }

      if (routeId === "49" && url.pathname.endsWith("/stops/wait")) {
        return notFoundResponse(
          "No stop wait hotspots found for route_id=49 and direction=1",
        );
      }

      if (url.pathname.endsWith("/segments") || url.pathname.endsWith("/stops/wait")) {
        return notFoundResponse(`No published detail layer for ${routeId}`);
      }

      return notFoundResponse(`Unexpected request: ${url.pathname}`);
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("public pages", () => {
  it("renders the homepage editorial shell from the live rankings and map contract", async () => {
    const page = await HomePage({});
    const html = renderToStaticMarkup(page);

    expect(html).toContain("Where Muni");
    expect(html).toContain("Riders Lose");
    expect(html).toContain("Most Time");
    expect(html).toContain("Three Highest Rider-Loss Routes");
    expect(html).toContain("three routes with the highest published rider time loss");
    expect(html).toContain("MapLibre GL JS route surface");
    expect(html).toContain("A public map and ranking of where Muni riders lose the most time.");
    expect(html).toContain("Using the last 3 published months of route-delay data across San Francisco.");
    expect(html).toContain("Last updated");
    expect(html).toContain("expected rider time loss");
    expect(html).toContain("wait +0.8 min");
    expect(html).toContain("ride +1.5 min");
    expect(html).toContain("See full rankings");
    expect(html).toContain("See how we calculate time loss");
    expect(html).toContain("9:00-9:59 AM");
    expect(html).toContain("/routes/14");
  });

  it("renders the route detail page with the published corridor language", async () => {
    const page = await RouteDetailPage({ params: Promise.resolve({ routeId: "14" }) });
    const html = renderToStaticMarkup(page);

    expect(html).toContain("Route detail");
    expect(html).toContain(
      "Published route summary, corridor map, stop hotspot, and sample context.",
    );
    expect(html).toContain("16th St Mission -&gt; 24th St Mission");
    expect(html).toContain("Where does the wait pile up?");
    expect(html).toContain("When is it worst?");
    expect(html).toContain("Vs. system median");
    expect(html).toContain("MapLibre");
  });

  it("renders empty directional notices when route detail layers are not published", async () => {
    const page = await RouteDetailPage({ params: Promise.resolve({ routeId: "49" }) });
    const html = renderToStaticMarkup(page);

    expect(html).toContain("No directional segment layer is published for this route yet.");
    expect(html).toContain("No stop-wait hotspot layer is published for this route yet.");
  });

  it("renders compare, map, and methodology pages from the live API contract", async () => {
    const comparePage = await ComparePage({
      searchParams: Promise.resolve({ ids: "14,49" }),
    });
    const compareHtml = renderToStaticMarkup(comparePage);
    const mapHtml = renderToStaticMarkup(await MapPage());
    const rankingsHtml = renderToStaticMarkup(await RankingsPage());
    const methodologyHtml = renderToStaticMarkup(<MethodologyPage />);

    expect(compareHtml).toContain("Compare routes or corridors.");
    expect(compareHtml).toContain("Pick two to four published routes");
    expect(compareHtml).toContain("Compare uses the current published route snapshot.");
    expect(compareHtml).toContain("Median route loss");
    expect(compareHtml).toContain("Expected rider loss");
    expect(compareHtml).toContain("9:00-9:59 AM");
    expect(compareHtml).toContain("/routes/14");
    expect(mapHtml).toContain("Citywide route delay map");
    expect(mapHtml).toContain("expected rider time loss");
    expect(mapHtml).toContain("Transit-only lanes");
    expect(mapHtml).toContain("MapLibre GL JS citywide surface");
    expect(mapHtml).toContain("Show transit lane overlay");
    expect(rankingsHtml).toContain("Published route rankings");
    expect(rankingsHtml).toContain("current published snapshot");
    expect(rankingsHtml).toContain("Click any route row to open its route detail.");
    expect(rankingsHtml).toContain("9:00-9:59 AM");
    expect(rankingsHtml).toContain("/routes/14");
    expect(methodologyHtml).toContain("How the route time-loss number is calculated.");
    expect(methodologyHtml).toContain("Typical route time loss");
    expect(methodologyHtml).toContain("median full-trip in-vehicle loss");
    expect(methodologyHtml).toContain("grouped by route_id, not by route_id plus direction_id");
    expect(methodologyHtml).toContain("The current published metric combines two 511 data paths");
  });
});
