.PHONY: install run test lint format demo clean

install:  ## install package + dev/viz extras (editable)
	pip install -e ".[viz,dev]"

run:      ## run the live console demo (bundled default scenario)
	region-sim

test:     ## run the test suite
	pytest -q

lint:     ## lint + format-check + type-check (same as CI)
	ruff check . && black --check src tests && mypy

format:   ## auto-fix lint and format
	ruff check --fix . && black src tests

demo:     ## render the demo GIF (needs the viz extra)
	region-sim --config configs/two_circles.yaml --save-gif examples/demo.gif --duration 30

clean:    ## remove caches and build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
