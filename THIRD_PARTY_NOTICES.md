# Third-party notices

## Upstream reference (not distributed)
The tool-call format and protocol shape were studied from an open-source function-calling reference
repository (MIT License), pinned at commit `ea3c4723e4cefdac760d483ccac6c8a428c95ab8`.
Details, including the repository URL, are in `docs/UPSTREAM_PROVENANCE.md`.
No code from that repository is included in this package; the reference clone is kept outside version control (`upstream/`).
Its MIT licence text travels with the reference clone (`upstream/*/LICENSE`) and must accompany any future reuse.

## Runtime dependencies
| Package | Licence |
|---|---|
| pydantic, pydantic-core | MIT |
| annotated-types | MIT |
| typing-extensions, typing-inspection | PSF-2.0 / MIT |

The full dependency list with versions is in `uv.lock` and the CycloneDX SBOM produced by CI (`sbom.cdx.json`).
