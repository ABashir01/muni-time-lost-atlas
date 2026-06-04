import {
  ApiRequestError,
  getCompare,
  getMapRoutes,
  getRankings,
  getRouteSegments,
  getRouteStopWait,
  getRouteSummary,
} from "@/lib/api";
import { loadTransitLaneOverlay } from "@/lib/fixtures";
import type {
  CompareResponse,
  DataNotice,
  FeatureLine,
  MapBounds,
  MapNeighborhoodLabel,
  MapRouteBadge,
  MethodologySection,
  RouteMapResponse,
  RouteSegmentsResponse,
  RouteStopWaitResponse,
  RouteSummary,
} from "@/lib/types";
import { median, routeLossShares } from "@/lib/utils";

const transitLaneOverlay = loadTransitLaneOverlay();
const preferredDirections = [1, 0] as const;
const homepageHeroBounds: MapBounds = [
  [-122.511, 37.708],
  [-122.389, 37.811],
];
const homepageNeighborhoodLabels: MapNeighborhoodLabel[] = [
  { coordinate: [-122.485, 37.779], text: "Richmond" },
  { coordinate: [-122.482, 37.746], text: "Sunset" },
  { coordinate: [-122.405, 37.794], text: "Chinatown" },
  { coordinate: [-122.421, 37.758], text: "Mission" },
  { coordinate: [-122.394, 37.732], text: "Bayview" },
];
const homepageFeaturedRouteColors = ["#d81420", "#e85c10", "#fcc000"] as const;
const defaultFeatureAnchorRatios = [0.5, 0.38, 0.62, 0.26, 0.74] as const;

type HomepageHeroMap = {
  backgroundFeatures: FeatureLine[];
  featuredColorByRouteId: Record<string, string>;
  featuredFeatures: FeatureLine[];
  neighborhoodLabels: MapNeighborhoodLabel[];
  routeBadges: MapRouteBadge[];
  viewportBounds: MapBounds;
};

const methodologySections: MethodologySection[] = [
  {
    kicker: "Headline metric",
    title: "Typical extra time on a full one-way trip",
    paragraphs: [
      "The homepage headline uses Typical trip: +X.X min because it is direct, rider-facing, and honest about the MVP scope.",
      "It combines extra waiting time and extra in-vehicle travel time instead of falling back to an on-time percentage or an operations-only index.",
    ],
  },
  {
    kicker: "Waiting loss",
    title: "Extra waiting is published separately, not hidden inside a score.",
    formula: "E(W) = E(H)/2 + V(H)/(2E(H))\nL_wait = max(0, W_obs - W_sched)",
    paragraphs: [
      "Irregular headways increase effective passenger waiting even when average scheduled service looks reasonable.",
      "For the first implementation, waiting loss is measured from exact matched first-stop events only so the published value stays conservative.",
    ],
    bullets: [
      "No fuzzy reconciliation across missing trips",
      "No inferred headways across unmatched observations",
      "Unmatched rows stay visible in coverage counts instead of being blended into the metric numerator",
    ],
  },
  {
    kicker: "In-vehicle loss",
    title: "Slow travel is the extra runtime after boarding.",
    formula:
      "L_veh(k) = max(0, T_obs_full(k) - T_base_full(k))\nL_typical(route, W) = L_wait(route, W) + median(L_veh(k))",
    paragraphs: [
      "The first MVP baseline is scheduled trip time. If a trip is faster than schedule, the public-facing loss is clamped at zero rather than treated as negative loss.",
      "The current joined model exposes matched first-stop and last-stop arrivals, so the first full-trip proxy is terminal to terminal.",
    ],
  },
  {
    kicker: "Caveats",
    title: "What the metric does not claim",
    paragraphs: [
      "It is not a passenger-weighted population average, not a causal proof for why a route is slow, and not full coverage of unmatched historic rows.",
      "The historical/static frontend keeps those caveats visible instead of burying them behind generic dashboard chrome.",
    ],
    bullets: [
      "Current historical window support is all_day only",
      "Bunching is interpreted as rider consequence context, not a standalone published endpoint yet",
      "Transit-only lanes are shown as spatial context, not as causal evidence",
    ],
  },
];

export type MapPageData = Awaited<ReturnType<typeof getMapPageData>>;
export type RankingsPageData = Awaited<ReturnType<typeof getRankingsPageData>>;
export type RouteDetailPageData = Awaited<ReturnType<typeof getRouteDetailPageData>>;

