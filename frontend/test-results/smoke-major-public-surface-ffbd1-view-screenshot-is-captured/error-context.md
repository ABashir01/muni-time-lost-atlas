# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: smoke.spec.ts >> major public surfaces render and a desktop review screenshot is captured
- Location: e2e\smoke.spec.ts:5:5

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('heading', { name: /Where Muni riders lose/i })
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByRole('heading', { name: /Where Muni riders lose/i })

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - generic [ref=e2]:
    - banner [ref=e3]:
      - link "Muni Muni Lost Time AtlasWhere riders lose the most time" [ref=e4] [cursor=pointer]:
        - /url: /
        - generic [ref=e5]: Muni
        - generic [ref=e6]:
          - strong [ref=e7]: Muni Lost Time Atlas
          - text: Where riders lose the most time
      - navigation "Primary" [ref=e8]:
        - link "Explore the map" [ref=e9] [cursor=pointer]:
          - /url: /map
        - link "Rankings" [ref=e10] [cursor=pointer]:
          - /url: /
        - link "Compare" [ref=e11] [cursor=pointer]:
          - /url: /compare?ids=14,49
        - link "Data and methods" [ref=e12] [cursor=pointer]:
          - /url: /methodology
    - main [ref=e13]:
      - generic [ref=e14]:
        - generic [ref=e15]:
          - link "Muni Lost Time Atlas" [ref=e16] [cursor=pointer]:
            - /url: /
            - text: MuniMuni Lost Time Atlas
          - navigation "Homepage" [ref=e17]:
            - link "Explore the Map" [ref=e18] [cursor=pointer]:
              - /url: /map
            - link "Rankings" [ref=e19] [cursor=pointer]:
              - /url: /#rankings
            - link "Compare" [ref=e20] [cursor=pointer]:
              - /url: /#compare
            - link "Data & Methods" [ref=e21] [cursor=pointer]:
              - /url: /methodology
        - generic [ref=e22]:
          - generic [ref=e23]:
            - generic [ref=e24]:
              - heading "Where MuniRiders LoseTheMost Time" [level=1] [ref=e25]:
                - text: Where MuniRiders Lose
                - generic [ref=e26]:
                  - text: The
                  - strong [ref=e27]: Most Time
              - paragraph [ref=e29]: Live and historical data on delays, congestion, and crowding across San Francisco.
            - generic [ref=e30]:
              - generic "Published time windows" [ref=e31]:
                - generic [ref=e32]: Now
                - generic [ref=e33]: Today
                - generic [ref=e34]: This week
                - generic [ref=e35]: This month
              - paragraph [ref=e36]: Updates every 60 seconds
            - generic [ref=e37]:
              - text: Worst Routes Right Now
              - link "See all rankings" [ref=e38] [cursor=pointer]:
                - /url: /map
          - generic [ref=e40]:
            - img "Extra time per trip" [ref=e41]:
              - generic [ref=e69]: "5"
              - generic [ref=e72]: "38"
              - generic [ref=e75]: T
              - generic [ref=e78]: "22"
              - generic [ref=e81]: "N"
              - generic [ref=e89]: "14"
              - generic [ref=e97]: "49"
              - generic [ref=e98]: Richmond District
              - generic [ref=e99]: Golden Gate Park
              - generic [ref=e100]: Haight Ashbury
              - generic [ref=e101]: Marina
              - generic [ref=e102]: Fisherman's Wharf
              - generic [ref=e103]: Mission District
              - generic [ref=e104]: Soma
              - generic [ref=e105]: Bayview
              - generic [ref=e106]: Sunset District
              - generic [ref=e107]: Excelsior
            - generic [ref=e108]:
              - heading "Extra time per trip" [level=3] [ref=e109]
              - paragraph [ref=e110]: vs. ideal trip
              - list [ref=e111]:
                - listitem [ref=e112]: +10 min or more
                - listitem [ref=e113]: +5 to +10 min
                - listitem [ref=e114]: +2 to +5 min
                - listitem [ref=e115]: +0 to +2 min
                - listitem [ref=e116]: On time / better
                - listitem [ref=e117]: Live vehicle
            - generic [ref=e118]: Published route surface
            - generic [ref=e119]: +−↗
            - link "Explore the map" [ref=e121] [cursor=pointer]:
              - /url: /map
        - generic [ref=e122]:
          - generic [ref=e123]:
            - article [ref=e124]:
              - generic [ref=e125]:
                - text: "114"
                - paragraph [ref=e127]: Mission
              - generic [ref=e128]:
                - generic [ref=e129]:
                  - strong [ref=e130]: "+2.3"
                  - text: min
                - paragraph [ref=e131]: extra time per trip
              - generic [ref=e132]:
                - paragraph [ref=e133]:
                  - text: Worst on
                  - strong [ref=e134]: 09:00-09:59
                - paragraph [ref=e135]:
                  - text: Most loss
                  - strong [ref=e136]: 16th St Mission -> 24th St Mission
            - article [ref=e137]:
              - generic [ref=e138]:
                - text: "249"
                - paragraph [ref=e140]: Van Ness/Mission
              - generic [ref=e141]:
                - generic [ref=e142]:
                  - strong [ref=e143]: "+1.0"
                  - text: min
                - paragraph [ref=e144]: extra time per trip
              - generic [ref=e145]:
                - paragraph [ref=e146]:
                  - text: Worst on
                  - strong [ref=e147]: 07:00-07:59
                - paragraph [ref=e148]:
                  - text: Most loss
                  - strong [ref=e149]: Civic Center -> North Point Van Ness
            - article [ref=e150]:
              - generic [ref=e151]:
                - text: 3?
                - paragraph [ref=e153]: Published route pending
              - generic [ref=e154]:
                - generic [ref=e155]:
                  - strong [ref=e156]: —
                  - text: min
                - paragraph [ref=e157]: third ranking slot reserved
              - generic [ref=e158]:
                - paragraph [ref=e159]:
                  - text: Status
                  - strong [ref=e160]: Awaiting a third ranked fixture route
                - paragraph [ref=e161]:
                  - text: Why
                  - strong [ref=e162]: Triptych preserved for the locked homepage layout
          - complementary [ref=e163]:
            - heading "What Makes You Lose Time?" [level=2] [ref=e165]
            - generic [ref=e166]:
              - article [ref=e167]:
                - generic [ref=e168]: ○
                - generic [ref=e169]:
                  - heading "Waiting" [level=3] [ref=e170]
                  - paragraph [ref=e171]: Longer or more irregular headways push effective wait above the scheduled baseline.
              - article [ref=e172]:
                - generic [ref=e173]: ═
                - generic [ref=e174]:
                  - heading "Slow travel" [level=3] [ref=e175]
                  - paragraph [ref=e176]: Traffic, signals, and dwell pressure extend the in-vehicle part of the trip.
              - article [ref=e177]:
                - generic [ref=e178]: ≡
                - generic [ref=e179]:
                  - heading "Bunching" [level=3] [ref=e180]
                  - paragraph [ref=e181]: Vehicles clump together and leave gaps behind, amplifying rider delay even when service is present.
            - link "Learn more about lost time" [ref=e182] [cursor=pointer]:
              - /url: /methodology
        - generic [ref=e183]:
          - generic [ref=e184]:
            - heading "Compare Routes Or Corridors" [level=2] [ref=e185]
            - paragraph [ref=e186]: See how routes stack up or compare parts of the same route.
          - generic [ref=e187]:
            - combobox "Select first route" [ref=e188]:
              - option "Select a route..." [selected]
              - option "14 Mission"
              - option "49 Van Ness/Mission"
            - text: VS
            - combobox "Select second route" [ref=e189]:
              - option "Select a route..." [selected]
              - option "14 Mission"
              - option "49 Van Ness/Mission"
            - button "Compare" [disabled] [ref=e190]
    - contentinfo [ref=e191]: Built for riders. Backed by documented fixture payloads for review.Typical trip = waiting loss + in-vehicle loss on a full one-way trip.Static bundle now, live API integration later.
  - alert [ref=e192]
