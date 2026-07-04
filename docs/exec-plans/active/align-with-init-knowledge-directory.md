# Plan: Align with init-knowledge-directory

**Goal**: Rename directories and commands in every skill and script to match the conventions in `~/sources/skills/skills/init-knowledge-directory/SKILL.md`, and add a `kp-` prefix to every command/skill name.

**Status**: complete - all 8 phases done

---

## Rename map

### Directories

| Current | New |
|---|---|
| `extractions/` | `staging/` |
| `kb/` | `wiki/` |
| `kb/config/` | `wiki/config/` |
| `kb/questions/` | `wiki/queries/` |

`sources/` stays unchanged.

### Commands and skill folders

| Current command | New command | Skill folder |
|---|---|---|
| `/init` | `/kp-init` | `skills/kp-init/` |
| `/ingestion` | `/kp-source` | `skills/kp-source/` |
| `/extract` | `/kp-staging` | `skills/kp-staging/` |
| `/kb` | `/kp-wiki` | `skills/kp-wiki/` |
| `/query` | `/kp-query` | `skills/kp-query/` |

### Scripts

| Current | New |
|---|---|
| `skills/kb/scripts/kb_build.py` | `skills/kp-wiki/scripts/wiki_build.py` |

---

## Phase 1 - Rename folders and scripts

- [x] `git mv skills/init skills/kp-init`
- [x] `git mv skills/ingestion skills/kp-source`
- [x] `git mv skills/extract skills/kp-staging`
- [x] `git mv skills/kb skills/kp-wiki`
- [x] `git mv skills/query skills/kp-query`
- [x] `git mv skills/kp-wiki/scripts/kb_build.py skills/kp-wiki/scripts/wiki_build.py`
- [x] Run: `uv run pytest tests/test_skill_references.py` - 1 passed

---

## Phase 2 - Update `kp-staging` skill (was `extract`)

**`skills/kp-staging/SKILL.md`**
- [x] `name: extract` -> `name: kp-staging`
- [x] Description: `extractions/` -> `staging/`, `/extract` -> `/kp-staging`
- [x] All `extractions/<source-id>.json` -> `staging/<source-id>.json`
- [x] All `/extract` command refs -> `/kp-staging`
- [x] Edge case: `/ingestion add` -> `/kp-source add`
- [x] `metadata.version`: bumped to 1.9

**`skills/kp-staging/scripts/write_extraction.py`**
- [x] Docstring: `extractions/` -> `staging/`
- [x] Line 141: `extractions_dir = root / "extractions"` -> `staging_dir = root / "staging"`
- [x] Lines 121-125, 143, 146, 163, 170: renamed variable `extractions_dir` -> `staging_dir`
- [x] Line 146 print: `extractions/` -> `staging/`
- [x] Line 192: fixed em dashes in print output

**Tests**
- [x] `tests/conftest.py` line 8: `skills/extract/scripts` -> `skills/kp-staging/scripts`
- [x] `tests/test_write_extraction.py` line 9: SCRIPT path -> `skills/kp-staging/scripts/write_extraction.py`
- [x] `tests/test_write_extraction.py` lines 136, 176: `tmp_path / "extractions"` -> `tmp_path / "staging"`
- [x] `tests/test_write_extraction.py` lines 148, 187, 188: `tmp_path / "extractions" /` -> `tmp_path / "staging" /`
- [x] `tests/data/json/object.json` line 7: `"output_dir": "extractions"` -> `"output_dir": "staging"`
- [x] `tests/data/yaml/config.yaml` lines 18, 20: `output_dir: extractions` -> `staging`, `output_dir: kb` -> `wiki`
- [x] Run: `uv run pytest tests/test_write_extraction.py tests/test_extract_preprocess_*.py` - 39 passed

---

## Phase 3 - Update `kp-wiki` skill (was `kb`)

**`skills/kp-wiki/SKILL.md`**
- [x] `name: kb` -> `name: kp-wiki`
- [x] Description and all body text: `kb/` -> `wiki/`, `extractions/` -> `staging/`, `kb/questions/` -> `wiki/queries/`, `/kb` -> `/kp-wiki`, `/extract` -> `/kp-staging`
- [x] `metadata.version`: bumped to 1.5