type ReadyRouteDetailPageData = {
  kind: "ready";
  mapFeatures: RouteMapResponse["features"];
  mapNotice?: DataNotice;
  peers: RouteSummary[];
  peersNotice?: DataNotice;
  rankedRouteCount: number;
  routeRank: number | null;
  segmentCollection: RouteSegmentsResponse | null;
  segmentNotice?: DataNotice;
  stopWaitCollection: RouteStopWaitResponse | null;
  stopWaitNotice?: DataNotice;
  summary: RouteSummary;
  systemMedianTypicalTripLoss: number;
  transitLaneOverlay: FeatureLine[];
  waitingShare: number;
};

type FailedRouteDetailPageData = {
  kind: "error";
  notice: DataNotice;
  routeId: string;
};

type SuccessfulResult<T> = { data: T; ok: true };
type FailedResult = { error: unknown; ok: false };

export async function getRouteIds() {
  const rankingsResult = await safeLoad(getRankings);
  return rankingsResult.ok ? rankingsResult.data.routes.map((route) => route.route_id) : [];
}

export async function getHomepageData() {
  const [rankingsResult, mapResult] = await Promise.all([
    safeLoad(getRankings),
    safeLoad(getMapRoutes),
  ]);
  const rankings = rankingsResult.ok ? rankingsResult.data.routes : [];
  const map = mapResult.ok ? mapResult.data : emptyMapResponse();
  const notices: DataNotice[] = [];

  if (!rankingsResult.ok) {
    notices.push(
      buildErrorNotice(
        "Homepage rankings are unavailable right now.",
        "The live rankings feed could not be loaded.",
        rankingsResult.error,
      ),
    );
  } else if (rankings.length === 0) {
    notices.push(
      buildEmptyNotice(
        "No published route rankings are available yet.",
        "The homepage will populate once the API returns at least one ranked route.",
      ),
    );
  }

  if (!mapResult.ok) {
    notices.push(
      buildErrorNotice(
        "Homepage map data is unavailable right now.",
        "The live map surface could not be loaded.",
        mapResult.error,
      ),
    );
  } else if (map.features.length === 0) {
    notices.push(
      buildEmptyNotice(
        "No published route geometries are available yet.",
        "The map hero will populate once the API returns route corridors.",
      ),
    );
  }

  const heroMap = await buildHomepageHeroMap(rankings, map.features);

  return {
    heroMap,
    lastUpdatedAt: rankings[0]?.metric_updated_at ?? null,
    map,
    notices,
    problemTypes: [
      {
        copy: "You spend more time standing around because buses arrive later than expected or show up unevenly.",
        icon: "waiting",
        symbol: "O",
        title: "Waiting",
      },
      {
        copy: "Once you board, the trip itself takes longer because of traffic, red lights, and slow stop-by-stop movement.",
        icon: "travel",
        symbol: "=",
        title: "Slow travel",
      },
      {
        copy: "Buses bunch together, which creates a long gap before the next vehicle arrives.",
        icon: "bunching",
        symbol: "|||",
        title: "Bunching",
      },
    ],
    rankings,
    transitLaneOverlay,
    windowLabel: "All day",
  };
}

