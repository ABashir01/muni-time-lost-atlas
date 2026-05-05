# Title
S10 Route-Level Typical Trip Metric

## Goal
Define and test the first route-level aggregate for `Typical extra time on a full one-way trip`.

## Why this slice exists
This is the MVP headline metric and the first stable output that downstream API and UI work will depend on.

## Depends on
- `S08_waiting_time_math`
- `S09_in_vehicle_loss_math`

## Touches
- aggregate metric library
- route-level tests
- methodology or product wording if clarification is required

## Inputs
- waiting-loss outputs
- in-vehicle-loss outputs
- route/time-window grouping assumptions

## Outputs
- tested route-level metric function or query definition

## Implementation notes
- combine route-level waiting loss and route-level in-vehicle loss
- use a median-based aggregate for runtime loss
- keep public wording aligned with the final function name/behavior

## Tests required
- route-level aggregate test using fixture data
- tests confirming total = waiting + in-vehicle components
- tests for stable behavior under outlier trips

## Acceptance criteria
- the route-level headline metric is mathematically defined and tested
- downstream slices can treat this metric as a stable contract

## Non-goals
- full ranking mart
- endpoint work
- frontend integration

## Handoff to next slice
Next slice materializes the first metrics mart for ranking routes by time window.

## Completion notes

