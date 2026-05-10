import { CompareRouteBoard } from "@/components/compare-route-board";
import { CompareSelector } from "@/components/compare-selector";
import { getComparePageData } from "@/lib/site-data";

export default async function ComparePage({
  searchParams,
}: {
  searchParams?:
    | Promise<{ ids?: string | string[] }>
    | { ids?: string | string[] };
}) {
  const resolvedSearchParams: { ids?: string | string[] } | undefined =
    searchParams && "then" in searchParams ? await searchParams : searchParams;
  const data = getComparePageData(resolvedSearchParams?.ids);

  return (
    <div className="page-stack">
      <section className="section-shell compare-hero">
        <div>
          <p className="eyebrow">Compare routes</p>
          <h1 className="page-headline">Put the routes next to each other.</h1>
          <p className="page-dek">
            Which route loses more time, whether it is mostly waiting or travel,
            and which published window or segment stands out.
          </p>
        </div>
        <CompareSelector routes={data.availableRoutes} selectedIds={data.selectedIds} />
      </section>

      <CompareRouteBoard
        routes={data.selectedRoutes}
        systemMedianTypicalTripLoss={data.systemMedianTypicalTripLoss}
      />
    </div>
  );
}
