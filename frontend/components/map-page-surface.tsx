"use client";

import Link from "next/link";
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
                subtitle: "Route corridors colored by expected rider time loss",
                title: "Expected rider loss",
              }}
              fitMaxZoom={17}
              fitPadding={70}
              hoverRoutes
              lineMode="default"
              minHeight="540px"
              neighborhoodLabels={cityNeighborhoodLabels}
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
                  <Link
                    aria-label={`Open route detail for ${route.route_name}`}
                    className="map-rail-route-link"
                    href={`/routes/${encodeURIComponent(route.route_id)}`}
                  >
                    <div className="map-rail-route">
                      <RouteBadge routeId={route.route_id} label={route.route_short_name} />
                      <div>
                        <strong>{route.route_name}</strong>
                        <span className="map-route-cue">View route →</span>
                      </div>
                    </div>
                    <b>{formatMinutes(route.typical_trip_loss_minutes)}</b>
                  </Link>
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
            <p className="eyebrow">How to read it</p>
            <h2>What this map is showing</h2>
            <p>
              Each route is colored by expected rider time loss, not just slow vehicle
              movement. The published number combines extra waiting before boarding
              with extra time spent riding.
            </p>
            <ul className="method-list">
              <li>
                <strong>Waiting matters most:</strong> owl routes can rank high because
                sparse, uneven overnight headways create large rider wait penalties.
              </li>
              <li>
                <strong>Red does not mean traffic alone:</strong> a high-loss route can
                be driven mostly by waiting, mostly by ride time, or by both.
              </li>
              <li>
                <strong>Use route detail pages for evidence:</strong> open a route to see
                its worst stop wait, worst segment, and sample sizes behind the summary.
              </li>
            </ul>
            <Link className="text-link" href="/methodology">
              See how we calculate time loss
            </Link>
          </article>
        </aside>
      </div>
    </section>
  );
}
