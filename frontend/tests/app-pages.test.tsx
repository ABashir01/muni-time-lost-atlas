import { readFileSync } from "node:fs";
import path from "node:path";
import { renderToStaticMarkup } from "react-dom/server";
import ComparePage from "@/app/compare/page";
import HomePage from "@/app/page";
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
    expect(html).toContain("Mission");
    expect(html).toContain("Historical/static API snapshot");
    expect(html).toContain("extra time per trip");
  });

  it("renders the route detail page with the published corridor language", async () => {
    const page = await RouteDetailPage({ params: Promise.resolve({ routeId: "14" }) });
    const html = renderToStaticMarkup(page);

    expect(html).toContain("Route detail");
    expect(html).toContain("16th St Mission -&gt; 24th St Mission");
    expect(html).toContain("Worst published stop wait");
    expect(html).toContain("Worst time window");
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
    const methodologyHtml = renderToStaticMarkup(<MethodologyPage />);

    expect(compareHtml).toContain("Put the routes next to each other.");
    expect(compareHtml).toContain("Compare accepts two to four route ids");
    expect(compareHtml).toContain("Worst selected route");
    expect(mapHtml).toContain("The citywide evidence surface.");
    expect(mapHtml).toContain("Highest published loss");
    expect(mapHtml).toContain("Transit-only lane overlay");
    expect(methodologyHtml).toContain("Typical trip: +X.X min is the public promise.");
    expect(methodologyHtml).toContain("Plain-English contract");
    expect(methodologyHtml).toContain("Waiting loss");
  });
});
