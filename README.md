# HERMES Agent — Secure Local Foundation

This project is a local, deny-by-default controller for Nous Hermes function calls. It keeps model inference separate from tool authorization and execution.

## Current status

- `PASS-LOCAL`: the pinned upstream reference is present at `upstream/Hermes-Function-Calling` (`ea3c4723e4cefdac760d483ccac6c8a428c95ab8`).
- `PASS-LOCAL`: strict tool parsing, policy decisions, workspace boundaries, audit-chain verification, and sandbox-command construction are covered by local tests.
- `PARTIAL`: Docker Desktop can isolate a Python task with no network and dropped capabilities, but this host does not provide gVisor.
- `NO-GO MODEL DOWNLOAD`: only about 10 GiB was available during setup. The official Hermes 3 BF16 checkpoint and a reliable inference environment must not be downloaded until the model gate is cleared.

The upstream repository is a reference implementation. It is not used as the authorization or execution boundary because its demo tools include direct execution and live network behavior.

## What is implemented

```text
model tool-call payload
  -> strict Pydantic parse
  -> semantic policy decision
  -> explicit human approval for Python execution
  -> fixed Docker command (no shell, no network)
  -> normalized result and tamper-evident audit event
```

Only these initial tools exist:

- `workspace_list` — list non-sensitive files under the configured workspace.
- `workspace_read_text` — read a bounded UTF-8 text file under the workspace.
- `sandbox_run_python` — requires a trusted, out-of-band approval before it may reach the isolated executor.

There is deliberately no free-form shell, arbitrary HTTP client, browser, database query, or write-to-source tool.

## Controller setup

Use the native arm64 Python 3.12 installed on this Mac, not the default Python 3.14. Because this project resides in an iCloud-backed folder, its canonical controller environment is local to the machine at `~/.venvs/hermes-agent`:

```bash
HERMES_VENV=~/.venvs/hermes-agent
python3.12 -m venv "$HERMES_VENV"
"$HERMES_VENV/bin/python" -m pip install -r requirements-controller.lock
"$HERMES_VENV/bin/python" -m pip install --no-deps --no-build-isolation .
"$HERMES_VENV/bin/python" -m pytest
"$HERMES_VENV/bin/python" scripts/function_call_smoke.py
```

The smoke check validates a harmless `workspace_list` function-call payload. `scripts/verify_sandbox.py` runs only after the optional Docker image is built; it verifies that a trusted, approved Python task cannot reach an external IP. Neither check runs a model.

## Terminal shortcut

Open a new terminal and use `hermes`. It shows the current safe status by default. Available commands are `hermes test`, `hermes smoke`, `hermes sandbox`, `hermes tools`, and `hermes model-gate`. It intentionally refuses `serve`, `chat`, and `run` until the model gate is cleared. The previous legacy Docker command remains available as `hermes-legacy`.

## Inference is a separate gate

See [docs/MODEL_GATE.md](docs/MODEL_GATE.md). Inference must use its own Python 3.12 environment and a model store outside this iCloud-synchronised workspace. After the gate passes, bind any vLLM/vLLM-Metal server to `127.0.0.1` only and retain the controller as the only component allowed to decide whether a tool call can run.

## Security documents

- [Threat model](docs/THREAT_MODEL.md)
- [Operations and verification](docs/OPERATIONS.md)
- [Model and capacity gate](docs/MODEL_GATE.md)
- [Local verification record](docs/VERIFICATION.md)
- [Upstream provenance](docs/UPSTREAM_PROVENANCE.md)

## Upstream provenance

`upstream/Hermes-Function-Calling` is a shallow clone of the official Nous Research repository at the verified commit above. It remains separate from this controller so its legacy examples and dependencies cannot silently broaden the runtime’s permissions.
