# Title
B8 Editorial Visual System Bundle

## Goal
Turn the homepage style into the explicit cross-site visual system so the major
public pages feel like one civic/editorial product rather than one polished
homepage plus several generic utility views.

## Why this bundle exists
The MVP now has working historical data, routing, map infrastructure, and
rolling publication. The main remaining quality gap is presentation: the
homepage has the right sensibility, while the other pages still read as
functional scaffolds.

`B8` should therefore focus on visual coherence, hierarchy, and public-facing
credibility rather than new analytical features.

## Depends on
- `B6_frontend_api_integration_bundle`
- `B6b_real_map_engine_bundle`
- `B7_realtime_bundle` as redefined rolling historical publication

## Primary surfaces
- homepage polish cleanup
- full rankings page
- full map page redesign
- route detail visual redesign

## Secondary surface
- compare page alignment only

Compare should inherit the shared masthead, color tokens, type system, and
structural rules, but it does not need a first-class hero/mockup pass equal to
rankings, map, and route detail.

## Inputs
- approved homepage light-mode mockup
- existing homepage implementation as the aesthetic anchor
- current route-level public product behavior
- current fixed published-window product behavior

## Outputs
- new page mockups for rankings, map, and route detail
- typography comparison board for current condensed display vs Helvetica-led
  alternative
- strict markdown contract docs for the B8 visual system
- a worker prompt spec for implementation
- updated `B8` scope in the planning docs

## Implementation notes
- this is a mockup-and-contract bundle first, not a code-implementation bundle
- create mockups before implementation instructions
- keep the homepage as the source of truth for:
  - masthead structure
  - palette
  - border/rule system
  - transit-poster/editorial tone
- add a dedicated full rankings page to the public site structure
- do not add direction-level or date-range functionality in `B8`
- do reserve visual space so future direction labels and a future shared
  date-range control can be added cleanly later
- do not let the full map drift into a generic full-screen GIS app
- use the typography comparison stage to confirm that the current condensed
  display system stays stronger than a Helvetica-led alternative unless review
  says otherwise

## Small polish items that belong in B8
- route badge sizing for labels like `LOWL`
- compare-strip motif lines leaking into the compare button
- compare button yellow mismatching the locked palette
- `Explore the map` button feeling too large
- any remaining token drift where a component is close but not aligned with the
  homepage system

## Tests required
- screenshot-based visual review at `1440x900` for:
  - homepage
  - rankings page
  - full map page
  - route detail page
- one frontend regression sweep after implementation
- confirm no fake range/direction placeholders were added

## Acceptance criteria
- the homepage, rankings, map, and route detail pages clearly read as one
  product family
- the full rankings page feels like an expansion of the homepage rankings, not
  a generic data table
- the map page feels editorial and evidence-led, not app-template GIS
- route detail feels like a natural drilldown from the homepage cards
- compare no longer feels visually off-system
- homepage polish issues are resolved, including:
  - `LOWL` badge fit
  - compare motif leakage
  - compare button palette mismatch
  - oversized `Explore the map` button

## Non-goals
- new analytical features
- direction-level public shift
- public date-range support
- compare redesign beyond light alignment
- backend or API expansion

## Handoff to next work
After the visual system is accepted, implementation should be handed to a
worker using the dedicated B8 worker prompt and contract-doc set.

## Completion notes
- Primary review breakpoint remains `1440x900`
- Future direction/date-range support should be visually anticipated but not
  implemented
