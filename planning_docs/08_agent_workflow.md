# Agent Workflow

## Roles
- the main Codex thread is the central planner, reviewer, and release manager
- spawned agents are worker agents only
- worker agents should not propose the next overall plan, choose the next slice, or act as release managers
- worker agents should complete the assigned slice, document the result, and stop

## What Every Agent Reads First
Before implementing any slice, an agent should read:
1. [00_project_brief.md](./00_project_brief.md)
2. [01_product_experience.md](./01_product_experience.md)
3. [02_methodology.md](./02_methodology.md)
4. the assigned slice doc in `planning_docs/slices/`

Agents should also read:
- [05_api_contract.md](./05_api_contract.md) if touching API or fixtures
- [06_data_model.md](./06_data_model.md) if touching ingest, transforms, or DB models
- [09_decisions.md](./09_decisions.md) if there is any ambiguity about prior choices
- [11_design_reference.md](./11_design_reference.md) for frontend work

## Slice Ownership Rules
- one completed work unit should prove one meaningful subsystem milestone
- agents should not broaden scope beyond the slice
- if a dependency is missing, document it rather than silently re-scoping downstream slices
- do not mark a slice complete without tests

For future work after `S07`:
- use the bundle docs `B1` through `B8` as the source of truth
- the legacy future slice docs `S08` through `S35` are superseded and should not be implemented directly

## How To Claim A Slice
- confirm all dependencies listed in the slice doc are complete
- restate the goal in the implementation note or commit/PR description
- keep the change tightly aligned to the slice's acceptance criteria

## Testing Rules
- run the tests listed in the slice or bundle doc
- if a listed test cannot run, document exactly why
- prefer local, narrow tests over broad end-to-end work during early slices

For future bundles, use lean validation by default:
- one primary test suite per bundle
- one regression suite only when the bundle materially touches a prior subsystem
- live `511` checks only when the bundle directly depends on live `511` behavior
- DB-mutating integration suites must run sequentially, never in parallel, against the shared local Postgres instance

## Documentation Update Rules
If a slice changes any of these contracts, update the paired doc in the same change:
- API shape -> `05_api_contract.md`
- data model -> `06_data_model.md`
- public metric wording -> `01_product_experience.md` and `02_methodology.md`
- frontend visual contract -> `01_product_experience.md` and `11_design_reference.md`
- architecture decision -> `09_decisions.md`
- deferred work -> `10_backlog.md`

For frontend bundles, acceptance should include a screenshot-based review against the approved design reference, not just functional or DOM-level checks.

## Completion Notes
Each agent should fill the `Completion notes` section in the slice doc with:
- what changed
- what tests were run
- what passed
- any known limitations or follow-up issues

For bundles, use the same completion-notes pattern inside the bundle doc.

## Worker Completion Signal
When a worker agent finishes a slice, it should send one final message and then stop. That final message should include:
- the slice id and title
- a flat list of changed files
- tests run
- pass/fail status
- blockers or known limitations
- whether the slice is ready for central review
- a single sentinel line at the top so completion is easy to detect programmatically and visually

Use this shape:

```text
WORKER_DONE: SXX_<slice_name>

Completed SXX_<slice_name> and stopped.

Changed files:
- ...

Tests run:
- ...

Results:
- ...

Blockers / follow-up:
- ...
```

For bundle work, replace `SXX_<slice_name>` with the bundle id, for example:

```text
WORKER_DONE: B1_core_metrics_bundle
```

Do not continue with the next slice automatically. Do not restate the overall roadmap. Wait for the central planner to review, request revisions, accept, and handle git.

## Central Thread Handling
The central planner should treat either of these as valid completion signals:
- a successful `wait_agent` return with the worker's final message
- an asynchronous subagent notification containing the worker's final `WORKER_DONE:` message

The central planner should not rely on short polling timeouts alone to determine whether a worker is still running or finished.
