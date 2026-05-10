# Title
B5a Homepage Visual Lock

## Goal
Match the approved homepage mockup closely enough at the primary desktop breakpoint that the homepage layout, density, and hierarchy can be treated as locked for the rest of the frontend build.

## Why this bundle exists
The homepage is the visual anchor of the product. The earlier combined frontend pass left too much room for interpretation and caused repeated churn. This bundle isolates the homepage so visual fidelity can be reviewed directly before the rest of the frontend work continues.

## Depends on
- `B4_api_bundle`
- design reference docs:
  - `11_design_reference.md`
  - `12_frontend_design_system.md`
  - `13_homepage_layout_spec.md`
  - `14_homepage_rebuild_contract.md`

## Touches
- homepage only
- shared layout/design primitives only when strictly required to support the homepage

## Inputs
- homepage-related fixture payloads from `fixtures/api`
- approved mockup and design-reference documents
- hard layout rules targeting `1440x900`
- explicit rebuild permission and structure from `14_homepage_rebuild_contract.md`

## Outputs
- a homepage that is visually close to the approved mockup
- a review screenshot captured at `1440x900`
- a brief mismatch list documenting any remaining gaps

## Implementation notes
- optimize for the desktop breakpoint `1440x900` first
- preserve strong horizontal occupancy
- preserve the hero split ratio and dense lower-band composition
- enforce the three-card ranking rhythm on the lower band
- treat the "What makes you lose time?" explainer as a peer panel with the ranking cards, not leftover space
- if the current homepage structure conflicts with the contract, scrap it and rebuild it
- do not broaden scope to route detail, compare, map-only pages, or methodology unless a shared primitive absolutely must change
- do not accept generic centered-column or dashboard drift

## Tests required
- one screenshot-based review at `1440x900`
- one smoke/render pass sufficient to confirm the homepage still runs locally

## Acceptance criteria
- homepage composition clearly matches the approved mockup's tone, density, and horizontal layout
- hero proportions satisfy `13_homepage_layout_spec.md`
- the lower band reads as a deliberate three-column composition
- the homepage no longer reads as a generic SaaS/dashboard page
- a screenshot and short remaining-mismatches list are included in the worker handoff

## Non-goals
- live API integration
- broader frontend page completion
- mobile polish beyond avoiding obvious breakage

## Handoff to next bundle
After `B5a` is accepted, proceed to `B5b_static_surface_completion` to finish the remaining public screens against fixtures.
