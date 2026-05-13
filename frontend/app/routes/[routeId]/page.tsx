import { notFound } from "next/navigation";
import { DataStamp } from "@/components/data-stamp";
import { MapSchematic } from "@/components/map-schematic";
import { RouteBadge } from "@/components/route-badge";
import { getRouteDetailPageData, getRouteIds } from "@/lib/site-data";
import {
  formatMinutes,
  formatPercent,
  formatSignedMinutes,
  routeDominantProblem,
} from "@/lib/utils";

export function generateStaticParams() {
  return getRouteIds().map((routeId) => ({ routeId }));
}

export default async function RouteDetailPage({
  params,
}: {
  params: Promise<{ routeId: string }> | { routeId: string };
}) {
  const resolvedParams: { routeId: string } = "then" in params ? await params : params;
  const data = getRouteDetailPageData(resolvedParams.routeId);

  if (!data) {
    notFound();
  }

  const dominantProblem = routeDominantProblem(data.summary);
  const peerGap =
    data.summary.typical_trip_loss_minutes - data.systemMedianTypicalTripLoss;
  const topStopWait = data.stopWaitCollection?.features[0];

  return (
    <div className="page-stack detail-stack">
      <section className="section-shell detail-hero">
        <div className="detail-heading">
          <div className="route-heading">
            <RouteBadge
              routeId={data.summary.route_id}
              label={data.summary.route_short_name}
              large
            />
            <div>
              <p className="eyebrow">Route detail</p>
              <h1>
                {data.summary.route_name}
                <span>{data.summary.route_long_name}</span>
              </h1>
            </div>
          </div>
          <p className="detail-summary">
            Typical trip:{" "}
            <strong>{formatMinutes(data.summary.typical_trip_loss_minutes)}</strong>.
            The strongest signal on this route is{" "}
            <strong>{dominantProblem}</strong>, with the worst published window
            at <strong>{data.summary.worst_time_band}</strong>.
          </p>
        </div>
        <div className="detail-metrics">
          <article className="metric-tile">
            <span>Typical trip</span>
            <strong>{formatMinutes(data.summary.typical_trip_loss_minutes)}</strong>
            <small>Typical extra time on a full one-way trip</small>
          </article>
          <article className="metric-tile">
            <span>Waiting loss</span>
            <strong>{formatMinutes(data.summary.waiting_loss_minutes)}</strong>
            <small>{formatPercent(data.waitingShare)} of published route loss</small>
          </article>
          <article className="metric-tile">
            <span>In-vehicle loss</span>
            <strong>{formatMinutes(data.summary.in_vehicle_loss_minutes)}</strong>
            <small>{formatPercent(1 - data.waitingShare)} of published route loss</small>
          </article>
          <article className="metric-tile">
            <span>System comparison</span>
            <strong>{formatSignedMinutes(peerGap)}</strong>
            <small>Compared with the current fixture-set route median</small>
          </article>
        </div>
        <DataStamp value={data.summary.metric_updated_at} />
      </section>

      <section className="detail-grid section-shell">
        <article className="panel-card">
          <div className="panel-heading">
            <p className="eyebrow">Where on the route?</p>
            <h2>Corridor evidence before any theory.</h2>
          </div>
          <MapSchematic
            features={data.mapFeatures}
            focusRouteId={data.summary.route_id}
            showDistrictLabels
            title="Published corridor geometry"
            subtitle={
              data.segmentCollection
                ? `${data.segmentCollection.direction_label} adjacent-stop segments`
                : "Route corridor from the citywide map layer"
            }
          />
          {data.segmentCollection ? (
            <ol className="segment-list">
              {data.segmentCollection.features.map((feature) => (
                <li key={feature.properties.segment_sequence}>
                  <div>
                    <strong>{feature.properties.segment_label}</strong>
                    <span>
                      Scheduled{" "}
                      {(feature.properties.scheduled_segment_minutes ?? 0).toFixed(1)} min
                    </span>
                  </div>
                  <b>
                    +{(feature.properties.segment_in_vehicle_loss_minutes ?? 0).toFixed(1)} min
                  </b>
                </li>
              ))}
            </ol>
          ) : (
            <p className="fixture-note">
              This route reuses the shared summary and map fixtures. A dedicated
              adjacent-stop segment payload has only been published for route 14
              in the current static set.
            </p>
          )}
        </article>

        <article className="panel-card">
          <div className="panel-heading">
            <p className="eyebrow">Where does the wait pile up?</p>
            <h2>Stop-hotspot evidence is separate from segment travel loss.</h2>
          </div>
          {topStopWait ? (
            <div className="stop-hotspot-card">
              <div className="time-band-card">
                <span>Worst published stop wait</span>
                <strong>{topStopWait.properties.stop_wait_label}</strong>
                <p>
                  Scheduled effective wait {formatMinutes(
                    topStopWait.properties.scheduled_effective_wait_minutes ?? 0,
                  )}, observed effective wait{" "}
                  {formatMinutes(topStopWait.properties.observed_effective_wait_minutes ?? 0)}.
                </p>
              </div>
              <dl className="detail-definition-grid">
                <div>
                  <dt>Waiting loss</dt>
                  <dd>{formatMinutes(topStopWait.properties.waiting_loss_minutes ?? 0)}</dd>
                </div>
                <div>
                  <dt>Direction</dt>
                  <dd>{topStopWait.properties.direction_label ?? data.summary.window}</dd>
                </div>
                <div>
                  <dt>Strategy</dt>
                  <dd>{topStopWait.properties.stop_wait_strategy ?? "fixture only"}</dd>
                </div>
                <div>
                  <dt>Matched intervals</dt>
                  <dd>{topStopWait.properties.matched_headway_interval_count ?? 0}</dd>
                </div>
              </dl>
            </div>
          ) : (
            <p className="fixture-note">
              Dedicated stop-wait hotspot data is currently published only for
              route 14 outbound. Other route detail pages keep the route-level
              worst stop label visible until broader fixtures land.
            </p>
          )}
        </article>

        <article className="panel-card">
          <div className="panel-heading">
            <p className="eyebrow">When does it break down?</p>
            <h2>The current public window points to one especially bad band.</h2>
          </div>
          <div className="time-band-card">
            <span>Worst time window</span>
            <strong>{data.summary.worst_time_band}</strong>
            <p>
              The accepted historical API bundle currently publishes the
              all-day window plus this route-level worst time band label. The
              frontend keeps that language intact.
            </p>
          </div>
          <div className="interpretation-stack">
            <div>
              <span>Main burden</span>
              <strong>{dominantProblem}</strong>
            </div>
            <div>
              <span>Worst stop wait</span>
              <strong>{data.summary.worst_stop_wait_label}</strong>
            </div>
            <div>
              <span>Worst segment</span>
              <strong>{data.summary.worst_segment_label}</strong>
            </div>
          </div>
        </article>

        <article className="panel-card">
          <div className="panel-heading">
            <p className="eyebrow">Evidence coverage</p>
            <h2>Keep the public metric tied to what was actually matched.</h2>
          </div>
          <dl className="detail-definition-grid">
            <div>
              <dt>Route rank</dt>
              <dd>{data.routeRank ? `#${data.routeRank}` : "Fixture-only"}</dd>
            </div>
            <div>
              <dt>Matched full trips</dt>
              <dd>{data.summary.matched_full_trip_count}</dd>
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

        <article className="panel-card">
          <div className="panel-heading">
            <p className="eyebrow">How does it compare?</p>
            <h2>Peer context without dashboard sprawl.</h2>
          </div>
          <ul className="peer-list">
            {data.peers.map((peer) => (
              <li key={peer.route_id}>
                <div className="peer-route">
                  <RouteBadge routeId={peer.route_id} label={peer.route_short_name} />
                  <div>
                    <strong>{peer.route_name}</strong>
                    <span>{peer.worst_time_band}</span>
                  </div>
                </div>
                <b>{formatMinutes(peer.typical_trip_loss_minutes)}</b>
              </li>
            ))}
          </ul>
        </article>
      </section>
    </div>
  );
}
