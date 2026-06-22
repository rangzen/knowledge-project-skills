---
name: init
description: >
  Scaffold a new knowledge project in the current directory. Creates sources/,
  extractions/, kb/, and kb/questions/ directories, writes .knowledge-project
  config, and generates .gitignore defaults. Use when the user runs /init,
  wants to start a new knowledge project, or needs to set up the directory
  structure before adding sources or running extraction.
metadata:
  version: "1.0"
  project: knowledge-project-skills
---

## Instructions

### When to activate

Activate when the user invokes `/init` or asks to create or initialize a
knowledge project in the current directory.

---

### Steps

**1. Check for existing project**

Read `.knowledge-project` in the current directory.
- If it exists: warn the user and ask for confirmation before proceeding.
  Do not overwrite silently.
- If it does not exist: proceed.

**2. Create directories**

```
sources/
extractions/
kb/
kb/questions/
```

**3. Write `.knowledge-project`**

```yaml
name: <directory name, or --name value if provided>
schema_version: "1"
created_at: <current ISO datetime>
```

**4. Write `.gitignore`**

```gitignore
# Sensitive sources (add individually with /ingestion add --sensitive)

# Uncomment to exclude question history from public repos:
# kb/questions/
```

If `--private-queries` was passed, uncomment the `kb/questions/` line.

**5. Confirm to the user**

Print the directories created and the path to `.knowledge-project`.
Suggest the next step: `/ingestion add <path-or-url>`.

---

### Flags

| Flag | Effect |
|---|---|
| `--name "My Project"` | Sets `name` in `.knowledge-project`. Defaults to current directory name. |
| `--private-queries` | Adds `kb/questions/` to `.gitignore`. |

---

### Edge cases

- If a directory already exists (e.g. a `sources/` folder was created manually):
  leave it untouched, do not error.
- If `.gitignore` already exists: append the knowledge-project section rather
  than overwriting.
