---
bug_id: BUG-004
title: "Compilation PP doesn't support P2P delegation"
date_discovered: 2026-03-29
status: fixed
severity: blocker
stage: "test submission"
bundle: bundle1068
category: infrastructure
related_patterns: []
tags: [simregress, PP, P2P, feeder, NB, delegation, queue]
---

# BUG-004: Compilation PP doesn't support P2P delegation

## Symptom
WARN: Queue cth_dvb_tbaziza_sccc14644327 is not responding, it may be down
Dont know yet version of resource cth_dvb_tbaziza_sccc14644327[null] - will not query its jobs

## Triggered By
`simregress -P cth_dvb_tbaziza_sccc14644327 ...` (using the compilation PP as the test submission pool)

## Root Cause
The compilation PP feeder (`cth_dvb_tbaziza_sccc14644327`) does NOT support P2P (feeder-to-feeder) delegation — its Command port is `-1` (disabled). A test feeder routing through it via `Queue cth_dvb_tbaziza_sccc14644327 {...}` can never connect; jobs stay in "Wait" indefinitely.

## Fix / Solution
Use the NB queue directly: `Queue zsc11_express { Qslot /IVE/NVL/emu ... }` instead of routing through the compilation PP.
The correct simregress command is:
```
simregress -dut nvlsi7_n2p -save -no_xs -trex -emu_model pkg_ghpf_model -emu_tech zse5 \
  -no_compress EMUL_QSLOT=/prj/sv/nvl/emu/interactive -trex- \
  -P zsc11_express -Q /IVE/NVL/emu \
  -l reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list
```

## Files Affected
None (command-line issue)

## Verification
Confirm tests are submitted directly to `zsc11_express` queue and are dispatched to NB farm without "Queue not responding" warnings.

## Notes
Never use the compilation PP feeder as the test submission pool — its Command port is disabled.
