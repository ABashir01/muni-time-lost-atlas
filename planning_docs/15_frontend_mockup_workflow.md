# Frontend Mockup Workflow

## Purpose
This note captures the pattern used in this project for turning a homepage mockup into a strict implementation workflow for frontend workers.

## Use this pattern when
- a frontend page should closely match a specific mockup
- generic “make it look like this” prompting is drifting
- a worker keeps preserving the wrong layout
- the page needs hard ratios and width-occupancy rules

## Workflow
1. establish the exact approved mockup asset
2. pick a primary review breakpoint
3. create the contract docs:
   - `11_design_reference.md`
   - `12_frontend_design_system.md`
   - `13_homepage_layout_spec.md`
   - `14_homepage_rebuild_contract.md`
4. if the page is still visually unstable, split the work:
   - visual lock first
   - broader static completion second
5. write a worker-only prompt that:
   - references the exact asset path
   - references the docs above
   - permits scrapping the current layout
   - requires a screenshot and mismatch list
6. review screenshots against the mockup before accepting the frontend pass

## Current project-specific defaults
- primary breakpoint: `1440x900`
- homepage top-level ratios:
  - header: `8%`
  - hero: `43%`
  - rankings + explainer row: `38%`
  - compare footer strip: `11%`
- hero split:
  - left: `38%`
  - right: `62%`

## Reusable skill
A reusable local Codex skill was created for this pattern:
- `frontend-mockup-contract`

It lives in the local skills directory and is intended to be reused for future frontend visual-lock tasks.
