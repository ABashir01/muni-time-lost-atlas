import type { CSSProperties } from "react";
import { getRouteTheme } from "@/lib/presentation";

export function RouteBadge({
  routeId,
  label,
  large = false,
}: {
  routeId: string;
  label: string;
  large?: boolean;
}) {
  const theme = getRouteTheme(routeId);

  return (
    <span
      className={`route-badge${large ? " large" : ""}`}
      style={{ background: theme.color } as CSSProperties}
    >
      {label}
    </span>
  );
}
