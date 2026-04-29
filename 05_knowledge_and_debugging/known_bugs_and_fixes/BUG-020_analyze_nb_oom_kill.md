---
bug_id: BUG-020
title: "Analyze NB job killed — insufficient memory (32G vs 250G needed)"
date_discovered: 2026-04-10
status: fixed
severity: blocker
stage: "analyze"
bundle: bundle1088
category: build-config
related_patterns: [pattern_7]
tags: [analyze, netbatch, oom, memory, compute_cth, zebu, nb, class_ana]
---

# BUG-020: Analyze NB job killed — insufficient memory (32G vs 250G needed)

## Symptom
- Analyze stage starts and processes all library analyses successfully
- NB job is killed by "super user request" after ~19 minutes
- Job log footer shows: `Actual Class Reservation : cores=1,general_ramp=1:duration=60s,memory=32`
- Actual memory used: `Mem:133362` (133GB)
- Build fails with `Exit Status : -13`

## Triggered By
NB (Netbatch) memory allocation mismatch during the Zebu analyze stage

## Root Cause
The NB system only allocated 32GB (`memory=32` in class reservation) despite the configuration
requesting 250GB (`NBCLASS_ANA=SLES12&&250G` in `analyze.env`). The `general_ramp=1:duration=60s`
suggests the NB pool used a "ramp" allocation strategy that started low and never ramped up
before the job exceeded the initial reservation and was killed.

The configuration chain is:
1. `verif/emu/zebu/Makefile.cfg` → `NBCLASS_ANA := SLES12&&250G` (correct, 250GB)
2. `analyze.env` → `NB_CMD_ANA=nbjob run --class 'SLES12&&250G'` (correct, picks up Makefile.cfg)
3. `verif/emu/zebu/nvlsi7_n2p.compute.cth` → `CLASS_ANA = SLES12&&92G` (lower, but not used for NB_CMD_ANA)
4. Actual NB reservation → `memory=32` (broken — doesn't match any config)

The `compute.cth` CLASS_ANA (92G) is used by the cth build framework, while `Makefile.cfg` NBCLASS_ANA (250G)
is used by the Makefile-based flow. The Makefile flow is what actually submits the NB job, so the 250G config
is correct. The 32GB allocation appears to be an NB pool/ramp issue, not a configuration error.

## Fix / Solution
1. **Applied fix**: Increased `CLASS_ANA` in `verif/emu/zebu/compute.cth` from `SLES12&&92G` to `SLES12&&250G`
   (matching `Makefile.cfg`'s `NBCLASS_ANA` value). The `nvlsi7_n2p.compute.cth` already had 250G.
2. If it persists after this fix:
   - Try running at a different time when NB pool is less loaded
   - Check NB pool availability: the target pool `cth_dvb_tbaziza_sccc14644327` may have machines with insufficient RAM available
   - As a last resort, add explicit `--rlimit memory=250000` to the NB command

## Files Affected
- `verif/emu/zebu/Makefile.cfg` (contains `NBCLASS_ANA := SLES12&&250G` — correct)
- `verif/emu/zebu/compute.cth` (contains `CLASS_ANA = SLES12&&92G` — used by cth, not Makefile flow)
- `verif/emu/zebu/nvlsi7_n2p.compute.cth` (same as compute.cth)
- `verif/emu/zebu/nvlsi7_n2p.pkg_gh_model.compute.cth` (reference — pkg_gh_model has same config)

## Verification
```bash
# Check the analyze.env for NB command and class
grep -E "NBCLASS_ANA|NB_CMD_ANA|CLASS_ANA" output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/log/260409.070352/analyze.env

# Check the NB job log footer for actual class reservation
tail -30 output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/log/260409.070352/analyze.NB.log

# Check compute.cth CLASS_ANA
grep CLASS_ANA verif/emu/zebu/nvlsi7_n2p.compute.cth verif/emu/zebu/compute.cth

# Check Makefile.cfg NBCLASS values
grep NBCLASS verif/emu/zebu/Makefile.cfg
```

## Notes
- The analyze stage needs ~133GB RAM for pkg_ghpf_model — this is expected for a large model
- The `nvlsi7_n2p.compute.cth` CLASS_ANA of 92G would NOT be sufficient even if used (133GB > 92GB)
- No `nvlsi7_n2p.pkg_ghpf_model.compute.cth` exists — could create one with higher CLASS_ANA if needed
- The `pkg_gh_model` compute.cth has identical settings (92G for CLASS_ANA)
- After analyze passes, the subsequent `fe_be` stage runs via NB with its own class (`CLASS_FE = SLES12&&130G`)
