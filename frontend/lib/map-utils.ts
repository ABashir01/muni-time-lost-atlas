import type { FeatureLine, StopWaitFeature } from "@/lib/types";
import { getRouteTheme } from "@/lib/presentation";

export type MapLegendItem = {
  color: string;
  label: string;
};

type DecoratedLineFeature = FeatureLine & {
  properties: FeatureLine["properties"] & {
    map_color: string;
    map_opacity: number;
    map_width: number;
  };
};

type DecoratedStopFeature = StopWaitFeature & {
  properties: StopWaitFeature["properties"] & {
    map_color: string;
    map_radius: number;
  };
};

export const routeLossLegendItems: MapLegendItem[] = [
  { color: "#d81420", label: "+10 min or more" },
  { color: "#e85c10", label: "+5 to +10 min" },
  { color: "#fcc000", label: "+2 to +5 min" },
  { color: "#0868d0", label: "+0 to +2 min" },
  { color: "#138646", label: "On time / better" },
  { color: "#0868d0", label: "Transit-only lanes" },
];

export function decorateRouteFeatures(
  features: FeatureLine[],
  options?: {
    colorOverrides?: Record<string, string>;
    focusRouteId?: string;
    mode?: "focus" | "metric";
  },
): DecoratedLineFeature[] {
  const mode = options?.mode ?? "metric";
  const colorOverrides = options?.colorOverrides ?? {};
  const focusRouteId = options?.focusRouteId;

  return features.map((feature) => {
    const isFocused = !focusRouteId || focusRouteId === feature.properties.route_id;
    const metricValue =
      feature.properties.typical_trip_loss_minutes ?? feature.properties.metric_value ?? 0;
    const routeTheme = getRouteTheme(feature.properties.route_id);
    const color =
      colorOverrides[feature.properties.route_id] ??
      (mode === "focus"
        ? isFocused
          ? routeTheme.color
          : "#707070"
        : getRouteLossColor(metricValue));

    return {
      ...feature,
      properties: {
        ...feature.properties,
        map_color: color,
        map_opacity: isFocused ? 0.94 : 0.28,
        map_width: isFocused ? 4.75 : 3.1,
      },
    };
  });
}

export function decorateContextRouteFeatures(features: FeatureLine[]): DecoratedLineFeature[] {
  return features.map((feature) => ({
    ...feature,
    properties: {
      ...feature.properties,
      map_color: "#c7cfd5",
      map_opacity: 1,
      map_width: 1.4,
    },
  }));
}

export function decorateOverlayFeatures(features: FeatureLine[]): DecoratedLineFeature[] {
  return features.map((feature) => ({
    ...feature,
    properties: {
      ...feature.properties,
      map_color: "#0868d0",
      map_opacity: 0.55,
      map_width: 2.4,
    },
  }));
}

export function decorateSegmentFeatures(features: FeatureLine[]): DecoratedLineFeature[] {
  return features.map((feature) => {
    const loss = feature.properties.segment_in_vehicle_loss_minutes ?? 0;

    return {
      ...feature,
      properties: {
        ...feature.properties,
        map_color: getSegmentLossColor(loss),
        map_opacity: 0.92,
        map_width: 5.6,
      },
    };
  });
}

export function decorateStopHotspots(features: StopWaitFeature[]): DecoratedStopFeature[] {
  return features.map((feature) => {
    const loss = feature.properties.waiting_loss_minutes ?? 0;

    return {
      ...feature,
      properties: {
        ...feature.properties,
        map_color: getStopWaitColor(loss),
        map_radius: getStopWaitRadius(loss),
      },
    };
  });
}

export function toFeatureCollection<T>(features: T[]) {
  return {
    type: "FeatureCollection" as const,
    features,
  };
}

export function getMapBounds(input: {
  overlayFeatures?: FeatureLine[];
  routeFeatures?: FeatureLine[];
  segmentFeatures?: FeatureLine[];
  stopFeatures?: StopWaitFeature[];
}) {
  const lineFeatures = [
    ...(input.routeFeatures ?? []),
    ...(input.overlayFeatures ?? []),
    ...(input.segmentFeatures ?? []),
  ];
  const stopFeatures = input.stopFeatures ?? [];
  const coordinates: Array<[number, number]> = [];

  lineFeatures.forEach((feature) => {
    flattenLineGeometry(feature.geometry).forEach((segment) => {
      segment.forEach((coordinate) => {
        coordinates.push(coordinate);
      });
    });
  });

  stopFeatures.forEach((feature) => {
    coordinates.push(feature.geometry.coordinates);
  });

  if (coordinates.length === 0) {
    return null;
  }

  const longitudes = coordinates.map(([longitude]) => longitude);
  const latitudes = coordinates.map(([, latitude]) => latitude);
  const minLongitude = Math.min(...longitudes);
  const maxLongitude = Math.max(...longitudes);
  const minLatitude = Math.min(...latitudes);
  const maxLatitude = Math.max(...latitudes);
  const minimumSpan = 0.006;
  const longitudePadding = Math.max((maxLongitude - minLongitude) * 0.12, minimumSpan);
  const latitudePadding = Math.max((maxLatitude - minLatitude) * 0.12, minimumSpan);

  return [
    [minLongitude - longitudePadding, minLatitude - latitudePadding],
    [maxLongitude + longitudePadding, maxLatitude + latitudePadding],
  ] as [[number, number], [number, number]];
}

export function getRouteLossColor(value: number) {
  if (value >= 10) {
    return "#d81420";
  }

  if (value >= 5) {
    return "#e85c10";
  }

  if (value >= 2) {
    return "#fcc000";
  }

  if (value > 0) {
    return "#0868d0";
  }

  return "#138646";
}

export function getSegmentLossColor(value: number) {
  if (value >= 2) {
    return "#d81420";
  }

  if (value >= 1.4) {
    return "#e85c10";
  }

  if (value >= 0.8) {
    return "#fcc000";
  }

  if (value > 0) {
    return "#0868d0";
  }

  return "#138646";
}

export function getStopWaitColor(value: number) {
  if (value >= 3) {
    return "#d81420";
  }

  if (value >= 2) {
    return "#e85c10";
  }

  if (value >= 1) {
    return "#fcc000";
  }

  return "#0868d0";
}

function getStopWaitRadius(value: number) {
  if (value >= 3) {
    return 15;
  }

  if (value >= 2) {
    return 13;
  }

  if (value >= 1) {
    return 11;
  }

  return 9;
}

function flattenLineGeometry(geometry: FeatureLine["geometry"]) {
  return geometry.type === "MultiLineString" ? geometry.coordinates : [geometry.coordinates];
}
