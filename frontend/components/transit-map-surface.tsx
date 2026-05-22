"use client";

import type { CSSProperties } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import maplibregl, {
  type GeoJSONSource,
  type Map as MapLibreMap,
  type StyleSpecification,
} from "maplibre-gl";
import type {
  FeatureLine,
  MapBounds,
  MapNeighborhoodLabel,
  MapRouteBadge,
  StopWaitFeature,
} from "@/lib/types";
import {
  decorateContextRouteFeatures,
  decorateOverlayFeatures,
  decorateRouteFeatures,
  decorateSegmentFeatures,
  decorateStopHotspots,
  getMapBounds,
  routeLossLegendItems,
  toFeatureCollection,
  type MapLegendItem,
} from "@/lib/map-utils";

type MapFeatureCollection = {
  type: "FeatureCollection";
  features: unknown[];
};

const mapStyle: StyleSpecification = {
  version: 8,
  sources: {
    basemap: {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      tileSize: 256,
      tiles: ["https://basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png"],
      type: "raster",
    },
  },
  layers: [
    {
      id: "background",
      paint: {
        "background-color": "#e6eef2",
      },
      type: "background",
    },
    {
      id: "basemap",
      paint: {
        "raster-brightness-max": 1,
        "raster-brightness-min": 0.9,
        "raster-contrast": -0.22,
        "raster-fade-duration": 0,
        "raster-opacity": 0.42,
        "raster-saturation": -1,
      },
      source: "basemap",
      type: "raster",
    },
  ],
};

const sourceIds = {
  backgroundRoutes: "background-route-lines",
  overlays: "transit-overlays",
  routes: "route-lines",
  segments: "segment-lines",
  stops: "stop-hotspots",
} as const;

const layerIds = {
  backgroundRouteCasing: "background-route-casing",
  backgroundRouteLines: "background-route-lines",
  overlayCasing: "overlay-casing",
  overlayLines: "overlay-lines",
  routeCasing: "route-casing",
  routeHitbox: "route-hitbox",
  routeLines: "route-lines",
  segmentCasing: "segment-casing",
  segmentLines: "segment-lines",
  stopCasing: "stop-casing",
  stopCircles: "stop-circles",
} as const;

type TransitMapSurfaceProps = {
  ariaLabel: string;
  backgroundRouteFeatures?: FeatureLine[];
  ctaHref?: string;
  ctaLabel?: string;
  fitMaxZoom?: number;
  fitPadding?: number;
  focusRouteId?: string;
  gestureNavigation?: boolean;
  hoverRoutes?: boolean;
  interactive?: boolean;
  lineMode?: "compact" | "default";
  legend?: {
    items?: MapLegendItem[];
    subtitle: string;
    title: string;
  };
  minHeight?: string;
  neighborhoodLabels?: MapNeighborhoodLabel[];
  overlayFeatures?: FeatureLine[];
  routeColorOverrides?: Record<string, string>;
  routeColorMode?: "focus" | "metric";
  routeBadges?: MapRouteBadge[];
  routeFeatures: FeatureLine[];
  segmentFeatures?: FeatureLine[];
  showControls?: boolean;
  stopFeatures?: StopWaitFeature[];
  surfaceLabel?: string;
  viewportBounds?: MapBounds;
};

