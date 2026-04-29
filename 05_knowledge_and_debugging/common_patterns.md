---
title: "Common Failure Patterns"
module: 05_knowledge_and_debugging
tags: [patterns, failures, categories, recurring, classification]
---

# Common Failure Patterns

> Recurring issue categories and their general resolution strategies.
> When you encounter a new bug that fits a pattern, add a reference here.
> When you discover a NEW pattern, create a new section.

## Pattern 1: Interpreter / Shebang Errors
- **Symptom**: Script exits immediately; `bad interpreter: No such file or directory`
- **Cause**: Script uses a pinned interpreter path that doesn't exist on SLES15
- **General Fix**: Replace pinned path with generic `/usr/intel/bin/python3` or `/usr/intel/bin/perl`
- **Known-Bad Paths**: `/usr/intel/bin/python3.7.4`, `/usr/intel/pkgs/python3/3.7.4/bin/python3`, `/usr/intel/bin/python2.7`, `/usr/intel/pkgs/perl/5.14.1/bin/perl`
- **Known-Good Paths**: `/usr/intel/bin/python3` (→ 3.11.1), `/usr/intel/bin/perl`
- **Related Bugs**: BUG-010, BUG-018, BUG-019

## Pattern 2: IP / Filelist Not in IPX Cache
- **Symptom**: `hotfix_file_check` or `bump_pins_check_gen` fails; IP variant not found
- **Cause**: Specific IP release variant never released to IPX
- **General Fix**: Change to a released variant (e.g., `_Full_model` → `_reduced_2`)
- **Files to Check**: `filelists/*.soc.list`, `filelists/.soc.list.mako`
- **Related Bugs**: BUG-002

## Pattern 3: EDA Tool Path Not Found
- **Symptom**: VCS compilation fails; tool binary not found
- **Cause**: Mount point `/p/com/eda/` doesn't exist; tools at `/p/hdk/rtl/cad/x86-64_linux26/`
- **General Fix**: Run `scripts/fix_die_ctech_paths.csh`
- **Related Bugs**: (general — multiple bugs reference this)

## Pattern 4: Missing Module Instantiation (XMRE Errors)
- **Symptom**: VCS elaboration XMRE cross-module reference errors
- **Cause**: Module referenced but not instantiated in testbench
- **General Fix**: Add `<module_name> <module_name>();` to `src/val/emu/testbench/rtl/pkg_emu_tb.sv`

## Pattern 5: Disk Full During zDB_Global
- **Symptom**: `RDB0466E: basic_ios::clear: iostream error`
- **Cause**: NFS disk hits 100% during global database write
- **General Fix**: Free disk space, restart with `grdlbuild ... -id`

## Pattern 6: `vcs_splitter/` Deleted Before `zebu_tb`
- **Symptom**: `cp: cannot stat '../vcs_splitter/zemi3.h': No such file or directory`
- **Cause**: `vcs_splitter/` deleted for disk space before `zebu_tb`
- **General Fix**: Create stub `zemi3.h`, run `make -f dpixtor.mk install`, touch shadow
- **Related Bugs**: BUG-005

## Pattern 7: zDB_Global Log Appears Stuck
- **Symptom**: Log line count not increasing for 10+ minutes
- **Cause**: zDB runs on farm node with local scratch; NFS log flushed periodically
- **Diagnosis**: Check Controller log modify time — if recent, job is alive
- **Action**: WAIT. Do NOT restart.

## Pattern 8: Tests Fail — "No builds found to validate"
- **Symptom**: `emurun WARNING: Filtering out zse5/` + `No builds found to validate`
- **Cause**: `prepare_spark` and `spark_tb` never ran (zebu_tb was manually forced)
- **General Fix**: Re-run `grdlbuild :emu_build:zebu:pkg_ghpf_model_zse5 -Penv=immediate`
- **Related Bugs**: BUG-005

## Pattern 9: MuDb Missing / FpgaPostProc Skipped
- **Symptom**: `CORE0001E: Cannot read MuDb version` + `LUI1744E` + `ZHW0909E`
- **Cause**: FpgaPostProc skipped during fe_be (zPRD mode)
- **Diagnosis**: `grep "FpgaPostProc normal task termination: skipped" fe_be.log | wc -l`
- **General Fix**: Re-run fe_be: `rm .shadow/fe_be && grdlbuild ... -Penv=immediate`
- **Related Bugs**: BUG-007, BUG-008

## Pattern 10: `fuse_assembler/` Missing — pcd_ss_gen Fails
- **Symptom**: `bad interpreter` in softstrap/fuse assembler scripts
- **Cause**: Read-only PCD release symlinks with old Python shebangs
- **General Fix**: Replace symlinks with local copies, fix shebangs
- **Related Bugs**: BUG-010, BUG-019

## Pattern 11: Zebu FM — `zse_engine.so` Cannot Load Shared Libraries
- **Symptom**: `SimExc_General('Failed to load module...')` with missing `.so`
- **Cause**: gecco LD_LIBRARY_PATH points to wrong path; RPATHs need fixing
- **General Fix**: Create symlinks in `zse5/lib/` via `scripts/fix_zse5_libs.sh`; patch RPATH with `$ORIGIN`
- **Key insight**: `addEnv('LD_LIBRARY_PATH')` does NOT work in gecco FM env. Use RPATH/co-location.
- **Related Bugs**: BUG-011, BUG-014, BUG-024, BUG-026, BUG-028

## Pattern 12: Kerberos/SSH Authentication Failures
- **Symptom**: rsync "connection unexpectedly closed", SSH "Password change required"
- **Cause**: Kerberos ticket expired OR Intel/AD password expired
- **General Fix**: `kinit -R` for ticket renewal; change password if PAM blocks
- **Related Bugs**: BUG-033, BUG-034

## Pattern 13: GK Build Read-Only Permissions
- **Symptom**: "Permission denied" or "Read-only file system" when fixing libs
- **Cause**: `output/` symlinked to GK build owned by `sleadmin`, mode 750
- **General Fix**: `chmod -R g+w` on specific directories (requires GK owner or admin)
- **Related Bugs**: BUG-028
