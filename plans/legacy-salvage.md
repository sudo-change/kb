# PRD: Legacy Salvage — Extract Useful Bits from D:\KnowledgeBase into KnowledgeBase_Final

## Problem Statement

`D:\KnowledgeBase` is the previous, unstructured workspace where many half-baked attempts at building a personal knowledge pipeline accumulated over time: a working-but-messy `knowledgeforge` Python project (collectors, FTS storage, embedder, scheduler, kg-* CLIs, web UI, specgen), transcript-processing tools, sibling experiments (DailyForge, Vault playbook), and crystallized synthesis notes from a knowledge-extraction pass over the AI Crew playlist.

`KnowledgeBase_Final` is a fresh start that rebuilds the same idea cleanly per `plans/knowledge-forge-v1.md`. None of the legacy code or notes have been imported yet.

The risk if we ignore the legacy tree:

- We re-derive collectors, schema, scheduler patterns, and tag-normalization rules from scratch — slow and error-prone.
- We lose the crystallized synthesis docs that were the actual *output* of the prior thinking (glossary, workflows, cross-source synthesis, coverage/gaps).
- Useful tactical learnings (which feeds actually return clean signal, which scripts solved real problems) get forgotten.

The risk if we drag the legacy tree into `main`:

- The fresh repo is polluted with stale code, dead imports, machine-specific absolute paths, half-finished experiments, and 182 GB of `data/` artifacts.
- Future agents reading the repo can't tell which code is canonical and which is reference.

## Solution

Cleanly separate "what we are building" from "what we already learned" by using a dedicated `_legacy` git branch:

1. Catalog the useful items in `D:\KnowledgeBase` against the v1 PRD's phases.
2. Create branch `_legacy` off `main` and land a curated `legacy/` subdir there containing only the items that pass the filter (matches v1 PRD or is crystallized knowledge).
3. On `main`, ship a single `docs/legacy-manifest.md` that documents what's on `_legacy`, where each item came from, which v1 phase it informs, and the reuse verdict.

The manifest is the PRD's only required deliverable. Actually populating `_legacy` is an optional follow-up the manifest enables.

## User Stories

1. As a solo operator, I want a single manifest listing every salvaged item so I can find prior art in seconds.
2. As a solo operator, I want each item tagged with a reuse verdict so I know whether to copy, refactor, or just read it.
3. As a solo operator, I want each item mapped to a v1 PRD phase so I know when in the build I'll need it.
4. As a solo operator, I want the legacy code physically separated from `main` so the fresh repo stays lean.
5. As a solo operator, I want salvage notes per item so the "why useful" survives my own memory decay.
6. As a future agent (Devin/Claude), I want a discoverable pointer from `AGENTS.md` to the manifest so I can mine prior solutions without being told.
7. As a future agent, I want the manifest to use stable relative paths to the `_legacy` branch so I can read files via `git show _legacy:legacy/...`.
8. As a solo operator, I want the filter rules written down so I can re-run the audit if the source tree changes.
9. As a solo operator, I want the 182 GB legacy `data/` dump explicitly excluded so nobody accidentally tries to mirror it.
10. As a solo operator, I want the legacy `cookies/`, `__pycache__/`, `*.session`, `*.tmp`, and binary artifacts excluded so secrets and noise don't ride along.
11. As a solo operator, I want absolute paths (`D:\KnowledgeBase\...`) flagged in the manifest so I can rewrite them when porting.
12. As a solo operator, I want the prior `knowledgeforge/collectors/` mapped to v1 Phase 2 so I know what to reference when wiring RSS/YT.
13. As a solo operator, I want the prior `knowledgeforge/core/database.py` mapped to v1 Phase 1 so I can compare FTS schema choices.
14. As a solo operator, I want the prior `knowledgeforge/scripts/kg-*` mapped to v1 Phase 3/5 so I can lift CLI ergonomics for query/similar/tag.
15. As a solo operator, I want the synthesis docs (`data/knowledge-notes/00-07`) salvaged as docs (not code) so the knowledge is queryable.
16. As a solo operator, I want items with no v1 mapping but high crystallization value (synthesis notes, glossary) still salvaged under a `reference/` bucket.
17. As a solo operator, I want items that fail the filter listed in a "discarded" section with the rejection reason so the audit is reproducible.
18. As a solo operator, I want the manifest sorted by v1 phase so I can read it phase-by-phase during the build.
19. As a solo operator, I want the manifest checked in on `main` (not on `_legacy`) so it survives even if I delete the branch.
20. As a solo operator, I want a one-line `AGENTS.md` entry pointing at the manifest so agents discover it on first read.

## Modules

```
CREATE  docs/legacy-manifest.md
MODIFY  AGENTS.md                       (reason: add "Legacy reference" section pointing to docs/legacy-manifest.md and the _legacy branch)
MODIFY  README.md                       (reason: 1-line link to legacy manifest)
```

No code is created on `main`. The `_legacy` branch is created as a follow-up using:

