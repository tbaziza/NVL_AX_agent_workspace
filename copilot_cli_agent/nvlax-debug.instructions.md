---
applyTo: "**"
---

# Step 4: Debug Failures

When compilation or DOA tests fail, follow this procedure.

## Step 4a: Detect Which Phase Failed (90 seconds max)

```
Parse logbook.log stage table:
  "Test build" FAIL    → PHASE: BUILD
  "Model run" FAIL     → Check emurun.log:
     "force.*error"     → BUILD (compile issue leaked to runtime)
     "plugin.*fail"     → EMU_SETUP
     "timeout"/"WMTRUN" → RUNTIME
     No errors          → TEST_EXECUTION
  "Post processing" FAIL → POST_PROCESS
  All PASS but FAILED    → POST_PROCESS (SVA/TLM check failed)
```

Quick command:
```bash
zgrep -A 10 "Stage.*Elapsed.*Status" logbook.log.gz | tail -6
```

## Step 4b: Collect Symptoms (60 seconds max)

| Phase | Primary Logs | Search For |
|-------|-------------|------------|
| BUILD | grdlbuild output, `.shadow/` | `Error:`, `undefined`, missing modules |
| EMU_SETUP | emurun.log, testbench.log | `plugin`, `license`, `RPATH` |
| RUNTIME | emurun.log, ptracker.log | `timeout`, `RASSERT`, `mailbox` |
| TEST_EXECUTION | bootfsm_state_tracker.log.gz, uop_log_*.log | Stuck FSM, no `[PERSPEC]` |
| POST_PROCESS | assertion_failures.log, DEBUG | SVA violations, TLM errors |

Symptom expansion rules:
- `mailbox/timeout` → also check `ptracker*` for request/response
- `boot/hang/fsm` → also check `bootfsm*` for state/secure/protocol
- `kerberos/expired` → check `emurun*` for kinit/ticket/ssh/exit_66
- `memory/corruption` → check `*ddr*` for read/write/timing

## Step 4c: Match Known Bugs (30 seconds max)

There are 34 BUG files (BUG-001 to BUG-034) in the KB. ALWAYS search them before investigating from scratch.

**Search by symptom text:**
```bash
grep -rl "<error_text>" $KB_ROOT/05_knowledge_and_debugging/known_bugs_and_fixes/
```

**Search by phase:**
```bash
grep -l "stage:.*runtime" $KB_ROOT/05_knowledge_and_debugging/known_bugs_and_fixes/BUG-*.md
```

**Search by category (build-config | library | environment | runtime | test):**
```bash
grep -l "category:.*library" $KB_ROOT/05_knowledge_and_debugging/known_bugs_and_fixes/BUG-*.md
```

**Search by tag:**
```bash
grep -l "rpath\|dlopen\|symlink" $KB_ROOT/05_knowledge_and_debugging/known_bugs_and_fixes/BUG-*.md
```

**Automated scoring (ranks top-3 matches with confidence):**
```bash
$KB_ROOT/05_knowledge_and_debugging/run_phase_detection_nvlax.sh <test_directory>
```

Also check `common_patterns.md` for the 21 recurring failure patterns — these are broader than individual BUG files.

## Step 4d: Apply Fix and Re-Run

- If known bug matched → apply the documented fix → re-run Step 1 or Step 3
- If no match → gather full debug data → present to user → document as new BUG file

## Scoring Algorithm (Bug Match Confidence)

| Signal | Weight |
|--------|--------|
| Exact tag match | +50 pts |
| Category match | +30 pts |
| Phase match | +5 pts |
| Phase mismatch | x0.5 penalty |
| Critical symptom | +10 pts |

Confidence: >=200 VERY HIGH, 50-99 HIGH, 15-29 MEDIUM, <15 LOW
