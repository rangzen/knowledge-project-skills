#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Build the knowledge base from extraction JSON files."""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def project_root() -> Path:
    p = Path.cwd()
    while p != p.parent:
        if (p / ".knowledge-project").exists():
            return p
        p = p.parent
    raise SystemExit("No .knowledge-project found. Run /init first.")


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def load_extractions(root: Path) -> list[dict]:
    extractions = []
    for path in sorted((root / "extractions").glob("*.json")):
        if path.name.endswith(".failed.json"):
            continue
        try:
            data = json.loads(path.read_text())
            if data.get("schema_version") != "1":
                print(f"Warning: skipping {path.name} — unknown schema_version", file=sys.stderr)
                continue
            extractions.append(data)
        except Exception as e:
            print(f"Warning: could not read {path.name}: {e}", file=sys.stderr)
    return extractions


def resolve_entities(
    extractions: list[dict],
    confidence_threshold: float = 0.0,
) -> tuple[list[dict], list[dict]]:
    """Merge entities across extractions by canonical name (case-insensitive).

    Detects type conflicts (same name, different type) and performs alias-based
    merging (entity B is absorbed into A when B's name appears in A's alias list).
    Returns (resolved_entities, conflicts).
    """
    seen: dict[str, dict] = {}
    conflicts: list[dict] = []

    for ext in extractions:
        source_id = ext["source_id"]
        for entity in ext.get("entities", []):
            if confidence_threshold > 0 and entity.get("confidence", 1.0) < confidence_threshold:
                continue
            key = entity["name"].lower()
            if key in seen:
                existing = seen[key]
                if existing["type"] != entity["type"]:
                    conflicts.append({
                        "name": entity["name"],
                        "existing_type": existing["type"],
                        "new_type": entity["type"],
                        "source": source_id,
                    })
                elif source_id not in existing["_sources"]:
                    existing["_sources"].append(source_id)
                    if entity.get("body"):
                        existing.setdefault("_bodies", []).append({"source": source_id, "body": entity["body"]})
            else:
                merged = dict(entity)
                merged["_sources"] = [source_id]
                merged.setdefault("aliases", [])
                merged["_bodies"] = [{"source": source_id, "body": entity["body"]}] if entity.get("body") else []
                seen[key] = merged

    # Alias-based merge: if A has alias matching B's name, absorb B into A.
    to_remove: set[str] = set()
    for key, entity in list(seen.items()):
        for alias in entity.get("aliases", []):
            alias_key = alias.lower()
            if alias_key in seen and alias_key not in to_remove:
                other = seen[alias_key]
                for src in other["_sources"]:
                    if src not in entity["_sources"]:
                        entity["_sources"].append(src)
                if other["name"] not in entity["aliases"] and other["name"] != entity["name"]:
                    entity["aliases"].append(other["name"])
                for other_alias in other.get("aliases", []):
                    if other_alias not in entity["aliases"] and other_alias.lower() != key:
                        entity["aliases"].append(other_alias)
                to_remove.add(alias_key)

    for key in to_remove:
        del seen[key]

    return sorted(seen.values(), key=lambda e: e["name"].lower()), conflicts


_DOC_CODE_RE = re.compile(r'^[A-Z][A-Z0-9-]*\d[A-Z0-9-]*$')


def _load_stoplist(root: Path) -> set[str]:
    stoplist_path = root / "kb" / "config" / "entity_stoplist.txt"
    if not stoplist_path.exists():
        return set()
    return {
        line.strip().lower()
        for line in stoplist_path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }


def filter_entities(
    entities: list[dict],
    root: Path,
    min_source_count: int = 1,
) -> tuple[list[dict], int]:
    """Filter low-value entities before page generation.

    Applies (in order): stoplist, document-code, and min-source-count filters.
    Returns (kept_entities, filtered_count).
    """
    stoplist = _load_stoplist(root)
    kept = []
    filtered = 0
    for entity in entities:
        name = entity["name"]
        if name.lower() in stoplist:
            filtered += 1
            continue
        if _DOC_CODE_RE.match(name) and entity.get("type") != "document":
            filtered += 1
            continue
        if len(entity["_sources"]) < min_source_count:
            filtered += 1
            continue
        kept.append(entity)
    return kept, filtered


