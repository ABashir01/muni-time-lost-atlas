import type {
  CompareResponse,
  FeatureLine,
  PointGeometry,
  RankingsResponse,
  RouteIdentity,
  RouteMapResponse,
  RouteSegmentsResponse,
  RouteStopWaitResponse,
  RouteSummary,
  StopWaitFeature,
} from "@/lib/types";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_WINDOW = "all_day";
const PRIMARY_METRIC = "typical_trip_loss_minutes";

export class ApiRequestError extends Error {
  detail?: string;
  path: string;
  status: number;

  constructor(path: string, status: number, message: string, detail?: string) {
    super(message);
    this.name = "ApiRequestError";
    this.detail = detail;
    this.path = path;
    this.status = status;
  }
}

export function getApiBaseUrl() {
  return (
    process.env.API_BASE_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    DEFAULT_API_BASE_URL
  ).replace(/\/+$/, "");
}

export async function getRankings() {
  return fetchApi(
    "/rankings",
    { metric: PRIMARY_METRIC, mode: "routes", window: DEFAULT_WINDOW },
    parseRankingsResponse,
  );
}

export async function getRouteSummary(routeId: string) {
  return fetchApi(
    `/routes/${encodeURIComponent(routeId)}/summary`,
    { window: DEFAULT_WINDOW },
    parseRouteSummary,
  );
}

export async function getRouteSegments(routeId: string, direction: number) {
  return fetchApi(
    `/routes/${encodeURIComponent(routeId)}/segments`,
    { direction: String(direction), window: DEFAULT_WINDOW },
    parseRouteSegmentsResponse,
  );
}

export async function getRouteStopWait(routeId: string, direction: number) {
  return fetchApi(
    `/routes/${encodeURIComponent(routeId)}/stops/wait`,
    { direction: String(direction), window: DEFAULT_WINDOW },
    parseRouteStopWaitResponse,
  );
}

export async function getCompare(routeIds: string[]) {
  return fetchApi(
    "/routes/compare",
    { ids: routeIds.join(","), window: DEFAULT_WINDOW },
    parseCompareResponse,
  );
}

export async function getMapRoutes() {
  return fetchApi(
    "/map/routes",
    { metric: PRIMARY_METRIC, window: DEFAULT_WINDOW },
    parseRouteMapResponse,
  );
}

async function fetchApi<T>(
  pathname: string,
  query: Record<string, string>,
  parse: (value: unknown, path: string) => T,
) {
  const url = new URL(`${getApiBaseUrl()}${pathname}`);
  Object.entries(query).forEach(([key, value]) => {
    url.searchParams.set(key, value);
  });

  const response = await fetch(url, {
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw await createApiRequestError(pathname, response);
  }

  const payload = await response.json();
  return parse(payload, pathname);
}

async function createApiRequestError(pathname: string, response: Response) {
  const fallbackMessage = `API request failed with status ${response.status}`;

  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      return new ApiRequestError(pathname, response.status, fallbackMessage, payload.detail);
    }
  } catch {}

  return new ApiRequestError(pathname, response.status, fallbackMessage);
}

function parseRankingsResponse(value: unknown, path: string): RankingsResponse {
  const object = expectObject(value, path);

  return {
    metric: expectString(object.metric, `${path}.metric`),
    mode: expectString(object.mode, `${path}.mode`),
    routes: expectArray(object.routes, `${path}.routes`).map((route, index) =>
      parseRankedRouteSummary(route, `${path}.routes[${index}]`),
    ),
    window: expectString(object.window, `${path}.window`),
  };
}

function parseCompareResponse(value: unknown, path: string): CompareResponse {
  const object = expectObject(value, path);

  return {
    route_ids: expectArray(object.route_ids, `${path}.route_ids`).map((routeId, index) =>
      expectString(routeId, `${path}.route_ids[${index}]`),
    ),
    routes: expectArray(object.routes, `${path}.routes`).map((route, index) =>
      parseRouteSummary(route, `${path}.routes[${index}]`),
    ),
    window: expectString(object.window, `${path}.window`),
  };
}

