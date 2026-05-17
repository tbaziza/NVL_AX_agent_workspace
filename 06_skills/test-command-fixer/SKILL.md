---
name: test-command-fixer
description: Detect and fix common errors in SLE emulation (simregress / grdlbuild) testlists and commands for NVL_AX on ZeBu ZSE5. Use this skill when debugging SLE simregress failures, malformed `-trex ... -trex-` pairs, missing `-emu_model`, forbidden `-local` flag, wrong `EMUL_QSLOT`, missing `-P zsc11_express -Q /IVE/NVL/emu`, `-Penv=immediate` typos, or unknown grdlbuild build targets. Triggers - SLE testlist error, simregress failure, -trex unpaired, missing -emu_model, -local in simregress, EMUL_QSLOT showstopper, -P -Q missing, -Penv=immidiate, grdlbuild target typo, NVL_AX testlist syntax.
---

# Test Command Fixer (SLE / NVL_AX / ZeBu ZSE5)

## Overview

This skill detects and fixes common errors in SLE emulation testlist files and shell commands (simregress and grdlbuild) for the NVL_AX program running on ZeBu ZSE5. It enforces the project red-line rules and the canonical SLE simregress invocation.

Bundled tool: `scripts/fix_test_command.py` — Python 3, three modes (preview / apply / apply-suggested).

## When to Use This Skill

Trigger this skill when:

- A simregress run fails with "Unknown switches" or rejects the testlist
- The DOA monitor reports a regression queued but not executed (often a malformed testlist)
- A testlist line is missing the trailing `-trex-` or has it duplicated
- A simregress invocation lacks `-emu_model`, `-P zsc11_express`, `-Q /IVE/NVL/emu`, or `EMUL_QSLOT=/prj/sv/nvl/emu/interactive`
- A line contains `-local` (forbidden in SLE simregress)
- A `grdlbuild` target uses a misspelled `-Penv` or an unknown `:emu_build:zebu:` target
- The user pastes a command that's a slight variant of one of the four supported flows

## Canonical SLE simregress Command

The script targets and enforces this canonical invocation:

```
simregress -dut nvlsi7_n2p -save -no_xs \
  -trex -emu_model <EMU_MODEL> -emu_tech zse5 -no_compress \
        EMUL_QSLOT=/prj/sv/nvl/emu/interactive -trex- \
  -P zsc11_express -Q /IVE/NVL/emu \
  -l <DOA_REGLIST>
```

Valid `-emu_model` values (4):

| emu_model                          | grdlbuild target                            |
| ---------------------------------- | ------------------------------------------- |
| `pkg_ghpf_model`                   | `pkg_ghpf_model_zse5`                       |
| `pkg_chp_model_p2e4_fast`          | `pkg_chp_model_p2e4_fast_zse5`              |
| `pkg_chp_hubs_full_model_p2e4`     | `pkg_chp_hubs_full_model_p2e4_zse5`         |
| `pkg_chp_model_p2e4`               | `pkg_chp_model_p2e4_zse5`                   |

## Quick Start

```bash
# Preview (no modification)
python3 ~/.copilot/skills/test-command-fixer/scripts/fix_test_command.py \
  reglist/nvlsi7_n2p/emu/doa_pkg_chp_model_p2e4_fast_zse5.list

# Apply auto-fixes (modifies file in place)
python3 ~/.copilot/skills/test-command-fixer/scripts/fix_test_command.py \
  reglist/nvlsi7_n2p/emu/doa.list --apply

# Apply auto + suggested (spacing/balancing) fixes
python3 ~/.copilot/skills/test-command-fixer/scripts/fix_test_command.py \
  reglist.list --apply-suggested

# Explicit emu_model override (skips auto-detect)
python3 ~/.copilot/skills/test-command-fixer/scripts/fix_test_command.py \
  reglist.list --apply --model pkg_chp_model_p2e4

# List the 4 valid SLE emu_models / build targets
python3 ~/.copilot/skills/test-command-fixer/scripts/fix_test_command.py --list-models
```

