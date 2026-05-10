import Link from "next/link";
import { getMethodologyPageData } from "@/lib/site-data";

export default function MethodologyPage() {
  const data = getMethodologyPageData();

  return (
    <div className="page-stack">
      <section className="section-shell methodology-hero">
        <p className="eyebrow">Data and methods</p>
        <h1 className="page-headline">Typical trip: +X.X min is the public promise.</h1>
        <p className="page-dek">
          The site translates operations into rider consequences, separating
          extra waiting time from extra in-vehicle travel time and keeping the
          conservative MVP scope explicit.
        </p>
      </section>

      <section className="section-shell methodology-grid">
        {data.sections.map((section) => (
          <article className="panel-card" key={section.title}>
            <div className="panel-heading">
              <p className="eyebrow">{section.kicker}</p>
              <h2>{section.title}</h2>
            </div>
            {section.formula ? <pre className="formula-block">{section.formula}</pre> : null}
            <div className="copy-stack">
              {section.paragraphs.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
            </div>
            {section.bullets ? (
              <ul className="method-list">
                {section.bullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
            ) : null}
          </article>
        ))}
      </section>

      <section className="section-shell lower-grid">
        <article className="info-panel">
          <p className="eyebrow">Sources</p>
          <h2>Documented inputs, not hidden scoring.</h2>
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
        <article className="info-panel">
          <p className="eyebrow">Read the product</p>
          <h2>The map is evidence, not the only story.</h2>
          <p>
            Start with the rankings, then use the map, route detail, and compare
            screens to understand where and when riders lose time.
          </p>
          <Link className="text-link" href="/">
            Return to the homepage
          </Link>
        </article>
      </section>
    </div>
  );
}
