# 06_skills — Skill Catalog

Skills are **prose-first** Copilot extensions: each one is a directory containing a `SKILL.md`
(with YAML frontmatter the IDE auto-loads) plus any helper scripts. The agent reads them on
demand based on the `Triggers:` line in the description.

This directory is symlinked into `~/.copilot/skills/<name>/` by `init_agent.sh` so the IDE
discovers them automatically.

---

## Quick Index

| # | Skill | Category | Trigger Words | Has Script? |
|---|-------|----------|---------------|:-:|
| 1 | [`gk-turnin`](#1-gk-turnin) | Git / submit | turnin, gatekeeper, cth_psetup | — |
| 2 | [`intel-genai-api-setup`](#2-intel-genai-api-setup) | Auth / setup | OPENAI_API_KEY, genai key | — |
| 3 | [`intel-wiki-cli`](#3-intel-wiki-cli) | Docs / Confluence | wiki, confluence, wiki page | ✅ `wiki_cli.py` |
| 4 | [`intel-wiki-pat-setup`](#4-intel-wiki-pat-setup) | Auth / setup | wiki PAT, CONFLUENCE_PAT | — |
| 5 | [`skill-auto-extractor`](#5-skill-auto-extractor) | Meta / KB growth | save as skill, what did we learn | — |
| 6 | [`skill-creator`](#6-skill-creator) | Meta / authoring | create skill, new skill | ✅ 3 helpers |
| 7 | [`sle-build-new-target-analysis-opts`](#7-sle-build-new-target-analysis-opts) | Build debug | vlogan SVS, analysis opts missing | — |
| 8 | [`sle-build-rtlchanges-create`](#8-sle-build-rtlchanges-create) | Build / IP patch | create rtlchange, PKG_IP_CHANGES | — |
| 9 | [`sle-build-rtlchanges-refresh`](#9-sle-build-rtlchanges-refresh) | Build / IP patch | rtlchanges_precheck FAIL | — |
| 10 | [`sle-folsom-path-check`](#10-sle-folsom-path-check) | Site / NFS | folsom path, cross-site share | ✅ `folsom_path_check.sh` |
| 11 | [`test-command-fixer`](#11-test-command-fixer) | DOA / safety | simregress error, -trex unpaired | ✅ `fix_test_command.py` |
| 12 | [`tracker-info-usage`](#12-tracker-info-usage) | Debug / trackers | find tracker, IP tracker file | — |

> Pure-prose skills don't ship scripts — the SKILL.md *is* the deliverable; it teaches the
> agent the workflow. Skills with scripts execute concrete actions.

---

## 1. `gk-turnin`
**Category:** Git workflow (Intel Gatekeeper)

**What it does:** Walks the agent through Intel's Gatekeeper (CTH) turn-in flow for
`pcd` cluster, `ttl-h-main` stepping — including `cth_psetup` invocation, branch
hygiene checks, and review approval requirements before pushing to the shared GK branch.

**When the agent uses it:** User says "turnin", "submit to gatekeeper", or "GK push".

**Script:** none — prose runbook.

---

## 2. `intel-genai-api-setup`
**Category:** Authentication / first-run setup

**What it does:** Configures the `OPENAI_API_KEY` env var (from `~/.openai_api_key`)
required by Intel-GenAI-powered tools (`formatr`, `loggr`, `bucketr`, and our own
`copilot_cli_agent` LLM calls via the Intel proxy). Includes shell-profile snippet
for tcsh and bash, file-perm hardening (`chmod 600`), and troubleshooting.

**When the agent uses it:** Any tool reports `OPENAI_API_KEY not set` or
`API key not found`.

**Script:** none — config recipe.

---

## 3. `intel-wiki-cli` 🆕
**Category:** Documentation lookup (Confluence)

**What it does:** Provides CLI access to Intel Wiki (`wiki.ith.intel.com`) so the
agent can **search, read, create, update, comment on, and move** wiki pages without
the user leaving the terminal. Pairs with `intel-wiki-pat-setup` (which provisions
the PAT this skill consumes).

**Script:** `wiki_cli.py` — Python tool with sub-commands:
| Sub-command | Action |
|---|---|
| `check-setup` | Verify PAT is present & valid (run first!) |
| `search` | Full-text search across Intel Wiki |
| `search-pages` | Advanced search using CQL (Confluence Query Language) |
| `get` | Fetch page by **ID or title** (content + metadata) |
| `children` | List child pages — for hierarchy navigation |
| `create` / `create-draft` | Create new pages |
| `update` | Edit existing pages |
| `move` | Re-parent a page |
| `comments` / `add-comment` | Read or post comments |

**When the agent uses it:** A BUG fix references an Intel BKM/wiki page, or the user
asks "find me the wiki page for X".

---

## 4. `intel-wiki-pat-setup`
**Category:** Authentication / first-run setup

**What it does:** Step-by-step guide to generate an Intel Wiki Personal Access Token
at `https://wiki.ith.intel.com/plugins/personalaccesstokens/usertokens.action`,
save it to `~/.intel_wiki_pat` with `chmod 600`, and verify with
`wiki_cli.py check-setup`. Handles expired/invalid tokens too.

**When the agent uses it:** `intel-wiki-cli` reports `NOT CONFIGURED`, or user is
setting up wiki access for the first time.

**Script:** none — setup runbook.

---

## 5. `skill-auto-extractor`
**Category:** Meta / continuous KB growth

**What it does:** Autonomous "lessons learned" capture. After any debug session
involving non-obvious workarounds, this skill prompts the agent to ask
*"is this generalizable enough to become a new skill or BUG file?"* — and if yes,
drafts the SKILL.md / BUG-NNN.md automatically.

**When the agent uses it:** End of a triage session, `/skill-auto-extractor` slash
command, or user says "save this as a skill".

**Script:** none — orchestration prose (uses `skill-creator` to materialize).

---

## 6. `skill-creator`
**Category:** Meta / skill authoring

**What it does:** Templated workflow for creating new skills — picks the right
shape (prose-only vs. prose+script), validates the YAML frontmatter, ensures
triggers are unambiguous, and packages the directory.

**Scripts:**
- `init_skill.py` — scaffolds a new skill directory with template `SKILL.md`.
- `quick_validate.py` — lints frontmatter (name, description, triggers) before commit.
- `package_skill.py` — tar/zip a skill for distribution.

**When the agent uses it:** User says "create a skill" or `skill-auto-extractor`
delegates the materialization.

---

## 7. `sle-build-new-target-analysis-opts`
**Category:** Build debug (SLE / ZeBu)

**What it does:** Diagnoses the *"hundreds of `Error-[SVS]` errors when enabling a
new emulation build target"* failure mode. Walks through `vlogan` command comparison
between working and failing targets, checks `verif/emu/<dir>/` for missing
`global_*_vlog_opts.f` symlinks, and traces `analysis_opts` through `.model.cfg.mako`.

**When the agent uses it:** First time bringing up a new `BUILD_DIRNAME` and analyze
explodes with library-wide SV-construct errors.

**Script:** none — diagnostic runbook.

---

## 8. `sle-build-rtlchanges-create`
**Category:** Build / IP source patching

**What it does:** End-to-end workflow to create a new **rtlchange** (Intel's
mechanism for patching IP source files at build time without forking the IP).
Covers the 4 artifacts you must produce: replacement `.sv`, `.ref` checksum,
`HSDs.toml` entry, and `PKG_IP_CHANGES.cfg` directive. Includes how to find the
right VCS library via `analyzed_libs`.

**When the agent uses it:** User wants to patch a sub-IP RTL file for emulation
without altering the upstream IP package.

**Script:** none — authoring runbook.

---

## 9. `sle-build-rtlchanges-refresh`
**Category:** Build / IP source patching

**What it does:** Companion to skill #8 — diagnoses `rtlchanges_precheck` failures
(exit 256), refreshes stale `.ref` checksums after an IP drop, fills missing
`HSDs.toml` entries, and applies the mechanical emu transformations
(hierarchy rewrite, library-prefix, monitor comment-out, clock-guard injection).

**When the agent uses it:** `grdlbuild` fails at the `rtlchanges_precheck` stage,
or the user is porting rtlchanges between workspaces.

**Script:** none — diagnostic runbook.

---

## 10. `sle-folsom-path-check`
**Category:** Site / NFS path validation

**What it does:** Before sharing a workarea path with a Folsom-based teammate (or
submitting a cross-site job), classifies the path by NFS prefix (site-local vs.
multi-site replicated) and — if a Folsom probe host is configured — SSHes there
and runs `test -e` to confirm reachability. Returns one of
`ACCESSIBLE / NOT_ACCESSIBLE / UNCERTAIN` with reasoning.

**Script:** `scripts/folsom_path_check.sh` — does the classification + remote probe.

**When the agent uses it:** User asks "can Folsom see this path?" or pastes a
share-the-path request.

---

## 11. `test-command-fixer`
**Category:** DOA test safety / command linting

**What it does:** Detects and **auto-fixes** the recurring SLE simregress /
grdlbuild command mistakes the agent's red lines forbid:
- Unpaired `-trex … -trex-`
- Missing `-emu_model`
- Forbidden `-local` flag (BUG-001)
- `EMUL_QSLOT=/prj/sv/nvl/showstopper` (must be `/prj/sv/nvl/emu/interactive`)
- Missing `-P zsc11_express -Q /IVE/NVL/emu` (BUG-003)
- `-Penv=immidiate` typo (correct: `immediate`)
- Unknown grdlbuild target names

**Script:** `scripts/fix_test_command.py` — parses the command, applies fixes,
prints corrected version + a diff.

**When the agent uses it:** Before submitting any `simregress` or `grdlbuild`
command (Step 3 of the agent workflow), or when the user pastes a failing one.

---

## 12. `tracker-info-usage`
**Category:** Debug / RTL tracker discovery

**What it does:** Guide for finding the right `tracker_info` tool invocation to
discover tracker files (PMC boot flows, GPIO signals, register access, sideband
traffic, PCIe transactions) inside a test workarea — and how to interpret them.

**When the agent uses it:** Debug phase (Step 4) when the symptom points to a
specific IP/protocol and the agent needs the tracker log path for that subsystem.

**Script:** none — usage guide (the `tracker_info` tool itself lives in
`pcd-val-agents` repo, not in this skill).

---

## Adding a new skill

1. Use the **`skill-creator`** skill (`init_skill.py`) to scaffold the directory.
2. Drop it in `06_skills/<your-skill-name>/`.
3. Verify the symlink at `~/.copilot/skills/<your-skill-name>/` (init_agent.sh
   may need a re-run if the link is missing).
4. Add a row to the **Quick Index** above and a `## N. <name>` section below.
5. Commit with message `skills: add <your-skill-name>`.

## Skill anatomy reminder

```
06_skills/<name>/
├── SKILL.md          # required — YAML frontmatter (name, description, triggers) + body
├── scripts/          # optional — any helper .sh / .py
└── *.md              # optional — supplementary docs the SKILL.md links to
```

The `description:` field in the frontmatter **must** include a `Triggers:` line — that's
how the IDE matches user prompts to skills.
