"use client";

import { useMemo, useState } from "react";
import { DataStatePanel } from "@/components/data-state-panel";
import { TransitMapSurface } from "@/components/transit-map-surface";
import { segmentLossLegendItems } from "@/lib/map-utils";
import type {
  DataNotice,
  FeatureLine,
  RouteSegmentsResponse,
  RouteStopWaitResponse,
} from "@/lib/types";
import { formatMinutes } from "@/lib/utils";

type RouteCorridorEvidenceProps = {
  backgroundRouteFeatures: FeatureLine[];
  formattedWorstTimeBand: string;
  mapNotice?: DataNotice;
  routeFeatures: FeatureLine[];
  routeShortName: string;
  routeSlowTravelMinutes: number;
  segmentCollections: RouteSegmentsResponse[];
  segmentNotice?: DataNotice;
  stopWaitCollections: RouteStopWaitResponse[];
  summaryWorstSegmentLabel: string;
  transitLaneOverlay: FeatureLine[];
};

type ScopeOption = {
  id: string;
  label: string;
};

type RankedSegmentEntry = {
  directionLabels: string[];
  lossMinutes: number;
  scheduledMinutes: number;
  segmentLabel: string;
  variantCount: number;
};

export function RouteCorridorEvidence({
  backgroundRouteFeatures,
  formattedWorstTimeBand,
  mapNotice,
  routeFeatures,
  routeShortName,
  routeSlowTravelMinutes,
  segmentCollections,
  segmentNotice,
  stopWaitCollections,
  summaryWorstSegmentLabel,
  transitLaneOverlay,
}: RouteCorridorEvidenceProps) {
  const scopeOptions = useMemo<ScopeOption[]>(() => {
    if (segmentCollections.length <= 1) {
      return segmentCollections.map((collection) => ({
        id: `direction-${collection.direction_id}`,
        label: collection.direction_label ?? `Direction ${collection.direction_id}`,
      }));
    }

    return [
      { id: "both", label: "Both directions" },
      ...segmentCollections.map((collection) => ({
        id: `direction-${collection.direction_id}`,
        label: collection.direction_label ?? `Direction ${collection.direction_id}`,
      })),
    ];
  }, [segmentCollections]);
  const [activeScope, setActiveScope] = useState(scopeOptions[0]?.id ?? "both");

  const activeSegmentCollections = useMemo(() => {
    if (activeScope === "both") {
      return segmentCollections;
    }

    const activeDirectionId = Number(activeScope.replace("direction-", ""));
    return segmentCollections.filter((collection) => collection.direction_id === activeDirectionId);
  }, [activeScope, segmentCollections]);

  const activeStopWaitCollections = useMemo(() => {
    if (activeScope === "both") {
      return stopWaitCollections;
    }

    const activeDirectionId = Number(activeScope.replace("direction-", ""));
    return stopWaitCollections.filter((collection) => collection.direction_id === activeDirectionId);
  }, [activeScope, stopWaitCollections]);

  const activeSegments = useMemo(
    () =>
      activeSegmentCollections
        .flatMap((collection) => collection.features)
        .slice()
        .sort((left, right) => {
          const rightLoss = right.properties.segment_in_vehicle_loss_minutes ?? 0;
          const leftLoss = left.properties.segment_in_vehicle_loss_minutes ?? 0;

          if (rightLoss !== leftLoss) {
            return rightLoss - leftLoss;
          }

          if ((left.properties.direction_id ?? 0) !== (right.properties.direction_id ?? 0)) {
            return (left.properties.direction_id ?? 0) - (right.properties.direction_id ?? 0);
          }

          return (left.properties.segment_sequence ?? 0) - (right.properties.segment_sequence ?? 0);
        }),
    [activeSegmentCollections],
  );

  const activeStopFeatures = useMemo(
    () =>
      activeStopWaitCollections
        .flatMap((collection) => collection.features)
        .slice()
        .sort((left, right) => {
          const rightLoss = right.properties.waiting_loss_minutes ?? 0;
          const leftLoss = left.properties.waiting_loss_minutes ?? 0;

          if (rightLoss !== leftLoss) {
            return rightLoss - leftLoss;
          }

          return (left.properties.direction_id ?? 0) - (right.properties.direction_id ?? 0);
        }),
    [activeStopWaitCollections],
  );

  const topStopFeature = activeStopFeatures[0] ?? null;
  const rankedSegments = useMemo(
    () => buildRankedSegmentEntries(activeSegments),
    [activeSegments],
  );
  const topSegments = rankedSegments.slice(0, 4);
  const topSegment = topSegments[0] ?? null;
  const activeScopeLabel =
    scopeOptions.find((option) => option.id === activeScope)?.label ?? "Both directions";
  const activeSurfaceLabel =
    activeScope === "both"
      ? "Both directions MapLibre corridor"
      : `${activeScopeLabel} MapLibre corridor`;

  return (
    <article className="route-dossier-map-card">
      <div className="route-dossier-panel-bar route-dossier-panel-bar-blue">
        <span>Corridor evidence</span>
        {scopeOptions.length > 1 ? (
          <div
            aria-label="Corridor direction view"
            className="route-dossier-direction-toggle"
            role="tablist"
          >
            {scopeOptions.map((option) => (
              <button
                aria-selected={activeScope === option.id}
                className="route-dossier-direction-toggle-button"
                data-active={activeScope === option.id}
                key={option.id}
                onClick={() => setActiveScope(option.id)}
                role="tab"
                type="button"
              >
                {option.label}
              </button>
            ))}
          </div>
        ) : null}
      </div>
      <TransitMapSurface
        ariaLabel={`Route ${routeShortName} detail map`}
        backgroundRouteFeatures={backgroundRouteFeatures}
        fitBackgroundRouteFeatures={false}
        focusRouteId={routeFeatures[0]?.properties.route_id}
        hoverSegments
        key={activeScope}
        legend={{
          items: segmentLossLegendItems,
          subtitle: "Slow-travel loss per segment",
          title: "Segment key",
        }}
        minHeight="420px"
        overlayFeatures={transitLaneOverlay}
        routeColorMode="focus"
        routeFeatures={routeFeatures}
        segmentFeatures={activeSegments}
        stopFeatures={topStopFeature ? [topStopFeature] : []}
        stopMarkerScale={0.68}
        surfaceLabel={activeSurfaceLabel}
      />
      <div className="route-dossier-map-footer">
        <div>
          <p className="eyebrow">Worst section</p>
          <h2>{topSegment?.segmentLabel ?? summaryWorstSegmentLabel}</h2>
          <p>
            Evidence scope: {activeScopeLabel}. Worst time: {formattedWorstTimeBand}.
          </p>
        </div>
        <div className="route-dossier-segment-metric">
          <span>{topSegment ? "Segment slow travel" : "Route slow travel"}</span>
          <strong>{formatMinutes(topSegment?.lossMinutes ?? routeSlowTravelMinutes)}</strong>
        </div>
      </div>
      {mapNotice ? <DataStatePanel eyebrow="Route map" notice={mapNotice} /> : null}
      {segmentNotice && activeSegments.length === 0 ? (
        <DataStatePanel eyebrow="Segment layer" notice={segmentNotice} />
      ) : null}
      {topSegments.length > 0 ? (
        <>
          <div className="route-dossier-segment-list-heading">
            <strong>Highest-loss segments</strong>
            <span>
              The four segment links with the highest published in-vehicle loss in this view.
            </span>
          </div>
          <ol className="route-dossier-segment-list">
            {topSegments.map((feature, index) => (
              <li key={`${feature.segmentLabel}-${index}`}>
                <div>
                  <strong>{feature.segmentLabel}</strong>
                  <small>
                    {feature.directionLabels.join(" / ")}
                    {" · "}
                    Scheduled {feature.scheduledMinutes.toFixed(1)} min
                    {feature.variantCount > 1 ? ` · ${feature.variantCount} variants` : ""}
                  </small>
                </div>
                <b>+{feature.lossMinutes.toFixed(1)} min</b>
              </li>
            ))}
          </ol>
        </>
      ) : null}
    </article>
  );
}

