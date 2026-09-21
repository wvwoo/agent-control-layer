# Threat model

## Trust boundaries

The language model is not an authority. A model response may be malformed, maliciously induced, or wrong. Web pages, file contents, tool results, screenshots, and user-provided documents are all untrusted data.

```text
untrusted model/data
  -> strict tool-call parser
  -> semantic policy engine
  -> real human approval, when required
  -> isolated executor
  -> bounded/redacted result
  -> append-only hash-chained audit event
```

The controller owns policy, approval state, workspace roots, and audit storage. Neither the model nor an executed tool receives those capabilities.

## Initial capability boundary

| Capability | Initial status | Boundary |
|---|---|---|
| List/read text files | Enabled | Relative paths only; sensitive subtrees and symlink escapes are denied. |
| Python execution | Approval-gated | Docker command is fixed, offline, non-root, read-only, and has resource limits. |
| Shell | Disabled | No `shell=True`, `bash -c`, argv passthrough, or Docker socket exposure. |
| Web/API/browser | Disabled | Future implementation must use a separate egress gateway and SSRF policy. |
| Database | Disabled | Future connectors must be service-specific; raw SQL is not a tool. |
| Write operations | Disabled | Outputs and source modifications require a separate, user-approved capability. |

## Prompt-injection defence

Tool data is retained as a `tool`-role payload with a visible `UNTRUSTED_EXTERNAL_DATA` boundary. It is never promoted to a system/developer instruction, never allowed to activate a capability, and never allowed to supply an approval token. Detection of suspicious instructions is informative only; deterministic policy enforcement is the protection.

## Path defence

The workspace gateway rejects absolute paths, `..`, NUL bytes, sensitive path components, and any symlink in the requested path. It resolves the candidate and verifies containment below the configured root. The initial release is read-only; any future write operation must use directory-file-descriptor techniques and `O_NOFOLLOW` to close time-of-check/time-of-use races.

## Egress and SSRF

The local Python sandbox runs with Docker `--network none`. A future web gateway must be separate from the sandbox and workspace, default-deny egress, restrict HTTP(S) destinations by allowlist, reject loopback/private/link-local/metadata ranges, resolve and revalidate DNS before every redirect, limit redirects/bytes/time, and redact credentials.

## Sandbox limits

The command builder requires `--network none`, `--read-only`, `--cap-drop ALL`, `no-new-privileges`, a non-root UID, `pids-limit`, CPU/RAM limits, a no-exec temporary filesystem, a read-only workspace mount, and no Docker socket. Docker Desktop on this Mac uses `runc`, not gVisor; this is `PARTIAL` isolation and must not be described as a gVisor boundary.

## Audit boundary

Audit records store hashes of redacted arguments, policy decisions, approval identifiers, and chained event hashes. They never contain secret values. Local hash chains detect tampering but cannot protect against an operator with full host access; production-grade non-repudiation needs a protected signing key or remote checkpoint.
