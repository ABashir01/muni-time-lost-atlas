"use client";

import { Fragment, startTransition, useEffect, useMemo, useState } from "react";
import Select, { type FilterOptionOption, type StylesConfig } from "react-select";
import { useRouter } from "next/navigation";
import type { RouteSummary } from "@/lib/types";

type RouteOption = {
  aliases: string[];
  label: string;
  value: string;
};

const selectStyles: StylesConfig<RouteOption, false> = {
  container: (base) => ({
    ...base,
    width: "100%",
    minWidth: 0,
  }),
  control: (base, state) => ({
    ...base,
    minHeight: "var(--compare-field-height, 42px)",
    border: `2px solid ${state.isFocused ? "#111" : "var(--rule)"}`,
    borderRadius: 0,
    boxShadow: "none",
    backgroundColor: "#fff",
    cursor: "text",
    minWidth: 0,
  }),
  valueContainer: (base) => ({
    ...base,
    padding: "0 8px 0 10px",
    overflow: "hidden",
  }),
  input: (base) => ({
    ...base,
    margin: 0,
    padding: 0,
    color: "#111",
    font: "inherit",
  }),
  singleValue: (base) => ({
    ...base,
    color: "#111",
    font: "inherit",
    maxWidth: "100%",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  }),
  placeholder: (base) => ({
    ...base,
    color: "#6a6a6a",
    font: "inherit",
    maxWidth: "100%",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  }),
  indicatorsContainer: (base) => ({
    ...base,
    paddingRight: 4,
  }),
  dropdownIndicator: (base, state) => ({
    ...base,
    color: "#111",
    padding: "0 6px",
    transition: "transform 120ms ease",
    transform: state.selectProps.menuIsOpen ? "rotate(180deg)" : "none",
    ":hover": {
      color: "#111",
    },
  }),
  clearIndicator: (base) => ({
    ...base,
    padding: "0 6px",
  }),
  menuPortal: (base) => ({
    ...base,
    zIndex: 3000,
  }),
  menu: (base) => ({
    ...base,
    marginTop: 4,
    border: "2px solid var(--rule)",
    borderRadius: 0,
    boxShadow: "0 12px 28px rgba(0, 0, 0, 0.16)",
    backgroundColor: "#fff",
    overflow: "hidden",
  }),
  menuList: (base) => ({
    ...base,
    maxHeight: 280,
    padding: 0,
  }),
  option: (base, state) => ({
    ...base,
    padding: "10px 12px",
    backgroundColor: state.isFocused ? "#f3f3f3" : "#fff",
    color: state.isSelected ? "var(--blue)" : "#111",
    cursor: "pointer",
    font: "inherit",
  }),
  noOptionsMessage: (base) => ({
    ...base,
    padding: "10px 12px",
    color: "#6a6a6a",
    font: "inherit",
  }),
};

