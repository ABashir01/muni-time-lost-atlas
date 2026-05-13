"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="page-stack">
      <section className="section-shell">
        <p className="eyebrow">Live API error</p>
        <h1 className="page-headline">The frontend hit an unexpected integration failure.</h1>
        <p className="page-dek">{error.message}</p>
        <button onClick={() => reset()} type="button">
          Retry
        </button>
      </section>
    </div>
  );
}
