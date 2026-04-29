---
bug_id: BUG-017
title: "BKC builder missing for spacex — PCIe links never trained"
date_discovered: 2026-04-01
status: fixed
severity: blocker
stage: "DOA test runtime"
bundle: bundle1068
category: build-config
related_patterns: [pattern_5]
tags: [bkc, pcie, spacex, link_training, laguna, regflow, gpu, mmio]
---

# BUG-017: BKC builder missing for spacex — PCIe links never trained

## Symptom
From testbench.log — test timed out at 240ms with C0 still ACTIVE:
```
[240000000000] emu_cycle_limit: STOP
HUB_LPA0C0  ACTIVE  (never halted)
```
C0 (HUB_LPA0C0) was stuck in a tight polling loop in `guop_tracker_HUB_A8C0.log`:
```
LOAD  [0x000001cc400a0000]   # GPU MMIO read — unmapped, returns 0 forever
SUB   ...
JNE   <loop back>
```

## Triggered By
```bash
simregress -dut nvlsi7_n2p -save -no_xs -trex -emu_model pkg_ghpf_model -emu_tech zse5 \
  -no_compress EMUL_QSLOT=/prj/sv/nvl/showstopper -trex- -local \
  -l reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list
```
Test: `spacex_mobile` in `test_spacex.list`.

## Root Cause
At commit `ad4529ef5` (Feb 23 2026, "GHPF OOR"), the BKC builder options were removed from `test_spacex.list` when the test was taken Out Of Regression. At commit `e5dcf2dc1` (Mar 25 2026), the test was re-enabled in the DOA list but the BKC builder was **not** restored.

The BKC builder compiles and injects `REGFLOW_LGN_CFG1` — PCIe Gen4/Gen5 link training + Laguna PCIe setup code (`nvlh.32.obj`). Without it:
- PCIe links are never trained → GPU BAR space not assigned
- C0's SpaceX GPU MMIO accesses at `0x000001cc400a0000` go to unmapped space
- PCIe xactors (xtor7/8/9) show only flow control (IFC1, DLFE_REQ), zero actual TLPs
- `pcie_enumeration_done` signal never set → C0 polls forever

## Fix / Solution
1. **Compiler path update** — old paths (`gcc/9.2.0`, `gcc/4.7.2/gas`) no longer exist on this system. Working compilers: `gcc/12.1.0` + `/usr/bin/as`.

2. **Missing define** — `LAGUNA_IO_TC` used in `PCIE_Gen4_LinkTrain_NVLH.c` but not defined in any header. Value `0x9000` inferred from code comment.

3. **Restored BKC builder in `reglist/nvlsi7_n2p/emu/test_spacex.list`** (lines 22-27):
```
+options -run_bkc_builder
+options -mbx_optional_ips pcie_cfg1_pre -mbx_optional_ips-
+options -bkc_gmake_args 'CC=/usr/intel/pkgs/gcc/12.1.0/bin/gcc AS=/usr/bin/as BASE=0x45000 CFLAGS="-m64 -Wall -ffreestanding -Ilib -Ilib/pefw_lib -DLAGUNA_IO_TC=0x9000"'
+options -bkc_root $WORKAREA/src/val/emu/tests/sle_workarounds/REGFLOW_LGN_CFG1
+options -bkc_main nvlh
```

**BKC builder details**:
- `-bkc_root`: `src/val/emu/tests/sle_workarounds/REGFLOW_LGN_CFG1` (PCIe Gen4/5 init source)
- `-bkc_main nvlh`: builds `collateral/nvlh/` subdirectory → produces `nvlh.32.obj`
- `-mbx_optional_ips pcie_cfg1_pre`: injects `pcie_cfg1_pre.asm` into MiniBios `BSP_USER_CODE_AFTER_MRC_DONE` — sets DCCCB.RCRBNRCE and P2SB 0x1f00 for PXPA-PXPE
- `joinBKC.py nvlh.32.obj spacex.32.obj` — merges PCIe init binary with SpaceX test binary

## Files Affected
- `reglist/nvlsi7_n2p/emu/test_spacex.list` — lines 22-27: restored BKC builder options with updated compiler paths

## Verification
- BKC build succeeded locally: `nvlh.bin`, `nvlh.8.obj`, `nvlh.32.obj`, `nvlh.elf` generated
- Run .26: `joinBKC.py nvlh.32.obj spacex.32.obj` ran successfully in emurun
- PCIe xactor pcd_pcie_xtor8 showed actual `credit_status_update` with NP/P credits at 35ms (links UP)
- C0 halted with `EBX=0xaced` at 48ms — SpaceX GPU workload completed successfully
- `spacex_mobile` **PASSED** (run .26, 2026-04-02)

## Notes
- `LAGUNA_IO_TC=0x9000` — value from comment in `PCIE_Gen4_LinkTrain_NVLH.c`; not in any header file
- `BASE=0x45000` — BKC binary load address in memory; do NOT change
- Old compilers `gcc/9.2.0` and `gcc/4.7.2/gas` are gone; use `gcc/12.1.0` and `/usr/bin/as`
- `pkg_ghpf_model` = Package GPU HUB PCIe Free — GPU is simulated by SpaceX PCIe xactors in Simics; `hub_gdie_connected=False` in DutConfig.py is correct and expected
- Git history: `ad4529ef5` removed BKC; `e5dcf2dc1` re-enabled test without restoring BKC
