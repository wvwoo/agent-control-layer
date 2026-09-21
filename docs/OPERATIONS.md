# Operations and verification

## Local controller checks

From a new terminal, the short form is available:

```bash
hermes
hermes test
hermes smoke
hermes sandbox
```

```bash
HERMES_PYTHON=~/.venvs/hermes-agent/bin/python
"$HERMES_PYTHON" -m pytest
"$HERMES_PYTHON" scripts/function_call_smoke.py
"$HERMES_PYTHON" scripts/export_tool_registry.py
```

`pytest` verifies strict schemas, policy denial, path containment, redaction/audit integrity, untrusted-data role separation, and the exact Docker hardening flags. `scripts/function_call_smoke.py` additionally exercises the model-facing controller with a synthetic harmless payload.

## Building the optional sandbox image

Only after reviewing available disk capacity:

```bash
docker build -t hermes-sandbox:dev docker/sandbox
"$HERMES_PYTHON" scripts/verify_sandbox.py
```

The sandbox verifier uses a trusted, explicit test approval, confirms a host secret is absent, attempts a workspace write, and attempts to connect to `1.1.1.1:53`; any success is a failure. It is an evidence check for the local Docker path, not a production gVisor claim. The controller’s Docker executor is intentionally not triggered by model output alone. A trusted host application must attach a real approval identifier before it may call it.

## Operational prohibitions

- Never pass host environment variables, API keys, `~/.ssh`, `.git`, or the Docker socket into the sandbox.
- Never bind inference to `0.0.0.0` without a separately reviewed authentication and network design.
- Never add a raw shell, URL fetch, browser, database, or workspace-write tool as a shortcut.
- Never treat tool-parser output, `strict: true`, or a model confirmation as authorization.
