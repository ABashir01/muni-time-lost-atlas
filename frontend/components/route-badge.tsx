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
  const normalizedLabel = label.trim();
  const badgeLength = normalizedLabel.length;
  const badgeShapeClass = badgeLength >= 4 ? " wide" : badgeLength === 3 ? " medium" : "";

  return (
    <span
      className={`route-badge${large ? " large" : ""}${badgeShapeClass}`}
      data-label-length={badgeLength}
      style={{ background: colorOverride ?? theme.color } as CSSProperties}
    >
      {normalizedLabel}
    </span>
  );
}