export async function getComparePageData(ids?: string | string[]) {
  const requestedIds = parseRequestedIds(ids);
  const requestedSelectionIds =
    requestedIds.length >= 2 ? requestedIds.slice(0, 4) : [];
  const [rankingsResult, compareResult] = await Promise.all([
    safeLoad(getRankings),
    requestedSelectionIds.length >= 2
      ? safeLoad(() => getCompare(requestedSelectionIds))
      : Promise.resolve(null),
  ]);
  const rankedRoutes = rankingsResult.ok ? rankingsResult.data.routes : [];
  const defaultIds = rankedRoutes.slice(0, 2).map((route) => route.route_id);
  const selectedIds =
    requestedSelectionIds.length >= 2 ? requestedSelectionIds : defaultIds.slice(0, 4);
  const availableRoutes = buildRouteCatalog(
    rankedRoutes,
    compareResult?.ok ? compareResult.data : undefined,
  );
  const availableRouteById = new Map(
    availableRoutes.map((route) => [route.route_id, route] as const),
  );
  const selectedRoutes = compareResult?.ok
    ? compareResult.data.routes
    : selectedIds
        .map((routeId) => availableRouteById.get(routeId))
        .filter((route): route is RouteSummary => Boolean(route));
  const leadingRoute = selectedRoutes.reduce<RouteSummary | null>((currentLeader, route) => {
    if (!currentLeader) {
      return route;
    }

    return route.typical_trip_loss_minutes > currentLeader.typical_trip_loss_minutes
      ? route
      : currentLeader;
  }, null);
  const notices: DataNotice[] = [];

  if (!rankingsResult.ok) {
    notices.push(
      buildErrorNotice(
        "Route selection is unavailable right now.",
        "The compare controls could not load the published route catalog.",
        rankingsResult.error,
      ),
    );
  } else if (availableRoutes.length < 2) {
    notices.push(
      buildEmptyNotice(
        "At least two published routes are required to compare.",
        "The compare view will populate once the rankings surface returns enough routes.",
      ),
    );
  }

  if (compareResult && !compareResult.ok) {
    notices.push(
      buildErrorNotice(
        "Compare results are unavailable right now.",
        "The live compare endpoint did not return a usable route set.",
        compareResult.error,
      ),
    );
  } else if (selectedRoutes.length < 2) {
    notices.push(
      buildEmptyNotice(
        "Pick two to four routes to produce a compare readout.",
        "The current selection does not contain enough published routes yet.",
      ),
    );
  }

  return {
    availableRoutes,
    compareLimitations: [
      "Compare uses the current published route snapshot.",
      "The current release publishes one historical summary per route.",
    ],
    leadingRoute,
    notices,
    selectedIds,
    selectedRoutes,
    systemMedianTypicalTripLoss: median(
      availableRoutes.length > 0
        ? availableRoutes.map((route) => route.typical_trip_loss_minutes)
        : selectedRoutes.map((route) => route.typical_trip_loss_minutes),
    ),
  };
}

export async function getRankingsPageData() {
  const rankingsResult = await safeLoad(getRankings);
  const rankings = rankingsResult.ok ? rankingsResult.data.routes : [];
  const notices: DataNotice[] = [];

  if (!rankingsResult.ok) {
    notices.push(
      buildErrorNotice(
        "Published rankings are unavailable right now.",
        "The live rankings endpoint could not be loaded.",
        rankingsResult.error,
      ),
    );
  } else if (rankings.length === 0) {
    notices.push(
      buildEmptyNotice(
        "No published route rankings are available yet.",
        "The rankings page will populate once the API returns at least one ranked route.",
      ),
    );
  }

  return {
    featuredRoutes: rankings.slice(0, 3),
    lastUpdatedAt: rankings[0]?.metric_updated_at ?? null,
    notices,
    rankings,
    systemMedianTypicalTripLoss: median(
      rankings.map((route) => route.typical_trip_loss_minutes),
    ),
    windowLabel: rankingsResult.ok ? rankingsResult.data.window : "all_day",
  };
}

