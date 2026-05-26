# B8 Design Reference Addendum

## Purpose
This addendum extends the approved homepage visual language across the rest of
the public site.

It exists because the homepage has become the product's accepted source of
truth, while the map, compare, and route-detail pages still read as
implementation-first surfaces. `B8` should close that gap.

Use together with:
- [11_design_reference.md](./11_design_reference.md)
- [18_b8_visual_system.md](./18_b8_visual_system.md)
- [19_b8_surface_layout_spec.md](./19_b8_surface_layout_spec.md)
- [20_b8_rebuild_contract.md](./20_b8_rebuild_contract.md)

If these documents conflict:
1. `20_b8_rebuild_contract.md`
2. `19_b8_surface_layout_spec.md`
3. this addendum
4. `11_design_reference.md`

## Source Of Truth
The homepage remains the anchor. The non-homepage pages should inherit:
- the masthead attitude
- the red / yellow / blue transit palette
- the black-rule structural system
- the condensed editorial headline language
- the dense, horizontal desktop composition

Approved homepage visual anchor:
- [homepage-light-mode.png](/C:/Users/ahadb/Documents/New%20project%203/planning_docs/mockups/homepage-light-mode.png)

New B8 view mockups:
- [rankings-light-mode.svg](/C:/Users/ahadb/Documents/New%20project%203/planning_docs/mockups/rankings-light-mode.svg)
- [map-light-mode.svg](/C:/Users/ahadb/Documents/New%20project%203/planning_docs/mockups/map-light-mode.svg)
- [route-detail-light-mode.svg](/C:/Users/ahadb/Documents/New%20project%203/planning_docs/mockups/route-detail-light-mode.svg)
- [compare-light-alignment.svg](/C:/Users/ahadb/Documents/New%20project%203/planning_docs/mockups/compare-light-alignment.svg)

Typography review board:
- [typography-comparison-board.svg](/C:/Users/ahadb/Documents/New%20project%203/planning_docs/mockups/typography-comparison-board.svg)

Primary review breakpoint:
- `1440x900`

## Visual direction for B8
The other pages should feel:
- like a civic Sunday front page
- informed by transit signage
- dense and confident
- more poster/editorial than dashboard

They should not feel:
- SaaS-clean
- app-template minimal
- generic full-screen mapping UI
- card-grid admin tooling

## Page-specific direction
### Rankings page
Should feel like the homepage rankings band expanded into a full edition page:
- stacked rank triptych or tabloid-style list language
- strong left-to-right reading path
- route badges and loss numbers remain dominant
- supporting notes live in structured side panels, not dashboard widgets

### Map page
Should feel like an evidence page:
- the map is still the hero surface
- but the page should frame it with editorial context, rank cues, and clear
  structural panels
- avoid the feeling of a generic GIS tool or route-planning app

### Route detail page
Should feel like a route dossier:
- route identity is big and immediate
- summary numbers should feel like poster statistics, not utility cards
- map, hotspot, and interpretation sections should read as a designed spread

### Compare page
Should only be visually aligned:
- same masthead
- same palette
- same type and rule language
- same button system

It does not need a fully reimagined hero structure in B8.

## Future-proofing rule
The layouts should quietly leave room for:
- a future secondary direction label on ranking and route-detail surfaces
- a future shared date-range control on top-level pages

Do not add fake controls or placeholders now. The goal is compatibility, not
premature UI.

## Typography decision
Helvetica should be evaluated because of its transit association, but it should
not replace the current condensed editorial display system by default.

Default B8 assumption after comparison:
- keep the current condensed display-forward system
- keep Helvetica as a considered but not chosen alternate unless later review
  explicitly reverses that decision

Reason:
- Helvetica strengthens the transit-agency association
- but the current condensed display system better preserves the homepage's
  newspaper-front-page force and route-card drama

## Explicit polish concerns
`B8` should treat these as part of the visual-system pass:
- `LOWL` route badge clipping risk
- compare motif lines leaking into the button
- compare button yellow mismatch
- oversized `Explore the map` button
- any remaining token drift around masthead, rules, or CTA sizing
