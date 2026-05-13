import type { CSSProperties } from "react";
import Link from "next/link";
import { CompareSelector } from "@/components/compare-selector";
import { MapSchematic } from "@/components/map-schematic";
import { RouteBadge } from "@/components/route-badge";
import { TimeWindowStrip } from "@/components/time-window-strip";
import { getRouteTheme } from "@/lib/presentation";
import { getHomepageData } from "@/lib/site-data";

const homepageFontVariants = {
  "anton-oswald": "homepage-font-anton-oswald",
  "league-roboto": "homepage-font-league-roboto",
  "bebas-archivo": "homepage-font-bebas-archivo",
  "fjalla-archivo": "homepage-font-fjalla-archivo",
  "archivo-narrow": "homepage-font-archivo-narrow",
  "oswald-roboto": "homepage-font-oswald-roboto",
  oswald: "homepage-font-oswald",
} as const;

type HomepageFontVariant = keyof typeof homepageFontVariants;

export default async function HomePage({
  searchParams,
}: {
  searchParams?: Promise<{ font?: string | string[] }> | { font?: string | string[] };
}) {
  const resolvedSearchParams =
    searchParams && "then" in searchParams ? await searchParams : searchParams;
  const requestedVariant = Array.isArray(resolvedSearchParams?.font)
    ? resolvedSearchParams?.font[0]
    : resolvedSearchParams?.font;
  const homepageFontClass =
    homepageFontVariants[(requestedVariant as HomepageFontVariant) ?? "oswald"] ??
    homepageFontVariants.oswald;
  const data = getHomepageData();
  const mockedThirdRanking = {
    rank: 3,
    route_id: "38",
    route_name: "Geary",
    route_short_name: "38",
    typical_trip_loss_minutes: 0.9,
    worst_time_band: "16:00-16:59",
    worst_segment_label: "33rd Ave -> Stanyan St",
  };
  const rankingSlots = [...data.rankings, mockedThirdRanking].slice(0, 3);

  return (
    <div className={`homepage-viewport ${homepageFontClass === "homepage-font-oswald" ? "homepage-font-oswald-roboto" : homepageFontClass}`}>
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
          {rankingSlots.map((route) => (
            <article
              className="homepage-ranking-card"
              key={route.route_id}
              style={
                {
                  "--route-accent": getRouteTheme(route.route_id).color,
                } as CSSProperties
              }
            >
              <div className="homepage-ranking-header">
                <span className="homepage-ranking-rank">{route.rank}</span>
                <RouteBadge
                  label={route.route_short_name}
                  routeId={route.route_id}
                />
                <div className="homepage-ranking-route">
                  <p>{route.route_name}</p>
                </div>
              </div>

              <div className="homepage-ranking-metric">
                <div className="homepage-ranking-value">
                  <strong>{`+${route.typical_trip_loss_minutes.toFixed(1)}`}</strong>
                  <span>min</span>
                </div>
                <p>extra time per trip</p>
              </div>

              <div className="homepage-ranking-divider" />

              <div className="homepage-ranking-notes">
                <p>
                  <span>Worst on</span>
                  <strong>{route.worst_time_band}</strong>
                </p>
                <p>
                  <span>Most loss</span>
                  <strong>{route.worst_segment_label}</strong>
                </p>
              </div>
            </article>
          ))}
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

          <div className="homepage-explainer-footer">
            <Link className="homepage-explainer-link" href="/methodology">
              Learn more about lost time
            </Link>
          </div>
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