function buildRankedSegmentEntries(features: RouteSegmentsResponse["features"]): RankedSegmentEntry[] {
  const grouped = new Map<string, RankedSegmentEntry>();

  for (const feature of features) {
    const segmentLabel = feature.properties.segment_label ?? "Unnamed segment";
    const directionLabel =
      feature.properties.direction_label ??
      `Direction ${feature.properties.direction_id ?? "?"}`;
    const lossMinutes = feature.properties.segment_in_vehicle_loss_minutes ?? 0;
    const scheduledMinutes = feature.properties.scheduled_segment_minutes ?? 0;
    const existing = grouped.get(segmentLabel);

    if (!existing) {
      grouped.set(segmentLabel, {
        directionLabels: [directionLabel],
        lossMinutes,
        scheduledMinutes,
        segmentLabel,
        variantCount: 1,
      });
      continue;
    }

    existing.variantCount += 1;

    if (!existing.directionLabels.includes(directionLabel)) {
      existing.directionLabels.push(directionLabel);
    }

    if (lossMinutes > existing.lossMinutes) {
      existing.lossMinutes = lossMinutes;
      existing.scheduledMinutes = scheduledMinutes;
    }
  }

  return Array.from(grouped.values()).sort((left, right) => {
    if (right.lossMinutes !== left.lossMinutes) {
      return right.lossMinutes - left.lossMinutes;
    }

    return left.segmentLabel.localeCompare(right.segmentLabel);
  });
}
