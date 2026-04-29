---
title: "Debug Workflow — Log Analysis &amp; Troubleshooting Protocol"
module: 05_knowledge_and_debugging
tags: [debug, workflow, logs, troubleshooting, errors, root-cause]
---

# Debug Workflow — Log Analysis &amp; Troubleshooting Protocol

## Step 1: Identify the Failure Type

### Build Failure
```bash
# Check if build failed
cat output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/log/<TIMESTAMP>/failure_info.log 2>/dev/null || echo "no failure"

# Check top-level verdict
grep -E "PASSED|FAILED|Exit status" output/grdlbuild/logs/emu_build.zebu.pkg_ghpf_model_zse5.log | tail -10
```

### Test Failure
```bash
# Check test results
cat regression/nvlsi7_n2p/doa_pkg_ghpf_model_zse5.list.N/<test>/results.log
cat regression/nvlsi7_n2p/doa_pkg_ghpf_model_zse5.list.N/<test>/assertion_failures.log
cat regression/nvlsi7_n2p/doa_pkg_ghpf_model_zse5.list.N/<test>/postmortem.log | head -5
```

## Step 2: Find the Error

### Build Errors
```bash
ZSE5="output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5"
LOGDIR="$ZSE5/log/<TIMESTAMP>"

# Find which Zebu sub-stage failed
grep "abnormal task termination" "$LOGDIR/fe_be.NB.log" | grep -v "aborted" | tail -10

# Read the specific stage log
grep -i "error\|fatal\|fail" "$ZSE5/zcui.work/zCui/log/backend_default_<STAGENAME>.log" | grep -v "^#.*warning" | tail -20
```

### Test Errors
```bash
# Check logbook for exit status
grep -E "EXIT|FAIL|ERROR|exit" regression/.../logbook.log | tail -10

# Check testbench for runtime errors
grep -i "error\|fatal\|cannot" regression/.../testbench.log | head -20

# Check emurun for infrastructure errors
grep -i "error\|fail\|warning" regression/.../emurun.log | tail -20
```

## Step 3: Cross-Reference with Known Bugs

1. Search `known_bugs_and_fixes/` directory for matching error text
2. Check `common_patterns.md` for the error category
3. If match found → apply documented fix
4. If no match → continue to Step 4

## Step 4: Root Cause Analysis

### Checklist
1. Check `failure_info.log` — gives stage name and captured error lines
2. Open the stage's log file listed in `failure_info.log`
3. Search for `ERROR:`, `Fatal:`, `Error 1`, `No such file`, `cannot stat`
4. Check if the error is a known pattern (see `common_patterns.md`)
5. If a missing binary/script: check if path exists; check shebang line
6. If a missing file: determine if it should have been generated or came from IPX
7. If disk-related: check `df` output; free space; restart the failed stage
8. If permissions: check ownership (`ls -la`), group membership (`id`), symlink target

## Step 5: Document the Fix

After resolving the issue:
1. Create a new file in `known_bugs_and_fixes/` using `bug_template.md`
2. Include exact error text, exact fix commands, files affected, verification steps
3. Update `common_patterns.md` if applicable
4. Update `commands_reference.md` if you used new commands
