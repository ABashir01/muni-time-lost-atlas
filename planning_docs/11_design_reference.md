# Design Reference

## Purpose
This document is the explicit visual contract for the first public frontend implementation.

The goal is not generic “modern UI.” The goal is a forceful civic/editorial product that feels closer to a newspaper front page, transit-signage system, and campaign site than to a SaaS dashboard.

This reference should guide `B5_frontend_static_bundle` and any later frontend revisions unless a newer design decision replaces it.

Use together with:
- [12_frontend_design_system.md](./12_frontend_design_system.md)
- [13_homepage_layout_spec.md](./13_homepage_layout_spec.md)

## Primary Reference
Use the attached mockup the user approved as the main visual reference for:
- hierarchy
- typography
- color emphasis
- spacing density
- map prominence
- card treatment

The agent should follow the mockup’s tone and layout logic even if exact pixel matching is not possible.

Primary review breakpoint:
- `1440x900`

## Visual Direction
The frontend should feel:
- editorial
- civic
- bold
- urgent
- transit-map-informed
- information-dense without feeling cluttered

Avoid:
- startup dashboard UI
- soft cards and pastel gradients
- generic component-library aesthetics
- dark mode as the default presentation
- purple-heavy accent palettes

## Layout Rules
### Homepage hero
The homepage should open with a split-screen composition:
- left: oversized headline and framing copy
- right: large map panel

This split should remain the dominant above-the-fold structure on desktop.
The homepage layout spec defines the exact desktop ratio and occupancy rules.

### Header
The header should be compact, horizontal, and editorial:
- strong wordmark / brand block on the left
- terse navigation on the right
- minimal chrome

### Below-the-fold order
Below the hero, preserve this order:
1. rankings / worst routes block
2. explanatory “what makes you lose time?” strip
3. compare section
4. lower-supporting content

### Map priority
The map should be visible immediately and feel like a primary product surface, not a secondary widget.

## Typography
### Headline treatment
Use a heavy, condensed, uppercase display style for the main homepage headline.

The headline should feel:
- blunt
- immediate
- oversized

Preferred qualities:
- condensed width
- very high weight
- tightly stacked lines
- minimal decorative flourish

### Supporting typography
Use:
- bold uppercase labels for navigation, section bars, and small headers
- clean readable sans-serif for descriptions and supporting copy
- oversized numeric treatment for route ranking values

Avoid:
- friendly rounded fonts
- light geometric minimalism
- overly elegant editorial serif systems

## Color System
Base palette:
- white background
- black typography and rules
- strong red as the primary emphasis color

Supporting accents:
- yellow
- blue
- orange
- green

Use accent colors sparingly and purposefully. The UI should not become rainbow-heavy outside the route/map context.

### Emphasis rules
- red is for urgency and headline emphasis
- yellow can be used for controls or CTA emphasis
- route colors can appear in badges, map lines, compare motifs, and small highlights
- black rules and borders should help structure the page

## Component Style
Use components that feel:
- flat
- sharp
- bordered
- compact

Preferred:
- strong outlines
- shallow or no shadows
- minimal border radius
- solid fills
- dense cards

Avoid:
- glassmorphism
- floating translucent panels
- oversized rounded corners
- generic pill-heavy dashboard controls everywhere

## Homepage-Specific Requirements
The homepage should preserve these mockup ideas:
- giant civic headline
- route-ranking cards with oversized numbers
- map legend embedded inside the map
- route badges that feel like transit route markers
- clear distinction between waiting, slow travel, and bunching
- compare controls visible without deep scrolling

## Motion
Motion should be restrained and structural:
- subtle page-load reveal
- slight stagger for cards or map overlays
- no playful microinteraction overload

Motion should never weaken the punchy editorial feel.

## Responsiveness
On mobile:
- preserve the hierarchy, not the exact desktop arrangement
- keep the headline strong
- keep the map high on the page
- keep route cards compact but readable
- avoid collapsing into generic stacked-card SaaS layout

The design can reflow, but it should still feel like the same product.

## Review Standard For B5
The frontend bundle should not be accepted unless the review can honestly say:
- it clearly resembles the approved mockup’s tone and hierarchy
- it avoids generic dashboard aesthetics
- the homepage headline, map, and rankings feel like the main story
- the route cards and compare controls are visually prominent
- the result feels intentional and specific, not template-like

## Implementation Guidance For Agents
When building `B5`:
- start from this design reference before selecting colors, type, or spacing
- prefer custom CSS variables and deliberate composition over library-default appearance
- treat the approved mockup as a style target, not just inspiration
- if a design tradeoff is necessary, preserve hierarchy and tone before preserving exact layout details