function parseRouteSegmentsResponse(value: unknown, path: string): RouteSegmentsResponse {
  const object = expectObject(value, path);
  const features = expectArray(object.features, `${path}.features`)
    .map((feature, index) => parseSegmentFeature(feature, `${path}.features[${index}]`))
    .sort(
      (left, right) =>
        (left.properties.segment_sequence ?? Number.MAX_SAFE_INTEGER) -
        (right.properties.segment_sequence ?? Number.MAX_SAFE_INTEGER),
    );

  return {
    direction_id: expectInteger(object.direction_id, `${path}.direction_id`),
    direction_label: expectString(object.direction_label, `${path}.direction_label`),
    features,
    metric_updated_at: expectString(object.metric_updated_at, `${path}.metric_updated_at`),
    route_id: expectString(object.route_id, `${path}.route_id`),
    route_long_name: optionalString(object.route_long_name, ""),
    route_name: expectString(object.route_name, `${path}.route_name`),
    route_short_name: optionalString(
      object.route_short_name,
      expectString(object.route_id, `${path}.route_id`),
    ),
    type: expectLiteral(object.type, "FeatureCollection", `${path}.type`),
    window: expectString(object.window, `${path}.window`),
  };
}

function parseRouteMapResponse(value: unknown, path: string): RouteMapResponse {
  const object = expectObject(value, path);

  return {
    features: expectArray(object.features, `${path}.features`).map((feature, index) =>
      parseMapFeature(feature, `${path}.features[${index}]`),
    ),
    metric: expectString(object.metric, `${path}.metric`),
    type: expectLiteral(object.type, "FeatureCollection", `${path}.type`),
    window: expectString(object.window, `${path}.window`),
  };
}

function parseRouteStopWaitResponse(value: unknown, path: string): RouteStopWaitResponse {
  const object = expectObject(value, path);
  const features = expectArray(object.features, `${path}.features`)
    .map((feature, index) => parseStopWaitFeature(feature, `${path}.features[${index}]`))
    .sort(
      (left, right) =>
        (right.properties.waiting_loss_minutes ?? 0) - (left.properties.waiting_loss_minutes ?? 0),
    );

  return {
    direction_id: expectInteger(object.direction_id, `${path}.direction_id`),
    direction_label: expectString(object.direction_label, `${path}.direction_label`),
    features,
    metric_updated_at: expectString(object.metric_updated_at, `${path}.metric_updated_at`),
    route_id: expectString(object.route_id, `${path}.route_id`),
    route_long_name: optionalString(object.route_long_name, ""),
    route_name: expectString(object.route_name, `${path}.route_name`),
    route_short_name: optionalString(
      object.route_short_name,
      expectString(object.route_id, `${path}.route_id`),
    ),
    type: expectLiteral(object.type, "FeatureCollection", `${path}.type`),
    window: expectString(object.window, `${path}.window`),
  };
}

function parseRankedRouteSummary(value: unknown, path: string): RouteSummary {
  const object = expectObject(value, path);
  const summary = parseRouteSummary(object, path);

  return {
    ...summary,
    rank: expectInteger(object.rank, `${path}.rank`),
  };
}

export function parseRouteSummary(value: unknown, path: string): RouteSummary {
  const object = expectObject(value, path);
  const routeId = expectString(object.route_id, `${path}.route_id`);
  const routeName = expectString(object.route_name, `${path}.route_name`);

  return {
    direction_id: optionalInteger(object.direction_id, null),
    direction_label: optionalNullableString(object.direction_label, null),
    in_vehicle_loss_minutes: optionalNumber(object.in_vehicle_loss_minutes, 0),
    matched_full_trip_count: expectInteger(
      object.matched_full_trip_count,
      `${path}.matched_full_trip_count`,
    ),
    matched_headway_interval_count: expectInteger(
      object.matched_headway_interval_count,
      `${path}.matched_headway_interval_count`,
    ),
    matched_observed_stop_event_count: expectInteger(
      object.matched_observed_stop_event_count,
      `${path}.matched_observed_stop_event_count`,
    ),
    metric_updated_at: expectString(object.metric_updated_at, `${path}.metric_updated_at`),
    rank: optionalInteger(object.rank, undefined),
    resolved_unmatched_observation_count: expectInteger(
      object.resolved_unmatched_observation_count,
      `${path}.resolved_unmatched_observation_count`,
    ),
    route_id: routeId,
    route_long_name: optionalString(object.route_long_name, ""),
    route_name: routeName,
    route_short_name: optionalString(object.route_short_name, routeId),
    typical_trip_loss_minutes: optionalNumber(object.typical_trip_loss_minutes, 0),
    waiting_loss_minutes: optionalNumber(object.waiting_loss_minutes, 0),
    window: expectString(object.window, `${path}.window`),
    worst_segment_label: optionalString(object.worst_segment_label, "Not published"),
    worst_stop_wait_label: optionalString(object.worst_stop_wait_label, "Not published"),
    worst_time_band: optionalString(object.worst_time_band, "Not published"),
  };
}

