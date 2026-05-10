import { readFileSync } from "node:fs";
import path from "node:path";
import type {
  CompareFixture,
  RankingsFixture,
  RouteMapFixture,
  RouteSegmentFixture,
  RouteSummary,
} from "@/lib/types";

const fixturesDir = path.join(process.cwd(), "..", "fixtures", "api");

function loadJson<T>(fileName: string): T {
  return JSON.parse(readFileSync(path.join(fixturesDir, fileName), "utf8")) as T;
}

export const rankingsFixture = loadJson<RankingsFixture>(
  "rankings_all_day_typical_trip_loss_minutes_routes.json",
);

export const route14SummaryFixture = loadJson<RouteSummary>("route_14_summary_all_day.json");

export const route14SegmentsFixture = loadJson<RouteSegmentFixture>(
  "route_14_segments_direction_1_all_day.json",
);

export const compareFixture = loadJson<CompareFixture>("routes_compare_14_49_all_day.json");

export const routeMapFixture = loadJson<RouteMapFixture>(
  "map_routes_all_day_typical_trip_loss_minutes.json",
);

export function loadTransitLaneOverlay() {
  const overlayDir = path.join(
    process.cwd(),
    "..",
    "fixtures",
    "geospatial",
    "transit_only_lanes",
    "minimal.geojson",
  );
  const overlay = JSON.parse(readFileSync(overlayDir, "utf8")) as {
    features: Array<{
      geometry: { coordinates: [number, number][] };
    }>;
  };

  return overlay.features.map((feature, featureIndex) => ({
    type: "Feature" as const,
    geometry: {
      type: "LineString" as const,
      coordinates: feature.geometry.coordinates,
    },
    properties: {
      ...rankingsFixture.routes[0],
      route_id: `overlay-${featureIndex}`,
      route_short_name: "TL",
      route_name: "Transit lane",
      route_long_name: "Transit lane context",
      metric_value: 0,
    },
  }));
}
