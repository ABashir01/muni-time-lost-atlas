# Title
S09 In-Vehicle Loss Math

## Goal
Implement and test the in-vehicle runtime-loss calculations using observed vs baseline trip times.

## Why this slice exists
The product headline metric depends on combining waiting loss with onboard travel loss.

## Depends on
- `S07_scheduled_observed_join`

## Touches
- Python metric library
- runtime-loss unit tests

## Inputs
- formulas from `02_methodology.md`
- observed trip times from joined data
- scheduled baseline trip times

## Outputs
- tested runtime-loss functions for segment and full-trip calculations

## Implementation notes
- use scheduled trip time as the MVP baseline
- clamp negative loss to zero
- test both segment and full-trip variants

## Tests required
- exact runtime-difference tests
- zero-floor behavior
- segment-level and full-trip examples

## Acceptance criteria
- in-vehicle loss math is implemented and tested
- baseline choice matches documented methodology

## Non-goals
- route-level aggregate metric
- map endpoint work
- passenger weighting

## Handoff to next slice
Next slice combines waiting and runtime into the route-level typical-trip metric.

## Completion notes