def collect_key_facts(extractions: list[dict]) -> list[dict]:
    facts = []
    for ext in extractions:
        for fact in ext.get("key_facts", []):
            facts.append(fact)
    return facts


def entity_type_dir(entity_type: str) -> str:
    mapping = {
        "person": "people",
        "organization": "organizations",
        "place": "places",
        "product": "products",
        "concept": "concepts",
        "event": "events",
        "other": "other",
    }
    return mapping.get(entity_type, "other")


def resolve_slugs(entities: list[dict]) -> list[tuple[str, list[str]]]:
    """Assign globally unique slugs; disambiguate collisions by appending entity type.

    Links use bare slugs. Slugs must be globally unique across all entity
    subdirectories. Obsidian resolves [[slug]] links by basename; other consumers
    must implement equivalent lookup.

    Returns list of (base_slug, types) for each collision found.
    """
    slug_to_indices: dict[str, list[int]] = {}
    for i, entity in enumerate(entities):
        slug = slugify(entity["name"])
        slug_to_indices.setdefault(slug, []).append(i)

    collisions: list[tuple[str, list[str]]] = []
    for slug, indices in slug_to_indices.items():
        if len(indices) > 1:
            types = [entities[i]["type"] for i in indices]
            collisions.append((slug, types))
            for i in indices:
                entities[i]["_slug"] = f"{slug}-{slugify(entities[i]['type'])}"
        else:
            entities[indices[0]]["_slug"] = slug

    return collisions


_STUB_TEXT = "> Stub: no usable definition extracted. See sources for context."


def _glossary_definition(entity: dict, facts: list[dict]) -> tuple[str, bool]:
    """Return (definition_text, is_stub) applying summary/fact fallback logic."""
    context = entity.get("context", "").strip()
    summary = entity.get("summary", "").strip()

    candidate = summary if (summary and len(summary) > len(context)) else context

    def usable(text: str) -> bool:
        return bool(text) and not text.startswith("#") and len(text) >= 30

    if usable(candidate):
        return candidate, False

    name_lower = entity["name"].lower()
    for fact in facts:
        fact_text = fact.get("fact", "").strip()
        if name_lower in fact_text.lower() and len(fact_text) >= 30:
            return fact_text, False

    return _STUB_TEXT, True


def write_glossary(root: Path, entities: list[dict], mode: str, facts: list[dict]) -> list[str]:
    """Write glossary.md and return list of entity names that became stubs."""
    glossary_path = root / "kb" / "glossary.md"
    lines = [
        "---",
        "title: Glossary",
        "generated: true",
        f"last_built: {datetime.now(timezone.utc).date()}",
        "---",
        "",
        "# Glossary",
        "",
    ]

    stubs: list[str] = []
    current_letter = ""
    for entity in entities:
        first = entity["name"][0].upper()
        if first != current_letter:
            current_letter = first
            lines.append(f"## {current_letter}")
            lines.append("")

        definition, is_stub = _glossary_definition(entity, facts)
        if is_stub:
            stubs.append(entity["name"])

        aliases = entity.get("aliases", [])
        alias_str = f" _(also: {', '.join(aliases)})_" if aliases else ""
        slug = entity.get("_slug", slugify(entity["name"]))
        etype = entity_type_dir(entity["type"])
        lines.append(f"### [[{slug}|{entity['name']}]]{alias_str}")
        lines.append("")
        lines.append(definition)
        lines.append("")
        sources = ", ".join(f"`{s}`" for s in entity["_sources"])
        lines.append(f"_Sources: {sources} · [{entity['type']}]({etype}/{slug}.md)_")
        lines.append("")

    glossary_path.write_text("\n".join(lines))
    print(f"  Written: kb/glossary.md ({len(entities)} entries, {len(stubs)} stub(s))")
    return stubs


