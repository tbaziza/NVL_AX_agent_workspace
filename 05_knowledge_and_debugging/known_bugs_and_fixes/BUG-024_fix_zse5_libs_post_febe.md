---
bug_id: BUG-024
title: "fix_zse5_libs.sh must run after every fe_be build"
date_discovered: 2026-04-11
status: fixed
severity: critical
stage: "Post-fe_be (manual step before DOA/FM testing)"
bundle: all
category: library
related_patterns: [pattern_1, pattern_2]
tags: [fix_zse5_libs, fe_be, zse5, symlinks, rpath, zse_engine, fm, doa, post_build]
---

# BUG-024: fix_zse5_libs.sh must run after every fe_be build

## Symptom
Without running `fix_zse5_libs.sh`, the FM (Functional Model) runtime
will fail to find Zebu libraries. The `zse_engine.so` shared library has RPATH
entries pointing to `zse5/lib/` which needs to contain symlinks to the actual
library locations scattered across the build tree.

## Triggered By
FM runtime fails with missing library errors if `fix_zse5_libs.sh` is not run after fe_be completion — bundle1088, pkg_ghpf_model_zse5, 2026-04-11

## Root Cause
The `zse5/lib/` directory is wiped by every clean fe_be rebuild. The `zse_engine.so` shared library has RPATH entries pointing to `zse5/lib/` which needs to contain symlinks to the actual library locations scattered across the build tree. Without these symlinks, all FM/DOA runtime tests will fail with missing `.so` errors.

## Fix / Solution
Run after every successful fe_be completion:
```bash
cd /nfs/site/disks/ive_sle_zsc11_tbaziza/models/integrate_bundle1088
bash scripts/fix_zse5_libs.sh
```

**What it does**:
- Creates ~100 symlinks in `output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/lib/`
- Links point to actual `.so` files in `zcui.work/` subdirectories
- Patches RPATH on 352 `.so` files for correct library resolution
- Ensures `zse_engine.so` can find all its dependencies at runtime

## Files Affected
- `scripts/fix_zse5_libs.sh` — the script itself
- `output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/lib/` — ~100 symlinks created

## Verification
```bash
# Check no missing dependencies
ldd output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/simics_workspace/linux64/lib/zse_engine.so 2>/dev/null | grep "not found"
# Should produce NO output (all resolved)
```

## Notes
- **When to run**: After every `fe_be` completion, before any FM/DOA testing. Must be re-run if fe_be is rebuilt.
- This is a **mandatory manual step** in the post-build workflow.
- Related to BUG-014 (libsimics-common.so/libvtutils.so broken symlinks) and BUG-015 (libRunControlDriverAdapter.so).
