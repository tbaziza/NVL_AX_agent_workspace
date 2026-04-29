---
bug_id: BUG-028
title: "Read-Only GK Integration output/ Blocks All FM Runtime Fixes"
date_discovered: 2026-04-26
status: fixed
severity: blocker
stage: "FM runtime / library loading"
bundle: bundle1106
category: permissions
related_patterns: [pattern_gk_permissions, pattern_rpath]
tags: [gatekeeper, permissions, read-only, sleadmin, output, fm, zse5, rpath]
---

# BUG-028: Read-Only GK Integration `output/` Blocks All FM Runtime Fixes (bundle1106)

## Symptom

Error in `regression/.../spacedoa_mobile/testbench.log` (FM machine `fmez5072`):
```
ERROR: ld.so: object '$WORKAREA/output/.../zse5/lib/libtinfo.so.6'        from LD_PRELOAD cannot be preloaded (cannot open shared object file): ignored.
ERROR: ld.so: object '$WORKAREA/output/.../zse5/lib/libreadline.so.7.0'   from LD_PRELOAD cannot be preloaded (cannot open shared object file): ignored.
ERROR: ld.so: object '$WORKAREA/output/.../zse5/lib/libRunControlDriverAdapter.so' from LD_PRELOAD cannot be preloaded (cannot open shared object file): ignored.
[emu error] SimExc_General('Failed to load module 'zse_engine'
   ('.../zse5/simics_workspace/linux64/lib/zse_engine.so'):
   "libxactor_lib.so: cannot open shared object file: No such file or directory"')
* spacedoa   Result: FAILED  SimTime: 0 clocks
```

And from `emurun.log`:
```
WARNING (emu::test:3014): IO::Tee->new() failed on ".../report.rpt" ...
   last error: Read-only file system
```

## Triggered By

```bash
simregress -dut nvlsi7_n2p -save -no_xs -trex -emu_model pkg_ghpf_model -emu_tech zse5 \
  -no_compress EMUL_QSLOT=/prj/sv/nvl/emu/interactive -trex- \
  -P zsc11_express -Q /IVE/NVL/emu \
  -l reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list
```

(NB feeder `sccc14644327.zsc11:42711`, task .1, jobs 29998/29999, ran on `fmez5072`.)

## Root Cause

Bundle1106's `output/` is a **symlink to a Gatekeeper integration build owned by `sleadmin`**:
```
output -> /nfs/site/disks/ive_nvl_efs_gk_002/GK4/integrate/sle_emu/integrate_bundle1106/output/
```
Permissions on every directory under that tree are `drwxr-s--- sleadmin nvlcn2` (mode 750, no group write). Although the user is in group `nvlcn2`, group write is not granted, and `chmod g+w` returns *Operation not permitted* (we don't own the dir).

This blocks every documented FM runtime fix:
- **BUG-024 (`scripts/fix_zse5_libs.sh`)** — must create ~100 symlinks in `output/.../zse5/lib/`. First `ln` fails: *Permission denied*. Result: only the originally-built `libemubuildtb.so` is in `zse5/lib/`; all 80+ xactor / Zebu / Simics / readline / tinfo / RunControl libs are absent.
- **BUG-026 ($ORIGIN RPATH patch)** — must `cp libRunControlDriverAdapter.so` into `simics_workspace/linux64/lib/` and `patchelf` `$ORIGIN` into RPATH of 9 `*.so` modules. Both writes are denied.
- **BUG-012 (`libreadline.so.7.0` LD_PRELOAD)** — needs the file present at `output/.../zse5/lib/libreadline.so.7.0`. Cannot place it.

Critically, `zse_engine.so`'s RPATH is the **absolute** GK path:
```
$ readelf -d output/.../zse_engine.so | grep RPATH
  RPATH: /usr/intel/pkgs/gcc/12.2.0/lib64:/usr/intel/pkgs/gcc/12.2.0/lib:
         /nfs/site/disks/ive_nvl_efs_gk_002/GK4/integrate/sle_emu/integrate_bundle1106/output/nvlsi7_n2p/emu/zebu_zebu//pkg_ghpf_model/zse5/lib
```

## Fix / Solution

**RESOLUTION (verified 2026-04-26 23:32)**:

The fix is a one-line GK/sleadmin perms grant followed by the canonical `fix_zse5_libs.sh`:
```bash
# Step 1 — performed by sleadmin (bundle owner) or any user with chmod rights on the GK tree:
chmod -R g+w \
  /nfs/site/disks/ive_nvl_efs_gk_002/GK4/integrate/sle_emu/integrate_bundle1106/output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/lib \
  /nfs/site/disks/ive_nvl_efs_gk_002/GK4/integrate/sle_emu/integrate_bundle1106/output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/simics_workspace/linux64/lib

# Step 2 — runs as workspace user (tbaziza); succeeds now that perms are open:
cd /nfs/site/disks/ive_sle_zsc11_tbaziza/models/integrate_bundle1106
bash scripts/fix_zse5_libs.sh
# → Linked: 100, Skipped (already exist): 0
# → Patched: 352 .so files in simics_workspace/linux64/lib/ ($ORIGIN RPATH)
# → Copied: libreadline.so.7.0, libtinfo.so.6
# → ldd verification: SUCCESS — all zse_engine.so dependencies resolved.

# Step 3 — re-submit DOA tests:
simregress -dut nvlsi7_n2p -save -no_xs -trex -emu_model pkg_ghpf_model -emu_tech zse5 \
  -no_compress EMUL_QSLOT=/prj/sv/nvl/emu/interactive -trex- \
  -P zsc11_express -Q /IVE/NVL/emu \
  -l reglist/nvlsi7_n2p/emu/doa_pkg_ghpf_model_zse5.list
```

**Diagnostic Commands** (capture state in seconds):
```bash
ls -ld output                                                     # confirm symlink target
ls -ld output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/lib/   # mode 750 sleadmin nvlcn2
ls    output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/lib/    # only libemubuildtb.so
readelf -d output/.../zse_engine.so | grep RPATH
chmod g+w output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/lib/  # confirms "Operation not permitted"
bash scripts/fix_zse5_libs.sh                                      # confirms "Permission denied"
```

## Files Affected

- `output/...` (symlinked) — entire tree was read-only; fixes blocked
- `scripts/fix_zse5_libs.sh` — the canonical fix script that requires write access

## Verification

Verified outcome (run `doa_pkg_ghpf_model_zse5.list.1`, 2026-04-26 23:32):
- spacedoa_mobile (job 30000) and spacex_mobile (job 30001) both progressed past `fuse_manager`, `ect`, and `emurun` setup (previously blocked at SimTime 0).
- Both submitted to FM netbatch (JobIDs 83580195, 83580200) and queued for FM ZSE5 emulator boards.
- Confirms `libxactor_lib.so cannot open shared object file` is resolved — root cause was confirmed permissions-only, not a build problem.

## Notes

**Distinguishing from Other Failures**: Symptom is identical to BUG-014 (libxactor_lib.so), but here the cause is *permissions on the output tree*, not a stale build. Verify by checking ownership of `output/` symlink target. If `sleadmin`-owned and mode 750, this is BUG-028. If user-owned, this is the original BUG-014 and `fix_zse5_libs.sh` will succeed.

**Prevention**: When a GK-integrated bundle is delivered with `output/` linked to an `ive_nvl_efs_gk_*` path, the post-build runtime patches MUST be applied either by GK before delivery, or with explicit `g+w` permissions on `zse5/lib/` and `simics_workspace/linux64/lib/`.