export function CompareSelector({
  routes,
  selectedIds,
  slotCount = 2,
  placeholderLabel,
  optionalPlaceholderLabel,
  className,
  actionLabel = "Compare",
  submitPath = "/compare",
  mobileMenuPlacement = "auto",
}: {
  routes: RouteSummary[];
  selectedIds: string[];
  slotCount?: number;
  placeholderLabel?: string;
  optionalPlaceholderLabel?: string;
  className?: string;
  actionLabel?: string;
  submitPath?: string;
  mobileMenuPlacement?: "auto" | "top" | "bottom";
}) {
  const router = useRouter();
  const normalizedSlotCount = Math.max(2, Math.min(slotCount, 4));
  const routeOptions = useMemo<RouteOption[]>(
    () =>
      routes.map((route) => ({
        aliases: [route.route_id, route.route_short_name, route.route_name].filter(Boolean),
        label: `${route.route_short_name || route.route_id} ${route.route_name}`,
        value: route.route_id,
      })),
    [routes],
  );
  const initialSelections = Array.from(
    { length: normalizedSlotCount },
    (_, index) => selectedIds[index] ?? "",
  );
  const [menuPortalTarget, setMenuPortalTarget] = useState<HTMLElement | null>(null);
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const [selections, setSelections] = useState<string[]>(() => initialSelections);

  const activeIds = selections.filter(Boolean);
  const uniqueIds = Array.from(new Set(activeIds));
  const canSubmit = uniqueIds.length >= 2;

  const slotOptions = useMemo(
    () =>
      selections.map((selection, index) => {
        const takenByOtherSlots = new Set(
          selections.filter((selectedId, selectedIndex) => selectedIndex !== index && selectedId),
        );

        return routeOptions.filter(
          (route) => route.value === selection || !takenByOtherSlots.has(route.value),
        );
      }),
    [routeOptions, selections],
  );

  const selectedOptions = useMemo(
    () =>
      selections.map(
        (selection, index) =>
          slotOptions[index]?.find((route) => route.value === selection) ?? null,
      ),
    [selections, slotOptions],
  );

  const placeholderForSlot = (index: number) =>
    index < 2 ? placeholderLabel ?? "Route" : optionalPlaceholderLabel ?? "Optional route";

  const filterRouteOption = (
    candidate: FilterOptionOption<RouteOption>,
    rawInput: string,
  ) => {
    const normalizedInput = rawInput.trim().toLowerCase();

    if (!normalizedInput) {
      return true;
    }

    const terms = normalizedInput.split(/\s+/).filter(Boolean);
    const searchable = [candidate.label, candidate.data.value, ...candidate.data.aliases]
      .join(" ")
      .toLowerCase();

    return terms.every((term) => searchable.includes(term));
  };

  useEffect(() => {
    setMenuPortalTarget(document.body);
  }, []);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(max-width: 760px)");
    const syncViewport = () => setIsMobileViewport(mediaQuery.matches);

    syncViewport();
    mediaQuery.addEventListener("change", syncViewport);

    return () => {
      mediaQuery.removeEventListener("change", syncViewport);
    };
  }, []);

  useEffect(() => {
    setSelections(initialSelections);
  }, [normalizedSlotCount, routeOptions, selectedIds]);

  const resolvedMenuPlacement =
    isMobileViewport && mobileMenuPlacement !== "auto" ? mobileMenuPlacement : "auto";

  return (
    <div className={className ? `compare-controls ${className}` : "compare-controls"}>
      <div className="compare-selection-group">
        {selections.map((selection, index) => (
          <Fragment key={`compare-slot-${index}`}>
            <div
              className={`compare-slot ${index < 2 ? "compare-slot-primary" : "compare-slot-optional"}`}
            >
              <div className="compare-field">
                <Select<RouteOption, false>
                  classNamePrefix="compare-react-select"
                  components={{ IndicatorSeparator: () => null }}
                  controlShouldRenderValue
                  filterOption={filterRouteOption}
                  inputId={`compare-route-${index + 1}`}
                  instanceId={`compare-route-${index + 1}`}
                  isClearable={index >= 2}
                  menuPlacement={resolvedMenuPlacement}
                  menuPortalTarget={menuPortalTarget ?? undefined}
                  menuPosition={menuPortalTarget ? "fixed" : "absolute"}
                  menuShouldBlockScroll={false}
                  menuShouldScrollIntoView={false}
                  noOptionsMessage={() => "No matching routes"}
                  onChange={(nextOption) => {
                    setSelections((currentSelections) =>
                      currentSelections.map((currentSelection, currentIndex) =>
                        currentIndex === index ? nextOption?.value ?? "" : currentSelection,
                      ),
                    );
                  }}
                  openMenuOnFocus
                  options={slotOptions[index] ?? []}
                  placeholder={placeholderForSlot(index)}
                  styles={selectStyles}
                  tabSelectsValue={false}
                  unstyled
                  value={selectedOptions[index]}
                />
              </div>
            </div>
            {index < selections.length - 1 ? <span className="compare-vs">VS</span> : null}
          </Fragment>
        ))}
      </div>
      <div className="compare-action-group">
        <button
          disabled={!canSubmit}
          onClick={() =>
            startTransition(() => {
              router.push(`${submitPath}?ids=${uniqueIds.join(",")}`);
            })
          }
          type="button"
        >
          {actionLabel}
        </button>
      </div>
    </div>
  );
}
