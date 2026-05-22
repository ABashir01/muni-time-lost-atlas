export const routeThemes: Record<
  string,
  { color: string; shortLabel: string; label: string }
> = {
  "14": { color: "#d81420", shortLabel: "14", label: "Mission" },
  "38": { color: "#6a43b0", shortLabel: "38", label: "Geary" },
  "49": { color: "#e85c10", shortLabel: "49", label: "Van Ness/Mission" },
};

function normalizeRouteThemeKey(routeId: string) {
  const suffix = routeId.split(":").at(-1) ?? routeId;
  return routeThemes[suffix] ? suffix : routeId;
}

export function getRouteTheme(routeId: string) {
  const themeKey = normalizeRouteThemeKey(routeId);
  return routeThemes[themeKey] ?? {
    color: "#0868d0",
    shortLabel: themeKey,
    label: themeKey,
  };
}
