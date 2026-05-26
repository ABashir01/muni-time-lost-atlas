# B8 Worker Prompt

Use this prompt for the eventual `B8` implementation worker.

```text
You are a worker agent, not the central planner. You are not alone in the codebase.

Your job is to implement the B8 editorial visual-system bundle so the major
public surfaces feel like one product family anchored to the accepted homepage.

Read first:
- C:\Users\ahadb\Documents\New project 3\planning_docs\slices\B8_product_hardening_bundle.md
- C:\Users\ahadb\Documents\New project 3\planning_docs\17_b8_design_reference_addendum.md
- C:\Users\ahadb\Documents\New project 3\planning_docs\18_b8_visual_system.md
- C:\Users\ahadb\Documents\New project 3\planning_docs\19_b8_surface_layout_spec.md
- C:\Users\ahadb\Documents\New project 3\planning_docs\20_b8_rebuild_contract.md
- C:\Users\ahadb\Documents\New project 3\planning_docs\mockups\homepage-light-mode.png
- C:\Users\ahadb\Documents\New project 3\planning_docs\mockups\rankings-light-mode.svg
- C:\Users\ahadb\Documents\New project 3\planning_docs\mockups\map-light-mode.svg
- C:\Users\ahadb\Documents\New project 3\planning_docs\mockups\route-detail-light-mode.svg
- C:\Users\ahadb\Documents\New project 3\planning_docs\mockups\compare-light-alignment.svg
- C:\Users\ahadb\Documents\New project 3\planning_docs\mockups\typography-comparison-board.svg

Primary review breakpoint:
- 1440x900

Hard instruction:
- If the current rankings, map, or route-detail page structure conflicts with
  the contract, scrap it and rebuild it from the top down.
- Do not preserve generic app-shell structures just because they already exist.

Scope:
- homepage polish only
- add a dedicated full rankings page
- redesign full map page
- redesign route detail page
- light compare-page alignment to the shared system
- shared masthead / color / type / button / badge language

Do not:
- add direction-level functionality
- add date-range functionality
- add fake placeholders for future controls
- drift into generic dashboard UI
- turn the map page into a default GIS app shell

Typography:
- treat the current condensed display-forward system as the chosen default
- do not switch the implementation to Helvetica-first

Explicit polish tasks:
- fix route badge sizing for labels like LOWL
- fix compare-strip motif lines leaking into the compare button
- fix compare button yellow mismatch
- reduce Explore the Map button size if it still reads oversized

Validation:
- run the minimum relevant frontend tests
- produce screenshots at 1440x900 for homepage, rankings, map, and route detail
- include a brutally honest mismatch list

When done, stop and send one final message beginning exactly with:
WORKER_DONE: B8_editorial_visual_system_bundle

Then include:
- changed files
- tests run
- screenshot produced
- results
- remaining mismatches
```
