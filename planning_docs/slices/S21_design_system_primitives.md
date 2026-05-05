# Title
S21 Design System Primitives

## Goal
Build the core UI primitives that express the approved civic/transit visual direction.

## Why this slice exists
The product needs consistent structure and typography before screen-level implementation.

## Depends on
- `S20_next_app_skeleton`

## Touches
- base UI components
- theme tokens
- typography and color primitives

## Inputs
- visual direction from `01_product_experience.md`
- planning mockups

## Outputs
- reusable stat cards, route badges, section headers, toggles, legends

## Implementation notes
- align with the mockup direction
- keep primitives generic enough for multiple pages

## Tests required
- component render tests
- visual smoke checks if available

## Acceptance criteria
- page slices can compose from a small, consistent primitive set

## Non-goals
- full page implementations
- API calls

## Handoff to next slice
Next slice builds the homepage against fixtures.

## Completion notes

