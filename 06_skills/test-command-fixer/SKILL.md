---
name: test-command-fixer
description: >-
  Automatically detect and fix common errors in PCH validation testlist files, including
  unpaired tags, missing model arguments, special characters, unbalanced pairs, and
  spacing violations. Use this skill when debugging simregress command failures related
  to incorrect test run commands, unknown switches, or malformed testlist entries.
  Triggers: testlist error, simregress failure, unpaired tag, malformed testlist, test
  command fix, unknown switch, testlist syntax error.
---

# Test Command Fixer

## Overview

Automatically fix common testlist command errors in PCH validation workflows that cause simregress failures. The skill detects 14+ error categories including unpaired `-simv_args-` and `-user_do_files_vcs-` tags, missing `-model` arguments, special characters (like `\x00`), spacing violations, and unbalanced tag pairs.

## When to Use This Skill

Trigger this skill when encountering:
- Simregress failures with "Unknown switches" errors
- Testlist bucket errors mentioning `-simv_args-` or `-user_do_files_vcs-`
- "NO TEST RESULTS REPORTED FROM MODEL TOOL" errors
- File not found errors for relative include paths
- Copy-paste corruption with special characters
- Need to validate or fix testlist syntax before running regression

## Quick Start

The skill provides the `fix_test_command.py` script with three modes:

**1. Preview Mode (Default - Safe)**
```bash
python3 scripts/fix_test_command.py testlist.list
```
Shows what would be fixed without modifying the file.

**2. Apply Auto-Fixes**
```bash
python3 scripts/fix_test_command.py testlist.list --apply
```
Applies safe automatic fixes and modifies the file.

**3. Apply All Fixes (Auto + Suggested)**
```bash
python3 scripts/fix_test_command.py testlist.list --apply-suggested
```
Applies all fixes including suggested fixes that may need review.

## Error Categories Detected

### Auto-Fixes (Applied with --apply)

1. **Unpaired Closing Tags** (Bucket 1)
   - Pattern: `-simv_args-` without matching `-simv_args`
   - Fix: Remove unpaired closing tag
   - Example: `test -simv_args- -dut pchlp` → `test -dut pchlp`

2. **Consecutive Closing Tags**
   - Pattern: `-simv_args- -simv_args-` (duplicate closes)
   - Fix: Remove duplicate closing tag
   - Example: `-simv_args +OPT -simv_args- -simv_args-` → `-simv_args +OPT -simv_args-`

3. **Missing Model Argument** (Bucket 3)
   - Pattern: Command missing `-model <type>`
   - Fix: Add `-model fc_rtl_with_upf` (auto-detected from testlist)
   - Example: `test -dut pchlp` → `test -dut pchlp -model fc_rtl_with_upf`

4. **Relative Include Paths** (Bucket 4)
   - Pattern: `-include flows/common.tcl` (relative path)
   - Fix: Add `$WORKAREA/` prefix
   - Example: `-include flows/common.tcl` → `-include $WORKAREA/flows/common.tcl`

5. **Special Characters**
   - Pattern: Literal escape sequences like `\x00`, `\u200b`
   - Fix: Remove special character
   - Example: `test -dut pchlp\x00` → `test -dut pchlp`

6. **File Existence Checks**
   - Pattern: `-user_do_files_vcs nonexistent.do`
   - Warning: File not found (does not auto-fix)

### Suggested Fixes (Applied with --apply-suggested)

7. **Unbalanced Tag Pairs**
   - Pattern: More opens than closes (or vice versa)
   - Fix: Smart placement of missing closing tags after last plusarg
   - Example: `-simv_args +OPT1 +OPT2 -pch_fw` → `-simv_args +OPT1 +OPT2 -simv_args- -pch_fw`

8. **Spacing Violations** (8 types)
   - Missing space between plusargs: `+OPT1+OPT2` → `+OPT1 +OPT2`
   - Missing space before opening tag: `-fw-simv_args` → `-fw -simv_args`
   - Missing space after opening tag: `-simv_args+OPT` → `-simv_args +OPT`
   - Missing space before closing tag: `+OPT-simv_args-` → `+OPT -simv_args-`
   - Missing space after closing tag: `-simv_args--dut` → `-simv_args- -dut`

9. **Consecutive Opening Tags**
   - Pattern: `-simv_args -simv_args` (duplicate opens without close between)
   - Fix: Add closing tag between them
   - Example: `-simv_args +OPT1 -simv_args +OPT2` → `-simv_args +OPT1 -simv_args- -simv_args +OPT2`

## Common Usage Patterns

### Validate Testlist Before Regression
```bash
# Preview all issues
python3 scripts/fix_test_command.py my_testlist.list

# Fix auto-fixable issues
python3 scripts/fix_test_command.py my_testlist.list --apply
```

