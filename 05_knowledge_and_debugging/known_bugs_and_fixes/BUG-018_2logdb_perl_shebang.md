---
bug_id: BUG-018
title: "2logdb.pl uses perl 5.14.1 shebang — not on SLES15"
date_discovered: 2026-04-09
status: fixed
severity: non-critical
stage: "TLM_POST logdb"
bundle: bundle1068
category: shebang
related_patterns: [pattern_6]
tags: [perl, shebang, utdb, 2logdb, sles15, tracker, jem, atom_tracker, iosf_sb]
---

# BUG-018: 2logdb.pl uses perl 5.14.1 shebang — not on SLES15

## Symptom
```
Stage(REPLAY JEM_PYTHON): tracker appears to be empty
```
(in run .9, when test FAILED due to libxactor_lib.so — no JEM traces captured)

For successful FPGA runs (e.g. run .26):
```
2logdb.pl: /usr/intel/pkgs/perl/5.14.1/bin/perl: bad interpreter: No such file or directory
```
(logdb stage of atom_tracker and iosf_sb_jem_tracker)

## Triggered By
```bash
simregress -dut nvlsi7_n2p -save -no_xs -trex -emu_model pkg_ghpf_model -emu_tech zse5 \
  -no_compress EMUL_QSLOT=/prj/sv/nvl/showstopper -trex- -local \
  -l reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list
```
Trackers: `atom_tracker_A8C0/1/2/3` and `iosf_sb_jem_tracker` in tlm_post.

## Root Cause
Both trackers use a `replay` + `logdb` pipeline:
1. **Replay stage** (`jem_py_replay.py`): reads JEM binary traces from `jem/` directory using `libtlmgen_pkg_py.so`. In a successful FPGA run, hub atom and IOSF SB JEM traces ARE captured (confirmed in run .27 jem/ directory: `hub_atom_hip_uri_tlm`, `hub_atom_hip_mec_hw_signals`, `hub_atom_hip_iprf_write`, `iosf_sb_tlm_req` binary traces exist).

2. **Logdb stage** (`2logdb.pl`): converts tracker output log to logdb format. The `logdb_script` path is resolved via: `cth_query -tool runtools params utdb_path -resolve` → path from `tool.cth` → `24.03_shOpt64`. The `2logdb.pl` in that version uses shebang `#!/usr/intel/pkgs/perl/5.14.1/bin/perl` which **does NOT exist** on SLES15 machines (only perl 5.26.1, 5.34.0, 5.36.0, 5.40.1 are installed).

## Fix / Solution
Changed `utdb` version in `tool.cth` from `24.03_shOpt64` to `24.06_shOpt64`. The `24.06` version uses shebang `#!/usr/intel/pkgs/perl/5.34.0/bin/perl` which IS installed at `/usr/intel/pkgs/perl/5.34.0/bin/perl`.

```bash
# In tool.cth — changed:
utdb = 24.06_shOpt64   # was: 24.03_shOpt64
```

## Files Affected
- `tool.cth` — line: `utdb = 24.06_shOpt64` (was `24.03_shOpt64`)

## Verification
```bash
cth_query -tool runtools params utdb_path -resolve
# Returns: /p/hdk/rtl/cad/x86-64_linux44/dt/utdb/24.06_shOpt64

/p/hdk/rtl/cad/x86-64_linux44/dt/utdb/24.06_shOpt64/scripts/2logdb.pl
# Returns: 2logdb-E-: Neither --convert and --is-supported flags were given
# (meaning it RUNS — no bad interpreter error)
```

## Notes
- `atom_tracker` JEM config: `src/val/emu/trackers/Atom_Core/atom_uip_lip_trk.py`
  - Uses `ATOM_ROOT_HUB = soc/nvlsi7_n2p/hub/subip/hip/hub_atomcpu`
  - Reads hub atom JEM traces: `hub_atom_hip_uri_tlm`, `hub_atom_hip_mec_hw_signals`, `hub_atom_hip_iprf_write`
- `iosf_sb_jem_tracker` JEM config: `subip/vip/sbr_network_gen/iosf_jem_tracker/nvl_hub_cdie_iosf_jem_tracker.py`
  - Reads IOSF SB traces: `iosf_sb_tlm_req` ports
- `libtlmgen_py.so` = `output/nvlsi7_n2p/jem/model/tlmgen_pkg/libtlmgen_pkg_py.so` (EXISTS)
- `2logdbConf.pm` = `verif/tlm_post/logdb_config/2logdbConf.pm` (workspace-local, works with both utdb versions)
- JEM trace index = `jem/tlm_map.txt` (generated per run in spacedoa/spacex result dir)
- `JEMSW_LIB = output/nvlsi7_n2p/jem/model/tlmgen_pkg/`
- In early failed runs (e.g. run .9 — libxactor_lib.so error), test doesn't run → no JEM traces → replay stage says "tracker appears to be empty" in 1 second. This is expected and different from the logdb failure.
- In successful FPGA runs, hub atom JEM traces ARE captured (model DOES have Atom cores — CDIE0_DUT_CONFIG_ATOM0_ENABLE=1, CDIE0_DUT_CONFIG_ATOM_NUM=4)
- Utdb `24.06_shOpt64` has identical API to `24.03_shOpt64` (same `2logdb.pl` command syntax)
- DO NOT change utdb back to `24.03_shOpt64` — perl 5.14.1 is not installed on this system
