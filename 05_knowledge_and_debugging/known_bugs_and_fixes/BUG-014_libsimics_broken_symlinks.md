---
bug_id: BUG-014
title: "libsimics-common.so/libvtutils.so broken symlinks"
date_discovered: 2026-04-01
status: fixed
severity: blocker
stage: "DOA test runtime"
bundle: bundle1068
category: library
related_patterns: [pattern_1, pattern_2]
tags: [simics, zse5, symlinks, rpath, ld_preload, zebu, fm, library]
---

# BUG-014: libsimics-common.so/libvtutils.so broken symlinks

## Symptom
```
[emu error] SimExc_General('Failed to load module 'zse_engine' ('.../zse_engine.so'): "libxactor_lib.so: cannot open shared object file: No such file or directory"')
Simics ran for only 54 seconds (configure=52s, runtime=0s)
(seen in `testbench.log` on FM machine fmez5072)
```

## Triggered By
DOA test run .14; spacedoa_mobile on board fmez5072

## Root Cause
- `zse_engine.so` RPATH: `gcc/12.2.0/lib64:gcc/12.2.0/lib:zse5/lib` (absolute)
- `zse5/lib/` had only `libreadline.so.7`, `libsimics-common.so` (broken), `libvtutils.so` (broken), `libemubuildtb.so`
- 33 additional required libs were NOT in `zse5/lib/`:
  - Xactor/DPI libs: in `simics_workspace/linux64/lib/`
  - Zebu system libs (libZebuZEMI3, libzRtl, libzRtlRt, libSledUtils, etc.): in `ZEBU_ROOT/lib/`
  - Simics core libs (libsimics-common, libvtutils): in `SIMICS/linux64/bin/` (NOT `bin/` as previously tried)
  - Python: libpython3.10.so.1.0 in `SIMICS/linux64/sys/lib/`
  - Other Zebu libs: libRtx, libMuDb, libtbb.so.2, libZebuOptionsdb, libzlog, libZxf, libtcl8.6-mt
- ALSO: The original libsimics-common.so and libvtutils.so symlinks pointed to wrong path `/p/hdk/cad/windriver/simics/6.0.210/bin/` (no `linux64/` component) — they were BROKEN
- LD_LIBRARY_PATH additions in zebu_libstdc_override.pm do NOT propagate to FM gecco (only LD_PRELOAD does)
- Run .13 worked because it landed on a machine with those libs in a different local path; run .14 landed on fmez5072 which didn't have them

## Fix / Solution
1. Symlinked ALL required libs into `zse5/lib/` (RPATH target, always accessible via NFS):
```bash
# All xactor/DPI libs from simics_workspace
for lib in $(ls output/.../zse5/simics_workspace/linux64/lib/lib*.so*); do
  ln -s "$lib" "zse5/lib/$(basename $lib)"
done
# Zebu system libs from ZEBU_ROOT/lib
for lib in libZebuZEMI3.so libzRtl.so libzRtlRt.so libZebu.so libSledUtils.so \
           libRtx.so libMuDb.so libtbb.so.2 libZebuOptionsdb.so libzlog.so libZxf.so libtcl8.6-mt.so; do
  ln -s "$ZEBU_ROOT/lib/$lib" "zse5/lib/$lib"
done
# Simics core libs (correct path: MUST include linux64/)
ln -s "/p/hdk/cad/windriver/simics/6.0.210/linux64/bin/libsimics-common.so" "zse5/lib/libsimics-common.so"
ln -s "/p/hdk/cad/windriver/simics/6.0.210/linux64/bin/libvtutils.so" "zse5/lib/libvtutils.so"
ln -s "/p/hdk/cad/windriver/simics/6.0.210/linux64/sys/lib/libpython3.10.so.1.0" "zse5/lib/libpython3.10.so.1.0"
```
2. **Automated with `scripts/fix_zse5_libs.sh`** — run after every fe_be rebuild:
```bash
bash scripts/fix_zse5_libs.sh
```
3. Verified with `ldd zse_engine.so | grep "not found"` → empty (all 87 deps resolved)

## Files Affected
- `output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/lib/` (87 symlinks added)
- `scripts/fix_zse5_libs.sh` (NEW — automated symlink recreation script)

## Verification
```bash
ldd output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/simics_workspace/linux64/lib/zse_engine.so 2>/dev/null | grep "not found"
# Should produce NO output (all resolved)
```

## Notes
- `zse5/lib/` is on the RPATH of `zse_engine.so` — all symlinks there work on ANY FM machine via NFS
- This directory is WIPED by every clean fe_be rebuild → run `scripts/fix_zse5_libs.sh` after each rebuild
- Simics 6.0.210 lib paths: core libs in `linux64/bin/`, Python in `linux64/sys/lib/`
- WRONG: `/p/hdk/cad/windriver/simics/6.0.210/bin/` (no linux64!) — broken symlinks here
- RIGHT: `/p/hdk/cad/windriver/simics/6.0.210/linux64/bin/` — this is where `libsimics-common.so` lives
