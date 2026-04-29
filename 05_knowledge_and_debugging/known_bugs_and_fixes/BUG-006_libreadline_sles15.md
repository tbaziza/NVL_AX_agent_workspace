---
bug_id: BUG-006
title: "libreadline.so.7 missing on SLES15 FM machines"
date_discovered: 2026-03-29
status: fixed
severity: blocker
stage: "test execution"
bundle: bundle1068
category: library
related_patterns: []
tags: [libreadline, SLES15, SLES12, hub_ifp, LD_PRELOAD, FM, zebu]
---

# BUG-006: libreadline.so.7 missing on SLES15 FM machines

## Symptom
testbench: [emu.engine error] {emu.engine 0x0 0} {0 ps} libreadline.so.7: cannot open shared object file: No such file or directory
\* spacedoa   Result: FAILED  SimTime: 0 clocks

## Triggered By
`simregress ... -emu_model pkg_ghpf_model -emu_tech zse5 ...` — tests submitted to FM Zebu hardware farm (`fm_zse` queue), executed on SLES15 machines at Folsom site

## Root Cause
`hub_ifp.so` (the hub interface .so at `output/nvlsi7_n2p/hub_ifp/hub_ifp.so`) was compiled on SLES12 and links against `libreadline.so.7`. The Zebu hardware execution machines at Folsom (`fm_zse` queue, e.g. `fmez5175`) are SLES15 which ships with `libreadline.so.8` — `libreadline.so.7` is not present on those machines.

## Fix / Solution
1. Copy `libreadline.so.7` from the local machine into the workspace (accessible via NFS from FM):
```bash
cp /lib64/libreadline.so.7 output/nvlsi7_n2p/hub_ifp/libreadline.so.7
cp /lib64/libreadline.so.7.0 output/nvlsi7_n2p/hub_ifp/libreadline.so.7.0
```
2. Add readline to `LD_PRELOAD` in the emurun plugin `verif/emu/plugins/emurun/zebu_libstdc_override.pm`:
```perl
&emu::test::addEnv('LD_PRELOAD' => '$WORKAREA/output/nvlsi7_n2p/hub_ifp/libreadline.so.7');
```
The `$WORKAREA` variable is expanded by emurun at test-launch time to the workspace NFS path accessible from the FM machines.

## Files Affected
- `verif/emu/plugins/emurun/zebu_libstdc_override.pm` (added readline LD_PRELOAD)
- `output/nvlsi7_n2p/hub_ifp/libreadline.so.7` (copied from /lib64/)
- `output/nvlsi7_n2p/hub_ifp/libreadline.so.7.0` (copied from /lib64/)

## Verification
Re-run tests on FM SLES15 machines and confirm `hub_ifp.so` loads without libreadline errors.

## Notes
See also BUG-012 for a more refined fix placing libreadline in `zse5/lib/` with LD_PRELOAD.
