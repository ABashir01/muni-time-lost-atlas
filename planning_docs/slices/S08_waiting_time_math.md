# Title
S08 Waiting Time Math

## Goal
Implement and test the waiting-time formulas that convert headway observations into expected passenger waiting and waiting loss.

## Why this slice exists
This is the mathematical foundation of the rider-facing waiting-loss component.

## Depends on
- `S07_scheduled_observed_join`

## Touches
- Python metric library
- unit tests for headway and waiting formulas
- methodology references if implementation clarifies wording

## Inputs
- formulas from `02_methodology.md`
- observed headway sequences
- scheduled headway sequences

## Outputs
- tested waiting-time functions
- tested waiting-loss function

## Implementation notes
- prove the equivalent formula forms match
- keep function interfaces small and deterministic

## Tests required
- equivalence test for:
  - `E(H)/2 + V(H)/(2E(H))`
  - `E(H^2)/(2E(H))`
  - sample-form approximation
- clamp-to-zero behavior for waiting loss
- at least one worked example

## Acceptance criteria
- waiting-time math is implemented and tested
- methodology and implementation agree

## Non-goals
- route-level aggregation
- API endpoints
- frontend rendering

## Handoff to next slice
Next slice implements in-vehicle travel loss math.

## Completion notes

