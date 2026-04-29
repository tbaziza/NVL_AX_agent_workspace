---
bug_id: BUG-007
title: "MuDb missing / FpgaPostProc skipped in zPRD mode"
date_discovered: 2026-03-29
status: open
severity: blocker
stage: "fe_be build / test execution"
bundle: bundle1068
category: build-config
related_patterns: []
tags: [MuDb, FpgaPostProc, zPRD, fe_be, FPGA, backend_default, Zebu, zMuDbMerge, zCreateEmptyMuDb]
---

# BUG-007: MuDb missing / FpgaPostProc skipped in zPRD mode

## Symptom
CORE0001E: Could not load database: Cannot read MuDb version from '...backend_default/MuDb/version'
LUI1744E: The directory "backend_default/U0" must be a valid path
ZHW0909E: Cannot open Zebu: an error occurred during the connection
terminate called after throwing an instance of 'std::bad_exception' (SIGSEGV in libZebu.so)
Result: FAILED  SimTime: 0 clocks

## Triggered By
Any hardware Zebu test (spacedoa_mobile, spacex_mobile) against the `pkg_ghpf_model/zse5` model

## Root Cause
The build ran in zPRD (Pre-Route Deployment) mode with `ZEBU_ENABLE_MUDB=1`. In this mode,
the `FpgaPostProc` task has **no command script** and is intentionally SKIPPED for all 192 FPGAs.
`FpgaPostProc` is the task responsible for:
1. Creating `backend_default/MuDb/equis/info` (binary file with FPGA-to-signal location mapping)
2. Populating `backend_default/MuDb/` from per-FPGA bitstream data
3. Creating the `backend_default/U0-U3/` FPGA deployment directories

Without `FpgaPostProc`:
- `backend_default/MuDb/` was never created → "Cannot read MuDb version"
- `backend_default/U0-U3/` were created by Vivado P&R but then DELETED (post-build cleanup)
- No FPGA bitstream data → Zebu hardware cannot initialize → `terminate()`

**COMPLETE BUILD TIMELINE (for reference):**
- P&R (`_Original`) ran for all 192 FPGAs and SUCCEEDED (WRITE_BITSTREAM completed)
- `_Finish` ran for each FPGA → created `backend_default/U0-U3/` dirs with `design.bit` files
- `FpgaPostProc` SKIPPED for all 192 FPGAs (no _command.sh file — intentional in zPRD mode)
- `Build_ZDBPostProc_Script` logged: "No zDBPostProc needed" — confirmed intentional skip
- `zDB_Global` ran 2.75 hours → created `backend_default/zrdb/` with coords/mems/properties
- `FpgaResultAnalyzer` ran at ~01:31 Mar 29 and still referenced `U3/M0/F05` (dirs existed then)
- `backend_default/U0-U3/` were DELETED before or during `zDB_Global` (cleanup or disk pressure)
- `fe_be` completed SUCCESSFULLY at 02:49 Mar 29 (exit 0) — build appears complete but is broken

**Investigation / Attempted Fixes**:
1. `zCreateEmptyMuDb` runs but crashes with assertion error (PropertySchema.cc:25) — creates partial
   MuDb (`version`, `properties`, `crcs`, `upf`) but NOT `equis/info`
2. `zMuDbMerge --zebu-work .` (from backend_default/) runs for ~5 minutes loading 28GB of data
   but fails: `MUDB0003: Cannot load file '.../MuDb/equis/info'`
3. The `equis/info` file is a proprietary binary file created only by `FpgaPostProc` from the
   FPGA bitstreams (`design.bit`) — there is NO tool to regenerate it from existing data
4. The `design.bit` bitstreams were in `backend_default/U0-U3/` which are now DELETED
5. Symlinking `nofpga/zrdb/0_equis.zrdb..7_equis.zrdb` into `backend_default/zrdb/` and retrying
   `zMuDbMerge` still fails with the same MUDB0003 error

**Root cause for `FpgaPostProc` skip**: In zPRD mode, `FpgaPostProc` task is listed in the build
graph but its `_command.sh` file is empty/absent → grid engine reports "normal task termination: skipped".
The skip is BY DESIGN for this build configuration (confirmed by "No zDBPostProc needed" message).
However, in a CORRECT zPRD build, something else should create MuDb — this did NOT happen here.

## Fix / Solution
**No fix is possible without re-running the `fe_be` step** (FPGA P&R and post-processing).

To fix this model:
```bash
# Option A: Full recompilation
cd /nfs/site/disks/ive_sle_zsc11_tbaziza/models/integrate_bundle1068.ww12
grdlbuild :emu_build:zebu:pkg_ghpf_model_zse5 -Penv=immediate

# Option B: Partial recompilation — re-run only fe_be (requires deleting fe_be shadow)
rm output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/.shadow/fe_be
grdlbuild :emu_build:zebu:pkg_ghpf_model_zse5 -Penv=immediate
# This will re-run the 25+ hour FPGA P&R + FpgaPostProc + zDB_Global pipeline
# All other stages (analyze, vcs_splitter, zebu_tb, etc.) will be SKIPPED via shadow files
```

**IMPORTANT**: Before re-running `fe_be`, verify that `FpgaPostProc` command scripts will be
present in the new build (check that `zCui/com/backend_default_U0_M0_F01_FpgaPostProc_command.sh`
gets created). If it's empty again, the MuDb still won't be created. This may require a build
configuration change (consult the emulation team about zPRD vs standard flow).

## Files Affected
- `output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/zcui.work/backend_default/MuDb/`
  (created with partial content — version, properties, crcs, upf, equis/info(empty) — needs complete data)
- `output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/zcui.work/backend_default/U0-U3/`
  (DELETED — needs to be regenerated by re-running fe_be)

## Verification
After re-running `fe_be`, confirm:
1. `backend_default/MuDb/equis/info` exists and is non-empty
2. `backend_default/U0-U3/` directories exist with `design.bit` files
3. Zebu tests connect successfully without CORE0001E / LUI1744E errors

## Notes
Status: open (requires fe_be recompilation or emulation team intervention)
