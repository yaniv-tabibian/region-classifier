# Contributing

Thanks for looking at the project. It is small; the workflow is simple.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
make install            # pip install -e ".[viz,dev]"
```

## Before you push
Everything CI enforces can be run locally:
```bash
make lint               # ruff + black --check + mypy
make test               # pytest
```
`make format` auto-applies ruff fixes and black.

## Conventions
- Python >= 3.10, fully type-hinted (the package ships `py.typed`).
- Formatting: **black**; linting: **ruff**; types: **mypy** (all wired in `pyproject.toml`).
- Keep the classifier dependency-light and O(1) per sample.
- Add/adjust tests under `tests/` for any behaviour change; keep the suite green.
