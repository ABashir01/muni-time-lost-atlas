export type RouteSummary = {
  direction_id?: number | null;
  direction_label?: string | null;
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

export type LineStringGeometry = {
  type: "LineString";
  coordinates: [number, number][];
};

export type MultiLineStringGeometry = {
  type: "MultiLineString";
  coordinates: [number, number][][];
};

export type PointGeometry = {
  type: "Point";
  coordinates: [number, number];
};

export type MapCoordinate = [number, number];

export type MapBounds = [MapCoordinate, MapCoordinate];

export type MapRouteBadge = {
  coordinate: MapCoordinate;
  fallback_candidate_coordinates: MapCoordinate[];
  route_id: string;
  route_short_name: string;
  stop_candidate_coordinates: MapCoordinate[];
};

export type MapNeighborhoodLabel = {
  coordinate: MapCoordinate;
  text: string;
};

export type RouteIdentity = {
  metric_updated_at: string;
  route_id: string;
  route_long_name: string;
  route_name: string;
  route_short_name: string;
  window: string;
};

export type FeatureLine = {
  type: "Feature";
  geometry: LineStringGeometry | MultiLineStringGeometry;
  properties: RouteIdentity &
    Partial<{
      direction_id: number | null;
      direction_label: string | null;
      from_stop_id: string;
      from_stop_name: string;
      in_vehicle_loss_minutes: number;
      matched_trip_segment_count: number;
      matched_full_trip_count: number;
      matched_headway_interval_count: number;
      matched_observed_stop_event_count: number;
      metric: string;
      metric_value: number;
      overlay_id: string;
      rank: number;
      resolved_unmatched_observation_count: number;
      scheduled_segment_minutes: number;
      segment_name: string;
      segment_in_vehicle_loss_minutes: number;
      segment_label: string;
      segment_sequence: number;
      segment_strategy: string;
      shape_id: string;
      street_name: string;
      to_stop_id: string;
      to_stop_name: string;
      typical_trip_loss_minutes: number;
      route_hint: string;
      waiting_loss_minutes: number;
      worst_segment_label: string;
      worst_stop_wait_label: string;
      worst_time_band: string;
    }>;
};

export type StopWaitFeature = {
  type: "Feature";
  geometry: PointGeometry;
  properties: RouteIdentity &
    Partial<{
      direction_id: number | null;
      direction_label: string | null;
      in_vehicle_loss_minutes: number;
      matched_headway_interval_count: number;
      matched_full_trip_count: number;
      matched_observed_stop_event_count: number;
      observed_effective_wait_minutes: number;
      rank: number;
      resolved_unmatched_observation_count: number;
      scheduled_effective_wait_minutes: number;
      stop_id: string;
      stop_name: string;
      stop_wait_label: string;
      stop_wait_strategy: string;
      typical_trip_loss_minutes: number;
      waiting_loss_minutes: number;
      worst_segment_label: string;
      worst_stop_wait_label: string;
      worst_time_band: string;
    }>;
};

export type RankingsResponse = {
  metric: string;
  mode: string;
  routes: RouteSummary[];
  window: string;
};

export type CompareResponse = {
  route_ids: string[];
  routes: RouteSummary[];
  window: string;
};

export type RouteSegmentsResponse = {
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

export type RouteMapResponse = {
  features: FeatureLine[];
  metric: string;
  type: "FeatureCollection";
  window: string;
};

export type RouteStopWaitResponse = {
  direction_id: number;
  direction_label: string;
  features: StopWaitFeature[];
  metric_updated_at: string;
  route_id: string;
  route_long_name: string;
  route_name: string;
  route_short_name: string;
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

export type DataNotice = {
  detail?: string;
  message: string;
  title: string;
};
