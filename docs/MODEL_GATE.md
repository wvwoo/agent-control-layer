# Model and capacity gate

## Status: `NO-GO MODEL DOWNLOAD`

At setup time this Mac had only about 10 GiB free. The official `NousResearch/Hermes-3-Llama-3.1-8B` BF16 checkpoint is larger than that before cache, runtime, and Docker overhead are considered. Do not put model weights in this iCloud-synchronised project folder.

## Preconditions

1. Free at least 35 GiB on a local, non-synchronised volume and choose an explicit model-store path.
2. Keep the controller environment on native arm64 Python 3.12. The default `python3` is 3.14 and is not the selected vLLM-Metal path.
3. Choose and record one model provenance:
   - Official Nous BF16 model: official provenance but too large for the present capacity.
   - A 4-bit MLX community conversion: smaller, but a separate third-party model decision that requires explicit owner approval and a pinned revision.
4. Install inference dependencies in a separate environment from the controller. Do not mix the upstream demo’s older CUDA-oriented requirements with vLLM/vLLM-Metal.
5. Pin the vLLM release and the matching Hermes tool chat template before serving.

## Intended serving boundary after approval

Bind inference only to loopback:

```text
vLLM/vLLM-Metal server: 127.0.0.1 only
        ↓ OpenAI-compatible tool calls
secure controller: schema + policy + approval + audit
        ↓
offline Docker executor
```

The future server invocation must use the current `vllm serve` interface with `--enable-auto-tool-choice`, `--tool-call-parser hermes`, a version-matched Hermes template, and a pinned model revision. The parser only translates model output; it grants no execution authority.

## Required smoke test after the gate clears

1. Verify `/health` and `/v1/models` over loopback.
2. Force a harmless strict `add(a, b)` tool call and validate exactly one returned call.
3. Repeat with automatic choice, then return a `tool`-role result and verify a natural-language completion.
4. Run negative cases: unknown tool, extra property, malformed JSON, traversal, prompt injection in a tool result, and an attempted sandbox network connection.