**`skills/kp-wiki/scripts/wiki_build.py`**
- [x] Line 35: `(root / "extractions").glob` -> `(root / "staging").glob`
- [x] Line 22: `Run /init first` -> `Run /kp-init first`
- [x] Line 41: em dash in warning -> hyphen
- [x] Line 124: `root / "kb" / "config"` -> `root / "wiki" / "config"`
- [x] Line 237: `root / "kb" / "glossary.md"` -> `root / "wiki" / "glossary.md"`
- [x] Line 324: `root / "kb" / etype` -> `root / "wiki" / etype`
- [x] Line 418: `root / "kb" / "index.md"` -> `root / "wiki" / "index.md"`
- [x] Line 433: `root / "kb" / "questions"` -> `root / "wiki" / "queries"`
- [x] Line 527: `root / "kb" / "index.yaml"` -> `root / "wiki" / "index.yaml"`
- [x] Line 624: `root / "kb" / "build-report.json"` -> `root / "wiki" / "build-report.json"`
- [x] Line 638: `kb = root / "kb"` -> `wiki = root / "wiki"`
- [x] Lines 684-685: `root / "kb" / "questions"` -> `root / "wiki" / "queries"`
- [x] Line 686 print: `/query first` -> `/kp-query first`
- [x] Lines 711, 732: `root / "kb" / ...` -> `root / "wiki" / ...`
- [x] Lines 734, 738 prints: `kb/` -> `wiki/`
- [x] Lines 746-749: `/extract` -> `/kp-staging`, `/kb` -> `/kp-wiki`
- [x] Line 767: `kb_dir = root / "kb"` -> `wiki_dir = root / "wiki"`
- [x] Line 771: `Run /extract first` -> `Run /kp-staging first`
- [x] Line 800: em dash in conflicts print -> hyphen
- [x] Line 815-817: em dashes -> hyphens
- [x] Line 819: `"questions"` entry in etype list -> `"queries"`
- [x] Line 820: `kb_dir / etype` -> `wiki_dir / etype`
- [x] Line 842: print `kb/build-report.json` -> `wiki/build-report.json`
- [x] Line 844: `root / "kb" / "config"` -> `root / "wiki" / "config"`

**Tests - update SCRIPT path and fixture paths**
- [x] 8 test files: SCRIPT path -> `skills/kp-wiki/scripts/wiki_build.py`, module name `kb_build` -> `wiki_build`
- [x] `tests/test_kb_entity_page_body.py`: `kb/` -> `wiki/`
- [x] `tests/test_kb_inject_wikilinks.py`: `kb/` -> `wiki/`
- [x] `tests/test_kb_wikilink_validation.py`: `kb/` -> `wiki/`
- [x] `tests/test_kb_enrich.py`: `kb/questions/` -> `wiki/queries/`, message strings
- [x] `tests/test_kb_entity_filtering.py`: `kb/config/` -> `wiki/config/`, `kb/` -> `wiki/`
- [x] `tests/test_kb_quality_metadata.py`: `kb/` -> `wiki/`, `kb/questions/` -> `wiki/queries/`
- [x] Run: `uv run pytest tests/test_kb_*.py` - 157 passed

---

## Phase 4 - Update `kp-init` skill (was `init`)

- [x] `name: init` -> `name: kp-init`
- [x] Step 3 directories: `extractions/` -> `staging/`, `kb/` -> `wiki/`, `kb/config/` -> `wiki/config/`, `kb/questions/` -> `wiki/queries/`, added `scripts/`
- [x] Step 3b: `kb/config/entity_stoplist.txt` -> `wiki/config/entity_stoplist.txt`
- [x] Step 5 `.gitignore` comment: `# kb/questions/` -> `# wiki/queries/`
- [x] Step 6 next-step suggestion: `/ingestion add` -> `/kp-source add`
- [x] Added step 6: generate `AGENTS.md` with role definitions for `sources/`, `staging/`, `wiki/`, `scripts/`
- [x] `metadata.version`: bumped to 1.3
- [x] Run: `uv run pytest tests/test_skill_references.py` - 1 passed

---

## Phase 5 - Update `kp-source` skill (was `ingestion`)

- [x] `name: ingestion` -> `name: kp-source`
- [x] All `/ingestion` command refs -> `/kp-source`
- [x] Cross-skill refs: `/init` -> `/kp-init`
- [x] Fixed em dashes and en dashes in body text
- [x] `metadata.version`: bumped to 1.5
- [x] Run: `uv run pytest tests/test_skill_references.py` - 1 passed

