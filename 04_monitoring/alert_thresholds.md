---
title: "Alert Thresholds &amp; Response Actions"
module: 04_monitoring
tags: [alerts, thresholds, intervention, response, anomaly]
---

# Alert Thresholds &amp; Response Actions

## Build Alerts

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Disk space critically low | < 30GB free | Stop build, free space (see environment.md safe-to-delete), restart |
| fe_be.NB.log not updated | > 45 minutes | Check `fe_be.NB.Controller.log` modify time; if recent → wait; if stale → investigate NB job |
| zDB_Global log not growing | > 60 minutes | Check Controller log — zDB runs on farm node with local scratch, NFS flush is periodic |
| NB job killed (exit -13) | OOM kill | Check CLASS_ANA in compute.cth (need 250G for analyze stage); see BUG-020 |
| "abnormal task termination" in fe_be.NB.log | Any count | NORMAL for FPGA P&R retries — only worry if `Compilation Ended successfully` is missing |
| `failure_info.log` appears | Existence | Read it — contains stage name and error. Cross-reference with known_bugs_and_fixes/ |

## Emulation Alerts

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Logbook frozen | Any duration during emulation | NORMAL — do NOT kill. Check NB job "Run" status |
| FM job exit code 66 | rsync copy-in failed | Check Kerberos: `klist`. If expired: `kinit` then resubmit |
| FM board died (exit 137/144) | Auto-requeued | Wait — emurun auto-requeues up to 10 times |
| Test FAILED with SimTime 0 | Library loading error | Check `ldd zse_engine.so | grep "not found"`. Run `fix_zse5_libs.sh` |
| Test FAILED but assertions pass | Validator mismatch | Check `doa_validator_override.pm` is registered (BUG-027) |
| SSH "Password change required" | Password expired | Change Intel/AD password → `kinit` → resubmit (BUG-034) |
| NB groups > 15 warning | Informational | Non-critical, but compounds auth issues. Kerberos is the real blocker |

## Intervention Decision Tree

```
Is the build/test making progress?
├── YES → Do nothing. Monitor periodically.
├── NO, logbook frozen → Check NB job status
│   ├── NB shows "Run" → NORMAL (offline rsync). Wait.
│   └── NB shows "Comp"/"Wait" → Job may have failed. Check emurun.log.
├── NO, failure_info.log exists → Read it, find matching bug
├── NO, disk full → Free space, restart stage
└── NO, Kerberos/SSH error → kinit, test SSH, resubmit
```

## Key Principle
> **When in doubt, WAIT.** Killing a seemingly-stuck job loses hours of emulation time (BUG-030/032).
> Only intervene when you have positive evidence of failure (failure_info.log, exit code in JOBS_STATUS, or confirmed Kerberos expiry).
