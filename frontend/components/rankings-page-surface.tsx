import type { CSSProperties } from "react";
import Link from "next/link";
import { DataStamp } from "@/components/data-stamp";
import { DataStatePanel } from "@/components/data-state-panel";
import { RouteBadge } from "@/components/route-badge";
import type { RankingsPageData } from "@/lib/site-data";
import { formatTimeBandLabel } from "@/lib/utils";

export function RankingsPageSurface({ data }: { data: RankingsPageData }) {
  const denseRoutes = data.rankings.slice(3);

  return (
    <section className="rankings-ledger">
      <div className="rankings-ledger-bar">
        <span>Worst routes right now</span>
        <span>{`${data.rankings.length} routes ranked`}</span>
      </div>

      <div className="rankings-ledger-meta">
        <span>Current published snapshot</span>
        <DataStamp value={data.lastUpdatedAt} />
      </div>

      <div className="rankings-ledger-body">
        {data.notices.map((notice) => (
          <DataStatePanel key={`${notice.title}-${notice.message}`} notice={notice} />
        ))}

        {data.featuredRoutes.map((route, index) => (
          <Link
            aria-label={`Open route detail for ${route.route_name}`}
            className={`rankings-feature-card rankings-feature-card-${index + 1}`}
            href={`/routes/${encodeURIComponent(route.route_id)}`}
            key={route.route_id}
            style={{ "--route-accent": "var(--red)" } as CSSProperties}
          >
            <div className="rankings-feature-rank">{route.rank ?? index + 1}</div>
            <div className="rankings-feature-main">
              <div className="rankings-feature-route">
                <RouteBadge label={route.route_short_name} routeId={route.route_id} />
                <div>
                  <h2>{route.route_name}</h2>
                </div>
              </div>

              <div className="rankings-feature-metric">
                <strong>{`+${route.typical_trip_loss_minutes.toFixed(1)} min`}</strong>
                <span>extra time per trip</span>
              </div>

              <dl className="rankings-feature-notes">
                <div>
                  <dt>Worst on</dt>
                  <dd>{formatTimeBandLabel(route.worst_time_band)}</dd>
                </div>
                <div>
                  <dt>Most loss</dt>
                  <dd>{route.worst_segment_label}</dd>
                </div>
                <div>
                  <dt>Open</dt>
                  <dd>Route detail</dd>
                </div>
              </dl>
            </div>
          </Link>
        ))}

        <div className="rankings-dense-list">
          {denseRoutes.length > 0 ? (
            denseRoutes.map((route, index) => (
              <Link
                aria-label={`Open route detail for ${route.route_name}`}
                className="rankings-dense-row"
                href={`/routes/${encodeURIComponent(route.route_id)}`}
                key={route.route_id}
              >
                <span className="rankings-dense-rank">
                  {route.rank ?? index + data.featuredRoutes.length + 1}
                </span>
                <div className="rankings-dense-route">
                  <RouteBadge label={route.route_short_name} routeId={route.route_id} />
                  <div>
                    <strong>{route.route_name}</strong>
                    <p>{route.worst_segment_label}</p>
                  </div>
                </div>
                <div className="rankings-dense-metric">
                  <b>{`+${route.typical_trip_loss_minutes.toFixed(1)} min`}</b>
                  <span>{formatTimeBandLabel(route.worst_time_band)}</span>
                </div>
                <span>Route detail</span>
              </Link>
            ))
          ) : (
            <article className="rankings-dense-row rankings-dense-row-empty">
              <span className="rankings-dense-rank">4</span>
              <div className="rankings-dense-route">
                <div>
                  <strong>Awaiting more published routes</strong>
                </div>
              </div>
              <div className="rankings-dense-metric">
                <b>--</b>
                <span>Not published</span>
              </div>
            </article>
          )}
        </div>
      </div>
    </section>
  );
}
