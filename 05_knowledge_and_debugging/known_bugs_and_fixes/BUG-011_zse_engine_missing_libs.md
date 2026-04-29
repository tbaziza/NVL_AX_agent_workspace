---
bug_id: BUG-011
title: "zse_engine.so missing 29 xactor/DPI shared libraries"
date_discovered: 2026-03-29
status: fixed
severity: blocker
stage: "test execution"
bundle: bundle1068
category: library
related_patterns: []
tags: [zse_engine, xactor, DPI, shared_library, RPATH, LD_LIBRARY_PATH, symlink, FM, gecco]
---

# BUG-011: zse_engine.so missing 29 xactor/DPI shared libraries

## Symptom
[emu error] SimExc_General('Failed to load module 'zse_engine' (...zse5/simics_workspace/linux64/lib/zse_engine.so'): "libxactor_lib.so: cannot open shared object file: No such file or directory"')
(subsequent runs may show next missing lib: libapb_xactor_dpi.so, etc.)

## Triggered By
Running DOA tests; `zse_engine.so` (Simics-Zebu bridge) fails to load on Zebu FM

## Root Cause
- `zse_engine.so` RPATH is: `gcc/12.2.0/lib64:gcc/12.2.0/lib:zse5/lib`
- The 29 xactor/DPI libs needed by `zse_engine.so` live in `simics_workspace/linux64/lib/` and Simics `bin/`
- The FM gecco environment has `PREPEND_LD_LIBRARY_PATH` set to wrong path (`_zebu/` instead of `zebu_zebu/pkg_ghpf_model/zse5/`)
- `addEnv('LD_LIBRARY_PATH')` in .pm plugins does NOT propagate to the FM gecco environment
- Only paths in RPATH of `zse_engine.so` are reliably searched — `zse5/lib/` is in RPATH

## Fix / Solution
Create symlinks in `zse5/lib/` (which IS in RPATH) pointing to all needed libs:
```bash
ZSE5="output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5"
SIMLIB="$(pwd)/$ZSE5/simics_workspace/linux64/lib"
SIMICS_BIN="/p/hdk/cad/windriver/simics/6.0.210/linux64/bin"
# All xactor/DPI libs in simics_workspace/linux64/lib/
for lib in libxactor_lib.so libapb_xactor_dpi.so libcsi_xactor_dpi.so \
  libddr_xactor_dpi.so libdirect_wires_bfm.so libdirect_wires_xtor.so \
  libdirect_wires_callback_adapter.so libdisplay_port_dpi.so libhdmi_dpi.so \
  libhsuart_dpi.so libi2c_xactor_dpi.so libi3c_xtor_utils.so \
  libi3c_master_xtor_dpi.so libi3c_slave_xtor_dpi.so libi3c_tracker_dpi.so \
  libiosf_p.so libiosf_sb.so.0 libjemsimics.so \
  libstreampcie_xtor_dpi.so libstreampcie_tracker_dpi.so \
  libsignal_control_xtor.so libspi_xactor_dpi.so libdpi_spi_master.so \
  libsvid_xtor.so libtest_end_checker.so libtime_update_xtor.so \
  libufi_xtor_dpi.so libusb3_dpi.so libusb4_xactor_dpi.so; do
  ln -sf "$SIMLIB/$lib" "$ZSE5/lib/$lib"
done
# libsimics-common.so and libvtutils.so are in Simics bin/
ln -sf "$SIMICS_BIN/libsimics-common.so" "$ZSE5/lib/libsimics-common.so"
ln -sf "$SIMICS_BIN/libvtutils.so" "$ZSE5/lib/libvtutils.so"
# libZebuZEMI3.so, libzRtl.so, libzRtlRt.so are in ZEBU_ROOT/lib (already in FM LD_LIBRARY_PATH)
# libemubuildtb.so is already in zse5/lib/ natively
```

## Files Affected
- `output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/lib/` — 29 new symlinks created
- `verif/emu/plugins/emurun/zebu_libstdc_override.pm` — two `addEnv('LD_LIBRARY_PATH')` lines added (ineffective for FM but harmless)

## Verification
**CONFIRMED FIXED** (run .12: zse_engine.so loaded, hub_ifp.so loaded, simulation reached Zebu connection step)

## Notes
**Key Technical Detail**:
- FM already has `ZEBU_ROOT/lib` in `LD_LIBRARY_PATH` via gecco env → `libZebuZEMI3.so`, `libzRtl.so`, `libzRtlRt.so` are found automatically
- The RPATH symlink approach bypasses the broken `PREPEND_LD_LIBRARY_PATH` entirely
- `readelf -d zse_engine.so | grep NEEDED` to inspect all 39 library dependencies
- `readelf -d zse_engine.so | grep RPATH` to confirm `zse5/lib` is in RPATH
