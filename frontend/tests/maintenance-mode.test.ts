import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { getMaintenanceState } from "@/lib/maintenance";

describe("maintenance mode detection", () => {
  const originalMaintenanceMode = process.env.MAINTENANCE_MODE;
  const originalMaintenanceFlagPath = process.env.MAINTENANCE_FLAG_PATH;

  afterEach(() => {
    if (originalMaintenanceMode === undefined) {
      delete process.env.MAINTENANCE_MODE;
    } else {
      process.env.MAINTENANCE_MODE = originalMaintenanceMode;
    }

    if (originalMaintenanceFlagPath === undefined) {
      delete process.env.MAINTENANCE_FLAG_PATH;
    } else {
      process.env.MAINTENANCE_FLAG_PATH = originalMaintenanceFlagPath;
    }
  });

  it("enables maintenance mode when the env flag is set", () => {
    process.env.MAINTENANCE_MODE = "true";
    delete process.env.MAINTENANCE_FLAG_PATH;

    expect(getMaintenanceState()).toEqual({ enabled: true, reason: "env" });
  });

  it("enables maintenance mode when the shared flag file exists", () => {
    const tempDir = mkdtempSync(path.join(tmpdir(), "muni-maintenance-"));
    const flagPath = path.join(tempDir, "maintenance.flag");
    process.env.MAINTENANCE_MODE = "false";
    process.env.MAINTENANCE_FLAG_PATH = flagPath;
    writeFileSync(flagPath, "maintenance\n", "utf8");

    expect(getMaintenanceState()).toEqual({ enabled: true, reason: "flag" });

    rmSync(tempDir, { force: true, recursive: true });
  });
});
