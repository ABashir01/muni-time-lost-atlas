"use client";

import { CompareSelector } from "@/components/compare-selector";
import type { RouteSummary } from "@/lib/types";

export function CompareEntryBand({
  actionLabel = "Compare",
  className,
  description,
  id,
  optionalPlaceholderLabel,
  placeholderLabel,
  routes,
  selectedIds,
  slotCount = 2,
  submitPath = "/compare",
  title,
}: {
  actionLabel?: string;
  className?: string;
  description: string;
  id?: string;
  optionalPlaceholderLabel?: string;
  placeholderLabel: string;
  routes: RouteSummary[];
  selectedIds: string[];
  slotCount?: number;
  submitPath?: string;
  title: string;
}) {
  return (
    <section
      className={className ? `compare-entry-band ${className}` : "compare-entry-band"}
      id={id}
    >
      <div className="compare-entry-band-copy">
        <h2>{title}</h2>
        <p>{description}</p>
      </div>

      <CompareSelector
        actionLabel={actionLabel}
        className="compare-entry-band-controls"
        optionalPlaceholderLabel={optionalPlaceholderLabel}
        placeholderLabel={placeholderLabel}
        routes={routes}
        selectedIds={selectedIds}
        slotCount={slotCount}
        submitPath={submitPath}
      />
    </section>
  );
}
