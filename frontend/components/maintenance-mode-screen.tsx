export function MaintenanceModeScreen() {
  return (
    <main className="maintenance-shell">
      <div className="maintenance-card">
        <p className="maintenance-eyebrow">Scheduled maintenance</p>
        <h1>Muni Lost Time Atlas is updating its published data.</h1>
        <p className="maintenance-copy">
          The site is performing scheduled maintenance while the latest historical
          publication is loaded. It should return in roughly 30 minutes.
        </p>
      </div>
    </main>
  );
}
