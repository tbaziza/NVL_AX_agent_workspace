---
bug_id: BUG-032
title: "FM Board g513 Died After ~17h10m — spacedoa Auto-Requeued to g508"
date_discovered: 2026-04-28
status: informational
severity: informational
stage: "FM emulation runtime"
bundle: bundle1106
category: monitoring
related_patterns: [pattern_board_failure, pattern_auto_requeue]
tags: [fm, board-failure, g513, requeue, emurun, zse5, emulation]
---

# BUG-032: FM Board g513 Died After ~17h10m — spacedoa Auto-Requeued to g508

## Symptom

FM board **g513** experienced an abnormal exit at approximately **03:40 AM PDT April 28, 2026**,
which is ~17h10m after the spacedoa emulation started on g513 (accepted 10:30:45 AM April 27).

The g513 job exited with one of the abnormal exit codes (likely 137=SIGKILL or 144=board crash),
triggering the automatic requeue mechanism.

## Triggered By

spacedoa_mobile emulation job running on FM board g513 in `.list.2/external/` — board died ~6 minutes before expected cycle limit completion.

## Root Cause

The emurun command was submitted with:
```
--on-job-finish 'exitstatus=137||exitstatus=138||exitstatus=140||exitstatus=162||exitstatus=165||
                 exitstatus=163||exitstatus=164||exitstatus=166||exitstatus=144:requeue(10)'
```
The g513 job exited with one of these abnormal exit codes (likely 137=SIGKILL or 144=board crash),
triggering the automatic requeue mechanism.

**Note**: The board died only ~6 minutes before the expected cycle limit. This may be coincidence
(hardware failure) or the board's exit code for cycle-limit SIGTERM was one of the requeue codes.

## Fix / Solution

None needed — emurun auto-requeue handled recovery automatically. Continue monitoring
feeder job 30002 (NB status "Run") and logbook for g508 emulation progress.

**If g508 also dies**: emurun will requeue again (up to 10 times per the `requeue(10)` spec).

**What emurun Did (Automatic Recovery)**:
```
g513 job exits with abnormal code → on-job-finish requeue condition matches → 
emurun submits to express queues: g509 → g508 → ... → g508 accepted (03:40:46 AM)
→ new emulation starts from scratch on g508
```

## Files Affected

- None (hardware failure + automatic recovery)

## Verification

### Evidence

- `emurun.log` last entry: `Tue Apr 28 03:40:46 2026: Your job has been queued (JobID 83627045, Class EXPR, Queue fm_zse5_g508_express, Slot /prj/sv/nvl/emu/interactive)` → requeue to g508
- `logbook.log` grew +150 bytes at 03:40 AM (from 350004B → 350154B): partial rsync of initial queue lines was dumped when g513 died
- `emurun.log` and `gecco.submission.*.log` both updated at `Apr 28 03:40`
- NB feeder job 30002 still shows "Run" → feeder alive, managing the retry on g508

### Timing Analysis

| Metric | Value |
|--------|-------|
| g513 start (accepted) | Mon Apr 27 10:30:45 AM PDT |
| g513 died | Tue Apr 28 ~03:40 AM PDT |
| g513 runtime | ~17h10m |
| Expected cycle limit (@26% speed) | ~17h16m |
| Delta to expected cycle limit | ~6 minutes early |
| g508 requeue time | Tue Apr 28 03:40:46 AM PDT |

## Notes

### Impact

1. All 17h10m of spacedoa emulation on g513 is **lost** — no partial results saved
2. Job restarted from SimTime 0 on g508 at ~03:40 AM April 28
3. g508 board speed unknown — estimated ~17h more wait time if at similar speed
4. New expected spacedoa completion: ~Tue Apr 28 08:40 PM PDT (if g508 = g513 speed)

**Severity**: CRITICAL DELAY — 17h of emulation lost, full restart required.
Discovered: Tue Apr 28 03:40 AM PDT (poll 83 at 03:46 AM showed +150B logbook growth).
Test affected: spacedoa_mobile (.list.2/external/).
