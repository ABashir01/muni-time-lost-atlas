export const routeThemes: Record<
  string,
  { color: string; shortLabel: string; label: string }
> = {
  "14": { color: "#e31e24", shortLabel: "14", label: "Mission" },
  "38": { color: "#7a4bc2", shortLabel: "38", label: "Geary" },
  "49": { color: "#f47c20", shortLabel: "49", label: "Van Ness/Mission" },
};

export function getRouteTheme(routeId: string) {
  return routeThemes[routeId] ?? {
    color: "#1f66d1",
    shortLabel: routeId,
    label: routeId,
  };
}
