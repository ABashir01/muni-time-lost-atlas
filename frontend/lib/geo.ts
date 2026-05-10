import type { FeatureLine } from "@/lib/types";

type ProjectedFeature = {
  routeId: string;
  path: string;
  nodes: Array<{ x: number; y: number }>;
  label: { x: number; y: number };
};

export const districtLabels = [
  { text: "Richmond District", x: 130, y: 140 },
  { text: "Haight", x: 305, y: 300 },
  { text: "Mission", x: 478, y: 350 },
  { text: "Soma", x: 600, y: 250 },
  { text: "Bayview", x: 610, y: 515 },
];

export function projectLineCollection(
  features: FeatureLine[],
  width: number,
  height: number,
  padding: number,
): ProjectedFeature[] {
  if (features.length === 0) {
    return [];
  }

  const points = features.flatMap((feature) => feature.geometry.coordinates);
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  const scaleX = (width - padding * 2) / Math.max(maxX - minX, 0.001);
  const scaleY = (height - padding * 2) / Math.max(maxY - minY, 0.001);

  const projectPoint = ([x, y]: [number, number]) => ({
    x: padding + (x - minX) * scaleX,
    y: height - padding - (y - minY) * scaleY,
  });

  return features.map((feature) => {
    const nodes = feature.geometry.coordinates.map(projectPoint);
    const path = nodes
      .map((node, index) => `${index === 0 ? "M" : "L"} ${node.x.toFixed(2)} ${node.y.toFixed(2)}`)
      .join(" ");
    const labelNode = nodes[Math.floor(nodes.length / 2)] ?? { x: width / 2, y: height / 2 };

    return {
      routeId: feature.properties.route_id,
      path,
      nodes,
      label: labelNode,
    };
  });
}
