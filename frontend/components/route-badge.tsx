import type { CSSProperties } from "react";
import { getRouteTheme } from "@/lib/presentation";

export function RouteBadge({
  routeId,
  label,
  large = false,
  colorOverride,
}: {
  routeId: string;
  label: string;
  large?: boolean;
  colorOverride?: string;
}) {
  const theme = getRouteTheme(routeId);

  return (
    <span
      className={`route-badge${large ? " large" : ""}`}
      style={{ background: colorOverride ?? theme.color } as CSSProperties}
    >
      {label}
    </span>
  );
}
