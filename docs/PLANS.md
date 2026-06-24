# Plans

Plans are first-class artifacts in this repository.

→ Active plans: [exec-plans/active/](exec-plans/active/)
→ Completed plans: [exec-plans/completed/](exec-plans/completed/)
→ Known tech debt: [exec-plans/tech-debt-tracker.md](exec-plans/tech-debt-tracker.md)
→ Feature backlog: [backlog.md](backlog.md)

---

## When to create a plan file

| Change size | Where to plan |
|---|---|
| Small (< 1 day, no design decisions) | Conversation context only — no file needed |
| Medium (multi-step, design decisions likely) | `docs/exec-plans/active/<slug>.md` |
| Large (cross-skill, breaking changes, new commands) | Same, with decision log section |

When in doubt, write the file. A plan that turns out to be small costs one
file; a large change without a plan costs coordination overhead.

---

## Plan file template

```markdown
# Plan: <title>

**Goal**: one sentence.
**Status**: in-progress | blocked | review | done
**Started**: YYYY-MM-DD
**Completed**: YYYY-MM-DD or —

## Steps

- [ ] Step one
- [ ] Step two

## Progress log

- YYYY-MM-DD: <what happened>

## Decision log

- YYYY-MM-DD: <decision> — <rationale>
```

---

## Lifecycle

1. Create in `exec-plans/active/` when work begins.
2. Update `Status` and `Progress log` as work proceeds.
3. Add entries to `Decision log` whenever a non-obvious choice is made.
4. Move to `exec-plans/completed/` when done — do not delete.

Completed plans are the project's institutional memory. They explain *why*
the code is the way it is, which code alone cannot express.

---

## Current active plans

*None. See [exec-plans/active/](exec-plans/active/).*
