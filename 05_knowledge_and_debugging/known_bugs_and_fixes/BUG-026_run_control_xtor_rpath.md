---
bug_id: BUG-026
title: "run_control_xtor_adapter.so RPATH — Simics namespace isolation blocks libRunControlDriverAdapter.so"
date_discovered: 2026-04-15
status: fixed
severity: blocker
stage: "Simics initialization"
bundle: bundle1088
category: library
related_patterns: [pattern_rpath, pattern_simics_module]
tags: [simics, rpath, dlopen, namespace-isolation, adapter, zse5]
---

# BUG-026: `run_control_xtor_adapter.so` Cannot Load — `libRunControlDriverAdapter.so` Not Found in Simics Module Namespace

## Symptom

Error in `testbench.log` at `[0:0ps]` during Simics initialization:
```
[0:0ps][PyDohRun] loading module run_control_xtor_adapter
Traceback (most recent call last):
  ...
  simics.SIM_load_module("run_control_xtor_adapter")
simics.SimExc_General: Failed to load module 'run_control_xtor_adapter'
  ('...simics_workspace/linux64/lib/run_control_xtor_adapter.so'):
  "libRunControlDriverAdapter.so: cannot open shared object file: No such file or directory"
```

Test continues running in degraded mode but exits with status 1 after the full wall-time limit (~41 min for spacedoa). `TestEndChecker` DPI call count = 0 (no pass signal ever detected). `postmortem.log` says PASS but `logbook.log` says FAIL with exit status 1.

## Triggered By

DOA test run on ZSE5 FM board via T-REX/emurun; happens when `run_control_xtor_adapter` Simics module is loaded in Simics's isolated module-loading namespace.

## Root Cause

Simics uses an isolated dlopen namespace for loading its modules (`SIM_load_module`). This namespace does NOT inherit the process's `LD_PRELOAD` libraries or `LD_LIBRARY_PATH` entries. When loading `run_control_xtor_adapter.so`, the dynamic linker searches for its dependency `libRunControlDriverAdapter.so` using only:
1. The RPATH embedded in `run_control_xtor_adapter.so` (only gcc compiler paths: `/usr/intel/pkgs/gcc/12.2.0/lib64:/usr/intel/pkgs/gcc/12.2.0/lib`)
2. Standard system paths

`libRunControlDriverAdapter.so` is not in any of those locations → "No such file or directory".

Although `LD_PRELOAD` loads `libRunControlDriverAdapter.so` into the main process namespace (confirmed by gecco.submission.log showing the path at 05:17:41), the Simics module loader's isolated namespace cannot see it.

## Fix / Solution

Two complementary changes:

**Step 1**: Copy `libRunControlDriverAdapter.so` into `simics_workspace/linux64/lib/` (same directory as `run_control_xtor_adapter.so`):
```bash
cp output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/lib/libRunControlDriverAdapter.so \
   output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/simics_workspace/linux64/lib/
chmod 755 output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/simics_workspace/linux64/lib/libRunControlDriverAdapter.so
```

**Step 2**: Patch `$ORIGIN` into the RPATH of `run_control_xtor_adapter.so` so the dynamic linker searches the `.so`'s own directory for its dependencies (using Python since `patchelf` is not available):
```python
target = "output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/simics_workspace/linux64/lib/run_control_xtor_adapter.so"
with open(target, 'rb') as f:
    data = bytearray(f.read())
old = b'/usr/intel/pkgs/gcc/12.2.0/lib64:/usr/intel/pkgs/gcc/12.2.0/lib'
new = b'$ORIGIN:/usr/intel/pkgs/gcc/12.2.0/lib64'
idx = data.find(old)
data[idx:idx+len(old)] = new + b'\x00' * (len(old) - len(new))
with open(target, 'wb') as f:
    f.write(data)
```

After this, `readelf -d run_control_xtor_adapter.so | grep RPATH` shows:
`$ORIGIN:/usr/intel/pkgs/gcc/12.2.0/lib64`

The `$ORIGIN` token causes the dynamic linker to search the directory of `run_control_xtor_adapter.so` for its dependencies, regardless of namespace isolation.

> **Important re-apply note**: If `fix_zse5_libs.sh` is re-run, it does NOT touch `simics_workspace/linux64/lib/`. However, if a new `fe_be` build replaces `run_control_xtor_adapter.so`, the RPATH patch must be re-applied and `libRunControlDriverAdapter.so` must be re-copied.

## Files Affected

Modules patched with `$ORIGIN` RPATH (`/usr/intel/pkgs/gcc/12.2.0/lib64:/usr/intel/pkgs/gcc/12.2.0/lib` → `$ORIGIN:/usr/intel/pkgs/gcc/12.2.0/lib64`):
- `run_control_xtor_adapter.so` (first fix applied)
- `signal_control_xtor_adapter.so` (second fix applied)
- `libIdiPyDohXtorAdapter.so`
- `libIosfSbXtorAdapter.so`
- `libStreampcieXtorAdapter.so`
- `libjemsimics.so`
- `sblink_pch_device.so`
- `zse_engine.so`
- `zse_hierarchy_expander.so`

Dependency libs copied as real files (world-readable) to `simics_workspace/linux64/lib/`:
- `libRunControlDriverAdapter.so` (from `zse5/lib/` via NFS to ive_sle_zsc11_001)
- `libSignalDriverAdapter.so` (from `zse5/lib/` via NFS to ive_sle_zsc11_001)
- `libIdiDriverAdapter.so`
- `libIosfSbDriverAdapter.so`
- `libPcieDriverAdapter.so`
- `libjemrt.so`
- `libPMWireDriverAdapter.so`
- `libZebuZEMI3.so`
- `libzRtl.so`
- `libzRtlRt.so`
- `libemubuildtb.so`
- `libNPI.so`
- `libnpiL1.so`

## Verification

```bash
readelf -d run_control_xtor_adapter.so | grep RPATH
# Should show: $ORIGIN:/usr/intel/pkgs/gcc/12.2.0/lib64
```

Run DOA test and confirm `testbench.log` no longer shows `libRunControlDriverAdapter.so: cannot open shared object file`.

## Notes

All known missing adapter libs were copied and all module RPATHs patched in batch.
