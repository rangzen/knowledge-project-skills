# Reliability

→ See [ARCHITECTURE.md](../ARCHITECTURE.md) for the system overview.
→ See [SECURITY.md](SECURITY.md) for security considerations.

---

## Failure modes

### LLM extraction failures

**Mode**: The LLM returns malformed JSON, hallucinates schema fields, or hits
a context-length limit mid-document.

**Mitigation**:
- Extraction validates output against the schema before writing to `extractions/`.
- Oversized sources are chunked; chunks are extracted independently and merged.
- Failed extractions write a `.failed.json` file with the error, not nothing.
  A missing extraction file means "never attempted"; a `.failed.json` means
  "attempted and failed" — distinguishable states.

---

### Source changes after extraction

**Mode**: A source file is updated after its extraction was written. The extraction
is now stale.

**Mitigation**:
- `ingestion` records a hash of each source at ingest time.
- `extract` (and `ingestion status`) compares the current hash to the stored hash
  and warns when they diverge.
- Stale extractions are marked in `extractions/<source-id>.json` with
  `stale: true` and the date of the detected divergence.

---

### Glossary alias conflicts

**Mode**: Two sources use the same term to mean different things, or two
different terms to mean the same thing.

**Mitigation**:
- `kb build` flags glossary alias conflicts rather than silently resolving them.
- Conflicting definitions are written to `kb/conflicts.md` for manual review.

---

### KB link rot

**Mode**: A `kb/` page references an entity that no longer exists in the
glossary or was renamed.

**Mitigation**:
- `kb build` validates all `[[wikilinks]]` before writing.
- `kb build` also validates all `file:` entries in `kb/index.yaml`.
- Broken links are reported as warnings with the originating page and the
  unresolved link target.
- `kb build` never fails on broken links; it completes and reports.

---

### `kb/questions/` grows over time

**Mode**: One Markdown file per question accumulates indefinitely.

**Mitigation**:
- Each question is a separate file, so growth does not degrade read performance
  on individual files. `/kb build` scans the directory index, not file contents,
  for the initial feedback pass.
- `/query --gaps` and `/query --related` operate on frontmatter only (no full-text
  load), keeping them fast at scale.
- Archival (moving old questions to `kb/questions/archive/`) is a v2 concern.
  Old questions retain compound knowledge value — they should not be deleted.

---

## Graceful degradation contract

Each skill degrades gracefully when its dependencies are missing:

| Skill | Missing dependency | Behavior |
|---|---|---|
| `extract` | No sources | Print helpful message, exit 0 |
| `kb build` | No extractions | Print message, exit 0 |
| `kb build` | Partial extractions | Build from what exists, warn about missing sources |
| `query` | No `kb/` | Fall back to querying extractions directly; still writes to `kb/questions/` |
| `kb build` | No `kb/questions/` | Build without feedback layer; warn that compound knowledge is empty |
