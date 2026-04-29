---
title: "ZeBu Emulator Setup"
module: 03_testing_and_validation
tags: [zebu, zse5, emulator, setup, fm, boards]
---

# ZeBu Emulator Setup

## ZSE5 Platform Overview
- **Platform**: Synopsys ZeBu ZSE5 (FPGA-based hardware emulation)
- **SDK**: V21.09-2_B4_250617
- **FPGA count**: 192 FPGAs per model partition
- **FM site**: Folsom (Intel FM — Functional Model farm)
- **Board naming**: g503-g514 (ZSE5 boards in the FM farm)

## Prerequisites Before Testing

1. **All 19 shadow files present** (model fully compiled):
   ```bash
   ls output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/.shadow/ | wc -l
   # Must be 19
   ```

2. **Library symlinks created** (BUG-024):
   ```bash
   bash scripts/fix_zse5_libs.sh
   # Creates ~100 symlinks in zse5/lib/, patches RPATH on 352 .so files
   ```

3. **No missing shared library dependencies**:
   ```bash
   ldd output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/simics_workspace/linux64/lib/zse_engine.so 2>/dev/null | grep "not found"
   # Must produce NO output
   ```

4. **Kerberos ticket valid** (for rsync to FM boards):
   ```bash
   klist 2>&1 | grep -E "Expires|>>>"
   # Must NOT show >>>Expired<<<
   ```

5. **SSH BatchMode works** (password not expired):
   ```bash
   ssh -o BatchMode=yes sccc14644327.zsc11.intel.com "echo OK"
   # Must print: OK
   ```

## Emulation Architecture

### Offline Rsync Mode (`-offline_rsync_wo_nb`)
- ALL FM board logs are written LOCALLY on the FM board
- Rsync to ZSC11 NFS happens ONLY AFTER the ENTIRE job completes
- Logbook stays completely frozen during active emulation — this is **NORMAL** (see BUG-030)
- When a board dies: partial rsync (~150 bytes) appears as the "death signal"

### Cycle Times (pkg_ghpf_model, ZSE5)
- Observed rate: ~2.3ms simulated time per hour of wall clock time
- `spacedoa_mobile`: cycle limit 50ms → ~5 hours (but common_defaults overrides to 11ms → ~4-5h)
- `spacex_mobile`: cycle limit 240ms → completes naturally at ~135ms SimTime

### FM Board Behavior
- Boards accessed via NB express queues: `fm_zse5_g503_express` through `fm_zse5_g514_express`
- "Wait Remote" in NB = job running on remote FM site (NOT stuck)
- "Wait Virtual" in FM = board occupied by active emulation
- Auto-requeue on board death: exit codes 137,138,140,162,165,163,164,166,144 → up to 10 retries
- Exit code 66 (rsync/copy-in failure) does NOT auto-requeue — requires manual resubmit

## Key Files in Test Directory
```
regression/nvlsi7_n2p/doa_pkg_ghpf_model_zse5.list.N/
├── spacedoa_mobile/
│   ├── logbook.log          # High-level test progress
│   ├── emurun.log           # Emulation run details, FM job IDs
│   ├── testbench.log        # Simics/DUT output
│   ├── results.log          # PASSED/FAILED verdict
│   ├── assertion_failures.log  # Assertion check results
│   ├── postmortem.log       # Post-run analysis
│   ├── JOBS_STATUS          # Job completion status
│   └── tlm_post/            # Post-processing tracker results
└── spacex_mobile/
    └── (same structure)
```
