---
title: "DOA Test Suites"
module: 03_testing_and_validation
tags: [doa, tests, spacedoa, spacex, simregress, trex]
---

# DOA Test Suites

## Overview
DOA (Dead-On-Arrival) tests verify that the compiled emulation model can boot and run basic workloads.
Two tests are run: `spacedoa_mobile` and `spacex_mobile`.

## Test Submission Command

```bash
cd /nfs/site/disks/ive_sle_zsc11_tbaziza/models/integrate_bundle1106
simregress -dut nvlsi7_n2p -save -no_xs -trex -emu_model pkg_ghpf_model -emu_tech zse5 \
  -no_compress EMUL_QSLOT=/prj/sv/nvl/emu/interactive -trex- \
  -P zsc11_express -Q /IVE/NVL/emu \
  -l reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list
```

## Test Details

### spacedoa_mobile
- **Purpose**: Boot test — all 4 Atom cores boot, execute SpaceDOA workload, report PASS
- **Cycle limit**: 50ms (but `common_defaults.list` overrides to 11ms)
- **Pass criteria**: All cores reach `EBX=0xaced` (PASS COMPLETE), zero assertion failures
- **Duration**: ~4-5 hours on ZSE5 hardware
- **Key files**: `test_doa.list`, `reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list`

### spacex_mobile
- **Purpose**: GPU PCIe workload — PCIe link training + SpaceX GPU MMIO test
- **Cycle limit**: 240ms (completes naturally at ~135ms SimTime)
- **Pass criteria**: C0 halts with `EBX=0xaced`, PCIe links trained, GPU workload complete
- **Duration**: ~5 hours on ZSE5 hardware
- **Requires**: BKC builder (`REGFLOW_LGN_CFG1`) for PCIe Gen4/5 init (BUG-017)
- **Key files**: `test_spacex.list`

## Reglist Configuration

### `reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list`
```
# Includes:
.include test_spacex.list
.include test_doa.list

# Workarounds applied:
+defaults -tlm_post -not_fail_on iosf_sb_jem_tracker -tlm_post-   # BUG-029
```

### Key Overrides in `common_defaults.list`
- `-pcode_path`: Points to ipcache pcode release (BUG-016)
- `-c 11000us`: Default cycle limit (overrides per-test limits)
- `-ms -c 11000us -ms-`: Model-specific cycle limit wrapper

## Test Progression (what to look for)

1. ✅ ECT (Environment Compile Test) — compiles test environment
2. ✅ PCD/fuse/softstrap generation — creates `pcd_fuse_gen/`, `pcd_ss_gen/`
3. ✅ emurun setup — prepares FM job, copies files to board
4. ✅ `zse_engine.so` loading — loads Zebu engine + xactor libs
5. ✅ `hub_ifp.so` loading — loads hub interface
6. ✅ ZRDB database loading — loads FPGA routing data
7. ✅ Zebu hardware connection — connects to physical ZSE5 board
8. ✅ Emulation runs — clock cycles advance
9. ✅ Test completion — cores halt with PASS or cycle limit reached
10. ✅ tlm_post — tracker post-processing

## Plugin Stack

| Plugin | Purpose | File |
|--------|---------|------|
| `zebu_libstdc_override.pm` | LD_PRELOAD for readline/tinfo | `verif/emu/plugins/emurun/` |
| `doa_validator_override.pm` | Override validator for DOA tests | `verif/emu/plugins/emurun/` |
| `pcd.pm` | PCD fuse/softstrap generation | `output/pchlp/emu/plugins/emurun/` |

## Current Test Status (bundle1106)

| Test | Last Run | Result | Notes |
|------|----------|--------|-------|
| spacedoa_mobile | .list.2 | FAILED (exit 66) | Kerberos expired — BUG-033/034 |
| spacex_mobile | .list.2 | FAILED (exit 66) | Kerberos expired — BUG-033/034 |

**Action**: Change Intel/AD password → `kinit` → submit `.list.4/`
