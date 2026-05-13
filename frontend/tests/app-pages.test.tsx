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
    expect(html).toContain("Worst published stop wait");
    expect(html).toContain("Worst time window");
  });

  it("renders a fallback route detail page when dedicated segment fixtures do not exist", async () => {
    const page = await RouteDetailPage({ params: Promise.resolve({ routeId: "49" }) });
    const html = renderToStaticMarkup(page);

    expect(html).toContain("Dedicated stop-wait hotspot data is currently published only for route 14 outbound.");
    expect(html).toContain("A dedicated adjacent-stop segment payload has only been published for route 14");
  });

  it("renders compare, map, and methodology pages from fixture-backed data", async () => {
    const comparePage = await ComparePage({
      searchParams: Promise.resolve({ ids: "14,49" }),
    });
    const compareHtml = renderToStaticMarkup(comparePage);
    const mapHtml = renderToStaticMarkup(<MapPage />);
    const methodologyHtml = renderToStaticMarkup(<MethodologyPage />);

    expect(compareHtml).toContain("Put the routes next to each other.");
    expect(compareHtml).toContain("The static compare view accepts up to four route slots");
    expect(compareHtml).toContain("Worst selected route");
    expect(mapHtml).toContain("The citywide evidence surface.");
    expect(mapHtml).toContain("Highest published loss");
    expect(mapHtml).toContain("Transit-only lane overlay");
    expect(methodologyHtml).toContain("Typical trip: +X.X min is the public promise.");
    expect(methodologyHtml).toContain("Plain-English contract");
    expect(methodologyHtml).toContain("Waiting loss");
  });
});