export async function getRouteDetailPageData(
  routeId: string,
): Promise<ReadyRouteDetailPageData | FailedRouteDetailPageData | null> {
  const [summaryResult, rankingsResult, mapResult] = await Promise.all([
    safeLoad(() => getRouteSummary(routeId)),
    safeLoad(getRankings),
    safeLoad(getMapRoutes),
  ]);

  if (!summaryResult.ok) {
    if (summaryResult.error instanceof ApiRequestError && summaryResult.error.status === 404) {
      return null;
    }

    return {
      kind: "error",
      notice: buildErrorNotice(
        "Route detail is unavailable right now.",
        `The live summary for route ${routeId} could not be loaded.`,
        summaryResult.error,
      ),
      routeId,
    };
  }

  const summary = summaryResult.data;
  const rankedRoutes = rankingsResult.ok ? rankingsResult.data.routes : [];
  const routeRankIndex = rankedRoutes.findIndex((route) => route.route_id === routeId);
  const routeRank = routeRankIndex >= 0 ? routeRankIndex + 1 : null;
  const peers =
    routeRankIndex >= 0
      ? rankedRoutes
          .slice(Math.max(0, routeRankIndex - 2), routeRankIndex + 3)
          .filter((route) => route.route_id !== routeId)
      : rankedRoutes.filter((route) => route.route_id !== routeId).slice(0, 4);
  const routeMapFeatures = mapResult.ok
    ? mapResult.data.features.filter((feature) => feature.properties.route_id === routeId)
    : [];
  const segmentResult = await loadDirectionalResource(
    (direction) => getRouteSegments(routeId, direction),
    "No directional segment layer is published for this route yet.",
    "The directional segment layer could not be loaded.",
  );
  const stopWaitResult = await loadDirectionalResource(
    (direction) => getRouteStopWait(routeId, direction),
    "No stop-wait hotspot layer is published for this route yet.",
    "The stop-wait hotspot layer could not be loaded.",
    segmentResult.direction,
  );

  return {
    kind: "ready",
    mapFeatures: routeMapFeatures,
    mapNotice: mapResult.ok
      ? routeMapFeatures.length === 0
        ? buildEmptyNotice(
            "No corridor geometry is published for this route yet.",
            "The route detail page can still show the route summary while the map layer catches up.",
          )
        : undefined
      : buildErrorNotice(
          "Route map context is unavailable right now.",
          "The route-level geometry could not be loaded from the live map endpoint.",
          mapResult.error,
        ),
    peers,
    peersNotice: rankingsResult.ok
      ? peers.length === 0
        ? buildEmptyNotice(
            "No peer routes are published alongside this route yet.",
            "Nearby route context will appear once the rankings endpoint includes more routes.",
          )
        : undefined
      : buildErrorNotice(
          "Peer rankings are unavailable right now.",
          "The route detail page could not load the broader rankings context.",
          rankingsResult.error,
        ),
    rankedRouteCount: rankedRoutes.length,
    routeRank,
    segmentCollection: segmentResult.data,
    segmentNotice: segmentResult.notice,
    stopWaitCollection: stopWaitResult.data,
    stopWaitNotice: stopWaitResult.notice,
    summary,
    systemMedianTypicalTripLoss: median(
      rankedRoutes.length > 0
        ? rankedRoutes.map((route) => route.typical_trip_loss_minutes)
        : [summary.typical_trip_loss_minutes],
    ),
    transitLaneOverlay: transitLaneOverlay.filter(
      (feature) => feature.properties.route_hint === routeId,
    ),
    waitingShare: routeLossShares(summary).waiting,
  };
}

export async function getMapPageData() {
  const [rankingsResult, mapResult] = await Promise.all([
    safeLoad(getRankings),
    safeLoad(getMapRoutes),
  ]);
  const notices: DataNotice[] = [];
  const map = mapResult.ok ? mapResult.data : emptyMapResponse();
  const rankings = rankingsResult.ok
    ? rankingsResult.data.routes
    : map.features.map((feature) => routeSummaryFromFeature(feature.properties));

  if (!mapResult.ok) {
    notices.push(
      buildErrorNotice(
        "The citywide map is unavailable right now.",
        "The live route choropleth could not be loaded.",
        mapResult.error,
      ),
    );
  } else if (map.features.length === 0) {
    notices.push(
      buildEmptyNotice(
        "No published route corridors are available yet.",
        "The citywide map will populate once the API returns route geometry.",
      ),
    );
  }

  if (!rankingsResult.ok) {
    notices.push(
      buildErrorNotice(
        "The ranking sidebar is unavailable right now.",
        "The live rankings endpoint could not be loaded.",
        rankingsResult.error,
      ),
    );
  }

  return {
    highestLossRoute: rankings[0] ?? null,
    lowestLossRoute: rankings[rankings.length - 1] ?? null,
    metricUpdatedAt:
      rankings[0]?.metric_updated_at ?? map.features[0]?.properties.metric_updated_at ?? null,
    notices,
    rankings,
    routeCount: map.features.length,
    routes: map,
    transitLaneOverlay,
  };
}

export function getMethodologyPageData() {
  return {
    caveats: [
      "The published historical window is all_day only in the current contract.",
      "Directional segment and stop-wait detail appears only where the API publishes route-direction layers.",
      "Transit-only lanes remain a context overlay, not causal proof.",
    ],
    contractFacts: [
      "Typical trip loss combines waiting loss and in-vehicle loss into one rider-facing headline.",
      "Waiting loss stays conservative by relying on exact first-stop matched headways only.",
      "Coverage counts remain visible so missing observations are not blended into the numerator.",
    ],
    sections: methodologySections,
    sources: [
      {
        href: "https://onlinepubs.trb.org/Onlinepubs/trr/1980/746/746-005.pdf",
        label: "TRB: Evaluating Potential Effectiveness of Headway Control Strategies for Transit Systems",
      },
      {
        href: "https://511.org/open-data/transit",
        label: "511 transit open data",
      },
      {
        href: "https://511.org/about/faq/open-data",
        label: "511 open data FAQ",
      },
    ],
  };
}

