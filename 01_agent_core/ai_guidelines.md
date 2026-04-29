---
title: "AI Behavioral Guidelines"
module: 01_agent_core
tags: [ai, guidelines, behavior, documentation, context]
---

# AI Behavioral Guidelines

## Documentation Mandate

> **RULE #1: Document everything. Documentation is part of the fix, not an afterthought.**

### What to Document
- Every shell command you run and its output (success or failure)
- Every fix you apply — exact commands, exact file paths, exact diffs
- Every workaround discovered — even temporary ones
- Every new pattern or failure mode encountered
- Every command the user teaches you that works

### Where to Document
| What | Where |
|------|-------|
| New bug/fix | `05_knowledge_and_debugging/known_bugs_and_fixes/BUG-NNN_description.md` |
| New shell command | `02_execution/commands_reference.md` |
| New failure pattern | `05_knowledge_and_debugging/common_patterns.md` |
| Build session log | Bottom of `02_execution/build_flow.md` (append) |
| Test results | `03_testing_and_validation/test_suites.md` (update status) |

### When to Document
- **Immediately** — as soon as a command works or a fix is verified
- NOT at the end of the session
- NOT after a checkpoint
- RIGHT NOW, while the context is fresh

## Command Discovery Protocol

When you encounter a situation where you don't know the correct shell command:

1. **DO NOT GUESS** — Intel infrastructure has non-standard tools, paths, and conventions
2. **ASK THE USER**: "I need to do X. What's the correct command on this system?"
3. **When the user provides the command**: Run it, verify it works
4. **DOCUMENT IT**: Add to `02_execution/commands_reference.md` with:
   - The exact command
   - What it does
   - When to use it
   - Expected output / success criteria

## Contextual Hints

### Build System
- `grdlbuild` wraps Gradle → DVB → Make → Zebu tools
- Shadow files in `.shadow/` track completed stages — presence = done
- `-id` flag = `-Pignore_deps` = skip upstream tasks (safe for mid-build restarts)
- `fe_be` is the longest stage (~25h) — FPGA place-and-route for 192 FPGAs

### Test System
- `simregress` → T-REX → emurun → FM netbatch → Zebu hardware
- DOA tests: `spacedoa_mobile` (50ms cycle limit) + `spacex_mobile` (240ms, completes at ~135ms)
- FM boards: ZSE5 machines at Folsom (fmez5xxx), accessed via NB express queues
- Logbook freezes during active emulation (BUG-030) — this is NORMAL

### Critical DOA Test Rules
- **EMUL_QSLOT**: ALWAYS use `/prj/sv/nvl/emu/interactive` — NEVER `/prj/sv/nvl/showstopper` (see BUG-025: showstopper has `user_max_waiting=2` which blocks simultaneous DOA jobs)
- **simregress command** — use EXACTLY this (do not modify flags without user approval):
  ```bash
  simregress -dut nvlsi7_n2p -save -no_xs -trex -emu_model pkg_ghpf_model -emu_tech zse5 \
    -no_compress EMUL_QSLOT=/prj/sv/nvl/emu/interactive -trex- \
    -P zsc11_express -Q /IVE/NVL/emu \
    -l reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list
  ```
- **NEVER use `-local` flag** for DOA tests — Zebu hardware requires NB farm submission (see BUG-001)
- **ALWAYS pass `-P zsc11_express -Q /IVE/NVL/emu`** explicitly — omitting causes queue collision (see BUG-003)

### Common Gotchas
- `output/` may be a symlink to a GK build (read-only) — check permissions first
- SLES15 machines don't have old tool versions (python3.7.4, perl 5.14.1) — fix shebangs
- `LD_PRELOAD` doesn't work in Simics module namespace — use RPATH + co-location
- FM gecco environment doesn't honor `LD_LIBRARY_PATH` additions from plugins
- Kerberos tickets expire after ~24h — renew with `kinit -R` for long queue waits

## Session Startup Checklist
1. Read `00_index.md` (this is done by reading this file)
2. Check disk space: `df -h /nfs/site/disks/ive_sle_zsc11_tbaziza | tail -1`
3. Check Kerberos: `klist 2>&1 | grep -E "Expires|>>>"`
4. Check what's running: `nbq -u tbaziza 2>/dev/null | head -10`
5. Check last build status: `ls output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/.shadow/ | wc -l` (19 = complete)
