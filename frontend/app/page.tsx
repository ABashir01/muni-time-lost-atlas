import type { CSSProperties } from "react";
import Link from "next/link";
import { CompareSelector } from "@/components/compare-selector";
import { HomeBodyClass } from "@/components/home-body-class";
import { MapSchematic } from "@/components/map-schematic";
import { RouteBadge } from "@/components/route-badge";
import { TimeWindowStrip } from "@/components/time-window-strip";
import { getRouteTheme } from "@/lib/presentation";
import { getHomepageData } from "@/lib/site-data";

export default function HomePage() {
  const data = getHomepageData();
  const rankingSlots = [
    ...data.rankings.map((route) => ({ kind: "route" as const, route })),
    ...Array.from({ length: Math.max(0, 3 - data.rankings.length) }, (_, index) => ({
      kind: "placeholder" as const,
      rank: data.rankings.length + index + 1,
    })),
  ];

  return (
    <div className="homepage-viewport">
      <HomeBodyClass />
      <header className="homepage-masthead">
        <Link className="homepage-brand" href="/">
          <span aria-hidden="true" className="homepage-brand-mark">
            Muni
          </span>
          <span className="homepage-brand-copy">Muni Lost Time Atlas</span>
        </Link>
        <nav aria-label="Homepage" className="homepage-nav">
          <Link href="/map">Explore the Map</Link>
          <Link href="/#rankings">Rankings</Link>
          <Link href="/#compare">Compare</Link>
          <Link href="/methodology">Data &amp; Methods</Link>
        </nav>
      </header>

      <section className="homepage-hero">
        <div className="homepage-story-panel">
          <div className="homepage-story-copy">
            <h1 aria-label="Where Muni Riders Lose The Most Time" className="homepage-headline">
              <span>Where Muni</span>
              <span>Riders Lose</span>
              <span className="homepage-headline-emphasis">
                <span>The</span>
                <strong>Most Time</strong>
              </span>
            </h1>

            <div className="homepage-subhead">
              <div aria-hidden="true" className="homepage-subhead-icon">
                <span />
              </div>
              <p>
                Live and historical data on delays, congestion, and crowding across
                San Francisco.
              </p>
            </div>
          </div>

          <div className="homepage-story-controls">
            <TimeWindowStrip currentWindow="Now" />
            <p>Updates every 60 seconds</p>
          </div>

          <div className="homepage-story-banner">
            <span>Worst Routes Right Now</span>
            <Link href="/map">See all rankings</Link>
          </div>
        </div>

        <div className="homepage-map-panel">
          <MapSchematic
            ctaHref="/map"
            ctaLabel="Explore the map"
            editorialContext
            features={data.map.features}
            showDistrictLabels
            showLegend
            subtitle="vs. ideal trip"
            title="Extra time per trip"
          />
        </div>
      </section>

      <section className="homepage-insights" id="rankings">
        <div className="homepage-rankings">
          {rankingSlots.map((slot) =>
            slot.kind === "route" ? (
              <article
                className="homepage-ranking-card"
                key={slot.route.route_id}
                style={
                  {
                    "--route-accent": getRouteTheme(slot.route.route_id).color,
                  } as CSSProperties
                }
              >
                <div className="homepage-ranking-header">
                  <span className="homepage-ranking-rank">{slot.route.rank}</span>
                  <RouteBadge
                    label={slot.route.route_short_name}
                    routeId={slot.route.route_id}
                  />
                  <div className="homepage-ranking-route">
                    <p>{slot.route.route_name}</p>
                  </div>
                </div>

                <div className="homepage-ranking-metric">
                  <div className="homepage-ranking-value">
                    <strong>{`+${slot.route.typical_trip_loss_minutes.toFixed(1)}`}</strong>
                    <span>min</span>
                  </div>
                  <p>extra time per trip</p>
                </div>

                <div className="homepage-ranking-divider" />

                <div className="homepage-ranking-notes">
                  <p>
                    <span>Worst on</span>
                    <strong>{slot.route.worst_time_band}</strong>
                  </p>
                  <p>
                    <span>Most loss</span>
                    <strong>{slot.route.worst_segment_label}</strong>
                  </p>
                </div>
              </article>
            ) : (
              <article className="homepage-ranking-card homepage-ranking-card-placeholder" key={`slot-${slot.rank}`}>
                <div className="homepage-ranking-header">
                  <span className="homepage-ranking-rank">{slot.rank}</span>
                  <span className="route-badge homepage-placeholder-badge">?</span>
                  <div className="homepage-ranking-route">
                    <p>Published route pending</p>
                  </div>
                </div>

                <div className="homepage-ranking-metric">
                  <div className="homepage-ranking-value">
                    <strong>&mdash;</strong>
                    <span>min</span>
                  </div>
                  <p>third ranking slot reserved</p>
                </div>

                <div className="homepage-ranking-divider" />

                <div className="homepage-ranking-notes">
                  <p>
                    <span>Status</span>
                    <strong>Awaiting a third ranked fixture route</strong>
                  </p>
                  <p>
                    <span>Why</span>
                    <strong>Triptych preserved for the locked homepage layout</strong>
                  </p>
                </div>
              </article>
            ),
          )}
        </div>

        <aside className="homepage-explainer">
          <div className="homepage-explainer-head">
            <h2>What Makes You Lose Time?</h2>
          </div>

          <div className="homepage-explainer-items">
            {data.problemTypes.map((item) => (
              <article className="homepage-explainer-item" key={item.title}>
                <div
                  aria-hidden="true"
                  className={`homepage-explainer-symbol homepage-explainer-symbol-${item.icon}`}
                >
                  {item.symbol}
                </div>
                <div className="homepage-explainer-copy">
                  <h3>{item.title}</h3>
                  <p>{item.copy}</p>
                </div>
              </article>
            ))}
          </div>

          <Link className="homepage-explainer-link" href="/methodology">
            Learn more about lost time
          </Link>
        </aside>
      </section>

      <section className="homepage-compare" id="compare">
        <div className="homepage-compare-copy">
          <h2>Compare Routes Or Corridors</h2>
          <p>See how routes stack up or compare parts of the same route.</p>
        </div>

        <CompareSelector
          placeholderLabel="Select a route..."
          routes={data.rankings}
          selectedIds={[]}
        />

        <div aria-hidden="true" className="homepage-compare-motif">
          <span />
          <span />
          <span />
          <span />
        </div>
      </section>
    </div>
  );
}
