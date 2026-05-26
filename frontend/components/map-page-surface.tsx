"use client";

import { useState } from "react";
import { DataStamp } from "@/components/data-stamp";
import { DataStatePanel } from "@/components/data-state-panel";
import { RouteBadge } from "@/components/route-badge";
import { TransitMapSurface } from "@/components/transit-map-surface";
import type { MapPageData } from "@/lib/site-data";
import type { MapBounds, MapNeighborhoodLabel } from "@/lib/types";
import { formatMinutes } from "@/lib/utils";

const cityViewportBounds: MapBounds = [
  [-122.511, 37.708],
  [-122.389, 37.811],
];

const cityNeighborhoodLabels: MapNeighborhoodLabel[] = [
  { coordinate: [-122.482, 37.779], text: "Richmond" },
  { coordinate: [-122.481, 37.747], text: "Sunset" },
  { coordinate: [-122.446, 37.771], text: "Golden Gate Park" },
  { coordinate: [-122.422, 37.791], text: "Downtown" },
  { coordinate: [-122.417, 37.759], text: "Mission" },
  { coordinate: [-122.395, 37.736], text: "Bayview" },
];

export function MapPageSurface({ data }: { data: MapPageData }) {
  const [lanesOn, setLanesOn] = useState(false);
  const hasRoutes = data.routes.features.length > 0;
  const leadingRoutes = data.rankings.slice(0, 5);

  return (
    <section className="map-edition-shell">
      {data.notices.map((notice) => (
        <DataStatePanel key={`${notice.title}-${notice.message}`} notice={notice} />
      ))}

      <div className="map-edition-frame">
        <div className="map-edition-canvas">
          <div className="map-edition-bar">
            <span>Citywide route loss</span>
            <span>Current published snapshot</span>
          </div>
          {hasRoutes ? (
            <TransitMapSurface
              ariaLabel="Published citywide route loss map"
              legend={{
                subtitle: "Route corridors colored by typical extra time",
                title: "Typical extra time",
              }}
              fitMaxZoom={17}
              fitPadding={2}
              hoverRoutes
              lineMode="default"
              minHeight="540px"
              neighborhoodLabels={cityNeighborhoodLabels}
              overlayFeatures={lanesOn ? data.transitLaneOverlay : []}
              routeFeatures={data.routes.features}
              routeColorMode="metric"
              surfaceLabel="MapLibre GL JS citywide surface"
              viewportBounds={cityViewportBounds}
            />
          ) : (
            <DataStatePanel
              eyebrow="Map surface"
              notice={{
                message:
                  "The live map panel will render once the API publishes at least one route geometry.",
                title: "No corridor geometry is available for the map yet.",
              }}
            />
          )}
        </div>

        <aside className="map-edition-rail">
          <article className="editorial-rail-card editorial-rail-card-accent">
            <p className="eyebrow">Top corridors</p>
            <h2>Highest delay routes</h2>
            <ul className="map-rail-route-list">
              {leadingRoutes.map((route) => (
                <li key={route.route_id}>
                  <div className="map-rail-route">
                    <RouteBadge routeId={route.route_id} label={route.route_short_name} />
                    <div>
                      <strong>{route.route_name}</strong>
                      <small>{route.worst_segment_label}</small>
                    </div>
                  </div>
                  <b>{formatMinutes(route.typical_trip_loss_minutes)}</b>
                </li>
              ))}
            </ul>
            <DataStamp value={data.metricUpdatedAt} />
          </article>

          <article className="editorial-rail-card">
            <p className="eyebrow">System snapshot</p>
            <h2>Current spread</h2>
            <div className="map-rail-stats">
              <div>
                <span>Highest loss</span>
                <strong>
                  {data.highestLossRoute
                    ? formatMinutes(data.highestLossRoute.typical_trip_loss_minutes)
                    : "--"}
                </strong>
              </div>
              <div>
                <span>Lowest loss</span>
                <strong>
                  {data.lowestLossRoute
                    ? formatMinutes(data.lowestLossRoute.typical_trip_loss_minutes)
                    : "--"}
                </strong>
              </div>
              <div>
                <span>Published corridors</span>
                <strong>{data.routeCount}</strong>
              </div>
            </div>
          </article>

          <article className="editorial-rail-card">
            <p className="eyebrow">Overlay</p>
            <h2>Transit-only lanes</h2>
            <p>
              Use this to see where dedicated transit lanes overlap the delayed routes.
              It is context, not the delay metric itself.
            </p>
            <button
              className="map-overlay-toggle"
              data-active={lanesOn}
              onClick={() => setLanesOn((value) => !value)}
              type="button"
            >
              {lanesOn ? "Hide transit-only lanes" : "Highlight transit-only lanes"}
            </button>
          </article>
        </aside>
      </div>
    </section>
  );
}
