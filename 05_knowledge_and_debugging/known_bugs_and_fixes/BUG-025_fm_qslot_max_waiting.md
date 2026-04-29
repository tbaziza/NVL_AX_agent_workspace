---
bug_id: BUG-025
title: "FM QSlot /prj/sv/nvl/showstopper Exceeds Waiting-Job Limit"
date_discovered: 2026-04-15
status: fixed
severity: blocker
stage: "FM job submission"
bundle: bundle1088
category: infrastructure
related_patterns: [pattern_fm_qslot]
tags: [fm, qslot, netbatch, job-submission, doa]
---

# BUG-025: FM QSlot `/prj/sv/nvl/showstopper` Exceeds Waiting-Job Limit — Use `/prj/sv/nvl/emu/interactive`

## Symptom

Error in `emurun.log` during FM job submission:
```
Failed to submit job. Failed to Register in Slot /fm_zse/prj/sv/nvl/showstopper
(QSlot prj/sv/nvl/showstopper exceeded qslots limits,
 wait jobs limit has reached user_max_waiting:default=2.0)
```

Additional distinguishing symptoms:
- `emurun.log` ends with `Failed to Register in Slot` (not a Simics crash)
- `logbook.log` shows `Model run ... FAIL` with exit 222 or 4
- `LOGS/PASS/` has `ect_run.pass` (ECT passed), but no `gecco_run.pass`
- No `testbench.log` generated in the test directory

## Triggered By

Running 2 DOA tests (`spacedoa_mobile` + `spacex_mobile`) with `EMUL_QSLOT=/prj/sv/nvl/showstopper` while another user job is already waiting in that slot. The second test's FM job submission fails immediately; T-REX exits with status 4 and marks the test FAIL (ECT passes, FM never runs).

## Root Cause

The `/prj/sv/nvl/showstopper` FM qslot enforces `user_max_waiting=2.0` — at most 2 of your jobs may be waiting for a ZSE5 board at any time. In a typical DOA run, both `spacedoa_mobile` and `spacex_mobile` queue FM jobs simultaneously. If any prior/stale job from the same user occupies a slot (e.g., from a previous failed run still cycling boards), the count hits 2 before the second test can register.

## Fix / Solution

Use `EMUL_QSLOT=/prj/sv/nvl/emu/interactive` instead. This slot has a higher (or unrestricted) per-user waiting-job limit and is appropriate for DOA / validation runs.

```bash
simregress -dut nvlsi7_n2p -save -no_xs -trex -emu_model pkg_ghpf_model -emu_tech zse5 \
  -no_compress EMUL_QSLOT=/prj/sv/nvl/emu/interactive -trex- \
  -P zsc11_express -Q /IVE/NVL/emu \
  -l reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list
```

> **Note**: Do NOT confuse the `EMUL_QSLOT` value (`/prj/sv/nvl/emu/interactive`) with running the test in "interactive" (local/foreground) mode. The test is still submitted to the NB farm in batch mode; `EMUL_QSLOT` is just the FM hardware reservation slot name.

## Files Affected

- None (command-line/qslot selection only)

## Verification

Submit DOA tests with `EMUL_QSLOT=/prj/sv/nvl/emu/interactive` and confirm FM jobs are accepted without `Failed to Register in Slot` errors.

## Notes

Always use `EMUL_QSLOT=/prj/sv/nvl/emu/interactive` for DOA runs to avoid hitting the `user_max_waiting` limit on the showstopper qslot.
