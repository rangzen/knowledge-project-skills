# Quality Score

Grades each product domain and architectural layer. Updated as skills are
implemented and verified.

**Grade key**: `A` excellent | `B` good | `C` acceptable | `D` needs work | `—` not yet assessed

---

## Domain grades

| Domain | Grade | Notes | Last updated |
|---|---|---|---|
| `init` | — | Not yet implemented | — |
| `ingestion` | — | Not yet implemented | — |
| `extract` | — | Not yet implemented | — |
| `kb` | — | Not yet implemented | — |
| `query` | — | Not yet implemented | — |

---

## Layer grades

| Layer | Grade | Notes | Last updated |
|---|---|---|---|
| Sources (raw storage) | — | Schema defined, not implemented | — |
| Extractions (structured output) | — | Schema defined, not implemented | — |
| Glossary (synthesis) | — | Not yet implemented | — |
| Wiki (presentation) | — | Not yet implemented | — |
| Query log (feedback) | — | Not yet implemented | — |

---

## Documentation grades

| Area | Grade | Notes |
|---|---|---|
| AGENTS.md | B | Written; not yet validated against implemented behavior |
| ARCHITECTURE.md | B | Written; not yet validated |
| Design docs | B | Core beliefs written; individual command docs pending |
| Product specs | C | Only onboarding spec written; command specs are stubs |
| Exec plans | — | No plans yet |

---

## Known gaps

1. All command specs under `docs/product-specs/` are stubs — need full
   input/output contracts. Tracked in
   [exec-plans/tech-debt-tracker.md](exec-plans/tech-debt-tracker.md).
2. No CI linting yet for cross-link validation or doc staleness detection.
3. No extraction schema formally versioned yet.

---

## Update policy

Update this file when:
- A skill reaches a first working implementation (assess `D` or `C`)
- A skill is tested against real sources (refine to `B`)
- A skill is stable and well-tested (consider `A`)
