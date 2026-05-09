# Methodology

## Public Metric Definition
The MVP headline metric is:

- `Typical extra time on a full one-way trip`

Short label:
- `Typical trip: +X.X min`

This metric represents extra minutes lost because service is less dependable than the baseline.

It is split into:
- `extra waiting time`
- `extra in-vehicle travel time`

## What "Time Lost" Means
Riders lose time in two ways:
- before boarding, when headways are longer or more irregular than expected
- after boarding, when vehicles take longer than the baseline trip time

The site is translating operations into rider consequences, not just publishing operations jargon.

## Waiting-Time Math
For frequent service and random passenger arrival, the expected wait time can be written as:

- `E(W) = E(H)/2 + V(H)/(2E(H))`

Equivalent forms:
- `E(W) = E(H^2)/(2E(H))`
- `E(W) ~= sum(h_i^2) / (2 * sum(h_i))`

Where:
- `W` is waiting time
- `H` is headway
- `E(H)` is mean headway
- `V(H)` is headway variance

This matters because irregular service increases effective passenger waiting even when the mean headway looks acceptable.

## Waiting Loss
Define extra waiting time as:

- `L_wait = max(0, W_obs - W_base)`

For MVP, use scheduled service as the baseline:

- `W_base = W_sched`

So:

- `L_wait = max(0, W_obs - W_sched)`

### First Implementation Scope
For the first SQL metric layer, waiting loss is measured from matched first-stop events only.

Implementation rule:
- identify the first scheduled stop on each trip
- keep only trips whose first stop matched exactly in `canonical.observed_stop_events`
- compute consecutive headways only when both adjacent scheduled trips have matched first-stop observations

This keeps the first waiting metric conservative:
- no fuzzy reconciliation
- no inferred headways across missing trips
- unmatched rows stay visible in audit counts but do not enter the waiting-loss numerator

## In-Vehicle Loss
For a trip from stop `a` to stop `b` on trip `k`:

- `T_obs(k,a,b) = t_obs_arr(k,b) - t_obs_dep(k,a)`
- `T_base(k,a,b) = t_base_arr(k,b) - t_base_dep(k,a)`

Then:

- `L_veh(k,a,b) = max(0, T_obs(k,a,b) - T_base(k,a,b))`

This means:
- if the vehicle took longer than baseline, the difference is time lost
- if it took less time than baseline, the public-facing loss is clamped at zero

### First Implementation Scope
The current joined model exposes observed arrivals, not observed departures.

For the first SQL metric layer, full-trip in-vehicle loss is therefore measured as:
- observed arrival at the matched last stop
- minus observed arrival at the matched first stop

with baseline:
- scheduled arrival at the last stop
- minus scheduled arrival at the first stop

The first implementation includes only trips where:
- the first scheduled stop matched exactly
- the last scheduled stop matched exactly

This is a narrow proxy for full one-way trip delay on the current joined model.

## Baseline Choice
Possible baselines:
- scheduled trip time
- best typical observed trip time
- dependable route-specific trip time

For MVP, use:
- `scheduled trip time`

Reason:
- it is easier to explain publicly
- it is available directly from GTFS
- it keeps the methodology stable during early implementation

## Route-Level Aggregate
For route-level reporting:

- `L_veh(route,W) = median over trips k in W of max(0, T_obs_full(k) - T_base_full(k))`

Use median instead of mean for MVP because it is less distorted by extreme trips.

Then define the headline route metric as:

- `L_typical(route,W) = L_wait(route,W) + L_veh(route,W)`

For the first SQL bundle:
- `L_wait(route,W)` is computed from matched first-stop headways only
- `L_veh(route,W)` is the median full-trip loss across matched terminal-to-terminal trips only
- route summaries currently materialize one supported window: `all_day`
- direction and hour summaries provide the first breakdowns beneath that route window

## What This Metric Does Not Claim
The MVP metric does not claim to be:
- a passenger-weighted population average
- a perfect substitute for origin-destination rider burden
- a causal claim about why the route is slow

The first implementation also does not claim to:
- cover unmatched historic observation rows
- infer missing trips or missing stop matches
- capture bunching as a separate published metric yet

It is a route-level typical-trip estimate.

## Passenger Weighting
If future ridership data becomes available, the project could later move toward a passenger-weighted metric. If that happens, the public language must change from:
- `Typical trip: +X.X min`

to something like:
- `Average rider loss: +X.X min`

This is out of MVP scope.

## Public Terminology Rules
Prefer:
- `Typical trip`
- `waiting loss`
- `in-vehicle loss`
- `worst segment`
- `worst time window`

Avoid as homepage language:
- `headway variance`
- `schedule adherence index`
- `runtime ratio`

## Core Sources
- TRB paper citing the classic waiting-time result:
  - [Evaluating Potential Effectiveness of Headway Control Strategies for Transit Systems](https://onlinepubs.trb.org/Onlinepubs/trr/1980/746/746-005.pdf)
- 511 transit data:
  - [https://511.org/open-data/transit](https://511.org/open-data/transit)
- 511 open data FAQ:
  - [https://511.org/about/faq/open-data](https://511.org/about/faq/open-data)