## SLE Red-Line Fixes (auto-applied with `--apply`)

| ID         | Detector                                        | Action                                                                              |
| ---------- | ----------------------------------------------- | ----------------------------------------------------------------------------------- |
| BUG-001    | `-local` in a simregress line                   | Strip it (SLE simregress runs through farm queues, never local)                     |
| BUG-002    | `EMUL_QSLOT=/prj/sv/nvl/showstopper`            | Rewrite to `EMUL_QSLOT=/prj/sv/nvl/emu/interactive`                                  |
| BUG-002b   | simregress line with **no** `EMUL_QSLOT=...`    | Append `EMUL_QSLOT=/prj/sv/nvl/emu/interactive`                                     |
| BUG-003    | simregress missing `-P zsc11_express` or `-Q /IVE/NVL/emu` | Append the missing token(s) before `-l`                                |
| —          | `-Penv=immidiate` / `immedate` / `imediate`     | Rewrite to `-Penv=immediate` (grdlbuild only)                                       |
| —          | Missing `-emu_model` on simregress with `-dut`  | Insert `-emu_model <auto-detected or default>` immediately after `-dut nvlsi7_n2p`  |
| —          | Unpaired trailing `-trex-`                      | Remove the orphan close tag                                                         |
| —          | Relative `-include` paths                       | Prepend `$WORKAREA/` if the file exists there; otherwise flag as ERROR              |
| —          | Invisible / non-printable characters            | Strip (zero-width spaces, BOM, `\x00`, etc.)                                        |

## SLE Suggestion-Only Detectors

| Detector                                              | Action                                                                                       |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Unknown `:emu_build:zebu:<target>` in `grdlbuild`     | Print the nearest valid SLE target (longest-common-prefix match). **Never auto-applied** — these are typically intentional new variants and require manual review. |

## `--apply-suggested` Additional Fixes

- Balance unbalanced `-trex` / `-trex-` pairs (smart placement around `+OPT=...` etc.)
- Fix spacing violations adjacent to `-trex` and `-trex-` tags
- Collapse consecutive opening or consecutive closing tags

## Auto-Detection

The script uses these strategies (each can be overridden):

1. **`-emu_model`** — scans non-comment lines for the most common `-emu_model <X>` and uses that as the canonical model for any line that's missing it. Falls back to `--model` arg or `pkg_chp_model_p2e4_fast`.
2. **`$WORKAREA`** — uses the env var if set, else walks up from the testlist looking for ≥2 of: `output/nvlsi7_n2p/`, `reglist/nvlsi7_n2p/`, `verif/emu/`.

## Suggested Workflow (when called from the SLE Emulation Agent)

```bash
# 1) Pinpoint the testlist that failed
ls -lt regression/nvlsi7_n2p/doa_*.list.latest | head -1

# 2) Preview issues
python3 ~/.copilot/skills/test-command-fixer/scripts/fix_test_command.py \
  $(readlink regression/nvlsi7_n2p/doa_pkg_chp_model_p2e4_fast_zse5.list.latest)

# 3) Auto-fix
python3 ~/.copilot/skills/test-command-fixer/scripts/fix_test_command.py \
  $(readlink regression/nvlsi7_n2p/doa_pkg_chp_model_p2e4_fast_zse5.list.latest) --apply

# 4) Re-launch simregress (the agent does this; canonical command at top of file)
```

## Output Conventions

- Lines that get auto-fixed are reported as `🔧 Line N:` followed by one indented `Would fix:` / `Fixed:` bullet per detector that fired.
- Suggestion-only items are reported as `⚠ Line N:` with a `⚠ ...` description.
- Special-character removals print the offset and Unicode code point.
- `--no-color` strips ANSI codes (useful when piping output into the watchdog log).

## Files

- `scripts/fix_test_command.py` — main script
- `scripts/fix_test_command.py.pchbak` — frozen PCH original (reference only; do not run)
- `SKILL.md.pchbak` — frozen PCH-flavored skill description (reference only)
