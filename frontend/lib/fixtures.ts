import { readFileSync } from "node:fs";
import path from "node:path";

function resolveFixturePath(...segments: string[]) {
  const configuredRoot = process.env.FIXTURES_ROOT?.trim();
  const candidateRoots = [
    configuredRoot,
    path.join(process.cwd(), "..", "fixtures"),
    path.join(process.cwd(), "fixtures"),
  ].filter((value): value is string => Boolean(value));

  let lastTriedPath = "";

  for (const root of candidateRoots) {
    const candidatePath = path.join(root, ...segments);

    try {
      readFileSync(candidatePath, "utf8");
      return candidatePath;
    } catch {
      lastTriedPath = candidatePath;
    }
  }

  throw new Error(
    `Unable to locate fixture ${segments.join("/")} from roots: ${candidateRoots.join(", ")}. Last attempted path: ${lastTriedPath}`,
  );
}

export function loadTransitLaneOverlay() {
  const overlayPath = resolveFixturePath(
    "geospatial",
    "transit_only_lanes",
    "minimal.geojson",
  );
  const overlay = JSON.parse(readFileSync(overlayPath, "utf8")) as {
    features: Array<{
      geometry: { coordinates: [number, number][] };
      properties?: {
        overlay_id?: string;
        route_hint?: string;
        segment_name?: string;
        street_name?: string;
      };
    }>;
  };

  return overlay.features.map((feature, featureIndex) => ({
    type: "Feature" as const,
    geometry: {
      type: "LineString" as const,
      coordinates: feature.geometry.coordinates,
    },
    properties: {
      in_vehicle_loss_minutes: 0,
      matched_full_trip_count: 0,
      matched_headway_interval_count: 0,
      matched_observed_stop_event_count: 0,
      metric_updated_at: "1970-01-01T00:00:00Z",
      metric: "context_overlay",
      metric_value: 0,
      overlay_id: feature.properties?.overlay_id ?? `overlay-${featureIndex}`,
      resolved_unmatched_observation_count: 0,
      route_id: `overlay-${featureIndex}`,
      route_hint: feature.properties?.route_hint ?? "",
      route_long_name: "Transit lane context",
      route_name: "Transit lane",
      route_short_name: "TL",
      segment_name: feature.properties?.segment_name ?? "Transit lane context",
      street_name: feature.properties?.street_name ?? "Transit lane",
      typical_trip_loss_minutes: 0,
      waiting_loss_minutes: 0,
      window: "all_day",
      worst_segment_label: "Context only",
      worst_stop_wait_label: "Context only",
      worst_time_band: "Not published",
    },
  }));
}
