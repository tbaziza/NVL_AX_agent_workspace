---
bug_id: BUG-012
title: "hub_ifp.so needs libreadline.so.7 via LD_PRELOAD"
date_discovered: 2026-03-29
status: fixed
severity: blocker
stage: "test execution"
bundle: bundle1068
category: library
related_patterns: []
tags: [hub_ifp, libreadline, LD_PRELOAD, FM, gecco, SLES15, SLES12, ABI]
---

# BUG-012: hub_ifp.so needs libreadline.so.7 via LD_PRELOAD

## Symptom
[emu.engine error] {emu.engine 0x0 0} {0 ps} libreadline.so.7: cannot open shared object file: No such file or directory
simics.SimExc_IllegalValue: load_lib attribute in emu.engine object: error loading lib
(seen in `testbench.log` and `emurun.log`)

## Triggered By
`init_before_connect.py` calls `emu.engine.load_lib = hub_ifp.so`; hub_ifp.so needs libreadline.so.7

## Root Cause
- `hub_ifp.so` (loaded via Simics `load_lib`) depends on `libreadline.so.7`
- The FM gecco environment's `LD_LIBRARY_PATH` does NOT include `/lib64` or any path with libreadline.so.7
- `addEnv('LD_LIBRARY_PATH')` in emurun plugins does NOT propagate to FM gecco env
- `addEnv('LD_PRELOAD')` DOES propagate to FM gecco env
- The build host (SLES15) has `libreadline.so.7.0` at `/lib64/libreadline.so.7.0` (despite being SLES15)

## Fix / Solution
```bash
# Copy readline to NFS-accessible workspace location
cp /lib64/libreadline.so.7.0 output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/lib/libreadline.so.7.0
ln -sf libreadline.so.7.0 output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/lib/libreadline.so.7
# Add to LD_PRELOAD in zebu_libstdc_override.pm (LD_PRELOAD propagates to FM, LD_LIBRARY_PATH does NOT):
# &emu::test::addEnv('LD_PRELOAD' => '$WORKAREA/output/.../zse5/lib/libreadline.so.7.0');
```

## Files Affected
- `output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/lib/libreadline.so.7.0` (copied binary)
- `output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/lib/libreadline.so.7` (symlink)
- `verif/emu/plugins/emurun/zebu_libstdc_override.pm` — added LD_PRELOAD for libreadline.so.7.0

## Verification
**CONFIRMED FIXED** (run .12: hub_ifp.so loaded successfully; readline symbol size mismatch warning is non-fatal; simulation progressed past library loading)

## Notes
**Key Technical Detail**:
- When a library is in LD_PRELOAD, it is loaded into the process BEFORE any other libraries. When
  hub_ifp.so is dlopen'd and needs libreadline.so.7, the dynamic linker finds the already-loaded
  preloaded copy — no RPATH/LD_LIBRARY_PATH needed.
- RULE: For FM library fixes, always use LD_PRELOAD (not LD_LIBRARY_PATH) in zebu_libstdc_override.pm
- `hub_ifp.so` RPATH paths are all in `/p/hdk/rtl/cad/x86-64_linux412/...` (NFS paths accessible from FM)
- `libxtmp.so`, `libxtparams.so` (also needed by hub_ifp.so) are found via hub_ifp.so's RPATH

**Caveat**: `libreadline.so.7.0` copied from SLES15 build host has `libtinfo.so.6` dep (SLES15) vs FM SLES12's `libtinfo.so.5`. This causes `Symbol 'rl_readline_state' has different size` warning. Non-fatal, but for a cleaner fix: find SLES12-built libreadline.so.7 to avoid the ABI mismatch warning.
