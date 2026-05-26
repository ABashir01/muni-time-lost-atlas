import { MapPageSurface } from "@/components/map-page-surface";
import { getMapPageData } from "@/lib/site-data";

export const dynamic = "force-dynamic";

export default async function MapPage() {
  const data = await getMapPageData();

  return (
    <div className="page-stack editorial-page map-page">
      <section className="map-page-intro">
        <div className="map-page-intro-copy">
          <p className="eyebrow">Map view</p>
          <h1>Citywide route delay map</h1>
          <p>
            Published routes colored by typical extra time per trip.
          </p>
        </div>
      </section>
      <MapPageSurface data={data} />
    </div>
  );
}
