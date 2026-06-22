# Design

→ See [AGENTS.md](../AGENTS.md) for the full repository map.
→ See [design-docs/index.md](design-docs/index.md) for individual design docs.
→ See [design-docs/core-beliefs.md](design-docs/core-beliefs.md) for operating principles.

---

## Design principles

### Pipeline over monolith
Each skill does one thing. `ingestion` does not extract. `extract` does not
build the KB. Composability is preferred over convenience shortcuts that
skip stages.

### Deterministic outputs
Given the same source and the same model/version, `extract` should produce
the same output. Nondeterminism is a bug, not a feature. Model temperature
is set to 0 by default for extraction.

### Graceful degradation
A missing extraction does not break `kb build`. Each skill degrades gracefully and communicates clearly
what is missing rather than failing silently.

### Python scripts for reproducible operations
Some skills include Python scripts for operations where reproducibility matters:
parsing source files, running extractors, writing structured output. When a skill
ships scripts, they are Python and they live in the skill's `scripts/` directory.

Not every skill needs scripts. Agent reasoning alone handles operations that
are naturally conversational or one-off. Scripts are the right tool when the
same input must produce the same output across different assistants, runs, or
model versions.

### Schema-first extraction
The `extractions/<source-id>.json` schema is defined up front and versioned in
`lib/schema.py`. Extractors conform to it. The schema version is recorded in
every output file so downstream tools can detect and handle breaking changes.

---

## Key decisions

| Decision | Rationale |
|---|---|
| One JSON file per source in `extractions/` | Simplest unit of reprocessing; easy to diff; no shared mutable state |
| `source_ref` required on every extracted item | Provenance is non-negotiable — see [core-beliefs.md](design-docs/core-beliefs.md#2-provenance-is-non-negotiable) |
| KB is a generated view | Prevents KB drift from becoming a maintenance burden |
| Questions in `kb/questions/` feed back into KB build | Connects user questions to knowledge organization structurally, not ad hoc |
| Python scripts when reproducibility is needed | Same input → same output across assistants and runs; avoids ad-hoc code generation |