def write_entity_page(root: Path, entity: dict, mode: str) -> Path:
    etype = entity_type_dir(entity["type"])
    slug = entity.get("_slug", slugify(entity["name"]))
    page_dir = root / "kb" / etype
    page_dir.mkdir(parents=True, exist_ok=True)
    page_path = page_dir / f"{slug}.md"

    if page_path.exists():
        text = page_path.read_text()
        if "generated: false" in text or "manual: true" in text:
            return page_path
        if mode == "update":
            match = re.search(r"last_built:\s*(\S+)", text)
            if match:
                last_built = match.group(1)
                max_extracted = max(entity.get("_extracted_at", ""), last_built)
                if max_extracted <= last_built:
                    return page_path

    aliases = entity.get("aliases", [])
    alias_yaml = ""
    if aliases:
        alias_yaml = "\naliases:\n" + "\n".join(f"  - {a}" for a in aliases)

    sources_yaml = "\n".join(f"  - {s}" for s in entity["_sources"])

    content = (
        f"---\n"
        f"title: {entity['name']}\n"
        f"entity_type: {entity['type']}\n"
        f"generated: true{alias_yaml}\n"
        f"sources:\n{sources_yaml}\n"
        f"last_built: {datetime.now(timezone.utc).date()}\n"
        f"---\n\n"
        f"# {entity['name']}\n\n"
        f"{entity['context']}\n"
    )

    bodies = entity.get("_bodies", [])
    if len(bodies) == 1:
        content += f"\n{bodies[0]['body']}\n"
    elif len(bodies) > 1:
        for b in bodies:
            content += f"\n### From {b['source']}\n\n{b['body']}\n"

    content += (
        f"\n**Type:** {entity['type']}  \n"
        f"**Sources:** {', '.join(entity['_sources'])}\n"
    )

    if aliases:
        content += f"\n**Also known as:** {', '.join(aliases)}\n"

    page_path.write_text(content)
    return page_path


def write_index_md(root: Path, entities: list[dict], extractions: list[dict]) -> None:
    by_type: dict[str, list[dict]] = {}
    for entity in entities:
        by_type.setdefault(entity["type"], []).append(entity)

    lines = [
        "---",
        "title: Knowledge Base Index",
        "generated: true",
        f"last_built: {datetime.now(timezone.utc).date()}",
        "---",
        "",
        "# Knowledge Base",
        "",
        f"Built from {len(extractions)} source(s) · {len(entities)} entities",
        "",
        "## Entry points",
        "",
        "- [[Glossary]]",
        "",
        "## By type",
        "",
    ]

    type_order = ["concept", "person", "organization", "place", "product", "event", "other"]
    for etype in type_order:
        if etype not in by_type:
            continue
        dir_name = entity_type_dir(etype)
        lines.append(f"### {etype.capitalize()}s")
        lines.append("")
        for entity in sorted(by_type[etype], key=lambda e: e["name"].lower()):
            slug = entity.get("_slug", slugify(entity["name"]))
            lines.append(f"- [[{slug}|{entity['name']}]]")
        lines.append("")

    (root / "kb" / "index.md").write_text("\n".join(lines))
    print(f"  Written: kb/index.md")


