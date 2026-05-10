import {
  compareFixture,
  loadTransitLaneOverlay,
  rankingsFixture,
  route14SegmentsFixture,
  route14SummaryFixture,
  routeMapFixture,
} from "@/lib/fixtures";
import { getRouteTheme } from "@/lib/presentation";
import type { MethodologySection, RouteSummary } from "@/lib/types";
import { median, routeLossShares } from "@/lib/utils";

const routeSummaries = (() => {
  const map = new Map<string, RouteSummary>();
  rankingsFixture.routes.forEach((route) => map.set(route.route_id, route));
  compareFixture.routes.forEach((route) => {
    if (!map.has(route.route_id)) {
      map.set(route.route_id, route);
    }
  });
  map.set(route14SummaryFixture.route_id, route14SummaryFixture);
  return Array.from(map.values()).sort(
    (left, right) => right.typical_trip_loss_minutes - left.typical_trip_loss_minutes,
  );
})();

const routeMapById = new Map(
  routeMapFixture.features.map((feature) => [feature.properties.route_id, feature]),
);

const transitLaneOverlay = loadTransitLaneOverlay();

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
      "The static B5 frontend intentionally keeps those caveats visible instead of burying them behind generic dashboard chrome.",
    ],
    bullets: [
      "Current historical window support is all_day only",
      "Bunching is interpreted as rider consequence context, not a standalone published endpoint yet",
      "Transit-only lanes are shown as spatial context, not as causal evidence",
    ],
  },
];

export type MapPageData = ReturnType<typeof getMapPageData>;

export function getRouteIds() {
  return routeSummaries.map((route) => route.route_id);
}

export function getHomepageData() {
  return {
    rankings: rankingsFixture.routes,
    map: routeMapFixture,
    windowLabel: "All day",
    metricUpdatedAt: rankingsFixture.routes[0]?.metric_updated_at ?? route14SummaryFixture.metric_updated_at,
    problemTypes: [
      {
        icon: "waiting",
        symbol: "○",
        title: "Waiting",
        copy: "Longer or more irregular headways push effective wait above the scheduled baseline.",
      },
      {
        icon: "travel",
        symbol: "═",
        title: "Slow travel",
        copy: "Traffic, signals, and dwell pressure extend the in-vehicle part of the trip.",
      },
      {
        icon: "bunching",
        symbol: "≡",
        title: "Bunching",
        copy: "Vehicles clump together and leave gaps behind, amplifying rider delay even when service is present.",
      },
    ],
  };
}

export function getComparePageData(ids?: string | string[]) {
  const requestedIds =
    typeof ids === "string"
      ? ids.split(",")
      : Array.isArray(ids)
        ? ids.flatMap((value) => value.split(","))
        : compareFixture.route_ids;
  const uniqueIds = Array.from(
    new Set(
      requestedIds.filter((routeId) => routeSummaries.some((route) => route.route_id === routeId)),
    ),
  );
  const selectedIds = uniqueIds.length >= 2 ? uniqueIds.slice(0, 2) : compareFixture.route_ids;
  const selectedRoutes = selectedIds
    .map((routeId) => routeSummaries.find((route) => route.route_id === routeId))
    .filter((route): route is RouteSummary => Boolean(route));

  return {
    availableRoutes: routeSummaries,
    selectedIds,
    selectedRoutes,
    systemMedianTypicalTripLoss: median(routeSummaries.map((route) => route.typical_trip_loss_minutes)),
  };
}

export function getRouteDetailPageData(routeId: string) {
  const summary = routeSummaries.find((route) => route.route_id === routeId);
  if (!summary) {
    return null;
  }

  const peers = routeSummaries.filter((route) => route.route_id !== routeId);
  const segmentCollection =
    routeId === route14SegmentsFixture.route_id ? route14SegmentsFixture : null;
  const mapFeature = routeMapById.get(routeId);

  return {
    summary,
    segmentCollection,
    mapFeatures: mapFeature ? [mapFeature] : [],
    peers,
    waitingShare: routeLossShares(summary).waiting,
    systemMedianTypicalTripLoss: median(routeSummaries.map((route) => route.typical_trip_loss_minutes)),
  };
}

export function getMapPageData() {
  return {
    routes: routeMapFixture,
    rankings: rankingsFixture.routes,
    transitLaneOverlay,
    metricUpdatedAt: rankingsFixture.routes[0]?.metric_updated_at ?? route14SummaryFixture.metric_updated_at,
  };
}

export function getMethodologyPageData() {
  return {
    sections: methodologySections,
    sources: [
      {
        label: "TRB: Evaluating Potential Effectiveness of Headway Control Strategies for Transit Systems",
        href: "https://onlinepubs.trb.org/Onlinepubs/trr/1980/746/746-005.pdf",
      },
      {
        label: "511 transit open data",
        href: "https://511.org/open-data/transit",
      },
      {
        label: "511 open data FAQ",
        href: "https://511.org/about/faq/open-data",
      },
    ],
  };
}
