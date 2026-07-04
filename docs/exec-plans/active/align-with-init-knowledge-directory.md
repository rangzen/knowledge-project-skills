# Plan: Align with init-knowledge-directory

**Goal**: Rename directories and commands in every skill and script to match the conventions in `~/sources/skills/skills/init-knowledge-directory/SKILL.md`, and add a `kp-` prefix to every command/skill name.

**Status**: in progress - phase 1 complete

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
- [x] Run: `uv run pytest tests/test_skill_references.py` (should still pass - no links changed yet)

---

## Phase 2 - Update `kp-staging` skill (was `extract`)

Files: `skills/kp-staging/SKILL.md`, `skills/kp-staging/scripts/write_extraction.py`

**`skills/kp-staging/SKILL.md`**
- [ ] `name: extract` -> `name: kp-staging`
- [ ] Description: `extractions/` -> `staging/`, `/extract` -> `/kp-staging`
- [ ] All `extractions/<source-id>.json` -> `staging/<source-id>.json`
- [ ] All `/extract` command refs -> `/kp-staging`
- [ ] `<skill-dir>` paths: no change needed (already relative)
- [ ] `metadata.version`: bump minor

**`skills/kp-staging/scripts/write_extraction.py`**
- [ ] Line 15 (docstring): `extractions/<source-id>.json` -> `staging/<source-id>.json`
- [ ] Line 141: `extractions_dir = root / "extractions"` -> `extractions_dir = root / "staging"`
- [ ] Lines 121-125, 143, 146, 163, 170: rename local variable `extractions_dir` -> `staging_dir` for clarity
- [ ] Lines 146 print: `extractions/{args.source_id}.json` -> `staging/{args.source_id}.json`

**Tests**
- [ ] `tests/test_write_extraction.py` line 136: `(tmp_path / "extractions").mkdir()` -> `(tmp_path / "staging").mkdir()`
- [ ] `tests/test_write_extraction.py` line 148: `tmp_path / "extractions" / "src-001.json"` -> `tmp_path / "staging" / "src-001.json"`
- [ ] `tests/test_write_extraction.py` line 176: `(tmp_path / "extractions").mkdir()` -> `(tmp_path / "staging").mkdir()`
- [ ] `tests/test_write_extraction.py` lines 187-188: `tmp_path / "extractions" / "src-002.json"` -> `tmp_path / "staging" / "src-002.json"`
- [ ] `tests/data/json/object.json` line 7: `"output_dir": "extractions"` -> `"output_dir": "staging"`
- [ ] `tests/data/yaml/config.yaml` line 18: `output_dir: extractions` -> `output_dir: staging`
- [ ] Run: `uv run pytest tests/test_write_extraction.py tests/test_extract_preprocess_csv.py tests/test_extract_preprocess_docx.py tests/test_extract_preprocess_excel.py tests/test_extract_preprocess_json.py tests/test_extract_preprocess_pdf.py tests/test_extract_preprocess_yaml.py`

---

## Phase 3 - Update `kp-wiki` skill (was `kb`)

Files: `skills/kp-wiki/SKILL.md`, `skills/kp-wiki/scripts/wiki_build.py`

**`skills/kp-wiki/SKILL.md`**
- [ ] `name: kb` -> `name: kp-wiki`
- [ ] Description and all body text: `kb/` -> `wiki/`, `extractions/` -> `staging/`, `kb/questions/` -> `wiki/queries/`, `/kb` -> `/kp-wiki`, `/extract` -> `/kp-staging`
- [ ] `metadata.version`: bump minor

**`skills/kp-wiki/scripts/wiki_build.py`**
- [ ] Line 35: `(root / "extractions").glob` -> `(root / "staging").glob`
- [ ] Line 124: `root / "kb" / "config"` -> `root / "wiki" / "config"`
- [ ] Line 237: `root / "kb" / "glossary.md"` -> `root / "wiki" / "glossary.md"`
- [ ] Line 324: `root / "kb" / etype` -> `root / "wiki" / etype`
- [ ] Line 418: `root / "kb" / "index.md"` -> `root / "wiki" / "index.md"`
- [ ] Line 433: `root / "kb" / "questions"` -> `root / "wiki" / "queries"`
- [ ] Line 527: `root / "kb" / "index.yaml"` -> `root / "wiki" / "index.yaml"`
- [ ] Line 624: `root / "kb" / "build-report.json"` -> `root / "wiki" / "build-report.json"`
- [ ] Line 638: `kb = root / "kb"` -> `wiki = root / "wiki"`
- [ ] Lines 684-685: `root / "kb" / "questions"` -> `root / "wiki" / "queries"`
- [ ] Line 686 print: `Ask a question with /query first` -> `Ask a question with /kp-query first`
- [ ] Line 711: `root / "kb" / g["target"]` -> `root / "wiki" / g["target"]`
- [ ] Line 732: `root / "kb" / gap["target"]` -> `root / "wiki" / gap["target"]`
- [ ] Line 767: `kb_dir = root / "kb"` -> `wiki_dir = root / "wiki"`
- [ ] Line 819: `"questions"` entry in etype list -> `"queries"`
- [ ] Line 844: `root / "kb" / "config"` -> `root / "wiki" / "config"`
- [ ] Rename local variables `kb_dir` -> `wiki_dir` and `kb` -> `wiki` throughout for consistency