```
git checkout main
git checkout -b _legacy
mkdir legacy
# (copy curated subset from D:\KnowledgeBase per manifest)
git add legacy/
git commit -m "Seed _legacy branch with curated salvage"
git push -u origin _legacy
git checkout main
```

The branch-creation step is **out of scope for this PRD** — the PRD's job is to produce the manifest that drives it.

## Schema Changes

None.

## Service Interfaces

None — this is a documentation deliverable, not a service.

The manifest is a markdown table. Each row has the schema:

| Column | Type | Description |
|---|---|---|
| `category` | enum | `code` \| `synthesis` \| `tool` \| `config` \| `playbook` |
| `source_path` | string | Absolute path in `D:\KnowledgeBase` |
| `destination_path` | string | Path on `_legacy` branch, e.g. `legacy/knowledgeforge/collectors/rss.py` |
| `maps_to_v1_phase` | enum | `P1` \| `P2` \| `P3` \| `P4` \| `P5` \| `P6` \| `cross-cutting` \| `reference-only` |
| `maps_to_v1_section` | string | Free-text pointer, e.g. `Phase 2 / collector/sources/rsshub.py` |
| `reuse_verdict` | enum | `copy-as-is` \| `refactor-then-port` \| `reference-only` \| `discard` |
| `salvage_notes` | string | Why useful, what to learn, what to avoid, known gotchas (e.g. hardcoded paths, missing deps) |

## Inter-module Dependencies

```
docs/legacy-manifest.md  -> (read by humans + agents)
AGENTS.md                -> docs/legacy-manifest.md   (pointer only)
README.md                -> docs/legacy-manifest.md   (pointer only)
_legacy branch           -> docs/legacy-manifest.md   (referenced from manifest; not vice versa)
```

The manifest on `main` is the source of truth. The `_legacy` branch is a content-addressed companion.

## Build Order

1. Audit `D:\KnowledgeBase` against the filter rules (see *Filter Rules* below). Walk the tree once, classify each leaf file.
2. Write `docs/legacy-manifest.md` with the full table + filter rules + discarded section.
3. Add pointer line to `AGENTS.md` under a new `## Legacy Reference` section.
4. Add one-line link to `README.md`.
5. (Out of scope, follow-up:) create `_legacy` branch and populate `legacy/` per the manifest.

## Implementation Phases

Durable decisions:

