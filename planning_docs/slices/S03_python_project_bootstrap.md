# Title
S03 Python Project Bootstrap

## Goal
Create the Python project foundations for the pipeline and API code, including test tooling and import structure.

## Why this slice exists
Later ETL, metrics, and API slices need a clean Python package layout and repeatable test runner.

## Depends on
- `S01_repo_structure`
- `S02_database_bootstrap`

## Touches
- Python package structure
- dependency configuration
- test runner configuration

## Inputs
- architecture in `04_architecture.md`

## Outputs
- pipeline package skeleton
- API package skeleton
- working unit test harness

## Implementation notes
- keep this slice to bootstrap and tooling
- do not implement GTFS parsing or HTTP endpoints yet

## Tests required
- one passing placeholder unit test
- import smoke test for both major Python packages

## Acceptance criteria
- Python tooling is runnable
- test harness works
- package structure is stable enough for later slices

## Non-goals
- endpoint behavior
- data modeling
- database schemas beyond connection readiness

## Handoff to next slice
Next slice ingests a tiny GTFS static fixture.

## Completion notes
- Changed files:
  - `pyproject.toml`
  - `.gitignore`
  - `README.md`
  - `api/README.md`
  - `pipeline/README.md`
  - `tests/README.md`
  - `api/src/muni_lta_api/__init__.py`
  - `api/src/muni_lta_api/app.py`
  - `api/src/muni_lta_api/config.py`
  - `pipeline/src/muni_lta_pipeline/__init__.py`
  - `pipeline/src/muni_lta_pipeline/config.py`
  - `tests/unit/test_python_bootstrap.py`
  - `tests/__init__.py`
  - `tests/unit/__init__.py`
  - `planning_docs/09_decisions.md`
  - `planning_docs/slices/S03_python_project_bootstrap.md`
- What changed:
  - added a root `pyproject.toml` to hold Python dependency metadata for the repo
  - initialized a local `.venv` so later slices have a project-scoped interpreter path
  - created separate `src` package skeletons for the API and pipeline code
  - added minimal environment-driven config helpers for both packages
  - added a lazy `FastAPI` application factory scaffold without creating endpoints
  - added a repository-level unit test file covering one placeholder test plus import smoke for both major packages
  - documented the bootstrap structure in the repo READMEs
  - recorded the Python bootstrap tooling choice in `planning_docs/09_decisions.md`
- Tests run:
  - `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
  - `.\.venv\Scripts\python.exe -c "from pathlib import Path; import sys; root = Path.cwd(); sys.path.insert(0, str(root / 'api' / 'src')); sys.path.insert(0, str(root / 'pipeline' / 'src')); import muni_lta_api, muni_lta_pipeline; print(muni_lta_api.__version__, muni_lta_pipeline.__version__)"`
- Results:
  - unit test harness passes
  - both Python packages import successfully
  - bootstrap package structure is ready for later slices without introducing GTFS logic or endpoints
- Follow-up issues:
  - the local `.venv` was created successfully, but pip seeding failed under the bundled Codex runtime because `ensurepip` could not write its temporary wheel files in this sandboxed environment
  - the `FastAPI` dependency is recorded in `pyproject.toml`, but local environments will still need a normal package-install step before executing the application factory itself
