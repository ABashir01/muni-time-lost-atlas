import { RouteBadge } from "@/components/route-badge";
import { MetricBreakout } from "@/components/metric-breakout";
import type { RouteSummary } from "@/lib/types";
import { formatMinutes } from "@/lib/utils";

export function CompareRouteBoard({
  routes,
  systemMedianTypicalTripLoss,
}: {
  routes: RouteSummary[];
  systemMedianTypicalTripLoss: number;
}) {
  return (
    <section className="compare-board">
      <div className="compare-summary">
        <article>
          <span className="eyebrow">Fixture route count</span>
          <strong>{routes.length}</strong>
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
          <span className="eyebrow">Top route</span>
          <strong>{routes[0]?.route_short_name ?? "-"}</strong>
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
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}
