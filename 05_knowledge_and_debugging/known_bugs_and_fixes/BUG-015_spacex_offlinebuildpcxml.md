---
bug_id: BUG-015
title: "spacex_mobile OfflineBuildPCXML posth failed CYCLES=0"
date_discovered: 2026-04-01
status: fixed
severity: non-critical
stage: "DOA test runtime"
bundle: bundle1068
category: runtime
related_patterns: [pattern_2]
tags: [simics, run_control_xtor_adapter, pydoh, ld_preload, rpath, fm, library]
---

# BUG-015: spacex_mobile OfflineBuildPCXML posth failed CYCLES=0

## Symptom
```
simics.SimExc_General: Failed to load module 'run_control_xtor_adapter'
('.../run_control_xtor_adapter.so'):
"libRunControlDriverAdapter.so: cannot open shared object file: No such file or directory"
(seen in testbench.log, causes test to abort at 0.5 clocks despite hardware connection succeeding)
```

## Triggered By
DOA tests run .15 (spacedoa_mobile, spacex_mobile on fmez5132)

## Root Cause
- `run_control_xtor_adapter.so` is a Simics module (loaded via `SIM_load_module`) that requires `libRunControlDriverAdapter.so`
- `libRunControlDriverAdapter.so` is from the PyDoh hotfix library at:
  `/nfs/site/disks/ive_sle_zsc11_001/nvl/hotfix/emulation_collateral/spark_repos/pydoh/25.02.008.nvlax/lib/gcc_12.2.0/`
- `run_control_xtor_adapter.so` RPATH = `gcc/12.2.0/lib64:gcc/12.2.0/lib` (no `zse5/lib`)
- So symlinking to `zse5/lib/` alone does NOT work (RPATH not consulted for this module)
- LD_LIBRARY_PATH additions do not propagate to FM gecco — only LD_PRELOAD does
- The `source_env_var` file DOES include `PYDOH_LD_LIBRARY_PATH` in LD_LIBRARY_PATH, but this is ignored on FM

## Fix / Solution
1. Added `libRunControlDriverAdapter.so` to LD_PRELOAD in `verif/emu/plugins/emurun/zebu_libstdc_override.pm`:
```perl
&emu::test::addEnv('LD_PRELOAD' => '/nfs/site/disks/ive_sle_zsc11_001/nvl/hotfix/emulation_collateral/spark_repos/pydoh/25.02.008.nvlax/lib/gcc_12.2.0/libRunControlDriverAdapter.so');
```
2. Also symlinked all PyDoh driver adapter libs into `zse5/lib/` (belt-and-suspenders):
```bash
PYDOH_LIB="/nfs/site/disks/ive_sle_zsc11_001/nvl/hotfix/emulation_collateral/spark_repos/pydoh/25.02.008.nvlax/lib/gcc_12.2.0"
for lib in $PYDOH_LIB/*.so; do ln -s "$lib" "zse5/lib/$(basename $lib)"; done
```
3. Updated `scripts/fix_zse5_libs.sh` to include PyDoh libs (now 100 total libs)

## Files Affected
- `verif/emu/plugins/emurun/zebu_libstdc_override.pm` — added LD_PRELOAD for libRunControlDriverAdapter.so
- `output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/lib/` — 14 PyDoh .so symlinks added
- `scripts/fix_zse5_libs.sh` — updated to include PyDoh libs

## Verification
Re-run DOA test and confirm `run_control_xtor_adapter` module loads successfully without "No such file or directory" error.

## Notes
- RULE: If a Simics module has RPATH that does NOT include `zse5/lib`, its dependencies MUST be added to LD_PRELOAD (not just symlinked in zse5/lib/)
- PyDoh PYDOH_HOME path: `/nfs/site/disks/ive_sle_zsc11_001/nvl/hotfix/emulation_collateral/spark_repos/pydoh/25.02.008.nvlax`
- PyDoh lib path: `$PYDOH_HOME/lib/gcc_12.2.0/`
- This lib is model-specific (from `source_env_var` PYDOH_LD_LIBRARY_PATH variable)
- Status: **APPLIED** — pending verification in run .16
