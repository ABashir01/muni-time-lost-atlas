# Title
B5 Frontend Static Bundle

## Goal
Build the complete Next.js product shell and all public-facing screens against fixture data.

## Why this bundle exists
The frontend should be built and reviewed as a coherent product experience instead of being fragmented into many tiny page/component slices.

## Depends on
- `B4_api_bundle`

## Touches
- Next.js app shell
- design primitives
- homepage
- route detail page
- compare view
- map view
- methodology page

## Inputs
- fixture payloads from the API bundle
- design direction already agreed for the public-facing product
- product framing in `01_product_experience.md`
- explicit visual contract in `11_design_reference.md`
- hard visual-system rules in `12_frontend_design_system.md`
- homepage numeric layout rules in `13_homepage_layout_spec.md`

## Outputs
- complete static frontend MVP
- no backend dependency for design validation

## Implementation notes
- build the full app shell in this bundle
- implement the design primitives and layout system as part of the same work
- keep the hierarchy:
  - rankings first
  - map second
  - explanatory context third
- keep the public language consistent with the methodology and API fields
- optimize for the public-facing product, not dashboards
- follow the approved mockup’s editorial/transit-signage visual language
- preserve the split hero structure:
  - oversized headline on the left
  - large interactive-feeling map surface on the right
- use a strong black / white / red base palette with limited route-color accents
- prefer sharp borders, compact cards, and minimal rounding over soft dashboard styling
- the frontend should be reviewable against the design reference, not just against functional completeness
- for homepage work, prioritize `1440x900` desktop fidelity before broader breakpoint generalization
- preserve horizontal occupancy at desktop widths; do not collapse into narrow centered layouts unless the layout spec explicitly allows it

## Tests required
- one primary frontend render/test suite covering the major screens against fixtures
- one responsive or smoke-level check for the main product surfaces
- one screenshot-based visual review against `11_design_reference.md`
- one screenshot-based visual review at `1440x900`

## Acceptance criteria
- homepage, route detail, compare, map, and methodology pages all render from fixtures
- the product hierarchy and core metric language read correctly
- the bundle is reviewable without live backend coupling
- the homepage clearly resembles the approved mockup’s tone, hierarchy, and density
- the result does not read as a generic SaaS dashboard
- the homepage satisfies the hard desktop ratio and occupancy rules in `13_homepage_layout_spec.md`

## Non-goals
- live API integration
- realtime overlays

## Handoff to next bundle
`B6_frontend_api_integration_bundle` should replace fixtures with live API responses while preserving the reviewed UI.

## Completion notes
- Changed:
  - scaffolded the full `frontend/` Next.js app with fixture-only data loading from `../fixtures/api`
  - implemented the homepage, route detail, compare, map, and methodology pages plus shared layout/design primitives
  - added Vitest render coverage and a Playwright smoke pass that also writes a homepage review screenshot to `artifacts/frontend/b5-homepage-desktop.png`
  - clarified in `05_api_contract.md` that only route 14 currently has a dedicated segment fixture, so secondary route detail pages fall back to shared summary/map payloads
- Tests run:
  - `npm test` in `frontend/`
  - `npm run build` in `frontend/`
  - `npm run smoke` in `frontend/`
- Passed:
  - all public pages render against fixtures
  - Next.js production build succeeds
  - browser smoke pass succeeds and captures the desktop homepage screenshot artifact for design review
- Known limitations / follow-up:
  - compare remains dynamic because it reads query-string route selections
  - the current B4 fixture set only provides deep segment detail for route 14, so other route detail pages intentionally fall back to the shared map/summary contract