- **Branch model:** `_legacy` is branched off current `main` and holds a `legacy/` subdir at root. `main` never imports the code.
- **Manifest location:** `docs/legacy-manifest.md` on `main`. Single source of truth.
- **Filter rules:** see below; recorded verbatim in the manifest so the audit is reproducible.
- **Paths:** manifest uses absolute Windows paths for `source_path` (the legacy tree is on `D:\`) and POSIX-style relative paths under `legacy/` for `destination_path`.

### Phase 1: Audit + Manifest (this PRD)

User stories: #1–#20 except #4, #7

What to build: One markdown file, `docs/legacy-manifest.md`, containing:

- Filter rules section (verbatim from this PRD).
- Salvage table grouped by `category`, sorted by `maps_to_v1_phase` then `source_path`.
- Discarded section: bullet list of `source_path — reason` for items considered and rejected.
- Pointer to the (not-yet-created) `_legacy` branch and the commands to create it.

Plus a 4-line addition to `AGENTS.md` under a new `## Legacy Reference` heading, and a 1-line link in `README.md`.

Acceptance criteria:

- [ ] `docs/legacy-manifest.md` exists on `main`.
- [ ] Manifest table has at least one row per category: `code`, `synthesis`, `tool`, `config`, `playbook`.
- [ ] Every row has all 7 columns populated.
- [ ] `maps_to_v1_phase` value is one of `P1`/`P2`/`P3`/`P4`/`P5`/`P6`/`cross-cutting`/`reference-only`.
- [ ] Filter rules section in manifest matches *Filter Rules* below verbatim.
- [ ] Discarded section lists at least the 182 GB `knowledgeforge/data/` dump, `__pycache__/`, `*.session`, `cookies/`, and the `.tmp` recovery files.
- [ ] `AGENTS.md` contains a `## Legacy Reference` section linking to the manifest and naming the branch.
- [ ] `README.md` contains a one-line link to the manifest.

### Phase 2 (out of scope, follow-up): Populate `_legacy` branch

Create `_legacy` off `main`, copy items per the manifest's `destination_path` column, commit, push. No code on `main` changes.

## Filter Rules

An item from `D:\KnowledgeBase` qualifies for salvage if **either**:

**(A) Matches v1 PRD:** the item informs an explicit module, schema element, route, collector, or phase in `plans/knowledge-forge-v1.md`. Examples:

- `kb-clean/projects/knowledgeforge/collectors/{rss,youtube,arxiv,bluesky,ctftime,github,hackernews,hackerone,lobsters,reddit,telegram}.py` → maps to v1 Phase 2 (`collector/sources/*.py`).
- `kb-clean/projects/knowledgeforge/core/database.py` → maps to v1 Phase 1 (SQLite schema + FTS).
- `kb-clean/projects/knowledgeforge/core/{embedder,graph,scheduler,retry,validation}.py` → maps to v1 cross-cutting.
- `kb-clean/projects/knowledgeforge/scripts/kg-{query,similar,tag,neighbors,health}` → maps to v1 Phase 3 (API + Quarry) and v1 Phase 5 (MCP tool ergonomics).
- `kb-clean/projects/knowledgeforge/web/` → maps to v1 Phase 3 (compare against Quarry approach; reference-only).
- `kb-clean/projects/knowledgeforge/{Dockerfile,docker-compose.yml,config.yaml,pyproject.toml,requirements.txt}` → maps to v1 Phase 6.
- `kb-clean/projects/knowledgeforge/specgen/` → maps to v1 cross-cutting (spec generation pattern).

**(B) Crystallized knowledge:** the item is the *output* of prior thinking, not raw inputs. Examples:

- `kb-clean/data/knowledge-notes/00-workspace-overview.md` through `07-evaluation-report.md`.
- `kb-clean/notes/Claude-Code-Knowledge-Base.md`.
- `kb-clean/notes/TODO_Thoughts.md`.
- `kb-clean/plans/prd-kb-clean-git-ready.md` (the prior PRD itself — informs lint/CI patterns).

An item is **discarded** if it matches any of:

- Raw content corpus (`content/ai-podlodka/`, `content/yt-transcripts/`, `content/yt-extractions/`) — already decided out of scope.
- Generated data dumps (`knowledgeforge/data/` — 182 GB SQLite + extracts).
- Caches and tmp (`__pycache__/`, `*.pyc`, `*.tmp.*`, `database_tmp.py`, `database_recovered.py`, `app_tmp.py`).
- Session / state files (`*.session`, `temp.txt`, `yt.txt`, `unique_domains_*.txt`, `url_domain_counts.txt`, `feeds_*.json`/`feeds_*.yaml_snippet.txt` unless explicitly mapped).
- Secrets and credentials (`cookies/`, `.env`, any token files).
- Binary screenshots, slides, PDFs unless they are crystallized knowledge artifacts.
- Sibling projects with no v1 mapping unless they qualify under (B): `dailyforge/` (treat as reference-only), `playbooks/vault-build/Vault-1.md` (Chase Hughes vault, domain-specific — discard or reference-only at operator's discretion).
- Anything under `IgnoreNowLater/` or `Vault_analyze_seaprate_dont_mix_with_kb/` in the legacy root.

## Acceptance Criteria

### Manifest is complete

- Every leaf file under `D:\KnowledgeBase\kb-clean\` and `D:\KnowledgeBase\00_knowledgebase_complete\KnowledgeBase\` has been classified as salvage or discard (directory-level classification is acceptable for `data/`, `__pycache__/`, `content/`).
- No row has empty cells.
- Every `maps_to_v1_phase = P*` row's `maps_to_v1_section` cites a real line/heading in `plans/knowledge-forge-v1.md`.

### Manifest is actionable

- A reader can execute the `_legacy` branch creation by reading only the manifest (the destination paths form a valid directory tree).
- Each `reuse_verdict` is justified in `salvage_notes`.

### Discoverability

- `AGENTS.md` `## Legacy Reference` section is reachable from a `Ctrl+F` on "legacy" in the repo.
- `README.md` link to the manifest is in the first 50 lines.

### Reproducibility

- Filter rules in the manifest match this PRD verbatim. Re-running the audit with the same rules on the same source tree yields the same manifest (modulo `salvage_notes` wording).

## Auth Rules

N/A — local repo, single operator.

## Out of Scope

- Actually creating the `_legacy` branch or copying any files. The manifest enables it; it doesn't perform it.
- Importing the raw content corpus (transcripts, extractions, ai-podlodka playlist). Already decided.
- Rewriting absolute paths inside salvaged files. Flagged in `salvage_notes` only.
- Porting any legacy code into `main`. v1 PRD phases own that decision.
- Auditing `D:\KnowledgeBase\IgnoreNowLater\` and `D:\KnowledgeBase\Vault_analyze_seaprate_dont_mix_with_kb\` — both explicitly excluded by their folder names.
- CI / lint tooling for the manifest itself.

## Further Notes

- The prior `knowledgeforge` project predates v1's Quarry frontend and MCP server. Its `web/` is a Flask + HTMX UI — useful as reference for what *not* to do if v1 is committed to Quarry + MCP.
- The prior project's collector list is **broader** than v1's Phase 2 (which only specifies RSS + YouTube). Treat the extras (arxiv, bluesky, ctftime, github, HN, hackerone, lobsters, reddit, telegram) as a backlog of v2 collectors with working reference implementations.
- The `data/knowledge-notes/` directory is the highest-value-per-byte salvage in the entire tree. Read it before starting v1 Phase 1.
- `D:\KnowledgeBase\compare_kbclean_report.json` exists at the legacy root and may already contain a partial audit from a prior pass. Worth reading during manifest authoring; not necessarily salvaged.
- `kb-clean/projects/quarry/` duplicates `KnowledgeBase_Final/quarry/`. Verify with a diff before salvaging — if identical, discard.
