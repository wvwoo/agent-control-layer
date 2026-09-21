# Upstream provenance

| Field | Evidence |
|---|---|
| Repository | `https://github.com/NousResearch/Hermes-Function-Calling.git` |
| Resolved commit | `ea3c4723e4cefdac760d483ccac6c8a428c95ab8` |
| Tree | `232dbef77eb802552f62c1c0be5e30bf40678bc0` |
| Local location | `upstream/Hermes-Function-Calling` |
| Check date | 2026-08-23 |
| Working tree at check | clean |

The upstream clone is reference material only. Its README documents a Transformers-based Hermes 2 example, and its demo functions include direct execution and network behavior. This project does not call those functions or install the upstream requirements into its controller environment.

The controller instead implements a separate, much smaller registry and security boundary. Replacing the reference, model, or chat template later requires a new provenance entry, a pinned revision, and fresh policy/integration verification.
