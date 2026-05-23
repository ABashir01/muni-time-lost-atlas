"use client";

import { useState } from "react";
import { DataStamp } from "@/components/data-stamp";
import { DataStatePanel } from "@/components/data-state-panel";
import { RouteBadge } from "@/components/route-badge";
import { TransitMapSurface } from "@/components/transit-map-surface";
import type { MapPageData } from "@/lib/site-data";
import { formatMinutes } from "@/lib/utils";

export function MapPageSurface({ data }: { data: MapPageData }) {
  const [lanesOn, setLanesOn] = useState(false);
  const [vehiclesOn, setVehiclesOn] = useState(true);
  const hasRoutes = data.routes.features.length > 0;

  return (
    <section className="map-surface-shell">
      <div className="map-summary-grid">
        <article className="metric-tile">
          <span>Highest published loss</span>
          <strong>
            {data.highestLossRoute
              ? formatMinutes(data.highestLossRoute.typical_trip_loss_minutes)
              : "--"}
          </strong>
          <small>
            {data.highestLossRoute
              ? `Route ${data.highestLossRoute.route_short_name} ${data.highestLossRoute.route_name}`
              : "Waiting for a published top route"}
          </small>
        </article>
        <article className="metric-tile">
          <span>Lower published loss</span>
          <strong>
            {data.lowestLossRoute
              ? formatMinutes(data.lowestLossRoute.typical_trip_loss_minutes)
              : "--"}
          </strong>
          <small>
            {data.lowestLossRoute
              ? `Route ${data.lowestLossRoute.route_short_name} ${data.lowestLossRoute.route_name}`
              : "Waiting for a published comparison route"}
          </small>
        </article>
        <article className="metric-tile">
          <span>Published corridors</span>
          <strong>{data.routeCount}</strong>
          <small>Current route geometries in the historical/static map layer</small>
        </article>
      </div>

      <div className="map-surface-header">
        <div className="section-heading">
          <p className="eyebrow">Citywide route choropleth</p>
          <h2>Start with the corridors, then read the route list beside them.</h2>
        </div>
        <div className="fixture-toggles">
          <label className="fixture-toggle">
            <span>Transit-only lane overlay</span>
            <button
              data-active={lanesOn}
              onClick={() => setLanesOn((value) => !value)}
              type="button"
            >
              {lanesOn ? "Overlay on" : "Overlay off"}
            </button>
          </label>
          <label className="fixture-toggle">
            <span>Route hover</span>
            <button disabled type="button">
              Name + time on hover
            </button>
          </label>
          <label className="fixture-toggle">
            <span>Live vehicles</span>
            <button
              data-active={vehiclesOn}
              disabled={data.liveVehicles.vehicle_count === 0}
              onClick={() => setVehiclesOn((value) => !value)}
              type="button"
            >
              {data.liveVehicles.vehicle_count === 0
                ? "No live vehicles"
                : vehiclesOn
                  ? "Overlay on"
                  : "Overlay off"}
            </button>
          </label>
        </div>
      </div>

      {data.notices.map((notice) => (
        <DataStatePanel key={`${notice.title}-${notice.message}`} notice={notice} />
      ))}

      <div className="map-layout">
        <div className="map-panel">
          {hasRoutes ? (
            <TransitMapSurface
              ariaLabel="Published citywide route loss map"
              legend={{
                subtitle: "Route corridors colored by published route loss",
                title: "Typical extra time",
              }}
              fitMaxZoom={17}
              fitPadding={2}
              hoverRoutes
              lineMode="compact"
              minHeight="620px"
              overlayFeatures={lanesOn ? data.transitLaneOverlay : []}
              routeFeatures={data.routes.features}
              routeColorMode="metric"
              surfaceLabel="MapLibre GL JS citywide surface"
              vehicleFeatures={vehiclesOn ? data.liveVehicles.features : []}
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
        <aside className="map-sidebar">
          <article className="panel-card map-card">
            <p className="map-card-label">Published map note</p>
            <p className="map-card-note">
              The city map is evidence, not the only story. Use the ranking and
              route detail views to read why a corridor is red before assuming
              causation from geometry alone.
            </p>
            <DataStamp value={data.metricUpdatedAt} />
          </article>
          <article className="panel-card map-card">
            <p className="map-card-label">Routes in this dataset</p>
            <ul className="map-list">
              {data.rankings.map((route) => (
                <li key={route.route_id}>
                  <div className="map-list-route">
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
          </article>
          <article className="panel-card map-card">
            <p className="map-card-label">Static limitations</p>
            <ul className="map-list map-note-list">
              <li>
                <div>
                  <strong>Overlay scope</strong>
                  <small>Transit-only lanes are optional spatial context only.</small>
                </div>
              </li>
              <li>
                <div>
                  <strong>Hover for route context</strong>
                  <small>Route name and published typical extra time appear directly on the map.</small>
                </div>
              </li>
              <li>
                <div>
                  <strong>Route coverage</strong>
                  <small>The live map shows whichever corridors the historical API publishes.</small>
                </div>
              </li>
              <li>
                <div>
                  <strong>Live overlay</strong>
                  <small>
                    {data.liveVehicles.vehicle_count > 0
                      ? `${data.liveVehicles.vehicle_count} live vehicle positions are available right now.`
                      : "Live vehicle context is optional and may be temporarily unavailable."}
                  </small>
                </div>
              </li>
            </ul>
          </article>
        </aside>
      </div>
    </section>
  );
}
