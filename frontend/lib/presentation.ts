export const routeThemes: Record<
  string,
  { color: string; shortLabel: string; label: string }
> = {
  "14": { color: "#d71920", shortLabel: "14", label: "Mission" },
  "38": { color: "#7a48b7", shortLabel: "38", label: "Geary" },
  "49": { color: "#ff7a00", shortLabel: "49", label: "Van Ness/Mission" },
};

export function getRouteTheme(routeId: string) {
  return routeThemes[routeId] ?? {
    color: "#0f63d8",
    shortLabel: routeId,
    label: routeId,
  };
}
