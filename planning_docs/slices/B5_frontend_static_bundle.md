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

## Tests required
- one primary frontend render/test suite covering the major screens against fixtures
- one responsive or smoke-level check for the main product surfaces
- one screenshot-based visual review against `11_design_reference.md`

## Acceptance criteria
- homepage, route detail, compare, map, and methodology pages all render from fixtures
- the product hierarchy and core metric language read correctly
- the bundle is reviewable without live backend coupling
- the homepage clearly resembles the approved mockup’s tone, hierarchy, and density
- the result does not read as a generic SaaS dashboard

## Non-goals
- live API integration
- realtime overlays

## Handoff to next bundle
`B6_frontend_api_integration_bundle` should replace fixtures with live API responses while preserving the reviewed UI.

## Completion notes