```

# Test source

```ts
  1  | import { mkdirSync } from "node:fs";
  2  | import path from "node:path";
  3  | import { expect, test } from "@playwright/test";
  4  | 
  5  | test("major public surfaces render and a desktop review screenshot is captured", async ({
  6  |   page,
  7  | }) => {
  8  |   const screenshotDir = path.join(process.cwd(), "..", "artifacts", "frontend");
  9  |   mkdirSync(screenshotDir, { recursive: true });
  10 | 
  11 |   await page.setViewportSize({ width: 1440, height: 900 });
  12 |   await page.goto("/");
> 13 |   await expect(page.getByRole("heading", { name: /Where Muni riders lose/i })).toBeVisible();
     |                                                                                ^ Error: expect(locator).toBeVisible() failed
  14 |   await page.waitForTimeout(500);
  15 |   await page.screenshot({ path: path.join(screenshotDir, "b5-homepage-desktop.png") });
  16 | 
  17 |   await page.goto("/routes/14");
  18 |   await expect(page.getByRole("heading", { name: /Mission/i })).toBeVisible();
  19 | 
  20 |   await page.goto("/compare?ids=14,49");
  21 |   await expect(page.getByRole("heading", { name: /Put the routes next to each other/i })).toBeVisible();
  22 | 
  23 |   await page.goto("/map");
  24 |   await expect(page.getByRole("heading", { name: /The citywide evidence surface/i })).toBeVisible();
  25 | 
  26 |   await page.setViewportSize({ width: 390, height: 844 });
  27 |   await page.goto("/");
  28 |   await expect(page.getByText(/Updates every 60 seconds/i)).toBeVisible();
  29 | 
  30 |   await page.goto("/methodology");
  31 |   await expect(page.getByRole("heading", { name: /Typical trip: \+X.X min is the public promise/i })).toBeVisible();
  32 | });
  33 | 
```