---
bug_id: BUG-023
title: "fix_readmem_dump runs twice, second fails"
date_discovered: 2026-04-12
status: informational
severity: non-critical
stage: "emu_post (post_zcui)"
bundle: bundle1088
category: build-config
related_patterns: [pattern_10]
tags: [fix_readmem_dump, emu_post, post_zcui, double_execution, readmem, sed, symlink]
---

# BUG-023: fix_readmem_dump runs twice, second fails

## Symptom
```
INFO: action fix_readmem_dump PASSED
...
7_n2p/emu/zebu_zebu//pkg_ghpf_model/zse5/zcui.work/backend_default/readmem.dump: No such file or directory
INFO: returned 1024
ERROR: action fix_readmem_dump FAILED
```

The action runs twice. First run succeeds — `sed -i.bak` converts the `readmem.dump`
symlink to a regular file (with modifications) and saves the original symlink as
`readmem.dump.bak`. Second run fails because it constructs a slightly different path
(note the double slash `//` in the error: `zebu_zebu//pkg_ghpf_model`) and can't find
the file.

## Triggered By
`emu_post` stage (during `post_zcui`) — bundle1088, pkg_ghpf_model_zse5, 2026-04-12

## Root Cause
The `fix_readmem_dump` action in `verif/emu/buildit/EmuPost.py` (around line 80-83) uses `sed -i.bak` on a symlink path. The first execution:
1. Resolves the symlink
2. Applies sed modifications (replacing relative ROM paths with absolute paths)
3. Writes result as a regular file (replacing the symlink)
4. Saves original symlink as `.bak`

The second execution constructs the path with a double-slash (`//`) which fails to find the already-converted regular file.

## Fix / Solution
No fix needed for the build — the model is complete and functional. The
`readmem.dump` file is correctly modified after the first successful execution.

To prevent the false failure, you could:
1. Edit `verif/emu/buildit/EmuPost.py` to check if `readmem.dump` is already a regular file (not a symlink) before running sed again
2. Or fix the double-slash path construction issue

## Files Affected
- `verif/emu/buildit/EmuPost.py` — source of double execution (no change applied)
- `output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/zcui.work/backend_default/readmem.dump` — file is correctly patched despite error

## Verification
After post_zcui, verify readmem.dump is correct:
```bash
# Should be a regular file, not a symlink
file output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/zcui.work/backend_default/readmem.dump
# Should show absolute paths to ROM directories
head -1 output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/zcui.work/backend_default/readmem.dump
```

## Notes
- **Impact**: **Non-critical but noisy**. Despite the FAILED message:
  - The `readmem.dump` file IS correctly patched (109KB regular file with absolute paths)
  - The `emu_post` shadow file IS created
  - The log shows "Target: emu_post PASSED" at the end
  - BUT `grdlbuild` reports overall exit code 2 (FAILED) due to `make` seeing the error