def write_index_yaml(
    root: Path,
    entities: list[dict],
    extractions: list[dict],
    key_facts: list[dict],
    stubs: list[str],
    quality_map: dict[str, str] | None = None,
    filtered_count: int = 0,
    broken_wikilink_count: int = 0,
) -> None:
    gaps: dict[str, dict] = {}
    for qfile in sorted((root / "kb" / "questions").glob("*.md")):
        text = qfile.read_text()
        fm_match = re.search(r"---\n(.*?)\n---", text, re.DOTALL)
        if not fm_match:
            continue
        fm = fm_match.group(1)
        conf_match = re.search(r"confidence:\s*(\S+)", fm)
        topic_match = re.search(r"topic:\s*(.+)", fm)
        if conf_match and topic_match:
            conf = conf_match.group(1).strip('"\'')
            topic = topic_match.group(1).strip('"\'')
            if conf in ("low", "medium"):
                if topic not in gaps:
                    gaps[topic] = {"topic": topic, "question_count": 0, "max_confidence": conf}
                gaps[topic]["question_count"] += 1

    by_type: dict[str, list[dict]] = {}
    for entity in entities:
        by_type.setdefault(entity["type"], []).append(entity)

    effective_quality_map = quality_map or {}

    pages_yaml: dict[str, list[dict]] = {}
    type_order = ["concept", "person", "organization", "place", "product", "event", "other"]
    for etype in type_order:
        dir_name = entity_type_dir(etype)
        entries = []
        for entity in sorted(by_type.get(etype, []), key=lambda e: e["name"].lower()):
            slug = entity.get("_slug", slugify(entity["name"]))
            entry = {
                "title": entity["name"],
                "file": f"{dir_name}/{slug}.md",
                "sources": entity["_sources"],
                "quality": _entity_quality(entity, effective_quality_map),
            }
            if entity.get("aliases"):
                entry["aliases"] = entity["aliases"]
            entries.append(entry)
        pages_yaml[f"{dir_name}"] = entries

    entity_quality_grade = _overall_entity_quality(entities, filtered_count, effective_quality_map)
    quality_block = {
        "entity_quality": entity_quality_grade,
        "broken_wikilinks": broken_wikilink_count,
        "skipped_low_confidence_entities": filtered_count,
        "glossary_stubs": len(stubs),
    }

    index = {
        "schema_version": "1",
        "last_built": datetime.now(timezone.utc).isoformat(),
        "source_count": len(extractions),
        "entity_count": len(entities),
        "quality": quality_block,
        "glossary": "glossary.md",
        "glossary_stubs": stubs,
        "pages": pages_yaml,
        "gaps": list(gaps.values()),
    }

    def to_yaml(obj, indent=0) -> str:
        pad = "  " * indent
        if isinstance(obj, dict):
            lines = []
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    lines.append(f"{pad}{k}:")
                    lines.append(to_yaml(v, indent + 1))
                else:
                    lines.append(f"{pad}{k}: {json.dumps(v)}")
            return "\n".join(lines)
        elif isinstance(obj, list):
            if not obj:
                return f"{pad}[]"
            lines = []
            for item in obj:
                if isinstance(item, dict):
                    first = True
                    for k, v in item.items():
                        prefix = f"{pad}- " if first else f"{pad}  "
                        first = False
                        if isinstance(v, list):
                            lines.append(f"{prefix}{k}:")
                            for vi in v:
                                lines.append(f"{pad}    - {json.dumps(vi)}")
                        else:
                            lines.append(f"{prefix}{k}: {json.dumps(v)}")
                else:
                    lines.append(f"{pad}- {json.dumps(item)}")
            return "\n".join(lines)
        else:
            return f"{pad}{json.dumps(obj)}"

    yaml_text = to_yaml(index)
    (root / "kb" / "index.yaml").write_text(yaml_text + "\n")
    print(f"  Written: kb/index.yaml")


def scan_extraction_quality(extractions: list[dict]) -> dict:
    """Scan extractions for quality signals. Returns a summary dict."""
    total = len(extractions)
    with_warnings = 0
    with_low_coverage = 0
    with_no_entities = 0
    for ext in extractions:
        q = ext.get("quality", {})
        if q.get("flags"):
            with_warnings += 1
        coverage = q.get("text_coverage")
        if coverage is not None and coverage < 0.5:
            with_low_coverage += 1
        if not ext.get("entities"):
            with_no_entities += 1
    return {
        "total": total,
        "sources_with_warnings": with_warnings,
        "sources_with_low_coverage": with_low_coverage,
        "sources_with_no_entities": with_no_entities,
    }


