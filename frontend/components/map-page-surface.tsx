"use client";

import { useState } from "react";
import { DataStamp } from "@/components/data-stamp";
import { MapSchematic } from "@/components/map-schematic";
import { RouteBadge } from "@/components/route-badge";
import type { MapPageData } from "@/lib/site-data";
import { formatMinutes } from "@/lib/utils";

export function MapPageSurface({ data }: { data: MapPageData }) {
  const [lanesOn, setLanesOn] = useState(true);

  return (
    <section className="map-surface-shell">
      <div className="map-summary-grid">
        <article className="metric-tile">
          <span>Highest published loss</span>
          <strong>{formatMinutes(data.highestLossRoute.typical_trip_loss_minutes)}</strong>
          <small>
            Route {data.highestLossRoute.route_short_name} {data.highestLossRoute.route_name}
          </small>
        </article>
        <article className="metric-tile">
          <span>Lower published loss</span>
          <strong>{formatMinutes(data.lowestLossRoute.typical_trip_loss_minutes)}</strong>
          <small>
            Route {data.lowestLossRoute.route_short_name} {data.lowestLossRoute.route_name}
          </small>
        </article>
        <article className="metric-tile">
          <span>Fixture corridors</span>
          <strong>{data.fixtureRouteCount}</strong>
          <small>Current route geometries in the static map bundle</small>
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
            <span>Live vehicles</span>
            <button disabled type="button">
              Deferred in static set
            </button>
          </label>
          <label className="fixture-toggle">
            <span>Stop hotspots</span>
            <button disabled type="button">
              Deferred in static set
            </button>
          </label>
        </div>
      </div>

      <div className="map-layout">
        <div className="map-panel">
          <MapSchematic
            features={data.routes.features}
            overlayFeatures={lanesOn ? data.transitLaneOverlay : []}
            showLegend
            showDistrictLabels
            title="Typical extra time"
            subtitle="Route corridors colored by published route loss"
          />
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
            <p className="map-card-label">Routes in this fixture</p>
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
                  <strong>No live fleet yet</strong>
                  <small>The deferred live vehicle layer stays disabled in this bundle.</small>
                </div>
              </li>
              <li>
                <div>
                  <strong>Route coverage</strong>
                  <small>The current published map fixture includes two route corridors.</small>
                </div>
              </li>
            </ul>
          </article>
        </aside>
      </div>
    </section>
  );
}
