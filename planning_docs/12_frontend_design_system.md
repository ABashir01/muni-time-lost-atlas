# Frontend Design System

## Purpose
This is the strict visual-system document for the public frontend.

It exists to reduce design drift by turning the approved homepage direction into concrete reusable rules. It should be used together with:
- `11_design_reference.md`
- `13_homepage_layout_spec.md`

If those documents conflict:
1. `13_homepage_layout_spec.md`
2. `11_design_reference.md`
3. this design system

## Primary Desktop Target
Primary design target:
- `1440x900`

This is the main review breakpoint for homepage fidelity.

Secondary desktop breakpoints may exist later, but workers should optimize the first strong visual pass for `1440x900`.

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
- content should use nearly the full browser width
- preferred content width: `min(1520px, calc(100vw - 48px))`
- avoid narrow centered article-style containers

### Horizontal occupancy rule
At desktop widths `>= 1280px`:
- the homepage should prefer side-by-side composition over stacking
- do not collapse major horizontal bands into vertical stacks unless technically necessary
- empty white space inside a major homepage panel should be treated as a layout bug, not a feature

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
- do not add whitespace just to make the page feel “cleaner”
- do not convert horizontal bands into vertical stacks at desktop width
- do not use default component-library proportions without overriding them

## Review Rules
When reviewing a homepage-oriented frontend pass:
- judge it first at `1440x900`
- compare hierarchy and density before polish
- reject if it reads as a generic dashboard
- reject if the hero feels under-scaled
- reject if major panels fail to occupy width
