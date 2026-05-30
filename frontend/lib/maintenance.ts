import { existsSync } from "node:fs";

const TRUE_VALUES = new Set(["1", "true", "yes", "on"]);
const DEFAULT_MAINTENANCE_FLAG_PATH = "/var/run/muni-lta/maintenance.flag";

export type MaintenanceState = {
  enabled: boolean;
  reason: "env" | "flag" | null;
};

function envValueIsTrue(value: string | undefined) {
  return value ? TRUE_VALUES.has(value.trim().toLowerCase()) : false;
}

export function getMaintenanceFlagPath() {
  return process.env.MAINTENANCE_FLAG_PATH?.trim() || DEFAULT_MAINTENANCE_FLAG_PATH;
}

export function getMaintenanceState(): MaintenanceState {
  if (envValueIsTrue(process.env.MAINTENANCE_MODE)) {
    return { enabled: true, reason: "env" };
  }

  const flagPath = getMaintenanceFlagPath();
  if (flagPath && existsSync(flagPath)) {
    return { enabled: true, reason: "flag" };
  }

  return { enabled: false, reason: null };
}
