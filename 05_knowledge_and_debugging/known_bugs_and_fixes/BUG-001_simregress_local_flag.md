---
bug_id: BUG-001
title: "simregress -local flag causes tests to go to .no_run"
date_discovered: 2026-03-29
status: fixed
severity: blocker
stage: "test submission"
bundle: bundle1068
category: build-config
related_patterns: []
tags: [simregress, local, trex, emurun, zebu, no_run]
---

# BUG-001: simregress -local flag causes tests to go to .no_run

## Symptom
(no error — all 2 tests silently placed in .no_run file with label "trex")

## Triggered By
`simregress -dut nvlsi7_n2p ... -local -l reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list`

## Root Cause
The `-local` flag in `simregress`/`ifeed` runs jobs sequentially on the current host. However, these are T-REX emulation tests (`-m emurun -zebu`) that require actual Zebu hardware, which is only accessible via NB farm submission. With `-local`, `ifeed` cannot dispatch to Zebu hardware and puts all tests in `.no_run` instead of submitting them.

## Fix / Solution
Remove `-local` from the simregress command to allow NB farm submission:
```
simregress -dut nvlsi7_n2p -save -no_xs -trex -emu_model pkg_ghpf_model -emu_tech zse5 -no_compress EMUL_QSLOT=/prj/sv/nvl/emu/interactive -trex- -l reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list
```
This allows the T-REX orchestration to allocate a real Zebu machine from the NB farm.

## Files Affected
None (command-line issue only)

## Verification
Confirm tests are no longer placed in `.no_run` and are submitted to the NB farm.

## Notes
Use simregress without `-local` for any T-REX emulation tests that require Zebu hardware.
