"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { RouteSummary } from "@/lib/types";

export function CompareSelector({
  routes,
  selectedIds,
  placeholderLabel,
}: {
  routes: RouteSummary[];
  selectedIds: string[];
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

  const [left, setLeft] = useState(selectedIds[0] ?? "");
  const [right, setRight] = useState(selectedIds[1] ?? "");

  const canSubmit = left && right && left !== right;

  return (
    <div className="compare-controls">
      <select
        aria-label="Select first route"
        onChange={(event) => setLeft(event.target.value)}
        value={left}
      >
        {placeholderLabel ? <option value="">{placeholderLabel}</option> : null}
        {routeOptions.map((route) => (
          <option key={route.value} value={route.value}>
            {route.label}
          </option>
        ))}
      </select>
      <span className="compare-vs">VS</span>
      <select
        aria-label="Select second route"
        onChange={(event) => setRight(event.target.value)}
        value={right}
      >
        {placeholderLabel ? <option value="">{placeholderLabel}</option> : null}
        {routeOptions.map((route) => (
          <option key={route.value} value={route.value}>
            {route.label}
          </option>
        ))}
      </select>
      <button
        disabled={!canSubmit}
        onClick={() => router.push(`/compare?ids=${left},${right}`)}
        type="button"
      >
        Compare
      </button>
    </div>
  );
}
