import type { CSSProperties } from "react";
import { RouteBadge } from "@/components/route-badge";
import { DataStatePanel } from "@/components/data-state-panel";
import { MetricBreakout } from "@/components/metric-breakout";
import { getRouteTheme } from "@/lib/presentation";
import type { DataNotice, RouteSummary } from "@/lib/types";
import { formatMinutes, formatSignedMinutes, routeDominantProblem } from "@/lib/utils";

export function CompareRouteBoard({
  compareLimitations,
  leadingRoute,
  notices,
  routes,
  systemMedianTypicalTripLoss,
}: {
  compareLimitations: string[];
  leadingRoute: RouteSummary | null;
  notices: DataNotice[];
  routes: RouteSummary[];
  systemMedianTypicalTripLoss: number;
}) {
  const routeCount = routes.length;

  return (
    <section className="compare-board">
      <div className="compare-meta-row">
        <span>{`${routeCount} routes selected`}</span>
        <span>Current published snapshot</span>
        <span>{`Median route loss: ${formatMinutes(systemMedianTypicalTripLoss)}`}</span>
        {leadingRoute ? <span>{`Highest: ${leadingRoute.route_name}`}</span> : null}
      </div>

      {notices.map((notice) => (
        <DataStatePanel key={`${notice.title}-${notice.message}`} notice={notice} />
      ))}

      <div className="compare-grid">
        {routes.map((route) => (
          <article
            className="compare-card"
            key={route.route_id}
            style={
              {
                "--compare-accent": getRouteTheme(route.route_id).color,
              } as CSSProperties
            }
          >
            <header>
              <div className="route-heading">
                <RouteBadge routeId={route.route_id} label={route.route_short_name} />
                <div>
                  <h2>{route.route_name}</h2>
                  <p>{route.route_long_name}</p>
                </div>
              </div>
              <div className="compare-card-headline-metric">
                <span>Typical trip</span>
                <div className="compare-card-headline-value">
                  <strong>{`+${route.typical_trip_loss_minutes.toFixed(1)}`}</strong>
                  <b>min</b>
                </div>
              </div>
            </header>
            <MetricBreakout route={route} />
            <div className="compare-delta-strip">
              <article>
                <span className="eyebrow">Vs. median</span>
                <strong>
                  {formatSignedMinutes(
                    route.typical_trip_loss_minutes - systemMedianTypicalTripLoss,
                  )}
                </strong>
              </article>
              <article>
                <span className="eyebrow">Main burden</span>
                <strong>{routeDominantProblem(route)}</strong>
              </article>
            </div>
            <ul className="compare-list">
              <li>
                <div>
                  <strong>Worst time</strong>
                  <small>{route.worst_time_band}</small>
                </div>
                <b>{route.worst_time_band}</b>
              </li>
              <li>
                <div>
                  <strong>Worst segment</strong>
                  <small>{route.worst_segment_label}</small>
                </div>
                <b>{formatMinutes(route.in_vehicle_loss_minutes)}</b>
              </li>
              <li>
                <div>
                  <strong>Worst stop wait</strong>
                  <small>{route.worst_stop_wait_label}</small>
                </div>
                <b>{formatMinutes(route.waiting_loss_minutes)}</b>
              </li>
              <li>
                <div>
                  <strong>Coverage</strong>
                  <small>{route.matched_full_trip_count} matched full trips</small>
                </div>
                <b>{route.matched_observed_stop_event_count} stop events</b>
              </li>
            </ul>
          </article>
        ))}
      </div>

      {compareLimitations.length > 0 ? (
        <p className="compare-footnote">
          {compareLimitations[0]}
        </p>
      ) : null}
    </section>
  );
}
