import { CompareRouteBoard } from "@/components/compare-route-board";
import { CompareEntryBand } from "@/components/compare-entry-band";
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
      <h1 className="sr-only">Compare routes or corridors</h1>
      <CompareEntryBand
        actionLabel="Update compare"
        className="compare-page-band"
        description="Pick two to four published routes to compare trip loss, waiting, and slow travel."
        optionalPlaceholderLabel="Add route"
        placeholderLabel="Select a route..."
        routes={data.availableRoutes}
        selectedIds={data.selectedIds}
        slotCount={4}
        submitPath="/compare"
        title="Compare routes or corridors."
      />

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
