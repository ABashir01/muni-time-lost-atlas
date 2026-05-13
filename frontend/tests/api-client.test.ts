import { getRankings } from "@/lib/api";

function jsonResponse(payload: unknown, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(payload), {
      headers: {
        "Content-Type": "application/json",
      },
      status,
    }),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("frontend API validation", () => {
  it("rejects invalid rankings payloads at the integration boundary", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        jsonResponse({
          metric: "typical_trip_loss_minutes",
          mode: "routes",
          routes: [
            {
              route_id: "14",
              window: "all_day",
            },
          ],
          window: "all_day",
        }),
      ),
    );

    await expect(getRankings()).rejects.toThrow("/rankings.routes[0].route_name must be a string");
  });
});
