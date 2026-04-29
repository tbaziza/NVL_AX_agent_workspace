---
bug_id: BUG-022
title: "resource_info OOM kill (Error 137) — non-critical"
date_discovered: 2026-04-10
status: informational
severity: non-critical
stage: "post_analyze (post_zcui)"
bundle: bundle1088
category: build-config
related_patterns: [pattern_9]
tags: [resource_info, oom, sigkill, post_zcui, post_analyze, non-critical]
---

# BUG-022: resource_info OOM kill (Error 137) — non-critical

## Symptom
```
INFO: returned 35072
ERROR: action resource_info FAILED
```
Exit code 35072 = 137 × 256 (SIGKILL via os.system() return code convention in Lib.py).

## Triggered By
`post_analyze` stage (during `post_zcui`) — bundle1088, pkg_ghpf_model_zse5, 2026-04-10

## Root Cause
The `resource_info` action runs a resource-intensive scan of the build
artifacts and gets killed by the OOM killer on the local machine. This happens when
post_zcui runs with `-Penv=immediate` (local execution) instead of on a high-memory
NB farm node.

## Fix / Solution
No fix needed. This is informational only. If you want it to pass cleanly,
run post_zcui on a machine with more RAM or submit to NB with a high-memory class.

## Files Affected
- None — no code changes required

## Verification
The `post_analyze` target still creates its shadow file and PASSES even when `resource_info` fails. Verify the shadow file exists:
```bash
ls output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/.shadow/post_analyze
```

## Notes
- **Impact**: **Non-critical**. The `resource_info` action only collects metadata/statistics about the build. It does NOT affect the actual build artifacts, shadow files, or model functionality.
- The `post_analyze` target still creates its shadow file and PASSES even when `resource_info` fails.
