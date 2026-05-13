import Link from "next/link";
import { districtLabels, projectLineCollection } from "@/lib/geo";
import { getRouteTheme } from "@/lib/presentation";
import type { FeatureLine } from "@/lib/types";

const legendItems = [
  { color: "#e31e24", label: "+10 min or more" },
  { color: "#f47c20", label: "+5 to +10 min" },
  { color: "#efb100", label: "+2 to +5 min" },
  { color: "#1f66d1", label: "+0 to +2 min" },
  { color: "#1e9c52", label: "On time / better" },
  { color: "#111111", label: "Live vehicle" },
];

const editorialContextLines = [
  {
    color: "#1f66d1",
    width: 4,
    path:
      "M 84 145 L 190 145 L 270 120 L 402 120 L 402 240 L 540 240 L 640 215 L 760 208 L 842 168",
  },
  {
    color: "#efb100",
    width: 3.5,
    path:
      "M 530 95 L 810 95 L 860 132 L 860 228 L 780 282 L 780 370 L 720 422 L 720 520",
  },
  {
    color: "#7a4bc2",
    width: 3.5,
    path: "M 118 348 L 346 348 L 430 338 L 502 338 L 502 456 L 566 512",
  },
  {
    color: "#1e9c52",
    width: 3.5,
    path: "M 244 350 L 244 458 L 386 458 L 454 515",
  },
  {
    color: "#20a8d8",
    width: 3.5,
    path: "M 744 276 L 744 480 L 806 542",
  },
  {
    color: "#efb100",
    width: 3.5,
    path: "M 218 492 L 318 492 L 386 544 L 520 544 L 650 544 L 790 544",
  },
];

const editorialContextStops = [
  [84, 145],
  [190, 145],
  [402, 120],
  [402, 240],
  [540, 240],
  [760, 208],
  [118, 348],
  [346, 348],
  [502, 338],
  [244, 458],
  [744, 480],
];

const editorialContextMarkers = [
  { x: 362, y: 120, label: "5", color: "#1f66d1" },
  { x: 258, y: 348, label: "38", color: "#7a4bc2" },
  { x: 410, y: 482, label: "T", color: "#1f66d1" },
  { x: 794, y: 346, label: "22", color: "#20a8d8" },
  { x: 612, y: 150, label: "N", color: "#efb100" },
];

const editorialDistrictLabels = [
  { text: "Richmond District", x: 88, y: 182 },
  { text: "Golden Gate Park", x: 136, y: 290 },
  { text: "Haight Ashbury", x: 346, y: 338 },
  { text: "Marina", x: 438, y: 152 },
  { text: "Fisherman's Wharf", x: 608, y: 122 },
  { text: "Mission District", x: 550, y: 384 },
  { text: "Soma", x: 640, y: 252 },
  { text: "Bayview", x: 646, y: 478 },
  { text: "Sunset District", x: 78, y: 420 },
  { text: "Excelsior", x: 230, y: 548 },
];

const cityLandPath =
  "M 302 18 L 404 44 L 524 42 L 652 54 L 780 78 L 862 132 L 876 198 L 868 302 L 828 420 L 790 544 L 730 606 L 524 618 L 470 604 L 450 560 L 396 546 L 326 542 L 280 516 L 214 478 L 166 416 L 136 350 L 118 286 L 108 216 L 126 160 L 168 122 L 214 104 L 248 62 Z";

const coastlinePath =
  "M 292 28 L 402 48 L 522 42 L 650 54 L 782 78 L 856 124 L 874 198 L 864 300 L 826 420 L 784 544 L 728 606";

const parkPaths = [
  "M 228 260 L 404 258 L 416 326 L 212 326 Z",
  "M 742 472 L 846 472 L 858 566 L 760 580 Z",
];

const majorStreetPaths = [
  "M 152 170 L 858 170",
  "M 162 226 L 850 226",
  "M 170 286 L 842 286",
  "M 168 346 L 832 346",
  "M 184 408 L 820 408",
  "M 204 470 L 802 470",
  "M 248 96 L 248 540",
  "M 326 80 L 326 546",
  "M 406 52 L 406 578",
  "M 486 48 L 486 604",
  "M 564 44 L 564 616",
  "M 642 54 L 642 610",
  "M 720 66 L 720 594",
  "M 792 96 L 792 558",
];

const fineStreetPaths = [
  "M 194 140 L 842 140",
  "M 186 196 L 848 196",
  "M 172 254 L 844 254",
  "M 170 314 L 836 314",
  "M 178 376 L 826 376",
  "M 196 438 L 810 438",
  "M 220 502 L 790 502",
  "M 286 88 L 286 544",
  "M 364 58 L 364 562",
  "M 444 48 L 444 590",
  "M 522 42 L 522 614",
  "M 602 48 L 602 616",
  "M 680 62 L 680 602",
  "M 758 82 L 758 572",
];