---

## Phase 6 - Update `kp-query` skill (was `query`)

- [x] `name: query` -> `name: kp-query`
- [x] Description: `kb/questions/` -> `wiki/queries/`, `kb/index.yaml` -> `wiki/index.yaml`
- [x] All body text: `extractions/` -> `staging/`, `kb/` -> `wiki/`, `kb/questions/` -> `wiki/queries/`
- [x] `<kb-skill-dir>/scripts/kb_build.py` -> `<kp-wiki-skill-dir>/scripts/wiki_build.py`
- [x] Cross-skill refs: `/kb` -> `/kp-wiki`, `/extract` -> `/kp-staging`, `/query` -> `/kp-query`
- [x] `metadata.version`: bumped to 1.2
- [x] Run: `uv run pytest tests/test_skill_references.py` - 1 passed

---

## Phase 7 - Update docs

**`docs/product-specs/init.md`**
- [x] Command: `/init` -> `/kp-init`
- [x] Directory tree: `extractions/` -> `staging/`, `kb/` -> `wiki/`, `kb/questions/` -> `wiki/queries/`
- [x] Next step suggestion: `/ingestion add` -> `/kp-source add`

**`docs/product-specs/extract.md`** (was extract, now kp-staging)
- [x] Command: `/extract` -> `/kp-staging`, output dir `extractions/` -> `staging/`

**`docs/product-specs/ingestion.md`** (was ingestion, now kp-source)
- [x] Command: `/ingestion` -> `/kp-source`

**`docs/product-specs/kb.md`**
- [x] Command: `/kb` -> `/kp-wiki`
- [x] All `extractions/` -> `staging/`, `kb/` -> `wiki/`, `kb/questions/` -> `wiki/queries/`

**`docs/product-specs/query.md`**
- [x] Command: `/query` -> `/kp-query`
- [x] All `extractions/` -> `staging/`, `kb/` -> `wiki/`, `kb/questions/` -> `wiki/queries/`
- [x] Cross-skill refs: `/kb` -> `/kp-wiki`, `/extract` -> `/kp-staging`

**`docs/product-specs/new-user-onboarding.md`**
- [x] All command refs updated
- [x] All dir refs: `extractions/` -> `staging/`, `kb/` -> `wiki/`

**`docs/product-specs/index.md`**
- [x] Command names in index

**`docs/FRONTEND.md`**
- [x] `extractions/` -> `staging/` in all examples

**`AGENTS.md`**
- [x] Commands table: update command column
- [x] Any dir refs: `extractions/` -> `staging/`, `kb/` -> `wiki/`

**`README.md`**
- [x] All command refs, dir refs, section headers, mermaid diagram, tier table, em dashes

**`docs/exec-plans/active/structured-content-in-kb.md`**
- [x] All path refs: `extractions/` -> `staging/`, `kb/` -> `wiki/`

- [x] Run: `uv run pytest tests/test_skill_references.py` - 1 passed

---

## Phase 8 - Full test run

- [x] Run: `uv run pytest` - 208 passed, 0 failed

---

## Decision log

| Date | Decision | Rationale |
|---|---|---|
| 2026-07-04 | `kb/` -> `wiki/` and `extractions/` -> `staging/` | aligns with init-knowledge-directory conventions |
| 2026-07-04 | `kp-` prefix on all commands | user requirement; avoids collision with generic skill names |
| 2026-07-04 | `/ingestion` -> `/kp-source` | command name matches the directory it writes to (`sources/`) |
| 2026-07-04 | `/extract` -> `/kp-staging` | command name matches the directory it writes to (`staging/`) |
| 2026-07-04 | `/kb` -> `/kp-wiki` | command name matches the directory it writes to (`wiki/`) |
| 2026-07-04 | `/query` writes to `wiki/queries/` (was `kb/questions/`) | subdirectory name aligns with the `/kp-query` command |
| 2026-07-04 | `kb_build.py` -> `wiki_build.py` | script name tracks the command/directory it serves |
| 2026-07-04 | Test method names with "extractions" can stay | they test logic, not filesystem paths; renaming adds noise with no benefit |
