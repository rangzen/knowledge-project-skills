---
name: kp-init
description: >
  Scaffold a new knowledge project in the current directory. Creates sources/,
  staging/, wiki/, wiki/config/, wiki/queries/, and scripts/ directories, writes
  .knowledge-project config, generates .gitignore defaults, and creates AGENTS.md
  with per-directory role definitions. Use when the user runs /kp-init,
  wants to start a new knowledge project, or needs to set up the directory
  structure before adding sources or running extraction. "kps" is the short
  name for this project (Knowledge Project Skills) - also activate when
  the user says "kps init".
metadata:
  version: "1.3"
  project: knowledge-project-skills
---

## Instructions

### When to activate

Activate when the user invokes `/kp-init` or asks to create or initialize a
knowledge project in the current directory.

---

### Steps

**1. Check prerequisites**

Run `uv --version`.
- If the command fails or is not found: stop and tell the user to install uv
  (`curl -LsSf https://astral.sh/uv/install.sh | sh`). Do not proceed.

**2. Check for existing project**

Read `.knowledge-project` in the current directory.
- If it exists: warn the user and ask for confirmation before proceeding.
  Do not overwrite silently.
- If it does not exist: proceed.

**3. Create directories**

```
sources/
staging/
wiki/
wiki/config/
wiki/queries/
scripts/
```

**3b. Write `wiki/config/entity_stoplist.txt`**

```
# Entity stoplist - one entry per line, case-insensitive.
# Entities whose normalized name matches any entry here are dropped before page generation.
# Add words you observe being extracted as false entities in your own wiki builds.
about
access
activating
```

**4. Write `.knowledge-project`**

```yaml
name: <directory name, or --name value if provided>
schema_version: "1"
created_at: <current ISO datetime>
```

**5. Write `.gitignore`**

```gitignore
# Sensitive sources (add individually with /kp-source add --sensitive)

# Uncomment to exclude query history from public repos:
# wiki/queries/
```

If `--private-queries` was passed, uncomment the `wiki/queries/` line.

**6. Write `AGENTS.md`**

```md
# AI Agent Directives for This Knowledge Directory

Follow the roles below strictly to preserve data integrity:

### sources/ (Read-Only)
- **Contents:** Raw documents, original PDFs, images, URL lists.
- **Golden rule:** NEVER MODIFY, DELETE, or WRITE into this directory. Only read from it during ingestion tasks.

### staging/ (Read / Write - /kp-staging only)
- **Contents:** Structured extraction JSON, one file per source.
- **Golden rule:** Written exclusively by /kp-staging. Do not edit manually. Keep an explicit trace of the original source via source_id.

### wiki/ (Read / Append / Update - /kp-wiki only)
- **Contents:** The knowledge wiki (glossary, entity pages, index, queries).
- **Golden rule:** Act as an "Archivist." Every page should be highly connected with wiki links like `[[file_name]]`. Information must always be sourced back to staging or sources.

### scripts/ (Read / Write)
- **Contents:** Reusable generated scripts and automation helpers.
- **Golden rule:** Store reusable scripts here only. All generated scripts must be Python scripts executed with `uv` so they do not pollute the environment.
```

**7. Confirm to the user**

Print the directories created and the path to `.knowledge-project`.
Suggest the next step: `/kp-source add <path-or-url>`.

---

### Flags

| Flag | Effect |
|---|---|
| `--name "My Project"` | Sets `name` in `.knowledge-project`. Defaults to current directory name. |
| `--private-queries` | Adds `wiki/queries/` to `.gitignore`. |

---

### Edge cases

- If a directory already exists (e.g. a `sources/` folder was created manually):
  leave it untouched, do not error.
- If `.gitignore` already exists: append the knowledge-project section rather
  than overwriting.
