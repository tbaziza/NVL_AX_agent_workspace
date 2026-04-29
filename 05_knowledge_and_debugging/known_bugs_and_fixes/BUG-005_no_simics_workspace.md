---
bug_id: BUG-005
title: "No simics_workspace — emurun rejects model"
date_discovered: 2026-03-29
status: fixed
severity: blocker
stage: "test execution"
bundle: bundle1068
category: build-config
related_patterns: [pattern_6]
tags: [simics_workspace, emurun, grdlbuild, zebu_tb, prepare_spark, spark_tb]
---

# BUG-005: No simics_workspace — emurun rejects model

## Symptom
emurun: WARNING: Filtering out <ZSE5_DIR>, since it does not contain simics_workspace
emurun: ERROR (emu::model::roles::builds:297): No builds found to validate.
ERROR: Model-Tool FAILED with exit status 20

## Triggered By
`trex spacedoa ...` / `trex spacex ...` test execution via `simregress` after a build where `zebu_tb` was manually force-completed

## Root Cause
The `zebu_tb` shadow file was manually `touch`-ed to bypass the `zemi3.h` copy failure (see BUG Pattern 6). However, the SUBSEQUENT build steps that depend on `zebu_tb` were NEVER run:
- `pre_spark_tb` — runs `buildit.py --group pre_spark_tb` (SEM config-user.mk workaround)
- `prepare_spark` — runs `prepareSpark.pl` which creates `zse5/simics_workspace/` via Simics workspace-setup
- `spark_tb` — generates `spark-module-all.mk` and compiles all Spark/Simics transactor modules via `gmake -j12 -f spark-module-all.mk all`
- `tb` — final testbench assembly
- `emu_post` — post-processing via `buildit.py --group post`

Without `simics_workspace/`, emurun cannot identify any valid Zebu model builds and fails immediately.

## Fix / Solution
Complete the missing build steps by re-running grdlbuild (it will skip already-done stages via shadow files):
```bash
cd /nfs/site/disks/ive_sle_zsc11_tbaziza/models/integrate_bundle1068.ww12
grdlbuild :emu_build:zebu:pkg_ghpf_model_zse5 -Penv=immediate
```
This will detect existing shadow files for all completed stages and ONLY run:
- `pre_spark_tb` (fast, seconds)
- `prepare_spark` (creates simics_workspace via Simics workspace-setup, ~5-10 min)
- `spark_tb` (compiles Spark transactor modules on NB farm, ~1-2 hours)
- `tb` + `emu_post` (fast, seconds to minutes)

After completion, verify: `ls output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/simics_workspace/`

## Files Affected
None (build outputs only — new directories created under `zse5/`)

## Verification
```bash
ls output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/simics_workspace/
```
Directory should exist and contain Simics workspace files.

## Notes
Run grdlbuild to complete missing steps. It will skip already-done stages via shadow files.
