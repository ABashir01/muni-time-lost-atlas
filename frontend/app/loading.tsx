export default function Loading() {
  return (
    <div className="page-stack">
      <section className="section-shell">
        <p className="eyebrow">Loading live data</p>
        <h1 className="page-headline">Reading the historical/static API.</h1>
        <p className="page-dek">
          The frontend is waiting for the latest published route summaries and map layers.
        </p>
      </section>
    </div>
  );
}
