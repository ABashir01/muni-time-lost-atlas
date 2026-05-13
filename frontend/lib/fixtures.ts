import { readFileSync } from "node:fs";
import path from "node:path";

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
      in_vehicle_loss_minutes: 0,
      matched_full_trip_count: 0,
      matched_headway_interval_count: 0,
      matched_observed_stop_event_count: 0,
      metric_updated_at: "1970-01-01T00:00:00Z",
      resolved_unmatched_observation_count: 0,
      route_id: `overlay-${featureIndex}`,
      route_long_name: "Transit lane context",
      route_name: "Transit lane",
      route_short_name: "TL",
      typical_trip_loss_minutes: 0,
      waiting_loss_minutes: 0,
      window: "all_day",
      worst_segment_label: "Context only",
      worst_stop_wait_label: "Context only",
      worst_time_band: "Not published",
      metric_value: 0,
    },
  }));
}
