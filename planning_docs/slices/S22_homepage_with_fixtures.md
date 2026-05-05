# Title
S22 Homepage With Fixtures

## Goal
Build the overview page against static fixture data.

## Why this slice exists
The homepage hierarchy should be validated before backend integration.

## Depends on
- `S21_design_system_primitives`

## Touches
- overview page
- fixture data
- homepage-specific components

## Inputs
- product hierarchy from `01_product_experience.md`
- fixture contract from `05_api_contract.md`

## Outputs
- homepage rendering from fixture JSON

## Implementation notes
- keep data local and deterministic
- focus on hierarchy and wording

## Tests required
- render test for hero, rankings, map placeholder/section, and explainer blocks

## Acceptance criteria
- homepage reads correctly without live backend data

## Non-goals
- real API integration
- live map

## Handoff to next slice
Next slice builds the map view with geometry fixtures.

## Completion notes

