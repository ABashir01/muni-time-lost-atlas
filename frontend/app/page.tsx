import type { CSSProperties } from "react";
import Link from "next/link";
import { CompareSelector } from "@/components/compare-selector";
import { DataStatePanel } from "@/components/data-state-panel";
import {
  HomepageExplainerSymbol,
  HomepageTransitSymbol,
} from "@/components/homepage-symbols";
import { RouteBadge } from "@/components/route-badge";
import { SiteHeader } from "@/components/site-header";
import { TransitMapSurface } from "@/components/transit-map-surface";
import { getRouteTheme } from "@/lib/presentation";
import { getHomepageData } from "@/lib/site-data";
import { formatTimeBandLabel } from "@/lib/utils";

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

export const dynamic = "force-dynamic";

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
  const data = await getHomepageData();
  const rankingSlots = data.rankings.slice(0, 3);

  return (
    <div className={`homepage-viewport ${homepageFontClass === "homepage-font-oswald" ? "homepage-font-oswald-roboto" : homepageFontClass}`}>
      <SiteHeader />

      <section className="homepage-hero">
        <div className="homepage-story-panel">
          <div className="homepage-story-copy">
            <h1 aria-label="Where Muni Riders Lose The Most Time" className="homepage-headline">
              <span>Where Muni</span>
              <span>Riders Lose</span>
              <span className="homepage-headline-emphasis">
                <span>The</span>
                <strong>&nbsp;Most Time</strong>
              </span>
            </h1>

            <div className="homepage-subhead">
              <div aria-hidden="true" className="homepage-subhead-icon">
                <HomepageTransitSymbol />
              </div>
              <p>
                A public map and ranking of where Muni riders lose the most time, using
                published route-delay data across San Francisco.
              </p>
            </div>
          </div>

          <div className="homepage-story-banner">
            <span>Worst Published Routes</span>
            <Link href="/rankings">See full rankings</Link>
          </div>
        </div>

        <div className="homepage-map-panel">
          <div className="homepage-map-explainer">
            <p>Homepage map key</p>
            <h3>Worst routes highlighted</h3>
            <span>
              Colored lines show the three highest-loss routes on the homepage. Gray lines
              keep the rest of the network in view.
            </span>
          </div>
          <TransitMapSurface
            ctaHref="/map"
            ctaLabel="Explore the map"
            ariaLabel="Published citywide route loss map"
            backgroundRouteFeatures={data.heroMap.backgroundFeatures}
            fitMaxZoom={13.4}
            fitPadding={0}
            gestureNavigation={false}
            hoverRoutes
            interactive
            lineMode="default"
            minHeight="100%"
            neighborhoodLabels={data.heroMap.neighborhoodLabels}
            routeColorOverrides={data.heroMap.featuredColorByRouteId}
            routeBadges={data.heroMap.routeBadges}
            routeFeatures={data.heroMap.featuredFeatures}
            routeColorMode="metric"
            showControls={false}
            surfaceLabel="MapLibre GL JS route surface"
            viewportBounds={data.heroMap.viewportBounds}
          />
        </div>
      </section>

      {data.notices.map((notice) => (
        <section className="section-shell" key={`${notice.title}-${notice.message}`}>
          <DataStatePanel notice={notice} />
        </section>
      ))}

      <section className="homepage-insights" id="rankings">
        <div className="homepage-rankings">
          {Array.from({ length: 3 }, (_, index) => rankingSlots[index]).map((route, index) =>
            route ? (
              <Link
                aria-label={`Open route detail for ${route.route_name}`}
                className="homepage-ranking-card"
                href={`/routes/${encodeURIComponent(route.route_id)}`}
                key={route.route_id}
                style={
                  {
                    "--route-accent":
                      data.heroMap.featuredColorByRouteId[route.route_id] ??
                      getRouteTheme(route.route_id).color,
                  } as CSSProperties
                }
              >
                <div className="homepage-ranking-header">
                  <span className="homepage-ranking-rank">{route.rank ?? index + 1}</span>
                  <RouteBadge
                    colorOverride={data.heroMap.featuredColorByRouteId[route.route_id]}
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
                    <span>Worst time</span>
                    <strong>{formatTimeBandLabel(route.worst_time_band)}</strong>
                  </p>
                  <p>
                    <span>Worst section</span>
                    <strong>{route.worst_segment_label}</strong>
                  </p>
                </div>
              </Link>
            ) : (
              <article className="homepage-ranking-card" key={`empty-ranking-${index}`}>
                <div className="homepage-ranking-header">
                  <span className="homepage-ranking-rank">{index + 1}</span>
                  <div className="homepage-ranking-route">
                    <p>Awaiting published route data</p>
                  </div>
                </div>
                <div className="homepage-ranking-metric">
                  <div className="homepage-ranking-value">
                    <strong>--</strong>
                    <span>min</span>
                  </div>
                  <p>extra time per trip</p>
                </div>
                <div className="homepage-ranking-divider" />
                <div className="homepage-ranking-notes">
                  <p>
                    <span>Worst time</span>
                    <strong>Not published</strong>
                  </p>
                  <p>
                    <span>Worst section</span>
                    <strong>Not published</strong>
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
                  <HomepageExplainerSymbol
                    icon={item.icon as "waiting" | "travel" | "bunching"}
                  />
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
          <h2>Compare routes or corridors.</h2>
          <p>See how routes stack up or compare parts of the same route.</p>
        </div>

        <CompareSelector
          className="homepage-compare-controls"
          placeholderLabel="Select a route..."
          routes={data.rankings}
          selectedIds={[]}
        />
      </section>
    </div>
  );
}