async function safeLoad<T>(loader: () => Promise<T>): Promise<SuccessfulResult<T> | FailedResult> {
  try {
    return { data: await loader(), ok: true };
  } catch (error) {
    return { error, ok: false };
  }
}

async function loadDirectionalResource<T>(
  loader: (direction: number) => Promise<T>,
  emptyTitle: string,
  errorTitle: string,
  preferredDirection?: number | null,
) {
  const orderedDirections = preferredDirection == null
    ? [...preferredDirections]
    : [preferredDirection, ...preferredDirections.filter((direction) => direction !== preferredDirection)];

  for (const direction of orderedDirections) {
    const result = await safeLoad(() => loader(direction));

    if (result.ok) {
      return {
        data: result.data,
        direction,
        notice: undefined,
      };
    }

    if (result.error instanceof ApiRequestError && result.error.status === 404) {
      continue;
    }

    return {
      data: null,
      direction: null,
      notice: buildErrorNotice(errorTitle, "The live endpoint returned an error.", result.error),
    };
  }

  return {
    data: null,
    direction: null,
    notice: buildEmptyNotice(
      emptyTitle,
      "The summary is available, but the matching directional layer is not published for this route yet.",
    ),
  };
}

function buildRouteCatalog(
  rankedRoutes: RouteSummary[],
  compareResponse?: CompareResponse,
) {
  const routeMap = new Map<string, RouteSummary>();

  rankedRoutes.forEach((route) => routeMap.set(route.route_id, route));
  compareResponse?.routes.forEach((route) => {
    if (!routeMap.has(route.route_id)) {
      routeMap.set(route.route_id, route);
    }
  });

  return Array.from(routeMap.values()).sort(
    (left, right) => right.typical_trip_loss_minutes - left.typical_trip_loss_minutes,
  );
}

async function buildHomepageHeroMap(
  rankings: RouteSummary[],
  features: FeatureLine[],
): Promise<HomepageHeroMap> {
  const routeFeatureIds = new Set(features.map((feature) => feature.properties.route_id));
  const featuredRankings = rankings
    .filter((route) => routeFeatureIds.has(route.route_id))
    .slice(0, 3);
  const featuredRouteIds = new Set(featuredRankings.map((route) => route.route_id));
  const featuredColorByRouteId = Object.fromEntries(
    featuredRankings.map((route, index) => [
      route.route_id,
      homepageFeaturedRouteColors[index] ?? homepageFeaturedRouteColors.at(-1)!,
    ]),
  );
  const featuredShortNameById = new Map(
    featuredRankings.map((route) => [route.route_id, route.route_short_name] as const),
  );
  const featuredFeatures = features.filter((feature) =>
    featuredRouteIds.has(feature.properties.route_id),
  );
  const badgeStopCoordinatesByRouteId = new Map<string, [number, number][]>(
    await Promise.all(
      featuredRankings.map(async (route) => [
        route.route_id,
        await loadHomepageRouteBadgeStops(route.route_id),
      ] as const),
    ),
  );
  const routeBadges = featuredFeatures.map((feature) => {
    const routeId = feature.properties.route_id;
    const routeShortName =
      featuredShortNameById.get(routeId) ?? feature.properties.route_short_name ?? routeId;
    const stopAnchors = badgeStopCoordinatesByRouteId.get(routeId) ?? [];
    const candidateCoordinates =
      stopAnchors.length > 0
        ? orderStopAnchorsFromMiddleOut(feature, stopAnchors)
        : getFeatureAnchorCandidates(feature);

    return {
      candidate_coordinates: candidateCoordinates,
      coordinate: candidateCoordinates[0] ?? getFeatureAnchorCoordinate(feature),
      route_id: routeId,
      route_short_name: routeShortName,
    };
  });

  return {
    backgroundFeatures: features.filter(
      (feature) => !featuredRouteIds.has(feature.properties.route_id),
    ),
    featuredColorByRouteId,
    featuredFeatures,
    neighborhoodLabels: homepageNeighborhoodLabels,
    routeBadges,
    viewportBounds: homepageHeroBounds,
  };
}

