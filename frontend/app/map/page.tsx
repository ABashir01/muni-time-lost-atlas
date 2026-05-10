import { MapPageSurface } from "@/components/map-page-surface";
import { getMapPageData } from "@/lib/site-data";

export default function MapPage() {
  const data = getMapPageData();

  return (
    <div className="page-stack">
      <section className="section-shell map-page-hero">
        <div>
          <p className="eyebrow">Map view</p>
          <h1 className="page-headline">The citywide evidence surface.</h1>
          <p className="page-dek">
            Corridors are colored by typical trip loss so the map supports the
            headline instead of replacing it.
          </p>
        </div>
      </section>
      <MapPageSurface data={data} />
    </div>
  );
}