**Tests - update `SCRIPT` path in 8 files**
- [ ] `tests/test_kb_entity_resolution.py` line 7: `skills/kb/scripts/kb_build.py` -> `skills/kp-wiki/scripts/wiki_build.py`
- [ ] `tests/test_kb_entity_page_body.py` line 7: same
- [ ] `tests/test_kb_inject_wikilinks.py` line 7: same
- [ ] `tests/test_kb_glossary_quality.py` line 7: same
- [ ] `tests/test_kb_wikilink_validation.py` line 7: same
- [ ] `tests/test_kb_link_generation.py` line 7: same
- [ ] `tests/test_kb_enrich.py` line 7: same
- [ ] `tests/test_kb_entity_filtering.py` line 7: same
- [ ] `tests/test_kb_quality_metadata.py` line 7 (if present): same
- [ ] Run: `uv run pytest tests/test_kb_entity_resolution.py tests/test_kb_entity_page_body.py tests/test_kb_inject_wikilinks.py tests/test_kb_glossary_quality.py tests/test_kb_wikilink_validation.py tests/test_kb_link_generation.py tests/test_kb_enrich.py tests/test_kb_entity_filtering.py tests/test_kb_quality_metadata.py`

---

## Phase 4 - Update `kp-init` skill (was `init`)

File: `skills/kp-init/SKILL.md`

- [ ] `name: init` -> `name: kp-init`
- [ ] Step 3 directories: add `staging/`, `wiki/`, `wiki/config/`, `wiki/queries/`; replace `extractions/` and `kb/` with new names
- [ ] Step 3b: `kb/config/entity_stoplist.txt` -> `wiki/config/entity_stoplist.txt`
- [ ] Step 5 `.gitignore` comment: `kb/questions/` -> `wiki/queries/`
- [ ] Step 6 next-step suggestion: `/ingestion add` -> `/kp-source add`
- [ ] Add new step after directory creation: generate `AGENTS.md` with role definitions for `sources/`, `staging/`, `wiki/`, `scripts/`
- [ ] `metadata.version`: bump minor
- [ ] Run: `uv run pytest tests/test_skill_references.py`

---

## Phase 5 - Update `kp-source` skill (was `ingestion`)

File: `skills/kp-source/SKILL.md`

- [ ] `name: ingestion` -> `name: kp-source`
- [ ] Description: `/ingestion` -> `/kp-source`
- [ ] All sub-command headers and body: `/ingestion add` -> `/kp-source add`, `/ingestion status` -> `/kp-source status`, `/ingestion check-updates` -> `/kp-source check-updates`
- [ ] Cross-skill refs: `/init` -> `/kp-init`
- [ ] `<skill-dir>` paths: no change needed (already relative)
- [ ] `metadata.version`: bump minor
- [ ] Run: `uv run pytest tests/test_skill_references.py`

---

## Phase 6 - Update `kp-query` skill (was `query`)

File: `skills/kp-query/SKILL.md`

- [ ] `name: query` -> `name: kp-query`
- [ ] Description: `kb/questions/` -> `wiki/queries/`, `kb/index.yaml` -> `wiki/index.yaml`
- [ ] All body text: `extractions/` -> `staging/`, `kb/` -> `wiki/`, `kb/questions/` -> `wiki/queries/`
- [ ] Line 102: `<kb-skill-dir>/scripts/kb_build.py` -> `<kp-wiki-skill-dir>/scripts/wiki_build.py`
- [ ] Cross-skill refs: `/kb` -> `/kp-wiki`, `/extract` -> `/kp-staging`, `/query` -> `/kp-query`
- [ ] `metadata.version`: bump minor
- [ ] Run: `uv run pytest tests/test_skill_references.py`

---

## Phase 7 - Update docs

**`docs/product-specs/init.md`**
- [ ] Command: `/init` -> `/kp-init`
- [ ] Directory tree: `extractions/` -> `staging/`, `kb/` -> `wiki/`, `kb/questions/` -> `wiki/queries/`
- [ ] Add `AGENTS.md` to the output file list
- [ ] Next step suggestion: `/ingestion add` -> `/kp-source add`

**`docs/product-specs/kb.md`**
- [ ] Command: `/kb` -> `/kp-wiki`
- [ ] All `extractions/` -> `staging/`, `kb/` -> `wiki/`, `kb/questions/` -> `wiki/queries/`

**`docs/product-specs/query.md`**
- [ ] Command: `/query` -> `/kp-query`
- [ ] All `extractions/` -> `staging/`, `kb/` -> `wiki/`, `kb/questions/` -> `wiki/queries/`
- [ ] Cross-skill refs: `/kb` -> `/kp-wiki`, `/extract` -> `/kp-staging`

**`docs/product-specs/new-user-onboarding.md`**
- [ ] All command refs: `/init` -> `/kp-init`, `/ingestion` -> `/kp-source`, `/extract` -> `/kp-staging`, `/kb` -> `/kp-wiki`, `/query` -> `/kp-query`
- [ ] All dir refs: `extractions/` -> `staging/`, `kb/` -> `wiki/`

**`docs/FRONTEND.md`**
- [ ] `extractions/` -> `staging/` in all examples

**`AGENTS.md`**
- [ ] Commands table: update command column (`/init` -> `/kp-init`, etc.)
- [ ] Any dir refs: `extractions/` -> `staging/`, `kb/` -> `wiki/`

**`docs/exec-plans/active/structured-content-in-kb.md`**
- [ ] All path refs: `extractions/` -> `staging/`, `kb/` -> `wiki/`

- [ ] Run: `uv run pytest tests/test_skill_references.py`

---

## Phase 8 - Full test run

- [ ] Run: `uv run pytest`
- [ ] Confirm all tests pass with zero failures

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
