# Agent Workflow

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

## Slice Ownership Rules
- one slice should prove one main thing
- agents should not broaden scope beyond the slice
- if a dependency is missing, document it rather than silently re-scoping downstream slices
- do not mark a slice complete without tests

## How To Claim A Slice
- confirm all dependencies listed in the slice doc are complete
- restate the goal in the implementation note or commit/PR description
- keep the change tightly aligned to the slice’s acceptance criteria

## Testing Rules
- run the tests listed in the slice doc
- if a listed test cannot run, document exactly why
- prefer local, narrow tests over broad end-to-end work during early slices

## Documentation Update Rules
If a slice changes any of these contracts, update the paired doc in the same change:
- API shape -> `05_api_contract.md`
- data model -> `06_data_model.md`
- public metric wording -> `01_product_experience.md` and `02_methodology.md`
- architecture decision -> `09_decisions.md`
- deferred work -> `10_backlog.md`

## Completion Notes
Each agent should fill the `Completion notes` section in the slice doc with:
- what changed
- what tests were run
- what passed
- any known limitations or follow-up issues

