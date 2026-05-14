# Contributing

## Branch policy

- `main` is protected. Direct pushes blocked once branch protection is enabled.
- All work happens on feature branches named `phase<N>/<short-topic>` — e.g. `phase1/heat-cost-field`, `phase2/variable-matrix`, `phase3/ab-runner`.
- Open a pull request to `main` and request review from at least one other team member before merging.

## Commit message format

Conventional commits:

```
<type>: <description>

<optional body>
```

Types: `feat`, `fix`, `refactor`, `docs`, `data`, `sim`, `analysis`, `chore`.

Example: `sim: add heat-cost field to ABM edge attributes`

## Review checklist (before opening a PR)

- [ ] The change references the phase it belongs to (in the PR title or description)
- [ ] New data files are listed in `data/README.md` with source, CRS, and date
- [ ] Simulation runs include a `run_config.json` with seed and parameters
- [ ] Notebooks have outputs cleared (`nbstripout`) before commit
- [ ] No raw API keys or credentials are committed (use `.env` — gitignored)
- [ ] Large binaries (>50 MB) go to the OneDrive shared folder, not Git

## Decision log

Material decisions live as ADR-style notes in `docs/decisions/NNNN-<topic>.md`. Open a PR for the decision; merge after team discussion.

## Issue labels

- `phase-1`, `phase-2`, `phase-3` — which phase the issue belongs to
- `area-abm`, `area-design`, `area-data`, `area-analysis` — functional area
- `blocker` — blocks other work
- `good-first-task` — onboarding-friendly

## Code style

- Python: PEP 8, type hints where they aid clarity, `ruff` for linting (config in `pyproject.toml` once added)
- Notebooks: keep exploratory; promote stable analysis to `analysis/*.py` modules
- Markdown: ATX headings, no trailing whitespace, lines wrapped at ~100 chars

## Adding new team members

Admins add via Settings → Collaborators on GitHub. New members are encouraged to start with a `good-first-task` issue.
