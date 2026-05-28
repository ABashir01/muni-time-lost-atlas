import { notFound } from "next/navigation";
import { DataStatePanel } from "@/components/data-state-panel";
import { RouteBadge } from "@/components/route-badge";
import { TransitMapSurface } from "@/components/transit-map-surface";
import { getRouteDetailPageData } from "@/lib/site-data";
import {
  formatMinutes,
  formatPercent,
  formatSignedMinutes,
  formatTimeBandLabel,
  routeDominantProblem,
} from "@/lib/utils";

export const dynamic = "force-dynamic";

function normalizeRouteIdParam(routeId: string) {
  try {
    return decodeURIComponent(routeId);
  } catch {
    return routeId;
  }
}

export default async function RouteDetailPage({
  params,
}: {
  params: Promise<{ routeId: string }> | { routeId: string };
}) {
  const resolvedParams: { routeId: string } = "then" in params ? await params : params;
  const routeId = normalizeRouteIdParam(resolvedParams.routeId);
  const data = await getRouteDetailPageData(routeId);

  if (!data) {
    notFound();
  }

  if (data.kind === "error") {
    return (
      <div className="page-stack editorial-page route-detail-page">
        <section className="route-dossier-summary route-dossier-summary-error">
          <div className="route-dossier-identity">
            <div>
              <p className="eyebrow">Route detail</p>
              <h1 className="route-dossier-headline">Route {data.routeId}</h1>
              <p className="route-dossier-dek">Live detail unavailable.</p>
            </div>
          </div>
          <DataStatePanel notice={data.notice} />
        </section>
      </div>
    );
  }

  const dominantProblem = routeDominantProblem(data.summary);
  const peerGap =
    data.summary.typical_trip_loss_minutes - data.systemMedianTypicalTripLoss;
  const formattedWorstTimeBand = formatTimeBandLabel(data.summary.worst_time_band);
  const topStopWait = data.stopWaitCollection?.features[0];
  const topSegments =
    [...(data.segmentCollection?.features ?? [])]
      .sort((left, right) => {
        const rightLoss = right.properties.segment_in_vehicle_loss_minutes ?? 0;
        const leftLoss = left.properties.segment_in_vehicle_loss_minutes ?? 0;

        if (rightLoss !== leftLoss) {
          return rightLoss - leftLoss;
        }

        return (left.properties.segment_sequence ?? 0) - (right.properties.segment_sequence ?? 0);
      })
      .slice(0, 4);

  return (
    <div className="page-stack editorial-page route-detail-page">
      <section className="route-dossier-summary">
        <div className="route-dossier-identity">
          <RouteBadge
            routeId={data.summary.route_id}
            label={data.summary.route_short_name}
            large
          />
          <div className="route-dossier-title">
            <p className="eyebrow">Route detail</p>
            <h1 className="route-dossier-headline">{data.summary.route_name}</h1>
            <p className="route-dossier-subtitle">{data.summary.route_long_name}</p>
            <p className="route-dossier-dek">
              Published route summary, corridor map, stop hotspot, and sample context.
            </p>
          </div>
        </div>

        <div className="route-dossier-scoreboard">
          <article>
            <span>Typical trip</span>
            <strong>{formatMinutes(data.summary.typical_trip_loss_minutes)}</strong>
            <small>full one-way trip</small>
          </article>
          <article>
            <span>Waiting loss</span>
            <strong>{formatMinutes(data.summary.waiting_loss_minutes)}</strong>
            <small>{formatPercent(data.waitingShare)} of burden</small>
          </article>
          <article>
            <span>Slow travel</span>
            <strong>{formatMinutes(data.summary.in_vehicle_loss_minutes)}</strong>
            <small>{formatPercent(1 - data.waitingShare)} of burden</small>
          </article>
          <article>
            <span>Vs. system median</span>
            <strong>{formatSignedMinutes(peerGap)}</strong>
            <small>{routeRankLabel(data.routeRank, data.rankedRouteCount)}</small>
          </article>
        </div>
      </section>

      <section className="route-dossier-grid">
        <article className="route-dossier-map-card">
          <div className="route-dossier-panel-bar route-dossier-panel-bar-blue">
            <span>Corridor evidence</span>
          </div>
          <TransitMapSurface
            ariaLabel={`Route ${data.summary.route_short_name} detail map`}
            focusRouteId={data.summary.route_id}
            minHeight="420px"
            overlayFeatures={data.transitLaneOverlay}
            routeColorMode="focus"
            routeFeatures={data.mapFeatures}
            segmentFeatures={data.segmentCollection?.features ?? []}
            stopFeatures={topStopWait ? [topStopWait] : []}
            surfaceLabel={
              data.segmentCollection
                ? `${data.segmentCollection.direction_label} MapLibre corridor`
                : "MapLibre route corridor"
            }
          />
          <div className="route-dossier-map-footer">
            <div>
              <p className="eyebrow">Worst section</p>
              <h2>{data.summary.worst_segment_label}</h2>
              <p>
                Main burden: {dominantProblem}. Worst time: {formattedWorstTimeBand}.
              </p>
            </div>
            <div className="route-dossier-segment-metric">
              <span>Route slow travel</span>
              <strong>{formatMinutes(data.summary.in_vehicle_loss_minutes)}</strong>
            </div>
          </div>
          {data.mapNotice ? <DataStatePanel eyebrow="Route map" notice={data.mapNotice} /> : null}
          {topSegments.length > 0 ? (
            <>
              <div className="route-dossier-segment-list-heading">
                <strong>Highest-loss segments</strong>
                <span>The four segment links with the highest published in-vehicle loss.</span>
              </div>
              <ol className="route-dossier-segment-list">
                {topSegments.map((feature, index) => (
                  <li
                    key={`${feature.properties.segment_sequence ?? "segment"}-${feature.properties.segment_label ?? "unknown"}-${index}`}
                  >
                    <div>
                      <strong>{feature.properties.segment_label}</strong>
                      <small>
                        Scheduled {(feature.properties.scheduled_segment_minutes ?? 0).toFixed(1)} min
                      </small>
                    </div>
                    <b>
                      +{(feature.properties.segment_in_vehicle_loss_minutes ?? 0).toFixed(1)} min
                    </b>
                  </li>
                ))}
              </ol>
            </>
          ) : data.segmentNotice ? (
            <DataStatePanel eyebrow="Segment layer" notice={data.segmentNotice} />
          ) : null}
        </article>

        <div className="route-dossier-sidebar">
          <article className="editorial-rail-card editorial-rail-card-accent">
            <p className="eyebrow">Where does the wait pile up?</p>
            <h2>{topStopWait?.properties.stop_wait_label ?? "Waiting hotspot pending"}</h2>
            {topStopWait ? (
              <>
                <p>Stop with the highest published waiting loss.</p>
                <dl className="route-dossier-definition-list">
                  <div>
                    <dt>Waiting loss</dt>
                    <dd>{formatMinutes(topStopWait.properties.waiting_loss_minutes ?? 0)}</dd>
                  </div>
                  <div>
                    <dt>Observed wait</dt>
                    <dd>{formatMinutes(topStopWait.properties.observed_effective_wait_minutes ?? 0)}</dd>
                  </div>
                  <div>
                    <dt>Scheduled wait</dt>
                    <dd>{formatMinutes(topStopWait.properties.scheduled_effective_wait_minutes ?? 0)}</dd>
                  </div>
                  <div>
                    <dt>Matched intervals</dt>
                    <dd>{topStopWait.properties.matched_headway_interval_count ?? 0}</dd>
                  </div>
                </dl>
              </>
            ) : data.stopWaitNotice ? (
              <DataStatePanel eyebrow="Stop hotspot layer" notice={data.stopWaitNotice} />
            ) : null}
          </article>

          <article className="editorial-rail-card route-dossier-sidebar-card-compact">
          <p className="eyebrow">When is it worst?</p>
          <h2>{formattedWorstTimeBand}</h2>
          <p>Time band with the highest published route-level delay.</p>
          <div className="route-dossier-lower-stat">
            <span>Main burden</span>
            <strong>{dominantProblem}</strong>
          </div>
        </article>

          <article className="editorial-rail-card route-dossier-sidebar-card-compact">
          <p className="eyebrow">Sample size</p>
          <h2>Matched trips and stops</h2>
          <p>Trips, headway intervals, and stop events behind this route summary.</p>
          <dl className="route-dossier-definition-list">
            <div>
              <dt>Route rank</dt>
              <dd>{data.routeRank ? `#${data.routeRank}` : "Not ranked yet"}</dd>
            </div>
            <div>
              <dt>Matched full trips</dt>
              <dd>{data.summary.matched_full_trip_count}</dd>
            </div>
            <div>
              <dt>Headway intervals</dt>
              <dd>{data.summary.matched_headway_interval_count}</dd>
            </div>
            <div>
              <dt>Matched stop events</dt>
              <dd>{data.summary.matched_observed_stop_event_count}</dd>
            </div>
            <div>
              <dt>Unmatched rows resolved</dt>
              <dd>{data.summary.resolved_unmatched_observation_count}</dd>
            </div>
          </dl>
        </article>
        </div>
      </section>
    </div>
  );
}

function routeRankLabel(routeRank: number | null, rankedRouteCount: number) {
  if (!routeRank) {
    return "Not ranked yet";
  }

  return rankedRouteCount > 0 ? `#${routeRank} of ${rankedRouteCount} routes` : `#${routeRank}`;
}
