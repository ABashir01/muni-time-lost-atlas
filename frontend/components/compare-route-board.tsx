import { RouteBadge } from "@/components/route-badge";
import { MetricBreakout } from "@/components/metric-breakout";
import type { RouteSummary } from "@/lib/types";
import { formatMinutes, formatSignedMinutes, routeDominantProblem } from "@/lib/utils";

export function CompareRouteBoard({
  compareLimitations,
  leadingRoute,
  routes,
  systemMedianTypicalTripLoss,
}: {
  compareLimitations: string[];
  leadingRoute: RouteSummary | null;
  routes: RouteSummary[];
  systemMedianTypicalTripLoss: number;
}) {
  const routeCount = routes.length;

  return (
    <section className="compare-board">
      <div className="compare-summary">
        <article>
          <span className="eyebrow">Routes selected</span>
          <strong>{routeCount}</strong>
        </article>
        <article>
          <span className="eyebrow">Current window</span>
          <strong>{routes[0]?.window ?? "all_day"}</strong>
        </article>
        <article>
          <span className="eyebrow">Median route loss</span>
          <strong>{formatMinutes(systemMedianTypicalTripLoss)}</strong>
        </article>
        <article>
          <span className="eyebrow">Worst selected route</span>
          <strong>{leadingRoute?.route_short_name ?? "-"}</strong>
        </article>
      </div>

      <div className="compare-topline">
        <article className="panel-card compare-callout">
          <p className="eyebrow">Topline read</p>
          <h2>
            {leadingRoute
              ? `${leadingRoute.route_name} currently publishes the biggest typical trip loss in this compare set.`
              : "Pick at least two routes to produce a compare readout."}
          </h2>
          {leadingRoute ? (
            <p>
              Its headline loss is {formatMinutes(leadingRoute.typical_trip_loss_minutes)} and
              the dominant burden is {routeDominantProblem(leadingRoute)}.
            </p>
          ) : null}
        </article>
        <article className="panel-card compare-callout compare-callout-muted">
          <p className="eyebrow">Static bundle note</p>
          <ul className="compare-note-list">
            {compareLimitations.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </article>
      </div>

      <div className="compare-grid">
        {routes.map((route) => (
          <article className="compare-card" key={route.route_id}>
            <header>
              <div className="route-heading">
                <RouteBadge routeId={route.route_id} label={route.route_short_name} />
                <div>
                  <h2>{route.route_name}</h2>
                  <p>{route.route_long_name}</p>
                </div>
              </div>
              <p>
                Typical trip: <strong>{formatMinutes(route.typical_trip_loss_minutes)}</strong>
              </p>
            </header>
            <MetricBreakout route={route} />
            <div className="compare-delta-strip">
              <article>
                <span className="eyebrow">Vs. fixture median</span>
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
                  <strong>Worst time window</strong>
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
    </section>
  );
}