def _extraction_quality_map(extractions: list[dict]) -> dict[str, str]:
    """Build source_id -> quality_level ('ok' | 'warning' | 'low') mapping."""
    mapping = {}
    for ext in extractions:
        source_id = ext["source_id"]
        q = ext.get("quality", {})
        flags = q.get("flags", [])
        if not flags:
            mapping[source_id] = "ok"
        elif "no_text" in flags or len(flags) >= 2:
            mapping[source_id] = "low"
        else:
            mapping[source_id] = "warning"
    return mapping


def _entity_quality(entity: dict, quality_map: dict[str, str]) -> str:
    """Derive entity quality from the worst quality of its contributing sources."""
    levels = [quality_map.get(src, "ok") for src in entity.get("_sources", [])]
    if "low" in levels:
        return "low"
    if "warning" in levels:
        return "warning"
    return "ok"


def _overall_entity_quality(
    entities: list[dict],
    filtered_count: int,
    quality_map: dict[str, str],
) -> str:
    """Derive overall entity quality grade based on flagged + filtered ratio."""
    flagged = sum(1 for e in entities if _entity_quality(e, quality_map) != "ok")
    total = len(entities) + filtered_count
    if total == 0:
        return "ok"
    ratio = (flagged + filtered_count) / total
    if ratio > 0.25:
        return "low"
    if ratio >= 0.05:
        return "warning"
    return "ok"


def _build_overall_quality(extraction_quality: dict) -> str:
    """Derive overall build quality from extraction summary."""
    total = extraction_quality["total"]
    if total == 0:
        return "ok"
    ratio = extraction_quality["sources_with_warnings"] / total
    if ratio > 0.25:
        return "low"
    if ratio > 0:
        return "warning"
    return "ok"