function parseSegmentFeature(value: unknown, path: string): FeatureLine {
  const object = expectObject(value, path);
  const geometry = parseLineGeometry(object.geometry, `${path}.geometry`);
  const properties = expectObject(object.properties, `${path}.properties`);
  const routeIdentity = parseRouteIdentity(properties, `${path}.properties`);

  return {
    type: expectLiteral(object.type, "Feature", `${path}.type`),
    geometry,
    properties: {
      ...routeIdentity,
      direction_id: expectInteger(properties.direction_id, `${path}.properties.direction_id`),
      direction_label: optionalString(properties.direction_label, "Unknown direction"),
      from_stop_id: expectString(properties.from_stop_id, `${path}.properties.from_stop_id`),
      from_stop_name: expectString(
        properties.from_stop_name,
        `${path}.properties.from_stop_name`,
      ),
      matched_trip_segment_count: expectInteger(
        properties.matched_trip_segment_count,
        `${path}.properties.matched_trip_segment_count`,
      ),
      scheduled_segment_minutes: optionalNumber(
        properties.scheduled_segment_minutes,
        0,
      ),
      segment_in_vehicle_loss_minutes: optionalNumber(
        properties.segment_in_vehicle_loss_minutes,
        0,
      ),
      segment_label: expectString(properties.segment_label, `${path}.properties.segment_label`),
      segment_sequence: expectInteger(
        properties.segment_sequence,
        `${path}.properties.segment_sequence`,
      ),
      segment_strategy: expectString(
        properties.segment_strategy,
        `${path}.properties.segment_strategy`,
      ),
      shape_id: expectString(properties.shape_id, `${path}.properties.shape_id`),
      to_stop_id: expectString(properties.to_stop_id, `${path}.properties.to_stop_id`),
      to_stop_name: expectString(properties.to_stop_name, `${path}.properties.to_stop_name`),
    },
  };
}

function parseMapFeature(value: unknown, path: string): FeatureLine {
  const object = expectObject(value, path);
  const geometry = parseLineGeometry(object.geometry, `${path}.geometry`);
  const properties = expectObject(object.properties, `${path}.properties`);
  const routeSummary = parseRouteSummary(properties, `${path}.properties`);

  return {
    type: expectLiteral(object.type, "Feature", `${path}.type`),
    geometry,
    properties: {
      ...routeSummary,
      metric: expectString(properties.metric, `${path}.properties.metric`),
      metric_value: optionalNumber(properties.metric_value, 0),
    },
  };
}

function parseStopWaitFeature(value: unknown, path: string): StopWaitFeature {
  const object = expectObject(value, path);
  const geometry = parsePointGeometry(object.geometry, `${path}.geometry`);
  const properties = expectObject(object.properties, `${path}.properties`);
  const routeIdentity = parseRouteIdentity(properties, `${path}.properties`);

  return {
    type: expectLiteral(object.type, "Feature", `${path}.type`),
    geometry,
    properties: {
      ...routeIdentity,
      direction_id: expectInteger(properties.direction_id, `${path}.properties.direction_id`),
      direction_label: optionalString(properties.direction_label, "Unknown direction"),
      matched_headway_interval_count: expectInteger(
        properties.matched_headway_interval_count,
        `${path}.properties.matched_headway_interval_count`,
      ),
      observed_effective_wait_minutes: optionalNumber(
        properties.observed_effective_wait_minutes,
        0,
      ),
      scheduled_effective_wait_minutes: optionalNumber(
        properties.scheduled_effective_wait_minutes,
        0,
      ),
      stop_id: expectString(properties.stop_id, `${path}.properties.stop_id`),
      stop_name: expectString(properties.stop_name, `${path}.properties.stop_name`),
      stop_wait_label: expectString(
        properties.stop_wait_label,
        `${path}.properties.stop_wait_label`,
      ),
      stop_wait_strategy: expectString(
        properties.stop_wait_strategy,
        `${path}.properties.stop_wait_strategy`,
      ),
      waiting_loss_minutes: optionalNumber(properties.waiting_loss_minutes, 0),
    },
  };
}

