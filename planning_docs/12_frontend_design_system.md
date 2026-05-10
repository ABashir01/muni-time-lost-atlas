# Frontend Design System

## Purpose
This is the strict visual-system document for the public frontend.

It exists to reduce design drift by turning the approved homepage direction into concrete reusable rules. It should be used together with:
- `11_design_reference.md`
- `13_homepage_layout_spec.md`
- `14_homepage_rebuild_contract.md`

If those documents conflict:
1. `14_homepage_rebuild_contract.md`
2. `13_homepage_layout_spec.md`
3. `11_design_reference.md`
4. this design system

## Primary Desktop Target
Primary design target:
- `1440x900`

This is the main review breakpoint for homepage fidelity.

Secondary review target:
- large high-density laptop setups after browser scaling, but only after the `1440x900` lock is correct

Primary visual source of truth:
- the approved light-mode homepage mockup shared in the project thread
- [homepage-light-mode.png](/C:/Users/ahadb/Documents/New%20project%203/planning_docs/mockups/homepage-light-mode.png)

Do not design from:
- any dark-mode variant
- the current implementation if it conflicts with the approved mockup
- generic dashboard instincts

## Design Philosophy
The frontend should default toward:
- horizontal composition
- dense information hierarchy
- editorial impact
- strong borders and rules
- visual compression over safe whitespace

It should not default toward:
- centered narrow content columns
- soft modern product UI
- excessive vertical stacking on desktop
- airy whitespace for its own sake

## Canvas Rules
### Desktop content width
At desktop widths `>= 1280px`:
- content should use essentially the full browser width
- preferred content width: `calc(100vw - 24px)`
- maximum allowed outer gutter at the primary breakpoint: `12px` on each side
- avoid narrow centered article-style containers

### Horizontal occupancy rule
At desktop widths `>= 1280px`:
- the homepage should prefer side-by-side composition over stacking
- do not collapse major horizontal bands into vertical stacks unless technically necessary
- empty white space inside a major homepage panel should be treated as a layout bug, not a feature
- the homepage should visually read edge-to-edge inside the allowed outer gutter
- any section that narrows into a centered content column should be treated as a failure unless the contract explicitly allows it

### Large-screen expansion rule
At desktop widths `>= 1600px`:
- keep the same composition
- increase horizontal span before increasing white space
- do not center the content into a narrow column
- allow the map half to breathe, but do not let the headline half become timid

## Homepage Height Tokens
For homepage work, define easy-to-edit custom properties near the top of the homepage stylesheet or page-level component.

Use this pattern:
- `--home-row-header`
- `--home-row-hero`
- `--home-row-insights`
- `--home-row-compare`
- `--home-gutter-inline`
- `--home-hero-left`
- `--home-hero-right`

Preferred default values at `1440x900`:
- `--home-row-header: 8fr`
- `--home-row-hero: 43fr`
- `--home-row-insights: 38fr`
- `--home-row-compare: 11fr`
- `--home-gutter-inline: 12px`
- `--home-hero-left: 38%`
- `--home-hero-right: 62%`

These values are intentionally simple and should be easy to tweak by hand later.
The implementation should prefer a single page-level grid whose row sizing is controlled by these tokens.

If the implementation uses CSS grid, those custom properties should be the only place a reviewer needs to edit to rebalance the four major homepage section heights.

## Color Tokens
### Base
- `--page-bg`: `#ffffff`
- `--ink`: `#111111`
- `--ink-strong`: `#000000`
- `--rule`: `#111111`

### Primary accents
- `--accent-red`: `#e21b23`
- `--accent-yellow`: `#f0c419`

### Support accents
- `--accent-blue`: transit blue
- `--accent-orange`: transit orange
- `--accent-green`: transit green
- `--accent-purple`: transit purple

### Usage rules
- red is reserved for the strongest emphasis moments
- yellow is for selected controls and CTA emphasis
- route colors are for route identity and map signals, not for general UI decoration
- this homepage is light-mode only for the primary implementation pass

## Border And Radius Rules
- outer section borders: `2px`
- inner dividers: `1px` to `1.5px`
- border radius: `0px` by default
- if a radius is used, max `2px`

Avoid:
- soft cards
- large rounded corners
- shadow-led separation

## Spacing Scale
Preferred desktop spacing tokens:
- `4px`
- `8px`
- `12px`
- `16px`
- `24px`

Avoid introducing large `32px+` gaps inside homepage sections unless explicitly required by the layout spec.

Default preference:
- compress before expanding
- tighten before stacking

## Typography System
### Display headline
Use:
- very heavy condensed uppercase display face
- negative or near-zero tracking
- line-height between `0.84` and `0.92`

Desktop headline target:
- size: `clamp(88px, 7vw, 132px)`

### Section bars and nav
Use:
- bold uppercase sans
- small but high-contrast
- compact spacing

### Ranking values
Use:
- oversized numeric emphasis
- stronger than the surrounding copy
- red for the main loss value

## Component Rules
### Cards
- flat fill
- strong border
- dense interior spacing
- compact labels

For the homepage lower band:
- left ranking cards should be full cards with outer borders
- right explainer cards should not read as isolated boxed cards
- the right explainer group should use internal dividers only between cards, with no extra top or bottom boxing beyond the section container
- the left ranking area and right explainer area should read as peer halves of one row
- the three ranking cards must stay visible as a deliberate triptych, even if placeholder data is needed to preserve rhythm

### Buttons
- rectangular
- strong outline or solid fill
- uppercase when used as primary structural control

### Route badges
- high-contrast circular or pill route markers
- sized large enough to read immediately
- should feel like transit markers, not generic tags

## Anti-Drift Rules
Frontend workers should assume the following unless explicitly overridden:
- do not optimize for comfortable article reading width on the homepage
- do not make the page more minimal if that reduces punch
- do not add whitespace just to make the page feel cleaner
- do not convert horizontal bands into vertical stacks at desktop width
- do not use default component-library proportions without overriding them
- do not keep iterating on the current homepage if its structure conflicts with the contract; rebuild it
- do not let the map, compare strip, or explainer group shrink the main horizontal composition into a narrow center block
- do not span the `Worst Routes Right Now` banner across the full page; keep it local to the left hero panel
- do not use the current homepage implementation as a layout source of truth if it conflicts with the light-mode mockup or rebuild contract

## Review Rules
When reviewing a homepage-oriented frontend pass:
- judge it first at `1440x900`
- compare hierarchy and density before polish
- reject if it reads as a generic dashboard
- reject if the hero feels under-scaled
- reject if major panels fail to occupy width
- reject if the top-level section heights do not approximately follow the documented ratios
- reject if the page drifts away from the approved light-mode mockup
