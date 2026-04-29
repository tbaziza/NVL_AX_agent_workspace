---
title: "Monitoring Metrics Definition"
module: 04_monitoring
tags: [monitoring, metrics, build, emulation, disk, health]
---

# Monitoring Metrics Definition

## Build Monitoring

### fe_be Progress
```bash
ZSE5="output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5"
LOGDIR="$ZSE5/log/<TIMESTAMP>"

# Current stage
tail -10 "$LOGDIR/fe_be.NB.log"

# Task completion counts
grep -c "<STAGENAME> spawned" "$LOGDIR/fe_be.NB.log"
grep -c "<STAGENAME> normal task termination" "$LOGDIR/fe_be.NB.log"

# Check for failure
cat "$LOGDIR/failure_info.log" 2>/dev/null || echo "no failure"

# Quick health check
echo "=== time ===" && date
echo "=== fe_be last 5 ===" && tail -5 "$LOGDIR/fe_be.NB.log"
echo "=== failure ===" && (cat "$LOGDIR/failure_info.log" 2>/dev/null || echo "none")
echo "=== disk ===" && df -h /nfs/site/disks/ive_sle_zsc11_tbaziza | tail -1
```

### Disk Space
- **Critical threshold**: < 30GB free during build
- **Warning threshold**: < 100GB free before starting build
- **Check frequency**: Every 15-30 minutes during active build
- **Command**: `df -h /nfs/site/disks/ive_sle_zsc11_tbaziza | tail -1`

### Shadow File Progress
```bash
ls -lt output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/.shadow/
# Each new shadow file = one stage completed
# 19 files = fully built
```

## Emulation Monitoring

### Logbook Freeze (BUG-030 — NORMAL BEHAVIOR)
- Logbook stays frozen during active emulation (offline rsync mode)
- Only updates at pre-exec, board acquisition, and post-exec
- Frozen size = emulation actively running on FM board
- **DO NOT KILL** a job based on frozen logbook alone!

### Correct Monitoring Approach
1. Check `logbook.log` SIZE — frozen = emulating
2. Check `JOBS_STATUS` for `END:` lines — only at completion
3. Check `emurun.log` timestamps — updated at board events only
4. Check NB job status: `nbstatus jobs | grep <job_id>` — "Run" = active
5. **DO NOT** kill "Wait Remote" FM jobs — they are actively emulating!

### Kerberos Ticket
- **TTL**: ~24 hours from `kinit`
- **Renew**: `kinit -R` (no password needed if renewable)
- **Check**: `klist 2>&1 | grep -E "Expires|>>>"`
- **Risk**: Long FM queue waits (26h+) can outlive ticket → BUG-033
- **Mitigation**: `kinit -r 7d` for 7-day renewable ticket
