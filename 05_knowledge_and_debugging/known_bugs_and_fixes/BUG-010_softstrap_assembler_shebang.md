---
bug_id: BUG-010
title: "softstrap_assembler bad Python shebang + missing fuse_assembler"
date_discovered: 2026-03-29
status: fixed
severity: blocker
stage: "test execution (PCD softstrap generation)"
bundle: bundle1068
category: shebang
related_patterns: [pattern_1]
tags: [softstrap_assembler, fuse_assembler, shebang, python, pcd, emurun]
---

# BUG-010: softstrap_assembler bad Python shebang + missing fuse_assembler

## Symptom
sh: .../output/pchlp/emu/pchlp/scripts/softstrap_assembler/FuseAssembler.py: /usr/intel/bin/python3.6.3a: bad interpreter: No such file or directory
(seen in `pcd_ss_gen.log`; test fails with "Test generation failed: Copying required files pcd_ss_gen")

## Triggered By
Running DOA tests via `simregress`; PCD/softstrap generation step inside test run

## Root Cause
1. The ACTIVE pcd.pm at runtime is `output/pchlp/emu/plugins/emurun/pcd.pm`, NOT `verif/emu/plugins/emurun/pcd.pm`
2. pcd.pm line 625 calls `$PCD_WORKAREA/emu/pchlp/scripts/softstrap_assembler/FuseAssembler.py`
3. `output/pchlp/emu/pchlp/scripts/softstrap_assembler/` was a symlink to read-only release path with Python 3.6.3a shebang
4. `output/pchlp/emu/pchlp/scripts/fuse_assembler/` symlink was missing entirely

## Fix / Solution
```bash
SOFT_TARGET="/nfs/site/disks/zsc11_nvlpcdh_00002/emu_pcd/emu_pcd-nvl-h-main-26ww05a/emu/pchlp/scripts/softstrap_assembler"
rm output/pchlp/emu/pchlp/scripts/softstrap_assembler
cp -r "$SOFT_TARGET" output/pchlp/emu/pchlp/scripts/softstrap_assembler
chmod u+w output/pchlp/emu/pchlp/scripts/softstrap_assembler/
chmod u+w output/pchlp/emu/pchlp/scripts/softstrap_assembler/*.py
sed -i 's|#!/usr/intel/bin/python3\.6\.3a|#!/usr/intel/bin/python3|g' \
  output/pchlp/emu/pchlp/scripts/softstrap_assembler/*.py
# Create missing fuse_assembler symlink
ln -s /nfs/site/disks/zsc11_nvlpcdh_00002/emu_pcd/emu_pcd-nvl-h-main-26ww05a/emu/pchlp/scripts/fuse_assembler_25ww45 \
  output/pchlp/emu/pchlp/scripts/fuse_assembler
```

## Files Affected
- `output/pchlp/emu/pchlp/scripts/softstrap_assembler/` (replaced read-only symlink with local writable copy, shebangs fixed)
- `output/pchlp/emu/pchlp/scripts/fuse_assembler` → `fuse_assembler_25ww45/` (new symlink)

## Verification
Re-run DOA tests and confirm `pcd_ss_gen` step completes without interpreter errors.

## Notes
Related to Pattern 1 (Interpreter / Shebang Errors). Known-bad path: `/usr/intel/bin/python3.6.3a`. Known-good path: `/usr/intel/bin/python3`.
