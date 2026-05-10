import { CompareSelector } from "@/components/compare-selector";
import type { RouteSummary } from "@/lib/types";

export function CompareTeaser({
  routes,
  compact = false,
}: {
  routes: RouteSummary[];
  compact?: boolean;
}) {
  return (
    <div className={compact ? "compare-teaser-compact" : "compare-shell section-shell"}>
      {compact ? null : (
        <div className="section-heading">
          <p className="eyebrow">Compare routes or corridors</p>
          <h2>See which route loses more time and what kind of time loss it is.</h2>
        </div>
      )}
      <CompareSelector routes={routes} selectedIds={["14", "49"]} />
    </div>
  );
}
