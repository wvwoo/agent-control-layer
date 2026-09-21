# Local verification record — 2026-08-23

## `PASS-LOCAL`

- Controller tests: `16 passed` with Python `3.12.13` from the local, non-iCloud controller environment `.venv`.
- Dependency consistency: `pip check` returned `No broken requirements found`.
- Synthetic strict Function Calling: `workspace_list` parsed, policy-authorized, dispatched, and recorded in a valid audit chain.
- Registry parity: runtime-emitted OpenAI tool schemas exactly match `config/tool_registry.json`.
- Docker image: `hermes-sandbox:dev` image `sha256:164944d4e92945b3056f9a383285dc6410c5cf2bf364eadd915140f2dcd2f46c`, configured as UID/GID `10001:10001`.
- Real sandbox check: an approved task emitted `SECRET_ABSENT`, `WORKSPACE_READ_ONLY`, and `EGRESS_BLOCKED`.
- Upstream source: official Nous reference cloned clean at `ea3c4723e4cefdac760d483ccac6c8a428c95ab8`.
- Terminal launcher: a fresh interactive `zsh` resolves `hermes` to `<local path>`; `hermes smoke` returned an `ok` controller result and `hermes test` exited successfully.

## `PARTIAL`

- Docker Desktop provides the checked `runc` runtime and seccomp support, but not gVisor. The local result is hardened container isolation, not a production gVisor assurance.

## `NOT_RUN`

- vLLM-Metal installation.
- Hermes model download, server startup, `/health`, `/v1/models`, and model-generated function calls.
- Web search, browser, database, API, shell, and workspace-write capabilities; they remain disabled by policy.

## `NO-GO MODEL DOWNLOAD`

At the final capacity check, the volume had `10,111,080 KiB` free (about 9.6 GiB). That fails the project’s 35 GiB model gate and is below the size of the requested official BF16 checkpoint alone.

## Integrity references

| File | SHA-256 |
|---|---|
| `config/policy.json` | `c01cc6f752aa631be9bde22d167c58c044fc58ec13fc4807c846152e7a98ba78` |
| `config/tool_registry.json` | `65e028806f74a70b93c64f416c2fadbda201979a9608f5918c8d676ba712fd4e` |
| `pyproject.toml` | `15f24e526983b53e669a1790a796cc632f4f9b628c3ebba7c08dcd8b8427dcdc` |
| `requirements-controller.lock` | `bde00be2bb7cd1f82f01b76feea221bb50c2bf095c1ebb0fa0e19eee5dfa0424` |
