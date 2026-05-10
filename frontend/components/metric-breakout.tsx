import type { RouteSummary } from "@/lib/types";
import { getRouteTheme } from "@/lib/presentation";
import { formatMinutes, routeLossShares } from "@/lib/utils";

export function MetricBreakout({ route }: { route: RouteSummary }) {
  const shares = routeLossShares(route);
  const theme = getRouteTheme(route.route_id);

  return (
    <div
      className="metric-breakout"
      style={{ ["--route-accent" as string]: theme.color }}
    >
      <div className="metric-row">
        <strong>
          <span>Waiting loss</span>
          <span>{formatMinutes(route.waiting_loss_minutes)}</span>
        </strong>
        <div className="metric-rail waiting" style={{ ["--share" as string]: shares.waiting }} />
      </div>
      <div className="metric-row">
        <strong>
          <span>In-vehicle loss</span>
          <span>{formatMinutes(route.in_vehicle_loss_minutes)}</span>
        </strong>
        <div className="metric-rail travel" style={{ ["--share" as string]: shares.travel }} />
      </div>
    </div>
  );
}
