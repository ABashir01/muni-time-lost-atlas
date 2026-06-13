import Link from "next/link";

const implementationDecisions = [
  "The public homepage, rankings, map, and compare pages currently use one route-level number per route. In practice, that means the published route loss is grouped by route_id, not by route_id plus direction_id, so inbound and outbound service are pooled into one public value.",
  "Waiting loss uses exact matched first-stop headway intervals only. If a trip does not have the exact first-stop match needed for that headway calculation, it does not enter the waiting-loss numerator.",
  "In-vehicle loss uses full matched trips only. A trip must have both the first and last scheduled stop matched before it enters the full-trip runtime sample.",
  "Negative differences are clamped at zero. If an observed headway or trip runtime is better than the scheduled baseline, the public loss is reported as zero rather than as a negative value.",
  "The current public window is all_day. The site does not yet expose a rider-selectable date range or time-range switch.",
];

const sourceLinks = [
  {
    href: "https://onlinepubs.trb.org/Onlinepubs/trr/1980/746/746-005.pdf",
    label:
      "Transportation Research Record: Evaluating Potential Effectiveness of Headway Control Strategies for Transit Systems",
  },
  {
    href: "https://511.org/open-data/transit",
    label: "511 transit open data",
  },
  {
    href: "https://511.org/about/faq/open-data",
    label: "511 open data FAQ",
  },
];

export default function MethodologyPage() {
  return (
    <div className="page-stack methodology-plain-page">
      <section className="section-shell methodology-plain-hero">
        <p className="eyebrow">Data and methods</p>
        <h1 className="page-headline">How the route time-loss number is calculated.</h1>
        <p className="page-dek">
          This site ranks Muni routes by one rider-facing number: typical extra time
          per one-way trip. The formula below is the actual public metric used by the
          app.
        </p>
      </section>

      <section className="section-shell methodology-plain-stack">
        <article className="info-panel methodology-plain-card">
          <h2>1. Route time loss</h2>
          <p>
            The route-level number shown on the homepage, rankings page, map, compare
            page, and route pages is:
          </p>
          <div className="methodology-formula-block" role="img" aria-label="Route time loss formula">
            <p className="methodology-formula-line">
              <strong>Typical route time loss</strong> = <strong>waiting loss</strong> +{" "}
              <strong>median full-trip in-vehicle loss</strong>
            </p>
          </div>
          <p>
            Routes are ranked from highest to lowest typical route time loss.
          </p>
        </article>

        <article className="info-panel methodology-plain-card">
          <h2>2. Waiting loss</h2>
          <p>
            Waiting loss estimates how much extra time a full-trip rider loses before
            boarding because actual headways are less regular than the schedule.
          </p>
          <div className="methodology-formula-block" role="img" aria-label="Waiting loss formula">
            <p className="methodology-formula-line">
              <strong>Observed waiting time</strong> =
              {" "}sum of observed headway squared ÷ (2 × sum of observed headway × 60)
            </p>
            <p className="methodology-formula-line">
              <strong>Scheduled waiting time</strong> =
              {" "}sum of scheduled headway squared ÷ (2 × sum of scheduled headway × 60)
            </p>
            <p className="methodology-formula-line">
              <strong>Waiting loss</strong> =
              {" "}the observed waiting time minus the scheduled waiting time, but never below zero
            </p>
          </div>
          <p>
            The formula comes from the headway-based expected-waiting result
            discussed in{" "}
            <a className="methodology-link" href={sourceLinks[0].href} rel="noreferrer" target="_blank">
              {sourceLinks[0].label}
            </a>
            .
          </p>
        </article>

        <article className="info-panel methodology-plain-card">
          <h2>3. In-vehicle loss</h2>
          <p>
            In-vehicle loss measures how much longer the trip took after boarding,
            compared with the scheduled one-way runtime.
          </p>
          <div className="methodology-formula-block" role="img" aria-label="In-vehicle loss formula">
            <p className="methodology-formula-line">
              <strong>Trip in-vehicle loss</strong> =
              {" "}observed full-trip runtime minus scheduled full-trip runtime, but never below zero
            </p>
            <p className="methodology-formula-line">
              <strong>Route in-vehicle loss</strong> =
              {" "}the median full-trip in-vehicle loss across all matched trips for that route
            </p>
          </div>
          <p>
            The route-level public metric uses the median full-trip loss rather than
            the mean so a few extreme trips do not dominate the route number.
          </p>
        </article>
      </section>

      <section className="section-shell methodology-plain-grid">
        <article className="info-panel methodology-plain-card">
          <h2>4. Decisions in the published metric</h2>
          <ul className="method-list">
            {implementationDecisions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="info-panel methodology-plain-card">
          <h2>5. Data sources</h2>
          <p>The current published metric combines two 511 data paths:</p>
          <ul className="method-list">
            <li>
              <strong>Scheduled baseline:</strong> the active operator-specific Muni
              GTFS feed from 511 (`operator_id=SF`).
            </li>
            <li>
              <strong>Observed historic arrivals:</strong> 511 historic regional `RG`
              archives with the `-so` stop-observations variant, filtered to SFMTA /
              Muni (`agency_id=SF`) for the published historical snapshot.
            </li>
          </ul>
          <p>Primary source links:</p>
          <ul className="method-list">
            {sourceLinks.map((source) => (
              <li key={source.href}>
                <a className="methodology-link" href={source.href} rel="noreferrer" target="_blank">
                  {source.label}
                </a>
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="section-shell methodology-plain-footer">
        <article className="info-panel methodology-plain-card">
          <h2>In short</h2>
          <p>
            The public route number is scheduled-vs-observed rider time loss: extra
            waiting before boarding plus the median extra runtime after boarding, using
            the 511 schedule and historical stop-observation feeds that the project
            currently publishes.
          </p>
          <Link className="text-link" href="/">
            Return to the homepage
          </Link>
        </article>
      </section>
    </div>
  );
}
