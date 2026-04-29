---
bug_id: BUG-003
title: "NB queue collision from Perl autovivification"
date_discovered: 2026-03-29
status: fixed
severity: blocker
stage: "test submission"
bundle: bundle1068
category: infrastructure
related_patterns: []
tags: [simregress, NB, queue, Perl, autovivification, nbtask_conf, ifeed]
---

# BUG-003: NB queue collision from Perl autovivification

## Symptom
(in NBFeeder log) Cannot resolve hostname for queue "-Q" (BAD_QUEUE)
Exit status ERROR_LOAD_TASK_GENERAL(102)

## Triggered By
`simregress ... -P <pool> -Q <qslot> -l <reglist>` (without explicit -P/-Q args)

## Root Cause
Perl autovivification bug in `simregress` (line 829): calling `${$opt{'P'}}[0]` on an undefined `$opt{'P'}` autovivifies it to `[]` (empty array ref). Then at line 840-841, `defined $opt{'P'}` is TRUE, so `-P undef` is pushed to the ifeed command. When joined and shell-parsed, the empty value causes `-P -Q` where `-Q` becomes the VALUE of `-P`. This creates `Queue -Q {...}` in the nbtask_conf — an invalid queue name.

## Fix / Solution
1. Always pass BOTH `-P <pool>` and `-Q <qslot>` explicitly to simregress to prevent the empty-value collision.
2. Use the correct NB queue `zsc11_express` with qslot `/IVE/NVL/emu` (discovered from compilation PP's RemoteQueuesData):
   ```
   simregress ... -P zsc11_express -Q /IVE/NVL/emu -l <reglist>
   ```
3. If nbtask_conf already generated with wrong Queue stanza, manually fix it:
   - Stop the feeder's stuck task: `nbtask stop --target <host>:<port> <taskid>`
   - Delete it: `nbtask delete --target <host>:<port> --force <taskid>`
   - Fix nbtask_conf: change `Queue -Q {...}` to `Queue zsc11_express { Qslot /IVE/NVL/emu MaxJobs 10000 MaxWaiting 50 }`
   - Reload: `nbtask load --target <host>:<port> <path/to/nbtask_conf>`

## Files Affected
- `regression/nvlsi7_n2p/doa_pkg_ghpf_model_zse5.list.3/doa_pkg_ghpf_model_zse5.nbtask_conf` (manually fixed)

## Verification
Confirm that `nbtask_conf` contains `Queue zsc11_express { Qslot /IVE/NVL/emu ... }` and tests are dispatched without BAD_QUEUE errors.

## Notes
Workaround: pass `-P zsc11_express -Q /IVE/NVL/emu` to simregress.
