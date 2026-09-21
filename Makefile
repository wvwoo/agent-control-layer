# All targets run through uv with the locked environment (uv.lock). No absolute paths.
.PHONY: verify test lint type audit smoke sandbox export-tools

verify: lint type test audit

test:
	uv run --locked pytest

lint:
	uv run --locked ruff check .
	uv run --locked ruff format --check .

type:
	uv run --locked mypy

audit:
	uv export --locked --no-dev --no-emit-project --format requirements-txt > .audit-requirements.txt
	uv run --locked pip-audit --strict --requirement .audit-requirements.txt
	rm -f .audit-requirements.txt

smoke:
	uv run --locked python scripts/function_call_smoke.py

sandbox:
	uv run --locked python scripts/verify_sandbox.py

export-tools:
	uv run --locked python scripts/export_tool_registry.py
