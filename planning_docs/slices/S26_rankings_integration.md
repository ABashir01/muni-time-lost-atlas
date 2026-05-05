# Title
S26 Rankings Integration

## Goal
Replace homepage ranking fixtures with live API-backed data.

## Why this slice exists
This is the first frontend-to-backend integration point for the public product.

## Depends on
- `S16_rankings_endpoint`
- `S22_homepage_with_fixtures`

## Touches
- homepage data fetching
- loading/error handling
- response validation

## Inputs
- live rankings endpoint
- fixture-backed homepage layout

## Outputs
- live homepage rankings

## Implementation notes
- keep route cards identical to fixture version where possible
- handle loading and no-data states explicitly

## Tests required
- fetch/render integration test
- error-state test

## Acceptance criteria
- homepage rankings render from the real API without changing the public contract

## Non-goals
- route page live integration
- map integration

## Handoff to next slice
Next slice wires route detail to the API.

## Completion notes

