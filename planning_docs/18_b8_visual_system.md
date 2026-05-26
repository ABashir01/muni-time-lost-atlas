# B8 Visual System

## Purpose
Turn the homepage's accepted look into a reusable visual system for the rest of
the public frontend.

This is not a second design language. It is the codification of the one that
already works.

## Primary desktop target
- `1440x900`

## Core system rules
### Masthead
- use one compact horizontal masthead across all primary pages
- left: `Muni Lost Time Atlas`
- right: one grouped nav row
- nav labels should stay:
  - `Explore the Map`
  - `Rankings`
  - `Compare`
  - `Data & Methods`
- the shared masthead should feel as strong as the homepage masthead, not like
  a lighter app shell

### Palette
Lock these as the site-wide primary tokens:
- `--muni-red: #ea0702`
- `--red: #d81420`
- `--yellow: #fcc000`
- `--blue: #0868d0`
- `--orange: #e85c10`
- `--green: #138646`
- `--purple: #6a43b0`
- `--teal: #118fbc`
- `--ink: #050505`
- `--rule: #101010`

Usage rules:
- red is the headline urgency color
- yellow is the utility CTA accent
- route colors should stay in route badges, compare motifs, and map features
- no off-token yellows or secondary CTA palettes

### Typography
Default B8 type system:
- display / headlines: current condensed display-forward system
- body: clean sans body copy
- labels and nav: compact uppercase sans

Typography rule:
- use the current condensed display language as the default
- do not switch the implementation to Helvetica-first unless an explicit visual
  review decides it beats the homepage anchor

### Borders and cards
- section borders: `2px`
- inner dividers: `1px` to `1.5px`
- minimal radius only
- flat fills
- no soft shadow-led separation

### Buttons
- rectangular
- uppercase or strong compact label treatment
- consistent height bands by role
- primary CTA yellow should match the locked token

### Route badges
- must accommodate short, medium, and wide labels cleanly
- plan for:
  - `14`
  - `49`
  - `LOWL`
  - future direction subtitle nearby

Badge rules:
- preserve transit-marker feel
- avoid clipping or over-tight letterforms
- allow slightly different font-size tracking rules for 4-character labels if
  needed

## Page-shell system
### Rankings
- page should behave like an expanded ranking edition
- main ranking surfaces should use strong horizontal list/card bands
- supporting notes and limitations should sit in sidebar or footer panels

### Map
- map remains the dominant surface
- surrounding panels should frame the map editorially
- legend, note, and ranked-route context should feel intentionally designed

### Route detail
- route identity and summary metrics should occupy strong top-of-page territory
- corridor map and hotspot evidence should live in heavier split panels, not
  scattered utility tiles

### Compare
- align to the shared shell and token system
- no major hero redesign required in B8

## Future-compatibility rules
- top-level pages should leave a clear zone where a future shared date-range
  control can sit without breaking the composition
- rankings and route-detail compositions should leave room for a future
  direction subtitle
- do not expose inactive placeholders now

## Homepage polish checklist inside B8
- `LOWL` route badge fit
- compare motif line containment
- compare button yellow consistency
- `Explore the map` button size tuning
- any remaining token drift in homepage CTA or label treatments
