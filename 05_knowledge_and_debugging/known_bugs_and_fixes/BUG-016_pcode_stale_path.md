---
bug_id: BUG-016
title: "pcode_path points to stale/non-existent workspace"
date_discovered: 2026-04-01
status: fixed
severity: blocker
stage: "CREATE-WA / runtime"
bundle: bundle1068
category: build-config
related_patterns: [pattern_4]
tags: [pcode, ipcache, pcode_builder, reglist, firmware, CREATE-WA]
---

# BUG-016: pcode_path points to stale/non-existent workspace

## Symptom
From logbook.log during CREATE-WA stage:
```
/scripts/pcode_builder.py: CMD Failed  Command '/bin/cp  /nfs/site/proj/nvlax/nvlax.gk.workarea.emulation.08/pkg_emu/integrate_bundle52273/.../pcode_iram.hex .' returned non-zero exit status 1.
```
Then at runtime on FM (~39.7M clocks / 4.97ms sim time):
```
NameError: Specified file name was not found ./pcode_firmware/pcode_iram_0.hex
```

## Triggered By
```bash
simregress -dut nvlsi7_n2p -save -no_xs -trex -emu_model pkg_ghpf_model -emu_tech zse5 -no_compress EMUL_QSLOT=/prj/sv/nvl/showstopper -trex- -local -l reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list
```

## Root Cause
The `-pcode_path` in `reglist/common/emu/common_defaults.list` pointed to a stale, non-existent workspace:
```
/nfs/site/proj/nvlax/nvlax.gk.workarea.emulation.08/pkg_emu/integrate_bundle52273/...
```
`pcode_builder.py` uses `run_command()` which wraps `subprocess.check_call` in a try/except — it prints "CMD Failed" but **exits with code 0**, so trex never aborted. The test ran without any pcode firmware files being generated. The failure only appeared at runtime on FM when `load_pcode_fw.py` tried to open `./pcode_firmware/pcode_iram_0.hex`.

**Pcode Generation Pipeline** (full trace):
1. `cfg/trex/hub_pcode_TREX.pm` → called during `CREATE-WA` stage
2. Runs `scripts/pcode_builder.py -fw valfw` and `-fw firmware` twice
3. `pcode_builder.py` copies `pcode_iram.hex`, `pcode_dram.hex` from `{pcode_path}/target/pcode-nvl-ax-a0/fw_build/production/firmware/`
4. Runs `fw_image_splitter.py pcode_iram.hex -mem_lines 2048 -add_ecc` → generates `pcode_iram_0.hex` through `pcode_iram_29.hex`
5. Runs same for dram → `pcode_dram_0.hex` through `pcode_dram_8.hex`
6. `src/val/emu/scripts/pcode_firmware_linker.py` (BUILD-TEST stage) creates `pcode_firmware/` from `valfw/`
7. Files rsynced to FM machine, loaded by `load_pcode_fw.py` at `start_fw_download` signal (~39.7M clocks)

## Fix / Solution
```bash
# In reglist/common/emu/common_defaults.list:
# Comment out the stale path (line ~62):
#+defaults -pcode_path  /nfs/site/proj/nvlax/nvlax.gk.workarea.emulation.08/pkg_emu/integrate_bundle52273/...

# Activate the valid ipcache path (line ~64):
+defaults -pcode_path  /p/ipx/ipcache2/nvlhaxfe/pcode/v1p52a-ax-ww03-release-branch-val-fw-ww08/2/nvlhaxfe.pcode
```
Verified: ipcache path contains `target/pcode-nvl-ax-a0/fw_build/production/firmware/pcode_iram.hex`

## Files Affected
- `reglist/common/emu/common_defaults.list` — line ~62-64 (pcode_path default)

## Verification
After fix: `spacedoa_mobile` test **PASSED** — all 4 cores reported `PASS COMPLETE` with `EBX=aced` at ~14.6ms sim time (run .25, 2026-04-01).

## Notes
- `pcode_builder.py` hardcodes `pcode-nvl-ax-a0` for BOTH desktop and mobile (both branches in the if/else are identical). Do NOT change this — the ipcache path has `pcode-nvl-ax-a0`.
- The `PCODE_DUT` env var set by `hub_pcode_TREX.pm` (`pcode-nvl-p-a0` for mobile) is NOT used by `pcode_builder.py` — it reads its own hardcoded value. This discrepancy is harmless.
- A non-critical `CMD Failed` for `bin/*` copy still appears (the bin/ subdir may be absent in ipcache) — this is benign, the essential hex files are copied successfully.