def write_build_report(root: Path, extraction_quality: dict, overall_quality: str) -> None:
    recommendation = (
        "Re-extract flagged sources before distributing this KB."
        if overall_quality != "ok"
        else "No action required."
    )
    report = {
        "build_date": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sources_total": extraction_quality["total"],
        "sources_with_warnings": extraction_quality["sources_with_warnings"],
        "overall_quality": overall_quality,
        "recommendation": recommendation,
    }
    (root / "kb" / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")


def _candidate_stoplist_entries(entities: list[dict]) -> list[str]:
    """Return entity names that look like structural noise: single lowercase word, not a proper noun."""
    return sorted({e["name"] for e in entities if " " not in e["name"] and e["name"].islower()})


def _wikilink_target(link: str) -> str:
    """Extract the link target from a wikilink, stripping alias and anchor."""
    return link.split("|")[0].split("#")[0].strip()


def validate_wikilinks(root: Path) -> list[tuple[Path, str]]:
    kb = root / "kb"
    broken = []
    for md_file in kb.rglob("*.md"):
        text = md_file.read_text()
        for link in re.findall(r"\[\[([^\]]+)\]\]", text):
            target = _wikilink_target(link)
            slug = slugify(target)
            matches = list(kb.rglob(f"{slug}.md"))
            if not matches and target.lower() not in ("glossary",):
                broken.append((md_file.relative_to(root), link))
    if broken:
        print(f"\n  Warnings — broken wikilinks ({len(broken)}):")
        for path, link in broken[:10]:
            print(f"    {path}: [[{link}]]")
        if len(broken) > 10:
            print(f"    ... and {len(broken) - 10} more")
    return broken


def _page_has_body(page_path: Path) -> bool:
    """Return True when a KB page has substantive body content beyond the context one-liner."""
    if not page_path.exists():
        return False
    text = page_path.read_text()
    fm_match = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
    body = text[fm_match.end():] if fm_match else text
    return bool(re.search(r"^#{2,}\s", body, re.MULTILINE))


def _page_sources(page_path: Path) -> list[str]:
    """Extract source IDs from a KB page's frontmatter sources list."""
    text = page_path.read_text()
    fm_match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not fm_match:
        return []
    return re.findall(r"^  - (\S+)", fm_match.group(1), re.MULTILINE)


def _clear_enrichment_flag(qfile: Path) -> None:
    text = qfile.read_text()
    text = re.sub(r"enrichment_needed:\s*true", "enrichment_needed: false", text)
    text = re.sub(r"\nenrichment_target:.*", "", text)
    qfile.write_text(text)


def run_enrich(root: Path) -> None:
    questions_dir = root / "kb" / "questions"
    if not questions_dir.exists():
        print("No questions found. Ask a question with /query first.")
        return

    gaps = []
    for qfile in sorted(questions_dir.glob("*.md")):
        text = qfile.read_text()
        fm_match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
        if not fm_match:
            continue
        fm = fm_match.group(1)
        if not re.search(r"enrichment_needed:\s*true", fm, re.IGNORECASE):
            continue
        date_match = re.search(r"date:\s*(\S+)", fm)
        question_match = re.search(r'question:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
        target_match = re.search(r"enrichment_target:\s*(.+)", fm)
        date = date_match.group(1) if date_match else "unknown"
        question = question_match.group(1).strip('"\'') if question_match else "unknown"
        target_raw = target_match.group(1).strip() if target_match else "null"
        target = None if target_raw == "null" else target_raw
        gaps.append({"date": date, "question": question, "target": target, "file": qfile})

    if not gaps:
        print("No enrichment gaps found.")
        return

    cleared = [g for g in gaps if g["target"] and _page_has_body(root / "kb" / g["target"])]
    still_open = [g for g in gaps if g not in cleared]

    if cleared:
        print(f"Clearing {len(cleared)} enrichment flag(s) (target pages now have body content):")
        for gap in cleared:
            _clear_enrichment_flag(gap["file"])
            print(f"  Cleared: {gap['file'].name}")
        print()

    if not still_open:
        print("All enrichment gaps resolved.")
        return

    print(f"Open enrichment gaps ({len(still_open)}):\n")
    sources_to_reextract: dict[str, list[str]] = {}

    for gap in still_open:
        print(f"  Date:     {gap['date']}")
        print(f"  Question: {gap['question']}")
        if gap["target"]:
            page_path = root / "kb" / gap["target"]
            if page_path.exists():
                print(f"  Target:   kb/{gap['target']} (thin page, needs enrichment)")
                for src in _page_sources(page_path):
                    sources_to_reextract.setdefault(src, []).append(gap["target"])
            else:
                print(f"  Target:   kb/{gap['target']} (page does not exist yet)")
        else:
            print(f"  Target:   (entity was never extracted -- no KB page exists)")
        print()

    if sources_to_reextract:
        print("Suggested re-extract commands:")
        for src in sorted(sources_to_reextract):
            print(f"  /extract --force {src}")
        print("\nAfter re-extracting, run /kb build, then /kb enrich again to clear flags.")
    else:
        print("Tip: identify the source for the above topics and run /extract --force <source-id>, then /kb build.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["build", "update", "enrich"], default="build")
    parser.add_argument("--min-sources", type=int, default=1, metavar="N",
                        help="Minimum source count for entity promotion (default: 1)")
    parser.add_argument("--confidence", type=float, default=0.0, metavar="THRESHOLD",
                        help="Minimum entity confidence score (default: 0, no filter)")
    args = parser.parse_args()

    root = project_root()

    if args.mode == "enrich":
        run_enrich(root)
        return

    kb_dir = root / "kb"

    extractions = load_extractions(root)
    if not extractions:
        print("No extractions found. Run /extract first.")
        sys.exit(0)

    for source_dir in sorted((root / "sources").iterdir()):
        meta_path = source_dir / ".meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            extraction = meta.get("extraction", {})
            is_extracted = (
                extraction.get("status") == "complete"
                or meta.get("extracted") is True
            )
            if not is_extracted:
                print(f"Warning: {source_dir.name} has not been extracted yet.")

    extraction_quality = scan_extraction_quality(extractions)
    print(f"Extraction quality summary:")
    print(f"  {extraction_quality['total']} sources total")
    if extraction_quality["sources_with_no_entities"]:
        print(f"  {extraction_quality['sources_with_no_entities']} with low entity count")
    if extraction_quality["sources_with_low_coverage"]:
        print(f"  {extraction_quality['sources_with_low_coverage']} with low text coverage")
    flagged_sources = extraction_quality["sources_with_warnings"]
    print(f"  {flagged_sources} failed extraction(s)" if flagged_sources else "  0 failed extractions")

    print(f"Building KB from {len(extractions)} extraction(s)...")

    entities, conflicts = resolve_entities(extractions, confidence_threshold=args.confidence)
    if conflicts:
        print(f"  Conflicts — type mismatches ({len(conflicts)}):")
        for c in conflicts[:5]:
            print(f"    {c['name']}: {c['existing_type']} vs {c['new_type']} (from {c['source']})")
        if len(conflicts) > 5:
            print(f"    ... and {len(conflicts) - 5} more")

    entities, filtered_count = filter_entities(entities, root, min_source_count=args.min_sources)
    if filtered_count:
        print(f"  Filtered {filtered_count} low-value entities before page generation.")

    quality_map = _extraction_quality_map(extractions)
    key_facts = collect_key_facts(extractions)

    slug_collisions = resolve_slugs(entities)
    if slug_collisions:
        print(f"  Warnings — slug collisions ({len(slug_collisions)}):")
        for slug, types in slug_collisions:
            print(f"    '{slug}': types {', '.join(types)} — disambiguated with type suffix")

    for etype in ["concepts", "people", "organizations", "places", "products", "events", "other", "topics", "questions"]:
        (kb_dir / etype).mkdir(parents=True, exist_ok=True)

    stubs = write_glossary(root, entities, args.mode, key_facts)

    page_count = 0
    for entity in entities:
        write_entity_page(root, entity, args.mode)
        page_count += 1
    print(f"  Written: {page_count} entity pages")

    write_index_md(root, entities, extractions)
    broken = validate_wikilinks(root)
    write_index_yaml(
        root, entities, extractions, key_facts, stubs,
        quality_map=quality_map,
        filtered_count=filtered_count,
        broken_wikilink_count=len(broken),
    )

    overall_quality = _build_overall_quality(extraction_quality)
    write_build_report(root, extraction_quality, overall_quality)
    print(f"  Written: kb/build-report.json (overall_quality: {overall_quality})")

    stoplist_path = root / "kb" / "config" / "entity_stoplist.txt"
    candidates = _candidate_stoplist_entries(entities)
    if candidates:
        active = _load_stoplist(root)
        file_text = stoplist_path.read_text() if stoplist_path.exists() else ""
        new_candidates = [c for c in candidates if c not in active and c not in file_text]
        if new_candidates:
            stoplist_path.parent.mkdir(parents=True, exist_ok=True)
            with stoplist_path.open("a") as f:
                f.write("\n# Suggested (review and uncomment to activate):\n")
                for c in new_candidates:
                    f.write(f"# {c}\n")
            print(f"  {len(new_candidates)} stoplist candidate(s) added to kb/config/entity_stoplist.txt")
    print(f"  Tip: edit kb/config/entity_stoplist.txt to suppress low-value entities.")

    print(f"\nDone. {len(entities)} entities across {len(extractions)} source(s).")
    if overall_quality != "ok":
        bad = extraction_quality["sources_with_warnings"]
        total = extraction_quality["total"]
        print(f"\nKB build completed with warnings.")
        print(f"Cause: {bad} of {total} source(s) have low-quality extractions.")
        print(f"Recommendation: re-run /extract with --force on flagged sources before distributing this KB.")


if __name__ == "__main__":
    main()
