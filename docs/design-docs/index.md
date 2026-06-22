# Design Docs Index

Catalogue of all design documents with verification status.

**Verification status key**
- `current` — reflects actual implemented behavior
- `draft` — proposed, not yet implemented
- `stale` — implementation has diverged; needs update
- `superseded` — replaced by a newer doc (link provided)

---

| Doc | Description | Status | Last verified |
|---|---|---|---|
| [core-beliefs.md](core-beliefs.md) | Agent-first operating principles | `current` | 2026-06-21 |

---

## Adding a new design doc

1. Create the file in `docs/design-docs/`.
2. Add a row to the table above with status `draft`.
3. Link it from [AGENTS.md](../../AGENTS.md) if agents need to be aware of it.
4. Update status to `current` once the behavior is implemented and verified.

## Stale doc policy

A doc is marked `stale` when a linter or CI job detects that the described
behavior no longer matches the code, or when a contributor notices divergence.
Stale docs are tracked as tech debt in
[exec-plans/tech-debt-tracker.md](../exec-plans/tech-debt-tracker.md).
