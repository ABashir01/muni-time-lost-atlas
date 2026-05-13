import type { RouteSummary } from "@/lib/types";

export function formatMinutes(value: number) {
  return `+${value.toFixed(1)} min`;
}

export function formatSignedMinutes(value: number) {
  return `${value >= 0 ? "+" : "-"}${Math.abs(value).toFixed(1)} min`;
}

export function median(values: number[]) {
  const sorted = [...values].sort((left, right) => left - right);
  const middle = Math.floor(sorted.length / 2);

  if (sorted.length === 0) {
    return 0;
  }

  if (sorted.length % 2 === 0) {
    return (sorted[middle - 1] + sorted[middle]) / 2;
  }

  return sorted[middle];
}

export function routeLossShares(route: RouteSummary) {
  const total = route.typical_trip_loss_minutes || 1;
  const waiting = route.waiting_loss_minutes / total;
  const travel = route.in_vehicle_loss_minutes / total;

  return {
    waiting: Math.max(0, Math.min(waiting, 1)),
    travel: Math.max(0, Math.min(travel, 1)),
  };
}

export function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function routeDominantProblem(route: RouteSummary) {
  return route.waiting_loss_minutes >= route.in_vehicle_loss_minutes
    ? "waiting loss"
    : "in-vehicle loss";
}

export function formatTimestamp(value: string) {
  return new Date(value).toLocaleString("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
