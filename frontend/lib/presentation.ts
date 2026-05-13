export const routeThemes: Record<
  string,
  { color: string; shortLabel: string; label: string }
> = {
  "14": { color: "#d81420", shortLabel: "14", label: "Mission" },
  "38": { color: "#6a43b0", shortLabel: "38", label: "Geary" },
  "49": { color: "#e85c10", shortLabel: "49", label: "Van Ness/Mission" },
};

export function getRouteTheme(routeId: string) {
  return routeThemes[routeId] ?? {
    color: "#0868d0",
    shortLabel: routeId,
    label: routeId,
  };
}
