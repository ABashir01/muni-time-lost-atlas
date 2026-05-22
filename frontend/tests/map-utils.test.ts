import {
  decorateContextRouteFeatures,
  decorateRouteFeatures,
  decorateSegmentFeatures,
  decorateStopHotspots,
  getMapBounds,
  getRouteLossColor,
} from "@/lib/map-utils";
import type { FeatureLine, StopWaitFeature } from "@/lib/types";

const routeFeature: FeatureLine = {
  type: "Feature",
  geometry: {
    type: "LineString",
    coordinates: [
      [-122.42, 37.75],
      [-122.41, 37.78],
    ],
  },
  properties: {
    in_vehicle_loss_minutes: 1.2,
    matched_full_trip_count: 4,
    matched_headway_interval_count: 3,
    matched_observed_stop_event_count: 8,
    metric_updated_at: "2026-05-08T19:30:00Z",
    resolved_unmatched_observation_count: 0,
    route_id: "14",
    route_long_name: "Mission",
    route_name: "Mission",
    route_short_name: "14",
    typical_trip_loss_minutes: 2.7,
    waiting_loss_minutes: 1.5,
    window: "all_day",
    worst_segment_label: "A -> B",
    worst_stop_wait_label: "Stop A",
    worst_time_band: "09:00-09:59",
  },
};

const segmentFeature: FeatureLine = {
  ...routeFeature,
  properties: {
    ...routeFeature.properties,
    direction_id: 1,
    direction_label: "Outbound",
    from_stop_id: "A",
    from_stop_name: "Stop A",
    matched_trip_segment_count: 2,
    scheduled_segment_minutes: 6,
    segment_in_vehicle_loss_minutes: 1.6,
    segment_label: "Stop A -> Stop B",
    segment_sequence: 1,
    segment_strategy: "adjacent_stop_pair",
    shape_id: "14_OB",
    to_stop_id: "B",
    to_stop_name: "Stop B",
  },
};

const stopFeature: StopWaitFeature = {
  type: "Feature",
  geometry: {
    type: "Point",
    coordinates: [-122.415, 37.772],
  },
  properties: {
    direction_id: 1,
    direction_label: "Outbound",
    matched_headway_interval_count: 2,
    metric_updated_at: "2026-05-08T19:30:00Z",
    observed_effective_wait_minutes: 7.4,
    route_id: "14",
    route_long_name: "Mission",
    route_name: "Mission",
    route_short_name: "14",
    scheduled_effective_wait_minutes: 5.1,
    stop_id: "A",
    stop_name: "Stop A",
    stop_wait_label: "Stop A (Outbound)",
    stop_wait_strategy: "first_stop_exact_match",
    waiting_loss_minutes: 2.3,
    window: "all_day",
  },
};

describe("map utils", () => {
  it("assigns route loss colors from the published threshold bands", () => {
    expect(getRouteLossColor(0)).toBe("#138646");
    expect(getRouteLossColor(1.1)).toBe("#0868d0");
    expect(getRouteLossColor(3.2)).toBe("#fcc000");
    expect(getRouteLossColor(6.3)).toBe("#e85c10");
    expect(getRouteLossColor(12)).toBe("#d81420");
  });

  it("decorates line and stop layers for map rendering", () => {
    const [decoratedRoute] = decorateRouteFeatures([routeFeature], { mode: "focus", focusRouteId: "14" });
    const [decoratedContextRoute] = decorateContextRouteFeatures([routeFeature]);
    const [decoratedSegment] = decorateSegmentFeatures([segmentFeature]);
    const [decoratedStop] = decorateStopHotspots([stopFeature]);

    expect(decoratedRoute.properties.map_color).toBe("#d81420");
    expect(decoratedRoute.properties.map_width).toBeCloseTo(4.75, 2);
    expect(decoratedContextRoute.properties.map_color).toBe("#728190");
    expect(decoratedContextRoute.properties.map_opacity).toBeGreaterThan(0.3);
    expect(decoratedSegment.properties.map_color).toBe("#e85c10");
    expect(decoratedStop.properties.map_color).toBe("#e85c10");
    expect(decoratedStop.properties.map_radius).toBeGreaterThan(10);
  });

  it("computes padded bounds across route, segment, and stop layers", () => {
    const bounds = getMapBounds({
      routeFeatures: [routeFeature],
      segmentFeatures: [segmentFeature],
      stopFeatures: [stopFeature],
    });

    expect(bounds).not.toBeNull();
    expect(bounds?.[0][0]).toBeLessThan(-122.42);
    expect(bounds?.[0][1]).toBeLessThan(37.75);
    expect(bounds?.[1][0]).toBeGreaterThan(-122.41);
    expect(bounds?.[1][1]).toBeGreaterThan(37.78);
  });
});
