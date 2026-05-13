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
    <div className="page-stack">
      <section className="section-shell compare-hero">
        <div>
          <p className="eyebrow">Compare routes</p>
          <h1 className="page-headline">Put the routes next to each other.</h1>
          <p className="page-dek">
            Which route loses more time, whether it is mostly waiting or travel,
            and which published window or segment stands out. The live compare
            surface accepts up to four route slots and reads directly from the
            historical/static API contract.
          </p>
        </div>
        <CompareSelector
          placeholderLabel="Select a route..."
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
