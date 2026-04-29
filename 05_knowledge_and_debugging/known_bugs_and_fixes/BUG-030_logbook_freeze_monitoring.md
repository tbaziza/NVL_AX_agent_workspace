---
bug_id: BUG-030
title: "ZSE5 Logbook Freeze During Emulation — Monitoring Pitfall"
date_discovered: 2026-04-27
status: informational
severity: informational
stage: "FM emulation runtime"
bundle: all
category: monitoring
related_patterns: [pattern_monitoring, pattern_emulation]
tags: [zse5, logbook, monitoring, netbatch, wait-remote, emulation, zebu]
---

# BUG-030: ZSE5 Emulation Logbook Freeze During Active Run (Monitoring Pitfall)

## Symptom

During Zebu ZSE5 emulation, the `logbook.log` file is written only during pre/post phases.
Once the FM emulation job is running on hardware, the logbook freezes at the last "queued" message:
```
emurun: Mon Apr 27 05:26:17 2026: Your job has been queued (JobID 83602489, Class EXPR, Queue fm_zse5_g506_express, ...)
```
No new log lines appear for the duration of emulation — which can be several hours (e.g., 5+ hours for 50ms of simulated time at ~10ms/hr Zebu rate).

**Why it looks like a stuck job**:
- `nbstatus jobs --target fm_zse` shows "Wait Remote" from local NB feeder for the entire run duration
- `nbstatus jobs --target fm_zse5_gNNN_express` shows "Wait Virtual" on each board
- `nbstatus remote-availability` shows 0 available ZSE5 resources
- The "Workstation" column in FM queue is empty

This combination was mistaken for a stuck/queued job, when in reality the job was actively emulating.

## Triggered By

Monitoring DOA emulation tests during the multi-hour hardware emulation phase and interpreting logbook silence + "Wait Remote/Virtual" NB status as a stuck job.

## Root Cause

- The local NB feeder (sccc14644327.zsc11) acts as a proxy for remote FM site jobs
- "Wait Remote" = NB feeder representation of a job running on a remote FM site
- "Wait Virtual" = FM PPM representation of a job occupying the physical Zebu board
- Logbook writes during emulation go directly from FM host to NFS, bypassing normal NB log streaming
- The logbook ONLY updates at: pre-exec (setup), board acquisition event, and post-exec (tlm_post)

## Fix / Solution

Not a bug — expected behavior. Use correct monitoring approach:

1. Check `logbook.log` SIZE (bytes) — it only grows during pre/post phases. Frozen size = emulating.
2. Check `JOBS_STATUS` file for `END:` or `TESTSTAT:` lines — only written at run completion.
3. Check `emurun.log` for new timestamp lines — updated during board acquisition/release only.
4. Check `nbstatus jobs | grep <NB_job_id>` — should show "Run" state throughout emulation.
5. **DO NOT kill a "Wait Remote" FM job — it is likely actively emulating!**

**Key indicator of active emulation vs truly stuck**:
- Active emulation: NB jobs show "Run", FM jobs show "Wait Remote/Virtual", logbook frozen, NB job has been running for expected emulation time (minutes to hours depending on SimTime target)
- Truly stuck (pre-board): same visual state BUT logbook shows no "queued" events from the last few minutes after initial submission

## Files Affected

- None (monitoring/operational guidance)

## Verification

**Cycle time reference (ZSE5, nvlsi7_n2p pkg_ghpf_model)**:
- Observed: ~10ms emulated time per hour of wall clock time (50ms took ~5 hours)
- spacedoa_mobile: cycle limit 50ms → expected ~5 hours wall time
- spacex_mobile: cycle limit 240ms → expected ~24 hours wall time (may complete earlier if test ends naturally; `.list.1/` spacex naturally ended at 53.2ms SimTime in ~5 hours)

## Notes

**Mistake made** (2026-04-27 10:20 PDT): The `.list.2/` jobs (30002/30003) were mistakenly killed after ~5 hours of active emulation, believing them to be stuck in queue. Both were actually running on FM ZSE5 boards.
- spacedoa was mid-emulation (SIGTERM caught)
- spacex was ~5h into emulation (also SIGTERM'd - "Custom exec limit" is trex's message for any SIGTERM when trex_copyback_on_sigkill=1)

After kill, NB automatically requeued both jobs and re-submitted new FM jobs (83627045/83627218).

**Resolution**: Let jobs run to completion. Do not intervene based on "Wait Remote/Virtual" status alone. Monitor `JOBS_STATUS` file for `END:` status as the authoritative completion signal.
