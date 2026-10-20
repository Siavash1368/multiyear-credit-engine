# Contributing and development workflow

## Workflow: notebook → engine

1. Develop a component in its notebook (`notebooks/NN_*.ipynb`).
2. When it works, move each function into its module under `src/creditengine/`.
3. Add a pytest test under `tests/unit/` for every function moved.
4. Change the notebook to import from the package instead of defining the function itself.
5. Update `docs/assumption_register.md`, `docs/limitations.md` and the README status table.

## Conventions

| Item | Convention |
|---|---|
| Branches | `feature/nbNN-short-name`, `fix/short-name` |
| Commits | Imperative mood: "Add migration thresholds" |
| Code style | `ruff` (lint and import order); line length 100 |
| Types | Type hints on all public functions; `mypy` clean |
| Docstrings | NumPy style, with units and the equation implemented |
| Randomness | Every simulation takes an explicit `seed` |
| Notebooks | Outputs kept so results are readable on GitHub |
| Assumptions | Every hard-coded number has an ID in the assumption register |

## Checks before a commit

```bash
ruff check src tests
mypy src
pytest -m "not slow"
```
