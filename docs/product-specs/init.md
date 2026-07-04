# Spec: kp-init

**Status**: draft
**Command**: `/kp-init`
**SKILL.md description**: Scaffold a new knowledge project in the current directory. Use when the user runs /init, wants to start a new knowledge project, or needs to create the project directory structure.

---

## Purpose

Create the directory scaffolding and config file for a knowledge project. After
`init`, the project is ready to receive sources via `/kp-source add`.

---

## Invocation

```
/init
/init --name "My Project"
/init --private-queries     # excludes wiki/queries/ from git
```

---

## Output

Creates the following structure in the current directory:

```
./
├── sources/
├── staging/
├── kb/
│   └── questions/
├── .knowledge-project      ← project config (see schema below)
└── .gitignore              ← generated defaults
```

### `.knowledge-project` schema

```yaml
name: <project name>
schema_version: "1"
created_at: <ISO date>
```

### Generated `.gitignore`

```gitignore
# Sensitive sources (add individually with /kp-source add --sensitive)

# Uncomment to exclude question history from public repos:
# wiki/queries/
```

---

## Behavior

- If `.knowledge-project` already exists: warn and ask for confirmation before
  overwriting. Do not silently clobber an existing project.
- `--name` sets the project name in `.knowledge-project`. If omitted, use the
  current directory name.
- `--private-queries` adds `wiki/queries/` to `.gitignore`.
- Does not create `AGENTS.md` or any documentation files - those are separate.

---

## Scripts

No scripts required. `init` is fully instruction-driven: create directories,
write `.knowledge-project`, write `.gitignore`.
