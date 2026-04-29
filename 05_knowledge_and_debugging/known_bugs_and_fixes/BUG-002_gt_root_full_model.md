---
bug_id: BUG-002
title: "GT_ROOT Full_model variant not in IPX"
date_discovered: 2026-03-29
status: fixed
severity: blocker
stage: "test runtime"
bundle: bundle1068
category: build-config
related_patterns: [pattern_2]
tags: [GT_ROOT, IPX, Full_model, reduced_2, GCD, GT, transactors]
---

# BUG-002: GT_ROOT Full_model variant not in IPX

## Symptom
(test runtime error — GT_ROOT env var points to non-existent path)
`.setenv GT_ROOT /p/ipx/ipcache2/nvlaxpkg/gcd_nvlax/gcd-nvlax-a0-26ww05_Full_model/...`

## Triggered By
Any test from `reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list` that uses GCD GT transactors

## Root Cause
`header_for_ghf.list` sets `GT_ROOT` to `Full_model` IP variant which was never released to IPX cache. Same root cause as compilation filelist issue (BUG Pattern 2). Must use `reduced_2` variant.

## Fix / Solution
In `reglist/nvlsi7_n2p/emu/header_for_ghf.list` line 30, change:
```
.setenv GT_ROOT /p/ipx/ipcache2/nvlaxpkg/gcd_nvlax/gcd-nvlax-a0-26ww05_Full_model/1/nvlaxpkg.gcd_nvlax/gcd_ip_release/sip/gcdax_gt
```
to:
```
.setenv GT_ROOT /p/ipx/ipcache2/nvlaxpkg/gcd_nvlax/gcd-nvlax-a0-26ww05_reduced_2/1/nvlaxpkg.gcd_nvlax/gcd_ip_release/sip/gcdax_gt
```

## Files Affected
- `reglist/nvlsi7_n2p/emu/header_for_ghf.list`

## Verification
Confirm the `GT_ROOT` path resolves to an existing directory after applying the fix.

## Notes
Same root cause as compilation filelist issue (BUG Pattern 2).
