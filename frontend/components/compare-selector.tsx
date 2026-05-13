"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { RouteSummary } from "@/lib/types";

export function CompareSelector({
  routes,
  selectedIds,
  slotCount = 2,
  placeholderLabel,
}: {
  routes: RouteSummary[];
  selectedIds: string[];
  slotCount?: number;
  placeholderLabel?: string;
}) {
  const router = useRouter();
  const routeOptions = useMemo(
    () =>
      routes.map((route) => ({
        label: `${route.route_short_name} ${route.route_name}`,
        value: route.route_id,
      })),
    [routes],
  );
  const normalizedSlotCount = Math.max(2, Math.min(slotCount, 4));
  const initialSelections = Array.from({ length: normalizedSlotCount }, (_, index) => selectedIds[index] ?? "");
  const [selections, setSelections] = useState(initialSelections);
  const activeIds = selections.filter(Boolean);
  const uniqueIds = Array.from(new Set(activeIds));
  const canSubmit = uniqueIds.length >= 2;
  const isOptionTaken = (routeId: string, currentIndex: number) =>
    selections.some((selectedId, index) => index !== currentIndex && selectedId === routeId);

  return (
    <div className="compare-controls">
      {selections.map((selection, index) => (
        <div className="compare-slot" key={`compare-slot-${index}`}>
          <select
            aria-label={`Select route ${index + 1}`}
            onChange={(event) =>
              setSelections((currentSelections) =>
                currentSelections.map((currentSelection, currentIndex) =>
                  currentIndex === index ? event.target.value : currentSelection,
                ),
              )
            }
            value={selection}
          >
            {placeholderLabel ? (
              <option value="">
                {index < 2 ? placeholderLabel : "Optional route"}
              </option>
            ) : null}
            {routeOptions.map((route) => (
              <option
                disabled={isOptionTaken(route.value, index)}
                key={route.value}
                value={route.value}
              >
                {route.label}
              </option>
            ))}
          </select>
          {index < selections.length - 1 ? <span className="compare-vs">VS</span> : null}
        </div>
      ))}
      <button
        disabled={!canSubmit}
        onClick={() => router.push(`/compare?ids=${uniqueIds.join(",")}`)}
        type="button"
      >
        Compare
      </button>
    </div>
  );
}
