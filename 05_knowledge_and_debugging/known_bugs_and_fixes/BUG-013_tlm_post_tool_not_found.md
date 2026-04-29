---
bug_id: BUG-013
title: "TLM_POST tool not found on FM"
date_discovered: 2026-04-01
status: fixed
severity: non-critical
stage: "TLM_POST processing"
bundle: bundle1068
category: runtime
related_patterns: [pattern_3]
tags: [tlm_post, fm, gecco, path, not_fail_on]
---

# BUG-013: TLM_POST tool not found on FM

## Symptom
```
spacedoa_mobile/testbench.log: "Model-Tool FAILED with exit status 1"
spacedoa_mobile/testbench.log: 4 TLM_POST jobs: "FAIL"
ect_logdb: 2logdb.pl: Command not found
uop_log: run_xmon_wrapper: Command not found
sai_input_checker_chk: No valid input files (depends on failed ect_logdb)
annotate_pcode_tracker: trace_parser.rb: Command not found
```

## Triggered By
TLM_POST processing after successful Zebu hardware run

## Root Cause
These 4 tools are not in PATH on FM gecco machines. They're optional post-processing tools for log analysis. The test itself ran correctly on hardware (postmortem PASS), but the TLM_POST jobs failed because the tools aren't available.

## Fix / Solution
Added `not_fail_on` for each in `reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list`:
```
+defaults -tlm_post -not_fail_on ect_logdb -not_fail_on uop_log -not_fail_on sai_input_checker_chk -not_fail_on annotate_pcode_tracker -tlm_post-
```

## Files Affected
- `reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list` (after line 43)

## Verification
Re-run DOA test and confirm TLM_POST no longer reports FAIL for these 4 tools.

## Notes
- The test itself ran correctly on hardware (postmortem PASS)
- These are optional post-processing tools for log analysis
- The `not_fail_on` directive prevents these non-critical failures from marking the test as FAIL
