import { renderToStaticMarkup } from "react-dom/server";
import ComparePage from "@/app/compare/page";
import HomePage from "@/app/page";
import RouteDetailPage from "@/app/routes/[routeId]/page";
import MapPage from "@/app/map/page";
import MethodologyPage from "@/app/methodology/page";

vi.mock("next/navigation", async () => {
  const actual = await vi.importActual<typeof import("next/navigation")>("next/navigation");

  return {
    ...actual,
    useRouter: () => ({
      push: vi.fn(),
    }),
  };
});

describe("public pages", () => {
  it("renders the homepage editorial shell from fixtures", async () => {
    const page = await HomePage({});
    const html = renderToStaticMarkup(page);

    expect(html).toContain("Where Muni");
    expect(html).toContain("Riders Lose");
    expect(html).toContain("Most Time");
    expect(html).toContain("Mission");
    expect(html).toContain("Van Ness/Mission");
    expect(html).toContain("extra time per trip");
  });

  it("renders the route detail page with the published corridor language", async () => {
    const page = await RouteDetailPage({ params: Promise.resolve({ routeId: "14" }) });
    const html = renderToStaticMarkup(page);

    expect(html).toContain("Route detail");
    expect(html).toContain("16th St Mission -&gt; 24th St Mission");
    expect(html).toContain("Worst time window");
  });

  it("renders compare, map, and methodology pages from fixture-backed data", async () => {
    const comparePage = await ComparePage({
      searchParams: Promise.resolve({ ids: "14,49" }),
    });
    const compareHtml = renderToStaticMarkup(comparePage);
    const mapHtml = renderToStaticMarkup(<MapPage />);
    const methodologyHtml = renderToStaticMarkup(<MethodologyPage />);

    expect(compareHtml).toContain("Put the routes next to each other.");
    expect(compareHtml).toContain("Typical trip:");
    expect(mapHtml).toContain("The citywide evidence surface.");
    expect(mapHtml).toContain("Transit-only lane overlay");
    expect(methodologyHtml).toContain("Typical trip: +X.X min is the public promise.");
    expect(methodologyHtml).toContain("Waiting loss");
  });
});