export function TransitMapSurface({
  ariaLabel,
  backgroundRouteFeatures = [],
  ctaHref,
  ctaLabel,
  fitMaxZoom = 15.4,
  fitPadding = 26,
  focusRouteId,
  gestureNavigation,
  hoverRoutes = false,
  interactive = true,
  lineMode = "default",
  legend,
  minHeight = "520px",
  neighborhoodLabels = [],
  overlayFeatures = [],
  routeColorOverrides,
  routeColorMode = "metric",
  routeBadges = [],
  routeFeatures,
  segmentFeatures = [],
  showControls = true,
  stopFeatures = [],
  surfaceLabel = "MapLibre GL JS route surface",
  viewportBounds,
}: TransitMapSurfaceProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);
  const lastFitKeyRef = useRef<string | null>(null);
  const [mapStatus, setMapStatus] = useState<"error" | "loading" | "ready">("loading");
  const [projectedNeighborhoodLabels, setProjectedNeighborhoodLabels] = useState<
    Array<MapNeighborhoodLabel & { x: number; y: number }>
  >([]);
  const [projectedRouteBadges, setProjectedRouteBadges] = useState<
    Array<MapRouteBadge & { color: string; x: number; y: number }>
  >([]);
  const [hoveredRoute, setHoveredRoute] = useState<{
    lossMinutes: number;
    routeName: string;
    routeShortName: string;
    x: number;
    y: number;
  } | null>(null);

  const decoratedRoutes = useMemo(
    () =>
      decorateRouteFeatures(routeFeatures, {
        colorOverrides: routeColorOverrides,
        focusRouteId,
        mode: routeColorMode,
      }),
    [focusRouteId, routeColorMode, routeColorOverrides, routeFeatures],
  );
  const decoratedBackgroundRoutes = useMemo(
    () => decorateContextRouteFeatures(backgroundRouteFeatures),
    [backgroundRouteFeatures],
  );
  const decoratedOverlays = useMemo(
    () => decorateOverlayFeatures(overlayFeatures),
    [overlayFeatures],
  );
  const decoratedSegments = useMemo(
    () => decorateSegmentFeatures(segmentFeatures),
    [segmentFeatures],
  );
  const decoratedStops = useMemo(
    () => decorateStopHotspots(stopFeatures),
    [stopFeatures],
  );
  const routeCollection = useMemo(
    () => toFeatureCollection(decoratedRoutes),
    [decoratedRoutes],
  );
  const backgroundRouteCollection = useMemo(
    () => toFeatureCollection(decoratedBackgroundRoutes),
    [decoratedBackgroundRoutes],
  );
  const overlayCollection = useMemo(
    () => toFeatureCollection(decoratedOverlays),
    [decoratedOverlays],
  );
  const segmentCollection = useMemo(
    () => toFeatureCollection(decoratedSegments),
    [decoratedSegments],
  );
  const stopCollection = useMemo(
    () => toFeatureCollection(decoratedStops),
    [decoratedStops],
  );
  const fitBounds = useMemo(
    () =>
      getMapBounds({
        overlayFeatures,
        routeFeatures: [...backgroundRouteFeatures, ...routeFeatures],
        segmentFeatures,
        stopFeatures,
      }),
    [backgroundRouteFeatures, overlayFeatures, routeFeatures, segmentFeatures, stopFeatures],
  );
  const targetBounds = viewportBounds ?? fitBounds;
  const fitKey = useMemo(
    () =>
      JSON.stringify({
        backgroundRouteIds: backgroundRouteFeatures.map(
          (feature) => feature.properties.route_id,
        ),
        focusRouteId,
        routeIds: routeFeatures.map((feature) => feature.properties.route_id),
        segmentIds: segmentFeatures.map((feature) => feature.properties.segment_label),
        stopIds: stopFeatures.map((feature) => feature.properties.stop_id),
        viewportBounds,
      }),
    [backgroundRouteFeatures, focusRouteId, routeFeatures, segmentFeatures, stopFeatures, viewportBounds],
  );
  const legendItems = legend?.items ?? routeLossLegendItems;
  const allowGestures = gestureNavigation ?? interactive;
  const routeColorById = useMemo(
    () =>
      new Map(
        decoratedRoutes.map((feature) => [
          feature.properties.route_id,
          feature.properties.map_color,
        ] as const),
      ),
    [decoratedRoutes],
  );

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return;
    }

    try {
      const map = new maplibregl.Map({
        attributionControl: false,
        center: [-122.4376, 37.7638],
        container: mapContainerRef.current,
        dragRotate: false,
        interactive,
        pitchWithRotate: false,
        style: mapStyle,
        zoom: 11.2,
      });

      if (!allowGestures) {
        map.boxZoom.disable();
        map.doubleClickZoom.disable();
        map.dragPan.disable();
        map.keyboard.disable();
        map.scrollZoom.disable();
        map.touchZoomRotate.disable();
      }

      mapRef.current = map;
      setMapStatus("loading");

      const sync = () => {
        syncMapSources(map, {
          backgroundRouteCollection,
          lineMode,
          overlayCollection,
          routeCollection,
          segmentCollection,
          stopCollection,
        });
        fitMapToBounds(
          map,
          targetBounds,
          interactive,
          false,
          fitMaxZoom,
          fitPadding,
        );
        lastFitKeyRef.current = fitKey;
        setMapStatus("ready");
      };

      if (isStyleReady(map)) {
        sync();
      } else {
        map.once("styledata", sync);
      }

      if (typeof ResizeObserver !== "undefined" && mapContainerRef.current) {
        resizeObserverRef.current = new ResizeObserver(() => {
          map.resize();
        });
        resizeObserverRef.current.observe(mapContainerRef.current);
      }
    } catch {
      setMapStatus("error");
    }

    return () => {
      resizeObserverRef.current?.disconnect();
      resizeObserverRef.current = null;
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, [
    fitBounds,
    fitKey,
    fitMaxZoom,
    fitPadding,
    interactive,
    allowGestures,
    backgroundRouteCollection,
    lineMode,
    overlayCollection,
    routeCollection,
    segmentCollection,
    stopCollection,
    targetBounds,
  ]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) {
      return;
    }

    const sync = () => {
      try {
        syncMapSources(map, {
          backgroundRouteCollection,
          lineMode,
          overlayCollection,
          routeCollection,
          segmentCollection,
          stopCollection,
        });

        if (lastFitKeyRef.current !== fitKey) {
          fitMapToBounds(
            map,
            targetBounds,
            interactive,
            true,
            fitMaxZoom,
            fitPadding,
          );
          lastFitKeyRef.current = fitKey;
        }

        setMapStatus("ready");
      } catch {
        setMapStatus("error");
      }
    };

    if (isStyleReady(map)) {
      sync();
      return;
    }

    map.once("styledata", sync);
  }, [
    fitBounds,
    fitKey,
    fitMaxZoom,
    fitPadding,
    interactive,
    backgroundRouteCollection,
    lineMode,
    overlayCollection,
    routeCollection,
    segmentCollection,
    stopCollection,
    targetBounds,
  ]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !interactive || !hoverRoutes || mapStatus !== "ready") {
      setHoveredRoute(null);
      return;
    }

    const handleMove = (event: maplibregl.MapMouseEvent) => {
      if (!map.getLayer(layerIds.routeHitbox)) {
        map.getCanvas().style.cursor = "";
        setHoveredRoute(null);
        return;
      }

      const features = map.queryRenderedFeatures(
        [
          [event.point.x - 6, event.point.y - 6],
          [event.point.x + 6, event.point.y + 6],
        ] as never,
        { layers: [layerIds.routeHitbox] },
      );
      const feature = features[0];
      const routeId = feature?.properties?.route_id;

      if (!feature || typeof routeId !== "string") {
        map.getCanvas().style.cursor = "";
        setHoveredRoute(null);
        return;
      }

      const containerWidth = mapContainerRef.current?.clientWidth ?? 720;
      map.getCanvas().style.cursor = "pointer";
      setHoveredRoute({
        lossMinutes: Number(
          feature.properties?.typical_trip_loss_minutes ??
            feature.properties?.metric_value ??
            0,
        ),
        routeName: String(feature.properties?.route_name ?? "Unknown route"),
        routeShortName: String(feature.properties?.route_short_name ?? routeId),
        x: Math.min(event.point.x + 16, Math.max(18, containerWidth - 232)),
        y: event.point.y,
      });
    };

    const handleLeave = () => {
      map.getCanvas().style.cursor = "";
      setHoveredRoute(null);
    };

    map.on("mousemove", handleMove);
    map.on("mouseout", handleLeave);

    return () => {
      map.off("mousemove", handleMove);
      map.off("mouseout", handleLeave);
      map.getCanvas().style.cursor = "";
    };
  }, [hoverRoutes, interactive, mapStatus]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || mapStatus !== "ready") {
      setProjectedNeighborhoodLabels([]);
      setProjectedRouteBadges([]);
      return;
    }

    const syncProjectedAnnotations = () => {
      const width = map.getCanvas().clientWidth;
      const height = map.getCanvas().clientHeight;
      const occupiedRects: Rect[] = [];
      const featuredRouteSegments = projectFeatureSegments(map, routeFeatures);
      const placedBadges = routeBadges
        .map((badge) => placeRouteBadge(map, badge, routeColorById, occupiedRects, width, height))
        .filter(
          (badge): badge is MapRouteBadge & { color: string; x: number; y: number } =>
            Boolean(badge),
        );
      const placedLabels = neighborhoodLabels
        .map((label) =>
          placeNeighborhoodLabel(
            map,
            label,
            featuredRouteSegments,
            occupiedRects,
            width,
            height,
          ),
        )
        .filter((label): label is MapNeighborhoodLabel & { x: number; y: number } =>
          Boolean(label),
        );

      setProjectedRouteBadges(placedBadges);
      setProjectedNeighborhoodLabels(placedLabels);
    };

    syncProjectedAnnotations();
    map.on("move", syncProjectedAnnotations);
    map.on("resize", syncProjectedAnnotations);

    return () => {
      map.off("move", syncProjectedAnnotations);
      map.off("resize", syncProjectedAnnotations);
    };
  }, [mapStatus, neighborhoodLabels, routeBadges, routeColorById]);

  return (
    <div
      className="map-surface"
      data-map-engine="maplibre-gl-js"
      data-background-route-count={backgroundRouteFeatures.length}
      data-map-loaded={mapStatus}
      data-overlay-count={overlayFeatures.length}
      data-route-count={routeFeatures.length}
      data-segment-count={segmentFeatures.length}
      data-stop-count={stopFeatures.length}
      style={{ "--map-min-height": minHeight } as CSSProperties}
    >
      <div aria-label={ariaLabel} className="map-canvas" ref={mapContainerRef} role="img" />
      {projectedNeighborhoodLabels.map((label) => (
        <div
          className="map-neighborhood-label"
          key={`${label.text}-${label.coordinate.join(",")}`}
          style={{ left: label.x, top: label.y }}
        >
          {label.text}
        </div>
      ))}
      {projectedRouteBadges.map((badge) => (
        <div
          className="map-route-badge"
          key={`${badge.route_id}-${badge.coordinate.join(",")}`}
          style={{
            "--map-route-badge-color": badge.color,
            left: badge.x,
            top: badge.y,
          } as CSSProperties}
        >
          <span>{badge.route_short_name}</span>
        </div>
      ))}
      {legend ? (
        <div className="map-legend">
          <h3>{legend.title}</h3>
          <p>{legend.subtitle}</p>
          <ul>
            {legendItems.map((item) => (
              <li key={item.label}>
                <span className="legend-swatch" style={{ background: item.color }} />
                <span>{item.label}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="map-schematic-chip map-engine-chip">{surfaceLabel}</div>
      {showControls ? (
        <div className="map-ui-controls">
          <button
            aria-label="Zoom in"
            disabled={!interactive || mapStatus !== "ready"}
            onClick={() => mapRef.current?.zoomIn()}
            type="button"
          >
            +
          </button>
          <button
            aria-label="Zoom out"
            disabled={!interactive || mapStatus !== "ready"}
            onClick={() => mapRef.current?.zoomOut()}
            type="button"
          >
            -
          </button>
          <button
            aria-label="Reset view"
            disabled={mapStatus !== "ready"}
            onClick={() => {
              if (mapRef.current) {
                fitMapToBounds(
                  mapRef.current,
                  fitBounds,
                  interactive,
                  true,
                  fitMaxZoom,
                  fitPadding,
                );
              }
            }}
            type="button"
          >
            Fit
          </button>
        </div>
      ) : null}
      {ctaHref && ctaLabel ? (
        <div className="schematic-cta map-surface-cta">
          <Link href={ctaHref}>{ctaLabel}</Link>
        </div>
      ) : null}
      <div className="map-attribution">
        Basemap ©{" "}
        <a href="https://www.openstreetmap.org/copyright" rel="noreferrer" target="_blank">
          OpenStreetMap contributors
        </a>{" "}
        +{" "}
        <a href="https://carto.com/attributions" rel="noreferrer" target="_blank">
          CARTO
        </a>
      </div>
      {hoveredRoute ? (
        <div
          className="map-route-tooltip"
          style={{
            left: hoveredRoute.x,
            top: Math.max(hoveredRoute.y - 18, 18),
          }}
        >
          <strong>
            Route {hoveredRoute.routeShortName} {hoveredRoute.routeName}
          </strong>
          <span>{hoveredRoute.lossMinutes.toFixed(1)} min typical extra time</span>
        </div>
      ) : null}
      {mapStatus === "loading" ? (
        <div className="map-loading-state">Loading MapLibre GL JS surface...</div>
      ) : null}
      {mapStatus === "error" ? (
        <div className="map-loading-state map-loading-error">
          MapLibre GL JS could not initialize in this browser session.
        </div>
      ) : null}
    </div>
  );
}

function fitMapToBounds(
  map: MapLibreMap,
  bounds: [[number, number], [number, number]] | null,
  interactive: boolean,
  animate: boolean,
  fitMaxZoom: number,
  fitPadding: number,
) {
  if (!bounds) {
    return;
  }

  map.fitBounds(bounds, {
    animate,
    duration: animate && interactive ? 600 : 0,
    maxZoom: fitMaxZoom,
    padding: interactive ? fitPadding : Math.max(12, fitPadding - 8),
  });
}

function syncMapSources(
  map: MapLibreMap,
  data: {
    backgroundRouteCollection: ReturnType<typeof toFeatureCollection>;
    lineMode: "compact" | "default";
    overlayCollection: ReturnType<typeof toFeatureCollection>;
    routeCollection: ReturnType<typeof toFeatureCollection>;
    segmentCollection: ReturnType<typeof toFeatureCollection>;
    stopCollection: ReturnType<typeof toFeatureCollection>;
  },
) {
  const compact = data.lineMode === "compact";
  upsertGeoJsonSource(map, sourceIds.backgroundRoutes, data.backgroundRouteCollection);
  upsertGeoJsonSource(map, sourceIds.overlays, data.overlayCollection);
  upsertGeoJsonSource(map, sourceIds.routes, data.routeCollection);
  upsertGeoJsonSource(map, sourceIds.segments, data.segmentCollection);
  upsertGeoJsonSource(map, sourceIds.stops, data.stopCollection);

  ensureLineLayer(map, layerIds.backgroundRouteLines, sourceIds.backgroundRoutes, {
    "line-color": ["coalesce", ["get", "map_color"], "#c7cfd5"],
    "line-opacity": ["coalesce", ["get", "map_opacity"], 1],
    "line-width": [
      "*",
      ["coalesce", ["get", "map_width"], 1.4],
      compact ? 0.82 : 1,
    ],
  });
  ensureLineLayer(map, layerIds.overlayCasing, sourceIds.overlays, {
    "line-color": "rgba(5, 5, 5, 0.35)",
    "line-dasharray": [1.4, 1.8],
    "line-opacity": 0.16,
    "line-width": compact ? 3.4 : 4.4,
  });
  ensureLineLayer(map, layerIds.overlayLines, sourceIds.overlays, {
    "line-color": ["coalesce", ["get", "map_color"], "#0868d0"],
    "line-dasharray": [1.4, 1.8],
    "line-opacity": ["coalesce", ["get", "map_opacity"], 0.55],
    "line-width": [
      "*",
      ["coalesce", ["get", "map_width"], 2.4],
      compact ? 0.78 : 1,
    ],
  });
  ensureLineLayer(map, layerIds.routeCasing, sourceIds.routes, {
    "line-color": "rgba(255, 255, 255, 0.92)",
    "line-opacity": 0.92,
    "line-width": [
      "+",
      ["*", ["coalesce", ["get", "map_width"], 4.75], compact ? 0.72 : 1],
      compact ? 0.82 : 1.35,
    ],
  });
  ensureLineLayer(map, layerIds.routeHitbox, sourceIds.routes, {
    "line-color": "rgba(0, 0, 0, 0)",
    "line-opacity": 0,
    "line-width": compact ? 12 : 10,
  });
  ensureLineLayer(map, layerIds.routeLines, sourceIds.routes, {
    "line-color": ["coalesce", ["get", "map_color"], "#0868d0"],
    "line-opacity": ["coalesce", ["get", "map_opacity"], 0.94],
    "line-width": [
      "*",
      ["coalesce", ["get", "map_width"], 4.75],
      compact ? 0.72 : 1,
    ],
  });
  ensureLineLayer(map, layerIds.segmentCasing, sourceIds.segments, {
    "line-color": "rgba(255, 255, 255, 0.94)",
    "line-opacity": 0.94,
    "line-width": [
      "+",
      ["*", ["coalesce", ["get", "map_width"], 5.6], compact ? 0.76 : 1],
      compact ? 0.92 : 1.5,
    ],
  });
  ensureLineLayer(map, layerIds.segmentLines, sourceIds.segments, {
    "line-color": ["coalesce", ["get", "map_color"], "#d81420"],
    "line-opacity": ["coalesce", ["get", "map_opacity"], 0.92],
    "line-width": [
      "*",
      ["coalesce", ["get", "map_width"], 5.6],
      compact ? 0.76 : 1,
    ],
  });
  ensureCircleLayer(map, layerIds.stopCasing, sourceIds.stops, {
    "circle-color": "rgba(5, 5, 5, 0.9)",
    "circle-radius": ["+", ["coalesce", ["get", "map_radius"], 10], 2],
    "circle-stroke-width": 0,
  });
  ensureCircleLayer(map, layerIds.stopCircles, sourceIds.stops, {
    "circle-color": ["coalesce", ["get", "map_color"], "#d81420"],
    "circle-radius": ["coalesce", ["get", "map_radius"], 10],
    "circle-stroke-color": "#ffffff",
    "circle-stroke-width": 2,
  });
}

function isPointInsideMap(
  x: number,
  y: number,
  width: number,
  height: number,
  margin: number,
) {
  return x >= margin && x <= width - margin && y >= margin && y <= height - margin;
}

type Rect = {
  bottom: number;
  left: number;
  right: number;
  top: number;
};

function placeRouteBadge(
  map: MapLibreMap,
  badge: MapRouteBadge,
  routeColorById: Map<string, string>,
  occupiedRects: Rect[],
  width: number,
  height: number,
) {
  const badgeWidth = Math.max(36, badge.route_short_name.length * 12 + 18);
  const badgeHeight = 36;

  for (const coordinate of badge.candidate_coordinates) {
    const point = map.project(coordinate);

    if (!isPointInsideMap(point.x, point.y, width, height, 20)) {
      continue;
    }

    const rect = {
      bottom: point.y + badgeHeight / 2,
      left: point.x - badgeWidth / 2,
      right: point.x + badgeWidth / 2,
      top: point.y - badgeHeight / 2,
    };

    if (occupiedRects.some((occupiedRect) => rectsOverlap(rect, occupiedRect))) {
      continue;
    }

    occupiedRects.push(rect);
    return {
      ...badge,
      color: routeColorById.get(badge.route_id) ?? "#0868d0",
      coordinate,
      x: point.x,
      y: point.y,
    };
  }

  return null;
}

function placeNeighborhoodLabel(
  map: MapLibreMap,
  label: MapNeighborhoodLabel,
  routeSegments: Array<[[number, number], [number, number]]>,
  occupiedRects: Rect[],
  width: number,
  height: number,
) {
  const labelWidth = Math.min(164, label.text.length * 7.2 + 18);
  const labelHeight = label.text.includes("/") ? 34 : 24;
  const basePoint = map.project(label.coordinate);
  const candidateOffsets = [
    [0, 0],
    [0, -22],
    [20, 0],
    [-20, 0],
    [0, 22],
    [18, -18],
    [-18, -18],
    [18, 18],
    [-18, 18],
    [0, -36],
    [30, 0],
    [-30, 0],
    [0, 36],
    [28, -28],
    [-28, -28],
    [28, 28],
    [-28, 28],
    [0, -48],
    [40, 0],
    [-40, 0],
    [0, 48],
  ] as const;

  for (const [offsetX, offsetY] of candidateOffsets) {
    const x = basePoint.x + offsetX;
    const y = basePoint.y + offsetY;

    if (!isPointInsideMap(x, y, width, height, 16)) {
      continue;
    }

    const rect = {
      bottom: y + labelHeight / 2,
      left: x - labelWidth / 2,
      right: x + labelWidth / 2,
      top: y - labelHeight / 2,
    };

    if (
      occupiedRects.some((occupiedRect) => rectsOverlap(rect, occupiedRect)) ||
      routeSegments.some((segment) => rectIntersectsRoute(rect, segment, 16))
    ) {
      continue;
    }

    occupiedRects.push(rect);
    return {
      ...label,
      x,
      y,
    };
  }

  return null;
}

function rectsOverlap(left: Rect, right: Rect) {
  return !(
    left.right < right.left ||
    left.left > right.right ||
    left.bottom < right.top ||
    left.top > right.bottom
  );
}

function projectFeatureSegments(
  map: MapLibreMap,
  features: FeatureLine[],
): Array<[[number, number], [number, number]]> {
  return features.flatMap((feature) => {
    const lines =
      feature.geometry.type === "MultiLineString"
        ? feature.geometry.coordinates
        : [feature.geometry.coordinates];

    return lines.flatMap((line) =>
      line.slice(1).map((coordinate, index) => {
        const start = map.project(line[index]);
        const end = map.project(coordinate);
        return [
          [start.x, start.y],
          [end.x, end.y],
        ] as [[number, number], [number, number]];
      }),
    );
  });
}

function rectIntersectsRoute(
  rect: Rect,
  segment: [[number, number], [number, number]],
  buffer: number,
) {
  const samplePoints: Array<[number, number]> = [
    [(rect.left + rect.right) / 2, (rect.top + rect.bottom) / 2],
    [rect.left, rect.top],
    [rect.right, rect.top],
    [rect.left, rect.bottom],
    [rect.right, rect.bottom],
  ];

  return samplePoints.some(
    (point) => pointToSegmentDistance(point, segment[0], segment[1]) <= buffer,
  );
}

function pointToSegmentDistance(
  point: [number, number],
  start: [number, number],
  end: [number, number],
) {
  const [px, py] = point;
  const [x1, y1] = start;
  const [x2, y2] = end;
  const dx = x2 - x1;
  const dy = y2 - y1;

  if (dx === 0 && dy === 0) {
    return Math.hypot(px - x1, py - y1);
  }

  const projection = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy);
  const clamped = Math.max(0, Math.min(1, projection));
  const closestX = x1 + dx * clamped;
  const closestY = y1 + dy * clamped;

  return Math.hypot(px - closestX, py - closestY);
}

function upsertGeoJsonSource(
  map: MapLibreMap,
  sourceId: string,
  data: MapFeatureCollection,
) {
  const existingSource = map.getSource(sourceId) as GeoJSONSource | undefined;

  if (existingSource) {
    existingSource.setData(data as never);
    return;
  }

  map.addSource(sourceId, {
    data: data as never,
    type: "geojson",
  });
}

function ensureLineLayer(
  map: MapLibreMap,
  layerId: string,
  sourceId: string,
  paint: Record<string, unknown>,
) {
  if (map.getLayer(layerId)) {
    return;
  }

  map.addLayer({
    id: layerId,
    paint: paint as never,
    source: sourceId,
    type: "line",
    layout: {
      "line-cap": "round",
      "line-join": "round",
    },
  });
}

function ensureCircleLayer(
  map: MapLibreMap,
  layerId: string,
  sourceId: string,
  paint: Record<string, unknown>,
) {
  if (map.getLayer(layerId)) {
    return;
  }

  map.addLayer({
    id: layerId,
    paint: paint as never,
    source: sourceId,
    type: "circle",
  });
}

function isStyleReady(map: MapLibreMap) {
  const style = map.getStyle();
  return Boolean(style && style.layers && style.layers.length > 0);
}