export function MapSchematic({
  features,
  overlayFeatures = [],
  focusRouteId,
  showLegend = false,
  showDistrictLabels = false,
  title,
  subtitle,
  ctaHref,
  ctaLabel,
  editorialContext = false,
}: {
  features: FeatureLine[];
  overlayFeatures?: FeatureLine[];
  focusRouteId?: string;
  showLegend?: boolean;
  showDistrictLabels?: boolean;
  title: string;
  subtitle: string;
  ctaHref?: string;
  ctaLabel?: string;
  editorialContext?: boolean;
}) {
  const allFeatures = [...features, ...overlayFeatures];
  const projected = projectLineCollection(allFeatures, 920, 620, 56);
  const routeCount = features.length;
  const routeStrokeWidth = editorialContext ? 5.5 : 8;
  const routeSecondaryWidth = editorialContext ? 4 : 6;
  const routeNodeRadius = editorialContext ? 4.25 : 5;
  const routeNodeSecondaryRadius = editorialContext ? 3.5 : 4;
  const routeLabelRadius = editorialContext ? 17 : 20;
  const routeLabelStroke = editorialContext ? 2.2 : 2.5;

  return (
    <div className="schematic">
      <svg aria-label={title} role="img" viewBox="0 0 920 620">
        <defs>
          <clipPath id="city-land-clip">
            <path d={cityLandPath} />
          </clipPath>
        </defs>
        <rect fill="#d6e7fb" height="620" width="920" />
        <path d={cityLandPath} fill="#f5f2eb" opacity="0.98" />
        <path d={coastlinePath} fill="none" stroke="rgba(12, 44, 88, 0.32)" strokeWidth="2.5" />
        {parkPaths.map((path) => (
          <path d={path} fill="#dbe8ce" key={path} opacity="0.95" />
        ))}
        <g clipPath="url(#city-land-clip)">
          {fineStreetPaths.map((path) => (
            <path
              d={path}
              fill="none"
              key={path}
              stroke="rgba(255, 255, 255, 0.58)"
              strokeWidth="1"
            />
          ))}
          {majorStreetPaths.map((path) => (
            <path
              d={path}
              fill="none"
              key={path}
              stroke="rgba(255, 255, 255, 0.9)"
              strokeWidth="2.2"
            />
          ))}
        </g>
        {editorialContext ? (
          <>
            <rect fill="rgba(255,255,255,0.26)" height="118" width="220" x="126" y="212" />
            <rect fill="rgba(255,255,255,0.22)" height="116" width="214" x="642" y="66" />
            {editorialContextLines.map((line) => (
              <path
                className="route-line editorial-context-line"
                d={line.path}
                key={line.path}
                stroke={line.color}
                strokeWidth={line.width}
              />
            ))}
            {editorialContextStops.map(([x, y], index) => (
              <circle className="route-node context-stop" cx={x} cy={y} key={`context-stop-${index}`} r="4.5" />
            ))}
            {editorialContextMarkers.map((marker) => (
              <g key={marker.label} transform={`translate(${marker.x}, ${marker.y})`}>
                <circle fill={marker.color} r="17" stroke="#111" strokeWidth="2" />
                <text
                  className="route-label context-marker"
                  dominantBaseline="central"
                  fill="#fff"
                  textAnchor="middle"
                >
                  {marker.label}
                </text>
              </g>
            ))}
          </>
        ) : null}
        {projected.slice(routeCount).map((feature, index) => (
          <path
            className="route-line secondary"
            d={feature.path}
            key={`overlay-${index}`}
            stroke="#1f66d1"
            strokeDasharray="14 12"
            strokeWidth={6}
          />
        ))}
        {projected.slice(0, routeCount).map((feature) => {
          const theme = getRouteTheme(feature.routeId);
          const emphasized = !focusRouteId || focusRouteId === feature.routeId;

          return (
            <g key={feature.routeId}>
              <path
                className={`route-line${emphasized ? "" : " secondary"}`}
                d={feature.path}
                stroke={theme.color}
                strokeWidth={emphasized ? routeStrokeWidth : routeSecondaryWidth}
              />
              {feature.nodes.map((node, index) => (
                <circle
                  className="route-node"
                  cx={node.x}
                  cy={node.y}
                  key={`${feature.routeId}-${index}`}
                  r={emphasized ? routeNodeRadius : routeNodeSecondaryRadius}
                />
              ))}
              <g transform={`translate(${feature.label.x}, ${feature.label.y})`}>
                <circle
                  fill={theme.color}
                  r={routeLabelRadius}
                  stroke="#111"
                  strokeWidth={routeLabelStroke}
                />
                <text
                  className="route-label"
                  dominantBaseline="central"
                  fill="#fff"
                  textAnchor="middle"
                >
                  {theme.shortLabel}
                </text>
              </g>
            </g>
          );
        })}
        {showDistrictLabels
          ? (editorialContext ? editorialDistrictLabels : districtLabels).map((label) => (
              <text className="district-label" key={label.text} x={label.x} y={label.y}>
                {label.text}
              </text>
            ))
          : null}
      </svg>
      {showLegend ? (
        <div className="map-legend">
          <h3>{title}</h3>
          <p>{subtitle}</p>
          <ul>
            {legendItems.map((item) => (
              <li key={item.label}>
                <span className="legend-swatch" style={{ background: item.color }} />
                <span>{item.label}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="map-schematic-chip">Published route surface</div>
      <div aria-hidden="true" className="map-ui-controls">
        <span>+</span>
        <span>−</span>
        <span>↗</span>
      </div>
      {ctaHref && ctaLabel ? (
        <div className="schematic-cta">
          <Link href={ctaHref}>{ctaLabel}</Link>
        </div>
      ) : null}
    </div>
  );
}