function parseRequestedIds(ids?: string | string[]) {
  const rawIds =
    typeof ids === "string"
      ? ids.split(",")
      : Array.isArray(ids)
        ? ids.flatMap((value) => value.split(","))
        : [];

  return Array.from(new Set(rawIds.map((routeId) => routeId.trim()).filter(Boolean)));
}

function buildEmptyNotice(title: string, message: string): DataNotice {
  return { message, title };
}

function buildErrorNotice(title: string, message: string, error: unknown): DataNotice {
  return {
    detail: formatApiError(error),
    message,
    title,
  };
}

function emptyMapResponse(): RouteMapResponse {
  return {
    features: [],
    metric: "typical_trip_loss_minutes",
    type: "FeatureCollection",
    window: "all_day",
  };
}

function routeSummaryFromFeature(feature: RouteMapResponse["features"][number]["properties"]): RouteSummary {
  return {
    direction_id: feature.direction_id,
    direction_label: feature.direction_label,
    in_vehicle_loss_minutes: feature.in_vehicle_loss_minutes ?? 0,
    matched_full_trip_count: feature.matched_full_trip_count ?? 0,
    matched_headway_interval_count: feature.matched_headway_interval_count ?? 0,
    matched_observed_stop_event_count: feature.matched_observed_stop_event_count ?? 0,
    metric_updated_at: feature.metric_updated_at,
    rank: feature.rank,
    resolved_unmatched_observation_count: feature.resolved_unmatched_observation_count ?? 0,
    route_id: feature.route_id,
    route_long_name: feature.route_long_name,
    route_name: feature.route_name,
    route_short_name: feature.route_short_name,
    typical_trip_loss_minutes: feature.typical_trip_loss_minutes ?? feature.metric_value ?? 0,
    waiting_loss_minutes: feature.waiting_loss_minutes ?? 0,
    window: feature.window,
    worst_segment_label: feature.worst_segment_label ?? "Not published",
    worst_stop_wait_label: feature.worst_stop_wait_label ?? "Not published",
    worst_time_band: feature.worst_time_band ?? "Not published",
  };
}

function getFeatureAnchorCoordinate(
  feature: FeatureLine,
  ratios: readonly number[] = defaultFeatureAnchorRatios,
): [number, number] {
  return getFeatureAnchorCandidates(feature, ratios)[0] ?? [-122.4376, 37.7638];
}

function getFeatureAnchorCandidates(
  feature: FeatureLine,
  ratios: readonly number[] = defaultFeatureAnchorRatios,
): [number, number][] {
  const coordinates =
    feature.geometry.type === "MultiLineString"
      ? feature.geometry.coordinates.flat()
      : feature.geometry.coordinates;

  if (coordinates.length === 0) {
    return [[-122.4376, 37.7638]];
  }

  return ratios.map((ratio) => getCoordinateAtLineRatio(coordinates, ratio));
}

async function loadHomepageRouteBadgeStops(routeId: string): Promise<[number, number][]> {
  const stopWaitResult = await loadDirectionalResource(
    (direction) => getRouteStopWait(routeId, direction),
    "",
    "",
  );

  if (!stopWaitResult.data) {
    return [];
  }

  const seen = new Set<string>();
  const coordinates: [number, number][] = [];

  for (const feature of stopWaitResult.data.features) {
    const coordinate = feature.geometry.coordinates;
    const key = `${coordinate[0].toFixed(6)},${coordinate[1].toFixed(6)}`;

    if (!seen.has(key)) {
      seen.add(key);
      coordinates.push(coordinate);
    }
  }

  return coordinates;
}

