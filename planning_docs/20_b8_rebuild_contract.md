# B8 Rebuild Contract

## Purpose
This is the strict agent-facing contract for the B8 visual-system pass.

It exists to prevent the implementation from preserving generic existing page
structures just because they already exist.

Use together with:
- `17_b8_design_reference_addendum.md`
- `18_b8_visual_system.md`
- `19_b8_surface_layout_spec.md`

If there is conflict:
1. this rebuild contract
2. `19_b8_surface_layout_spec.md`
3. `17_b8_design_reference_addendum.md`
4. `18_b8_visual_system.md`

## Source of truth
The homepage is the accepted aesthetic anchor.

The non-homepage pages must inherit from it using the B8 mockups, not from
their current implementation.

## Rebuild instruction
If the current rankings, map, or route-detail page structure conflicts with the
B8 mockups and layout spec, the worker should scrap and rebuild those page
structures rather than trying to cosmetically patch them.

Homepage rule:
- preserve the homepage's accepted overall composition
- only apply the explicit polish tasks listed in B8

Compare rule:
- align compare visually to the shared system
- do not treat compare as a primary redesign surface

## Required B8 outcomes
The worker must deliver:
- a dedicated full rankings page
- a redesigned map page that still centers the map but feels editorial
- a redesigned route-detail page that feels like a route dossier
- a shared masthead/system across primary pages
- the homepage polish fixes listed in B8

## Hard behavior rules
- do not add direction-level functionality
- do not add date-range functionality
- do not add fake placeholders for those future features
- do not drift into dashboard UI
- do not turn the map page into a default GIS app shell
- do not weaken the homepage masthead or headline system
- do not introduce off-token button colors

## Typography rule
The worker may see Helvetica exploration in the design package, but should
implement the condensed display-forward system unless the planner explicitly
changes that decision later.

## Review questions
Reject the B8 pass if:
- the new pages do not clearly belong to the same product family as the
  homepage
- the full rankings page feels like a utility table instead of an editorial
  ranking page
- the map page feels generic and app-like
- route detail loses the strong route identity / evidence rhythm
- compare still looks like a separate product
- the `LOWL` badge still clips
- compare motif lines still leak into the button
- compare button still uses the wrong yellow
- `Explore the map` still feels oversized

## Worker completion requirements
The eventual implementation worker must produce:
- screenshots at `1440x900` for:
  - homepage
  - rankings
  - map
  - route detail
- tests run
- a brutally honest mismatch list
