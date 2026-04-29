---
bug_id: BUG-034
title: "Intel/AD Password Expired — SSH BatchMode Fails on All ZSC11 Hosts"
date_discovered: 2026-04-28
status: open
severity: blocker
stage: "SSH authentication / job submission"
bundle: bundle1106
category: infrastructure
related_patterns: [pattern_authentication, pattern_ssh]
tags: [password-expiry, ssh, batchmode, ldap, pam, kerberos, zsc11]
---

# BUG-034: Intel/AD Password Expired — SSH BatchMode Fails on All ZSC11 Hosts

## Symptom

```
WARNING: Your password has expired.
Password change required but no TTY available.
exit: 1
```
Reproduced on:
- `sccf01361924.zsc11.intel.com` (previous feeder host)
- `sccc14644327.zsc11.intel.com` (login host)
→ System-wide; affects ALL ZSC11 cluster hosts

## Triggered By

Any SSH connection using `BatchMode=yes` (as used by emurun rsync) when the user's Intel LDAP/AD password has expired.

## Root Cause

Intel LDAP/AD account password has expired. PAM enforces password change
before allowing any interactive or batch SSH session to execute commands, even when Kerberos
GSSAPI authentication succeeds. With `BatchMode=yes` (as used by emurun rsync), no TTY is
available to prompt for new password → connection closes with exit 1.

This is why `.list.2/external/` jobs failed at emurun `prepTest` (copy-in phase):
the rsync uses `ssh -oBatchMode=yes` → password expiry → "connection unexpectedly closed".

**Note**: `kinit -R` was able to renew the Kerberos TGT (valid until 22:57 Apr 28), but
Kerberos auth alone is insufficient when PAM also requires password change.

## Fix / Solution

**REQUIRED before any new submission**:

1. **Change Intel/AD password** (interactive terminal required):
   - Option A: https://go.intel.com/mypassword (Intel self-service portal)
   - Option B: `passwd` on a host where you have TTY access
   - Option C: via Intel IT helpdesk

2. **After password change, renew Kerberos**:
   ```bash
   kinit
   # Enter NEW password
   klist  # verify TGT shows future expiry and NOT >>>Expired<<<
   ```

3. **Test SSH works**:
   ```bash
   ssh -o BatchMode=yes sccc14644327.zsc11.intel.com "echo OK"
   # Should print: OK  (no password warnings)
   ```

4. **Submit `.list.4/`** immediately:
   ```bash
   cd /nfs/site/disks/ive_sle_zsc11_tbaziza/models/integrate_bundle1106
   simregress -dut nvlsi7_n2p -save -no_xs -trex -emu_model pkg_ghpf_model -emu_tech zse5 \
     -no_compress EMUL_QSLOT=/prj/sv/nvl/emu/interactive -trex- \
     -P zsc11_express -Q /IVE/NVL/emu \
     -l reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list
   ```

## Files Affected

- None (user account / authentication issue)

## Verification

```bash
ssh -o BatchMode=yes sccc14644327.zsc11.intel.com "echo OK"
# Should print: OK  (no password warnings)
```

## Notes

**Note on ticket renewal strategy for long queue waits**:
- After `kinit`, use `kinit -r 7d` to get a 7-day RENEWABLE ticket
- Monitor board queue status — if wait >20h, run `kinit -R` to renew without re-entering password
- `.list.3/` was a kill/management operation (no test submissions) → next real run is `.list.4/`