### Fix Simregress Bucket Errors
When simregress reports bucket errors like:
```
Bucket 1: Unknown switches: '-simv_args-' (2 tests)
Bucket 3: NO TEST RESULTS REPORTED FROM MODEL TOOL !!! (1 test)
```

Run the fixer to identify and resolve:
```bash
python3 scripts/fix_test_command.py testlist.list --apply
```

### Handle Complex Unbalanced Cases
For unbalanced tag pairs (requires review):
```bash
# Preview the suggested fix first
python3 scripts/fix_test_command.py testlist.list

# If suggested fix looks correct, apply it
python3 scripts/fix_test_command.py testlist.list --apply-suggested
```

## Advanced Options

```bash
# Specify model type manually
python3 scripts/fix_test_command.py testlist.list --model fc_dfd_rtl_with_upf

# List available model types
python3 scripts/fix_test_command.py --list-models

# Disable color output (for log files)
python3 scripts/fix_test_command.py testlist.list --no-color

# Specify WORKAREA path for relative includes
python3 scripts/fix_test_command.py testlist.list --workarea /path/to/workarea
```

## Smart Balanced Fix Algorithm

The skill uses an intelligent algorithm for fixing unbalanced tag pairs:

1. **Tracks open/close state** while iterating through command parts
2. **Detects natural block boundaries** where plusargs end
3. **Handles quoted plusargs** like `"+vcs+learn+pli"`
4. **Inserts closing tags** at the correct location (after last plusarg, before non-plusarg)
5. **Prevents consecutive closes** during insertion

Example:
```bash
# Before: Missing close after first block
-simv_args +OPT1 +OPT2 -pch_fw -simv_args +OPT3 -simv_args- -dut pchlp

# After: Close added at natural boundary
-simv_args +OPT1 +OPT2 -simv_args- -pch_fw -simv_args +OPT3 -simv_args- -dut pchlp
```

## Understanding the Output

### Preview Mode Output
```
🔧 Line 5:
   Would fix: Added missing '-model fc_rtl_with_upf' (using default)
   ⚠ Unbalanced -simv_args: 1 open, 0 close (may need manual review)
```

### Fix Mode Output
```
✅ AUTO-FIXES APPLIED:
   Before: test -simv_args +OPT -dut pchlp
   After:  test -simv_args +OPT -dut pchlp -model fc_rtl_with_upf

💡 SUGGESTED FIX (requires --apply-suggested flag):
   Suggested line: test -simv_args +OPT -simv_args- -dut pchlp -model fc_rtl_with_upf
```

## Invoking the Script

To use the test command fixer, invoke the bundled Python script:

```bash
python3 scripts/fix_test_command.py <testlist_file> [options]
```

The script is self-contained and has no external dependencies beyond Python 3 standard library (sys, re, argparse, pathlib).

## Resources

### scripts/fix_test_command.py
The main command fixer script with comprehensive error detection and fixing capabilities. Includes:
- 14+ error category detectors
- Smart balanced fix algorithm for tag pairs
- Auto-detection of model types from testlist
- File existence validation
- Special character detection
- Detailed error visualization with line numbers and highlighting

## Usage from the SLE Emulation Agent

The SLE Emulation Agent (via `sle_emulation_agent` task) automatically invokes this skill to fix common grdlbuild and simregress command errors:

### Detected Errors

- **grdlbuild command not found**: When the SLE agent detects a build target not recognized by grdlbuild.
- **Misspelled grdlbuild flags**: Common typos such as `-Penv=immidiate` (should be `-Penv=immediate`).
- **Unknown grdlbuild targets**: Invalid target names that don't match one of the standard SLE targets.
- **simregress typos**: Accidental flag additions (e.g. accidentally adding `-local` to a simregress invocation; see BUG-001 in the SLE knowledge base).

### Valid grdlbuild Targets

The SLE Emulation Agent uses the following valid build targets:
- `pkg_ghpf_model_zse5` — GHPF emulation model
- `pkg_chp_model_p2e4_fast_zse5` — CHP fast model (ZSE5)
- `pkg_chp_hubs_full_model_p2e4_zse5` — CHP full model with hubs (ZSE5)
- `pkg_chp_model_p2e4_zse5` — CHP standard model (ZSE5)

### Valid Emulation Environment Flags

- `-Penv=immediate` — Fresh build (rebuild from source)
- `-id` — Resume build (incremental/incremental debug mode)

### How It Works

When the SLE agent encounters a build or test invocation error, it extracts the command from logs and invokes this skill to:
1. Detect the error category (misspelled flag, unknown target, typo in simregress args, etc.)
2. Map the user's intent to a valid target or flag using the script's error detectors
3. Suggest or apply the corrected command
4. Return the fixed command for the SLE agent to retry the build/test

This integration ensures that transient command typos and environment misconfiguration do not block the SLE emulation workflow.
