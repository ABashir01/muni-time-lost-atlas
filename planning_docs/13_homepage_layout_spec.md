# Homepage Layout Spec

## Purpose
This is the numeric layout contract for the homepage.

The mockup should be matched by enforcing composition rules, not just by describing aesthetic intent.

Primary review breakpoint:
- `1440x900`

## Top-Level Desktop Structure
At `1440x900`, the homepage should read as:
1. compact masthead
2. split hero
3. rankings band
4. explanatory strip
5. compare strip
6. footer/supporting line

The homepage should feel horizontally organized and visually dense.

## Masthead
### Height
- target height: `72px` to `86px`

### Composition
- left: logo / brand block
- right: compact nav

### Rules
- must span nearly full page width
- should feel like a civic masthead, not a generic site header
- nav should remain in one row on desktop

## Hero
### Height
- minimum desktop hero height: `520px`
- preferred range: `540px` to `620px`

### Width split
At desktop:
- left panel: `38%`
- right panel: `62%`

Allowed tolerance:
- left may vary between `35%` and `40%`
- right may vary between `60%` and `65%`

Do not allow the left panel to expand beyond `42%`.
Do not allow the map panel to shrink below `58%`.

### Left panel
The left hero panel must contain:
- eyebrow / short framing line
- giant stacked headline
- supporting one- or two-line explainer
- time-window controls

#### Headline
Rules:
- must dominate the panel vertically
- should occupy most of the left hero’s visual attention
- should use stacked lines, not long flowing lines
- final line must be red

Maximum content width:
- `520px` to `560px`

Whitespace rule:
- do not leave large empty white areas beneath the headline block
- the left hero should feel tightly packed, not sparse

### Right panel
The right hero panel must contain:
- map-like surface
- legend inside the map
- visible route emphasis
- strong CTA in the lower-right area

Rules:
- should feel like a real product map surface
- should visually outweigh the left panel in area, but not in hierarchy
- should not collapse into decorative illustration

## Rankings Band
### Strip
- should begin immediately below the hero
- should feel like a strong red band
- minimum height: `48px`
- preferred height: `56px`

### Cards
Desktop composition goal:
- preserve a strong horizontal rhythm
- cards must feel dense and forceful

If there are fewer real ranking cards than the mockup:
- maintain horizontal band logic anyway
- use neighboring content to preserve rhythm rather than letting the whole section collapse visually

Card rules:
- min height: `230px`
- preferred height: `250px` to `280px`
- oversized rank number
- oversized route badge
- oversized red loss value
- dense metadata beneath

## Explanatory Strip
The “what makes you lose time?” area should read as a single compact horizontal explanatory band.

Desktop rule:
- do not let it expand into tall airy feature cards
- keep copy short
- keep icons strong
- preserve quick scannability

## Compare Strip
Desktop compare controls should remain horizontal at `1440x900`.

Rules:
- selectors side by side
- compare CTA visible without wrapping
- must read as a horizontal utility band, not a form stack

## Width-Use Rules
At `1440x900`:
- homepage should use the desktop canvas aggressively
- avoid centered narrow-column behavior
- major sections should stretch across the layout width
- do not leave a major panel mostly empty if another panel is visually cramped

## Failure Conditions
Reject a homepage pass if any of these are true:
- hero headline feels secondary to the map
- left hero contains large dead white space
- map panel looks decorative rather than product-like
- rankings cards feel lightweight or too small
- desktop layout stacks when it should remain horizontal
- the page reads like a generic product landing page instead of a civic editorial homepage
