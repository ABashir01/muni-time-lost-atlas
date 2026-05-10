export type RouteSummary = {
  in_vehicle_loss_minutes: number;
  matched_full_trip_count: number;
  matched_headway_interval_count: number;
  matched_observed_stop_event_count: number;
  metric_updated_at: string;
  rank?: number;
  resolved_unmatched_observation_count: number;
  route_id: string;
  route_long_name: string;
  route_name: string;
  route_short_name: string;
  typical_trip_loss_minutes: number;
  waiting_loss_minutes: number;
  window: string;
  worst_segment_label: string;
  worst_stop_wait_label: string;
  worst_time_band: string;
};

export type FeatureLine = {
  type: "Feature";
  geometry: {
    type: "LineString";
    coordinates: [number, number][];
  };
  properties: RouteSummary &
    Partial<{
      direction_id: number;
      direction_label: string;
      from_stop_id: string;
      from_stop_name: string;
      matched_trip_segment_count: number;
      metric: string;
      metric_value: number;
      scheduled_segment_minutes: number;
      segment_in_vehicle_loss_minutes: number;
      segment_label: string;
      segment_sequence: number;
      segment_strategy: string;
      shape_id: string;
      to_stop_id: string;
      to_stop_name: string;
    }>;
};

export type RankingsFixture = {
  metric: string;
  mode: string;
  routes: RouteSummary[];
  window: string;
};

export type CompareFixture = {
  route_ids: string[];
  routes: RouteSummary[];
  window: string;
};

export type RouteSegmentFixture = {
  direction_id: number;
  direction_label: string;
  features: FeatureLine[];
  metric_updated_at: string;
  route_id: string;
  route_long_name: string;
  route_name: string;
  route_short_name: string;
  type: "FeatureCollection";
  window: string;
};

export type RouteMapFixture = {
  features: FeatureLine[];
  metric: string;
  type: "FeatureCollection";
  window: string;
};

export type MethodologySection = {
  kicker: string;
  title: string;
  formula?: string;
  paragraphs: string[];
  bullets?: string[];
};
