PYTHON ?= python

.PHONY: install test lint demo smoke audit

install:
	$(PYTHON) -m pip install -e '.[all]'

test:
	pytest -q

lint:
	ruff check .

demo:
	research-template demo --out artifacts/demo --plots --ml

smoke:
	research-template demo --out artifacts/smoke

audit:
	research-template audit --root .
