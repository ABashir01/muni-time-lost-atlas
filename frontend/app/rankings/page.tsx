import { RankingsPageSurface } from "@/components/rankings-page-surface";
import { getRankingsPageData } from "@/lib/site-data";

export const dynamic = "force-dynamic";

export default async function RankingsPage() {
  const data = await getRankingsPageData();

  return (
    <div className="page-stack editorial-page rankings-page">
      <section className="rankings-page-intro">
        <h1 className="sr-only">Published route rankings</h1>
        <div className="rankings-page-intro-copy">
          <p>
            <strong>Published route rankings.</strong> Routes are ordered by typical extra
            time per trip in the current published snapshot.
          </p>
          <p>Click any route row to open its route detail.</p>
        </div>
      </section>

      <RankingsPageSurface data={data} />
    </div>
  );
}
