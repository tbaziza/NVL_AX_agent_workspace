---
bug_id: BUG-019
title: "PCD scripts have bad Python/Perl shebangs"
date_discovered: 2026-04-09
status: fixed
severity: blocker
stage: "compile_pcd_jem"
bundle: bundle1088
category: shebang
related_patterns: [pattern_6]
tags: [python, perl, shebang, pcd, sles15, emu_build, psf_gen_jem, gen_iosf_sb_jem_trk]
---

# BUG-019: PCD scripts have bad Python/Perl shebangs

## Symptom
```
/bin/sh: .../psf_gen_jem.py: /usr/intel/pkgs/python3/3.7.4/bin/python3: bad interpreter: No such file or directory
make: *** [...Makefile.emu:120: generate_iosf_p_trk_insts] Error 1
```
and subsequently:
```
/bin/sh: .../gen_iosf_sb_jem_trk.py: /usr/intel/bin/python: bad interpreter: No such file or directory
make: *** [...Makefile.emu:125: generate_iosf_sb_trk_insts] Error 126
```

## Triggered By
```bash
grdlbuild :emu_build:zebu:pkg_ghpf_model_zse5 -Penv=immediate
```
(fails at `:emu_build:emu_build_common:compile_pcd_jem`)

## Root Cause
Multiple Python/Perl scripts in `output/pchlp/emu/pchlp/scripts/` are symlinks to the read-only PCD release
(`/nfs/site/disks/zsc11_nvlpcdh_00002/emu_pcd/emu_pcd-nvl-h-main-26ww05a/`). These scripts have pinned
interpreter shebangs that don't exist on SLES15:
- `psf_gen_jem.py`: `#!/usr/intel/pkgs/python3/3.7.4/bin/python3` (not installed)
- `gen_iosf_sb_jem_trk.py`: `#!/usr/intel/bin/python` (not installed — only `python3` exists)
- `csv_gen.py`: `#!/usr/intel/bin/python2.7` (not installed)
- `tcss_iom_ram_ecc.py`: `#!/usr/intel/bin/python3.7.4` (not installed)
- `lnl_setup_device.py`, `lnl_tcss_c20_phy_force.py`, `pcd_setup_device.py`, `pcd_tcss_emu_workaround_forces.py`: `#!/usr/intel/bin/python3.7.4`
- `gen_acemetafile.pl`: `#!/usr/intel/pkgs/perl/5.14.1/bin/perl` (not installed)

## Fix / Solution
Replaced each read-only symlink with a local writable copy, then fixed shebangs:
```bash
cd /nfs/site/disks/ive_sle_zsc11_tbaziza/models/integrate_bundle1068.ww12

# For each bad script: remove symlink, copy original, fix shebang
for f in output/pchlp/emu/pchlp/scripts/psf_gen_jem.py \
         output/pchlp/emu/pchlp/scripts/gen_iosf_sb_jem_trk.py \
         output/pchlp/emu/pchlp/scripts/csv_gen.py \
         output/pchlp/emu/pchlp/scripts/tcss_iom_ram_ecc.py \
         output/pchlp/emu/pchlp/pcd_run_dir/run_files/pcd_py_files/lnl_setup_device.py \
         output/pchlp/emu/pchlp/pcd_run_dir/run_files/pcd_py_files/lnl_tcss_c20_phy_force.py \
         output/pchlp/emu/pchlp/pcd_run_dir/run_files/pcd_py_files/pcd_setup_device.py \
         output/pchlp/emu/pchlp/pcd_run_dir/run_files/pcd_py_files/pcd_tcss_emu_workaround_forces.py; do
    target=$(readlink "$f"); rm "$f"; cp "$target" "$f"; chmod u+w "$f"
    sed -i 's|#!/usr/intel/bin/python3\.7\.4|#!/usr/intel/bin/python3|' "$f"
    sed -i 's|#!/usr/intel/pkgs/python3/3\.7\.4/bin/python3|#!/usr/intel/bin/python3|' "$f"
    sed -i 's|#!/usr/intel/bin/python2\.7|#!/usr/intel/bin/python3|' "$f"
    sed -i '1s|#!/usr/intel/bin/python$|#!/usr/intel/bin/python3|' "$f"
done
# Fix perl shebang
f=output/pchlp/emu/pchlp/scripts/gen_acemetafile.pl
target=$(readlink "$f"); rm "$f"; cp "$target" "$f"; chmod u+w "$f"
sed -i 's|#!/usr/intel/pkgs/perl/5\.14\.1/bin/perl|#!/usr/intel/bin/perl|' "$f"
```

## Files Affected
- `output/pchlp/emu/pchlp/scripts/psf_gen_jem.py` (shebang fixed to `#!/usr/intel/bin/python3`)
- `output/pchlp/emu/pchlp/scripts/gen_iosf_sb_jem_trk.py` (shebang fixed)
- `output/pchlp/emu/pchlp/scripts/csv_gen.py` (shebang fixed)
- `output/pchlp/emu/pchlp/scripts/tcss_iom_ram_ecc.py` (shebang fixed)
- `output/pchlp/emu/pchlp/scripts/gen_acemetafile.pl` (shebang fixed to `#!/usr/intel/bin/perl`)
- `output/pchlp/emu/pchlp/pcd_run_dir/run_files/pcd_py_files/*.py` (4 files, shebangs fixed)

## Verification
After fix, `compile_pcd_jem` passed and the build continued successfully.

## Notes
- These files are regenerated from PCD release symlinks by `pcd_workarea_overrides` at the start of each build. If the PCD release is updated, these fixes may need to be re-applied.
- The `export: Command not found` errors in the same log are from `cth_psetup` sourcing bash-style env scripts in a tcsh context. These are non-fatal warnings.
