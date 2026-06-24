# Feature Backlog

Ideas and wanted features not yet scheduled. Add entries freely; move to an exec-plan when work begins.

---

## Extraction

- **Question-driven extraction**: use `kb/questions/` as input to `/extract` so that low-confidence or unanswered questions steer what the extractor focuses on. Questions with `confidence < threshold` could generate targeted extraction prompts rather than running the default full-document pass.

## Ingestion

- **Obsidian vault support**: when the source is detected as an Obsidian vault (presence of `.obsidian/` dir), prompt the user whether to import the full vault or filter to pages related to specific topics. Topic filter could match on tags, folder paths, or a seeded keyword list.
