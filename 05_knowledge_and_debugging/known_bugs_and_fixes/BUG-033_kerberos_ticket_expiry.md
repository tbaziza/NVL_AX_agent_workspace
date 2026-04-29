---
bug_id: BUG-033
title: "Kerberos Ticket Expiry — emurun rsync Copy-In Fails After 26h Queue Wait"
date_discovered: 2026-04-28
status: fixed
severity: blocker
stage: "FM prepTest / copy-in"
bundle: bundle1106
category: infrastructure
related_patterns: [pattern_kerberos, pattern_rsync]
tags: [kerberos, rsync, ssh, ticket-expiry, copy-in, emurun, fm, queue-wait]
---

# BUG-033: Kerberos Ticket Expiry — emurun rsync Copy-In Fails After 26h Queue Wait

## Symptom

- Both FM jobs (83627045, 83627218) completed with **exit status 66**
- `BUCKET NAME: Emulation::Infra::rsync: connection unexpectedly closed`
- `SimTime: 0 clocks` — emulation never ran
- `Failed copy-in attempt 4 of 4` for `pcd_fuse_gen/` directory
- NB feeder jobs 30002/30003 **Completed** (not auto-requeued — exit 66 ∉ requeue set)

## Triggered By

Jobs were submitted at ~10:30 AM April 27 but FM boards (g507 for spacex, g508 for spacedoa)
did NOT pick them up for **~26 hours** (only started at 12:40 PM April 28). By that time,
the user's Kerberos ticket had expired (~24h TTL for Intel GER.CORP.INTEL.COM realm).

## Root Cause

When the FM board finally ran the job and emurun tried to rsync `pcd_fuse_gen/` FROM the
feeder host (`sccf01361924`) TO the FM board local storage via SSH, the SSH authentication
failed because the Kerberos ticket on the feeder host had expired. SSH exits unexpectedly,
rsync sees "connection unexpectedly closed (0 bytes received)". After 4 retry attempts, all
failing, emurun aborts with exit status 66 (test generation failed).

```
klist showed: Apr 27 20:51:43 2026  >>>Expired<<<
```

**Evidence timeline**:
```
Mon Apr 27 10:32:56: emurun queued to fm_zse5_g507_express (spacex)
Mon Apr 27 10:28:xx: emurun queued to fm_zse5_g508_express (spacedoa)
Tue Apr 28 12:40:49: Job 83627218 has STARTED on fmez5133.fm.intel.com  ← 26h queue wait
Tue Apr 28 12:40:53: WARNING: Number of groups (68) exceeds 15. NFS access may fail!
Tue Apr 28 12:41:02: rsync error: connection unexpectedly closed (0 bytes received)
Tue Apr 28 12:41:02: Failed copy-in attempt 4 of 4
Tue Apr 28 12:41:09: Job 83627218 has finished with exit status 66
```

**Secondary warning**: emurun also warns about 68 supplemental groups > 15 limit, which
compounds SSH/NFS authentication issues. However, the primary cause is Kerberos expiry.

## Fix / Solution

See **BUG-034** — root cause was ALSO Intel/AD password expiry (not just Kerberos TGT).
`kinit -R` can renew the TGT, but SSH still fails until password is changed.

**Procedure** (after password change per BUG-034):
1. `kinit` with new password → get fresh TGT
2. Test: `ssh -o BatchMode=yes sccc14644327.zsc11.intel.com "echo OK"`
3. Submit `.list.4/` immediately
4. Use `kinit -r 7d` for a 7-day renewable ticket to survive long queue waits

## Files Affected

- None (infrastructure/authentication issue)

## Verification

After `kinit` with valid credentials:
```bash
klist  # verify TGT shows future expiry and NOT >>>Expired<<<
ssh -o BatchMode=yes sccc14644327.zsc11.intel.com "echo OK"
# Should print: OK
```

## Notes

**emurun requeue behavior for exit 66**:
- The `--on-job-finish` requeue condition covers exit codes: 137,138,140,162,165,163,164,166,144
- Exit code **66** is NOT in this set → emurun does NOT auto-requeue
- NB feeder job goes to "Comp" state → manual resubmit required

**Affected tests**: Both `spacedoa_mobile` and `spacex_mobile` in `.list.2/external/`