function orderStopAnchorsFromMiddleOut(
  feature: FeatureLine,
  stopCoordinates: [number, number][],
): [number, number][] {
  const routeCoordinates =
    feature.geometry.type === "MultiLineString"
      ? feature.geometry.coordinates.flat()
      : feature.geometry.coordinates;

  const orderedStops = stopCoordinates
    .map((coordinate) => ({
      coordinate,
      progress: getCoordinateProgressAlongLine(routeCoordinates, coordinate),
    }))
    .sort((left, right) => left.progress - right.progress);

  if (orderedStops.length <= 1) {
    return orderedStops.map((item) => item.coordinate);
  }

  const middleIndex = Math.floor((orderedStops.length - 1) / 2);
  const orderedIndices: number[] = [middleIndex];

  for (let offset = 1; orderedIndices.length < orderedStops.length; offset += 1) {
    const forwardIndex = middleIndex + offset;
    const backwardIndex = middleIndex - offset;

    if (forwardIndex < orderedStops.length) {
      orderedIndices.push(forwardIndex);
    }

    if (backwardIndex >= 0) {
      orderedIndices.push(backwardIndex);
    }
  }

  return orderedIndices.map((index) => orderedStops[index].coordinate);
}

function getCoordinateProgressAlongLine(
  coordinates: [number, number][],
  coordinate: [number, number],
): number {
  if (coordinates.length <= 1) {
    return 0;
  }

  const segments = coordinates.slice(1).map((lineCoordinate, index) => {
    const start = coordinates[index];
    const dx = lineCoordinate[0] - start[0];
    const dy = lineCoordinate[1] - start[1];

    return {
      end: lineCoordinate,
      length: Math.hypot(dx, dy),
      start,
    };
  });
  const totalLength = segments.reduce((sum, segment) => sum + segment.length, 0);

  if (totalLength === 0) {
    return 0;
  }

  let traversed = 0;
  let bestProgress = 0;
  let bestDistance = Number.POSITIVE_INFINITY;

  for (const segment of segments) {
    const distance = pointToSegmentDistanceGeographic(coordinate, segment.start, segment.end);
    const projection = projectionRatioOnSegment(coordinate, segment.start, segment.end);
    const progress = (traversed + segment.length * projection) / totalLength;

    if (distance < bestDistance) {
      bestDistance = distance;
      bestProgress = progress;
    }

    traversed += segment.length;
  }

  return bestProgress;
}

function pointToSegmentDistanceGeographic(
  point: [number, number],
  start: [number, number],
  end: [number, number],
): number {
  const [px, py] = point;
  const [x1, y1] = start;
  const [x2, y2] = end;
  const dx = x2 - x1;
  const dy = y2 - y1;

  if (dx === 0 && dy === 0) {
    return Math.hypot(px - x1, py - y1);
  }

  const projection = projectionRatioOnSegment(point, start, end);
  const closestX = x1 + dx * projection;
  const closestY = y1 + dy * projection;

  return Math.hypot(px - closestX, py - closestY);
}

function projectionRatioOnSegment(
  point: [number, number],
  start: [number, number],
  end: [number, number],
): number {
  const [px, py] = point;
  const [x1, y1] = start;
  const [x2, y2] = end;
  const dx = x2 - x1;
  const dy = y2 - y1;

  if (dx === 0 && dy === 0) {
    return 0;
  }

  const projection = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy);
  return Math.max(0, Math.min(1, projection));
}

function getCoordinateAtLineRatio(
  coordinates: [number, number][],
  ratio: number,
): [number, number] {
  if (coordinates.length === 1) {
    return coordinates[0];
  }

  const segments = coordinates.slice(1).map((coordinate, index) => {
    const start = coordinates[index];
    const dx = coordinate[0] - start[0];
    const dy = coordinate[1] - start[1];

    return {
      end: coordinate,
      length: Math.hypot(dx, dy),
      start,
    };
  });
  const totalLength = segments.reduce((sum, segment) => sum + segment.length, 0);

  if (totalLength === 0) {
    return coordinates[Math.floor((coordinates.length - 1) * ratio)];
  }

  const targetLength = totalLength * ratio;
  let traversed = 0;

  for (const segment of segments) {
    if (traversed + segment.length >= targetLength) {
      const progress = (targetLength - traversed) / segment.length;
      return [
        segment.start[0] + (segment.end[0] - segment.start[0]) * progress,
        segment.start[1] + (segment.end[1] - segment.start[1]) * progress,
      ];
    }

    traversed += segment.length;
  }

  return coordinates.at(-1) ?? coordinates[0];
}

function formatApiError(error: unknown) {
  if (error instanceof ApiRequestError) {
    return error.detail
      ? `${error.path} returned ${error.status}: ${error.detail}`
      : `${error.path} returned ${error.status}.`;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unknown API error.";
}
