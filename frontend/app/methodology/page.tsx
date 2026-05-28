import Link from "next/link";
import { getMethodologyPageData } from "@/lib/site-data";

const keyPoints = [
  {
    body: "The main number on the site is typical extra time per trip. It is an estimate of how many extra minutes a rider loses on a one-way trip compared with a published baseline.",
    title: "What the headline number means",
  },
  {
    body: "That number is split into waiting loss and slow-travel loss. Waiting loss covers extra time before boarding. Slow-travel loss covers extra time after boarding.",
    title: "What is inside that number",
  },
  {
    body: "Routes are ordered by that total trip-loss number. A route with more extra minutes ranks worse than a route with fewer extra minutes.",
    title: "How rankings are built",
  },
];

const walkthrough = [
  {
    bullets: [
      "The homepage shows the routes with the highest published extra time per trip.",
      "The rankings page shows the full ordered list.",
      "The map colors route corridors by the same trip-loss metric.",
      "Each route page breaks the total into waiting, travel, worst time, worst section, and sample counts.",
    ],
    title: "1. What each page is trying to show you",
  },
  {
    bullets: [
      "Typical trip: the combined route-level delay for a one-way trip.",
      "Waiting loss: extra waiting before boarding.",
      "Slow travel: extra in-vehicle time after boarding.",
      "Worst time: the published time band where the route performs worst.",
      "Worst section: the route segment with the highest published delay burden.",
    ],
    title: "2. How to read the labels",
  },
  {
    bullets: [
      "Route rank tells you where this route sits in the current published order.",
      "Matched full trips tells you how many complete trip observations were used.",
      "Headway intervals and stop events show how much stop-level and waiting-time evidence exists behind the summary.",
      "These counts are shown so thin coverage stays visible instead of being hidden.",
    ],
    title: "3. Why sample size is shown",
  },
  {
    bullets: [
      "The transit-lane overlay is just map context.",
      "It shows where dedicated bus or transit lanes exist near the delayed routes.",
      "It does not change the scores.",
      "It does not prove that a lane caused a route to be fast or slow.",
    ],
    title: "4. What the transit-lane overlay is for",
  },
  {
    bullets: [
      "This is not a passenger-weighted citywide average.",
      "This is not a full explanation of why a route is delayed.",
      "This is not a real-time trip planner.",
      "This is not complete coverage of every possible unmatched observation.",
    ],
    title: "5. What this site is not claiming",
  },
];

const currentLimitations = [
  "The currently published historical window is all day, not a user-selectable date or time range.",
  "Direction-level detail appears only where the API publishes the directional route layers needed for it.",
  "The site is deliberately conservative about waiting-time measurement rather than filling gaps with aggressive inference.",
];

export default function MethodologyPage() {
  const data = getMethodologyPageData();

  return (
    <div className="page-stack methodology-plain-page">
      <section className="section-shell methodology-plain-hero">
        <p className="eyebrow">Data and methods</p>
        <h1 className="page-headline">How this site works.</h1>
        <p className="page-dek">
          This page explains the metric in plain language, what data is being used,
          what the map overlays mean, and what this project does not claim to measure.
        </p>
      </section>

      <section className="section-shell methodology-plain-grid methodology-plain-grid-tight">
        {keyPoints.map((item) => (
          <article className="info-panel methodology-plain-card" key={item.title}>
            <h2>{item.title}</h2>
            <p>{item.body}</p>
          </article>
        ))}
      </section>

      <section className="section-shell methodology-plain-stack">
        {walkthrough.map((section) => (
          <article className="info-panel methodology-plain-card" key={section.title}>
            <h2>{section.title}</h2>
            <ul className="method-list">
              {section.bullets.map((bullet) => (
                <li key={bullet}>{bullet}</li>
              ))}
            </ul>
          </article>
        ))}
      </section>

      <section className="section-shell methodology-plain-grid">
        <article className="info-panel methodology-plain-card">
          <h2>Current limitations</h2>
          <ul className="method-list">
            {currentLimitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="info-panel methodology-plain-card">
          <h2>Sources</h2>
          <ul className="method-list">
            {data.sources.map((source) => (
              <li key={source.href}>
                <a href={source.href} rel="noreferrer" target="_blank">
                  {source.label}
                </a>
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="section-shell methodology-plain-footer">
        <article className="info-panel methodology-plain-card">
          <h2>In one sentence</h2>
          <p>
            The site tries to answer a simple question: where do riders lose the
            most time, how much time is it, when is it worst, and how much evidence
            is behind that estimate?
          </p>
          <Link className="text-link" href="/">
            Return to the homepage
          </Link>
        </article>
      </section>
    </div>
  );
}
