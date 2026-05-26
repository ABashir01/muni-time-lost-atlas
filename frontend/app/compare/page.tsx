import { CompareRouteBoard } from "@/components/compare-route-board";
import { CompareSelector } from "@/components/compare-selector";
import { getComparePageData } from "@/lib/site-data";

export const dynamic = "force-dynamic";

export default async function ComparePage({
  searchParams,
}: {
  searchParams?:
    | Promise<{ ids?: string | string[] }>
    | { ids?: string | string[] };
}) {
  const resolvedSearchParams: { ids?: string | string[] } | undefined =
    searchParams && "then" in searchParams ? await searchParams : searchParams;
  const data = await getComparePageData(resolvedSearchParams?.ids);

  return (
    <div className="page-stack editorial-page compare-page">
      <section className="compare-toolbar-shell">
        <div className="compare-toolbar-copy">
          <h1 className="sr-only">Compare routes or corridors</h1>
          <p className="compare-toolbar-label">Compare routes or corridors.</p>
          <p>Pick two to four published routes to compare trip loss, waiting, and slow travel.</p>
        </div>
        <CompareSelector
          className="compare-page-controls"
          optionalPlaceholderLabel="Add route"
          placeholderLabel="Route"
          routes={data.availableRoutes}
          selectedIds={data.selectedIds}
          slotCount={4}
        />
      </section>

      <CompareRouteBoard
        compareLimitations={data.compareLimitations}
        leadingRoute={data.leadingRoute}
        notices={data.notices}
        routes={data.selectedRoutes}
        systemMedianTypicalTripLoss={data.systemMedianTypicalTripLoss}
      />
    </div>
  );
}
