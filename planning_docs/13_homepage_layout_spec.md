# Homepage Layout Spec

## Purpose
This is the numeric layout contract for the homepage.

The light-mode mockup should be matched by enforcing composition rules, not by describing aesthetic intent loosely.

Primary review breakpoint:
- `1440x900`

## Top-Level Desktop Structure
At `1440x900`, the homepage should read as four major horizontal sections:
1. header
2. hero
3. rankings + explainer row
4. compare footer strip

The page should feel horizontally organized, visually dense, and easy to rebalance by editing four top-level size variables.

## Top-Level Vertical Ratios
Target section-height ratios for the full homepage viewport:
- header: `8%`
- hero: `43%`
- rankings + explainer row: `38%`
- compare footer strip: `11%`

These are the default contract values for the first strict implementation pass.

Accepted tolerance:
- each section may drift by about `+/- 2%` only if the overall composition still clearly matches the mockup

### Code rule
The implementation should expose these values as obvious page-level tokens, for example:
- `--home-row-header: 8fr`
- `--home-row-hero: 43fr`
- `--home-row-insights: 38fr`
- `--home-row-compare: 11fr`
- `--home-gutter-inline: 12px`
- `--home-hero-left: 38%`
- `--home-hero-right: 62%`

Those tokens should be the easiest place for a reviewer to change the homepage height balance later.

## Header
### Height
- target ratio: `8%`
- practical range at `1440x900`: about `66px` to `78px`

### Composition
- left: `Muni Lost Time Atlas`
- right: one flex group of nav links matching the approved mockup order

Required nav links:
- `Explore the Map`
- `Rankings`
- `Compare`
- `Data & Methods`

Rules:
- header spans full width inside the small outer gutter
- brand sits left, nav group sits right
- no second row
- no extra decorative elements beyond what helps match the mockup
- the header should feel very close to the approved light-mode masthead
- the left brand text should be the strongest header element and should not be broken into multiple stacked lines

## Hero
### Height
- target ratio: `43%`

### Width split
At desktop:
- left panel: `38%`
- right panel: `62%`

Allowed tolerance:
- left may vary between `36%` and `40%`
- right may vary between `60%` and `64%`

The left panel must never exceed `42%`.
The right map panel must never shrink below `58%`.

### Left hero composition
The left hero panel has three vertical zones:
1. headline block
2. time-range controls block
3. local `Worst Routes Right Now` banner

Suggested internal ratios of the left hero panel:
- headline block: `72%`
- controls/meta block: `12%`
- local banner block: `16%`

### Left hero content
Must contain:
- large headline: `Where Muni Riders Lose The Most Time`
- time-range selector
- local red banner labeled `Worst Routes Right Now`

Rules:
- the headline dominates the panel
- stacked lines only
- final emphasis line in red
- no large dead white space below the headline
- the red `Worst Routes Right Now` strip belongs only to the left hero panel; it must not span the full page width
- the left panel should also contain the short supporting sentence under the headline, but it must stay subordinate to the headline

### Right hero content
- reserve the entire right panel for a map block
- current pass may use a simple placeholder map surface with a distinct background
- do not put rankings or explainer content into the right hero panel

Rules:
- the right side is just map territory for now
- keep it visually clean and obviously reserved for the future map implementation

## Rankings + Explainer Row
### Height
- target ratio: `38%`

### Top-level split
This row should read like six even columns split into two equal halves:
- left half = 3 ranking cards
- right half = 3 explainer cards

Top-level width split:
- left half: `50%`
- right half: `50%`

Within each half:
- use a `3`-column rhythm
- each internal column should be equal width
- the left and right halves should be close enough in total visual weight that one does not read as filler for the other

### Left half: ranking cards
The three ranking cards should be near-identical in size and structure.

Each ranking card must contain:
1. header row with ranking number and route label
2. large loss number row
3. `extra time per trip` row
4. horizontal divider
5. `worst on` row
6. `most loss` row

Ranking card rules:
- ranking number is prominent
- route identifier and route name sit together in the header
- the loss number is the strongest interior visual element
- the three cards must read as a unified triptych
- if real data only produces two route cards, a third placeholder card is acceptable temporarily to preserve layout rhythm

### Right half: explainer group
Header:
- `What Makes You Lose Time?`

Below the header:
- three explainer items:
  - `Waiting`
  - `Slow Travel`
  - `Bunching`

Each explainer item must contain:
- a small colored symbol area on the left
- a text area on the right
- a colored header matching the symbol
- a short explanation below

Divider rule:
- only show vertical dividers between the three explainer items
- do not box each item separately above and below
- the overall right half container holds the group together
- the explainer cards should be visually similar in height and weight to the ranking cards opposite them

Footer link:
- a link below the explainer items that points users toward learning more about lost time
- this link should stay inside the right half and below the explainer items, not drop into the compare strip

## Compare Footer Strip
### Height
- target ratio: `11%`

### Width split
- left half: label + short description
- right half: route selectors + compare action + small transit-line graphic

Rules:
- keep this strip thin
- keep it horizontal
- preserve the mockup's utility-band feel
- the left copy should stay compact
- the right controls should be visibly grouped and easy to edit later
- the small transit-line graphic on the far right is part of the contract, even if it remains simple in the first pass

## Width-Use Rules
At `1440x900`:
- every top-level section should take nearly the full page width
- avoid centered narrow-column behavior
- major sections should stretch across the layout width
- do not leave the hero left panel starved while the map panel is empty
- do not let the right half of the lower row collapse or shrink awkwardly

## Failure Conditions
Reject a homepage pass if any of these are true:
- header does not closely resemble the approved mockup structure
- hero is not a two-part split with left content and right map territory
- the local `Worst Routes Right Now` banner spans the full page instead of staying in the left hero panel
- the lower row is not a clean `3 ranking cards + 3 explainer cards` rhythm
- the lower row does not use the full available width
- the explainer group is boxed incorrectly instead of using divider-only separation
- the compare section becomes a bulky stacked form
- the page reads like a generic landing page instead of the approved civic/editorial layout
