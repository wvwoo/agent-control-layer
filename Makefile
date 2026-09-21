HERMES_VENV ?= ~/.venvs/hermes-agent
PYTHON ?= $(HERMES_VENV)/bin/python

.PHONY: test smoke sandbox export-tools

test:
	$(PYTHON) -m pytest

smoke:
	$(PYTHON) scripts/function_call_smoke.py

sandbox:
	$(PYTHON) scripts/verify_sandbox.py

export-tools:
	$(PYTHON) scripts/export_tool_registry.py