function parseRouteIdentity(value: Record<string, unknown>, path: string): RouteIdentity {
  const routeId = expectString(value.route_id, `${path}.route_id`);

  return {
    metric_updated_at: expectString(value.metric_updated_at, `${path}.metric_updated_at`),
    route_id: routeId,
    route_long_name: optionalString(value.route_long_name, ""),
    route_name: expectString(value.route_name, `${path}.route_name`),
    route_short_name: optionalString(value.route_short_name, routeId),
    window: expectString(value.window, `${path}.window`),
  };
}

function parseLineGeometry(value: unknown, path: string) {
  const object = expectObject(value, path);
  const type = expectString(object.type, `${path}.type`);

  if (type === "LineString") {
    return {
      coordinates: expectCoordinateArray(object.coordinates, `${path}.coordinates`),
      type,
    } as const;
  }

  if (type === "MultiLineString") {
    return {
      coordinates: expectArray(object.coordinates, `${path}.coordinates`).map((segment, index) =>
        expectCoordinateArray(segment, `${path}.coordinates[${index}]`),
      ),
      type,
    } as const;
  }

  throw new Error(`${path}.type must be LineString or MultiLineString`);
}

function parsePointGeometry(value: unknown, path: string): PointGeometry {
  const object = expectObject(value, path);

  return {
    coordinates: expectCoordinate(object.coordinates, `${path}.coordinates`),
    type: expectLiteral(object.type, "Point", `${path}.type`),
  };
}

function expectCoordinateArray(value: unknown, path: string) {
  return expectArray(value, path).map((entry, index) => expectCoordinate(entry, `${path}[${index}]`));
}

function expectCoordinate(value: unknown, path: string): [number, number] {
  const coordinate = expectArray(value, path);
  if (coordinate.length !== 2) {
    throw new Error(`${path} must contain exactly two numeric coordinates`);
  }

  return [
    expectNumber(coordinate[0], `${path}[0]`),
    expectNumber(coordinate[1], `${path}[1]`),
  ];
}

function expectObject(value: unknown, path: string) {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`${path} must be an object`);
  }

  return value as Record<string, unknown>;
}

function expectArray(value: unknown, path: string) {
  if (!Array.isArray(value)) {
    throw new Error(`${path} must be an array`);
  }

  return value;
}

function expectString(value: unknown, path: string) {
  if (typeof value !== "string") {
    throw new Error(`${path} must be a string`);
  }

  return value;
}

function expectNumber(value: unknown, path: string) {
  if (typeof value !== "number" || Number.isNaN(value) || !Number.isFinite(value)) {
    throw new Error(`${path} must be a finite number`);
  }

  return value;
}

function expectInteger(value: unknown, path: string) {
  const numericValue = expectNumber(value, path);
  if (!Number.isInteger(numericValue)) {
    throw new Error(`${path} must be an integer`);
  }

  return numericValue;
}

function expectLiteral<T extends string>(value: unknown, literal: T, path: string) {
  if (value !== literal) {
    throw new Error(`${path} must equal ${literal}`);
  }

  return literal;
}

function optionalString(value: unknown, fallback: string) {
  return typeof value === "string" ? value : value == null ? fallback : expectString(value, "value");
}

function optionalNullableString<T extends string | null>(value: unknown, fallback: T) {
  return typeof value === "string" ? value : value == null ? fallback : expectString(value, "value");
}

function optionalNumber(value: unknown, fallback: number) {
  return typeof value === "number" ? expectNumber(value, "value") : value == null ? fallback : expectNumber(value, "value");
}

function optionalInteger<T extends number | null | undefined>(value: unknown, fallback: T) {
  return typeof value === "number"
    ? expectInteger(value, "value")
    : value == null
      ? fallback
      : expectInteger(value, "value");
}
