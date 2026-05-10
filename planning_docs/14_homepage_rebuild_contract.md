# Homepage Rebuild Contract

## Purpose
This document is the strict agent-facing contract for the homepage rebuild.

It exists to remove interpretation drift. If the current homepage conflicts with this contract, the agent should scrap the current homepage layout and rebuild it from the top down.

Use this together with:
- `11_design_reference.md`
- `12_frontend_design_system.md`
- `13_homepage_layout_spec.md`

If there is conflict:
1. this rebuild contract
2. `13_homepage_layout_spec.md`
3. `11_design_reference.md`
4. `12_frontend_design_system.md`

## Source Of Truth
Primary visual source of truth:
- the approved light-mode homepage mockup in the project thread
- [homepage-light-mode.png](/C:/Users/ahadb/Documents/New%20project%203/planning_docs/mockups/homepage-light-mode.png)

Do not use as the primary reference:
- the current homepage implementation
- any dark-mode variant
- generic landing-page or dashboard patterns

## Rebuild Instruction
The agent is encouraged to scrap the current homepage structure and rebuild it completely if that is the fastest way to match this contract.

Do not preserve:
- current proportions
- current section nesting
- current card distribution
- current map treatment

unless they already match this contract.

## Structural Contract
At `1440x900`, the homepage must be one full-width page grid with exactly four top-level rows:
1. header
2. hero
3. rankings + explainer row
4. compare footer strip

The easiest place to rebalance these heights must be a small set of homepage-level variables.

Required top-level tokens:
- `--home-row-header: 8fr`
- `--home-row-hero: 43fr`
- `--home-row-insights: 38fr`
- `--home-row-compare: 11fr`
- `--home-gutter-inline: 12px`
- `--home-hero-left: 38%`
- `--home-hero-right: 62%`

The implementation should make these variables obvious near the top of the homepage code or stylesheet.

## Full-Width Rule
The homepage must use essentially the entire horizontal canvas.

Rules:
- max outer gutter at `1440x900`: `12px` each side
- no narrow centered content column
- no major row should leave large empty margin space by default
- when in doubt, expand horizontally before stacking vertically

## Header Contract
The header must closely match the light-mode mockup structure:
- left side: `Muni Lost Time Atlas`
- right side: one flex grouping of links

Required right-side links:
- `Explore the Map`
- `Rankings`
- `Compare`
- `Data & Methods`

Rules:
- one row only
- no extra utility row
- no decorative filler
- strong masthead feel

## Hero Contract
The hero is a two-part split:
- left = story panel
- right = map placeholder panel

Width split:
- left: `38%`
- right: `62%`

### Left hero
Must contain, in this order:
1. giant headline
2. time-range selector
3. local `Worst Routes Right Now` banner

The left hero must also include a short supporting sentence under the headline, but the headline remains dominant.

Rules:
- headline text: `Where Muni Riders Lose The Most Time`
- stacked lines only
- final emphasis line in red
- no large dead white space
- the red `Worst Routes Right Now` banner lives only in the left hero panel
- it must not span the full page width

### Right hero
The right hero is reserved for the map area.

Current pass:
- a simple placeholder block is acceptable
- it should clearly communicate map territory
- it should not host rankings or explainer content

## Rankings + Explainer Row Contract
This row should visually behave like six even columns split into two equal halves.

### Left half
Contains exactly three ranking cards.

Each card must include:
1. header row with ranking number plus route label
2. large loss number
3. `extra time per trip`
4. horizontal divider
5. `Worst on` row
6. `Most loss` row

Rules:
- cards should be near-identical in size
- ranking numbers must be large and immediate
- the three cards must read as one triptych
- if only two real routes exist in fixtures, a placeholder third card is acceptable to preserve layout rhythm

### Right half
Contains:
1. header: `What Makes You Lose Time?`
2. three explainer items:
   - `Waiting`
   - `Slow Travel`
   - `Bunching`
3. a footer link to learn more about lost time

Each explainer item must contain:
- a colored symbol block on the left
- a text block on the right
- a colored item heading
- a short explanation below

Rules:
- only show vertical dividers between explainer items
- do not box each explainer item individually on all four sides
- the explainer group should read as a peer block to the ranking cards opposite it
- the explainer cards should be similar in height/weight to the ranking cards

## Compare Footer Strip Contract
This row is a thin utility strip.

Left side:
- header: `Compare Routes Or Corridors`
- short descriptive line below

Right side:
- route selectors / compare control group
- small transit-line graphic at the far right

Rules:
- keep it thin
- keep it horizontal
- do not turn it into a bulky stacked section

## Agent Behavior Rules
When implementing this homepage:
- do not negotiate with the current layout if it conflicts with this contract
- rebuild instead of patching if rebuilding is cleaner
- do not optimize for dashboard neatness
- do not reduce width usage
- do not introduce extra vertical stacking on desktop
- do not promote the compare strip into a large section

## Review Questions
Reject the homepage if:
- it does not take up the full horizontal space
- the header does not closely match the mockup structure
- the hero is not clearly left-story / right-map
- the local red banner spans the full page
- the lower row is not `3 ranking cards + 3 explainer cards`
- the right explainer half looks like leftover filler instead of a peer panel
- the footer strip is too tall or stacked

## Implementation Hint
The agent should keep the top-level homepage proportions editable in one obvious place so the reviewer can quickly test alternate balances later without rewriting the layout structure.
