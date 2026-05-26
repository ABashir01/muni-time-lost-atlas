# B8 Surface Layout Spec

## Purpose
Define the literal desktop composition for the non-homepage pages so they can
inherit the homepage's design sensibility without improvisation.

Primary review breakpoint:
- `1440x900`

## Shared shell rules
All primary B8 pages should use:
1. masthead
2. top intro / title band
3. main evidence area

Shared rules:
- near-full-width layout
- small outer gutters
- strong horizontal bands before vertical stacks
- no narrow article column on desktop

## Rankings page
### Page intent
This is the full public edition of the homepage rankings.

### Top-level structure
1. masthead
2. intro band
3. main ranking field

### Desktop composition
- masthead: `8%`
- intro band: `15%`
- main field: `77%`

Main field split:
- ranking column: `68%`
- context/sidebar column: `32%`

Ranking-column behavior:
- top 3 should still read with strong card/poster energy
- lower routes can collapse into tighter list rows beneath the featured group
- preserve a visual transition from “featured” to “system list,” not a table

Reserve space:
- route title line should allow a future direction subtitle beneath it
- intro band should allow a future shared date-range control without changing
  the whole composition

## Map page
### Page intent
This is the citywide evidence spread, not a generic GIS tool.

### Top-level structure
1. masthead
2. intro band
3. map field

### Desktop composition
- masthead: `8%`
- intro band: `13%`
- map field: `79%`

Map field split:
- map canvas: `72%`
- editorial/sidebar rail: `28%`

Rules:
- map canvas remains dominant
- sidebar carries ranked context, notes, and controls
- avoid floating detached widgets over the map as the primary layout language
- keep a clear zone where a future shared date-range control can be introduced
  near the top of the page

## Route detail page
### Page intent
This is a route dossier or spread.

### Top-level structure
1. masthead
2. route summary band
3. evidence field

### Desktop composition
- masthead: `8%`
- route summary band: `22%`
- evidence field: `70%`

Evidence field preferred structure:
- first row:
  - corridor map panel `62%`
  - interpretation / hotspot panel `38%`
- second row:
  - supporting metric/evidence panels in a clean two- or three-panel rhythm

Rules:
- route badge and route identity must dominate the summary band
- summary metrics should feel poster-like rather than tile-grid generic
- preserve room for a future direction subtitle near the route title
- preserve a plausible top-level slot for a future shared date-range state

## Compare page
### Page intent
This is a secondary aligned surface.

### Desktop composition
- keep the existing basic compare structure
- align masthead, typography, buttons, borders, and colors to the shared system
- do not require a new hero concept equal to rankings/map/detail

Rules:
- compare selector and button should feel like the homepage compare strip grew
  up into its own page
- fix motif overlap and palette mismatch

## Failure conditions
Reject a B8 page pass if:
- the masthead does not feel shared across surfaces
- the rankings page reads like a generic sortable dashboard
- the map page reads like a default full-screen map app
- the route-detail page feels like stacked utility cards rather than a designed
  drilldown
- compare remains visually disconnected from the homepage system
- future route-direction/date-range additions would obviously break the page
  composition
