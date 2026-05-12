---
name: sle-build-new-target-analysis-opts
description: "Debug missing global analysis/elab opts when enabling a new emulation build target type. USE WHEN: VCS analysis fails with massive library failures (hundreds or thousands), Error-[SVS] or Error-[SVSTS] about SystemVerilog constructs not supported, vlogan ignoring unknown option '-sv', global_*_vlog_opts.f file missing from genfilelist_dv output, new BUILD_DIRNAME enabled but verif/emu/<dir>/ has no symlinks. Covers: analysis_opts symlink creation, vlogan command comparison between working/failing targets, genfilelist_dv file generation diagnosis, .model.cfg.mako analysis_opts tracing."
argument-hint: "Provide the MODEL_ROOT path and MODEL name. Specify the new build target type (e.g., emuvcs) and optionally a working reference target (e.g., zebu)."
---

# New Target Type — Missing Global Analysis/Elab Opts

## When to Use
- A new build target type is enabled and VCS analysis fails massively
- Hundreds or thousands of libraries fail analysis with the same error pattern
- `Error-[SVS]` — "Unsized literal constants are only supported in SystemVerilog"
- `Error-[SVSTS]` — "Using constructs outside of modules or primitives is only supported in SystemVerilog"
- VCS warns: `Warning-[UNKWN_OPTVSIM] Ignoring unknown option '-sv'`
- A working ZSE build has a `global_*_vlog_opts.f` file in `genfilelist_dv/` but the new target doesn't

## Background: How Global Analysis Opts Work

### The Symlink Convention

The emuvcs build infrastructure requires global opts files to be **symlinked** from the build-type directory into `verif/emu/rtl_cfg/`:

```
verif/emu/<BUILD_TYPE_DIR>/
    global_*_vlog_opts.f  →  ../rtl_cfg/global_*_vlog_opts.f
    global_*_elab_opts.f  →  ../rtl_cfg/global_*_elab_opts.f
```

The actual opts files live in `verif/emu/rtl_cfg/`. Each build-type directory (`zebu/`, `emuvcs/`, etc.) must have symlinks pointing to the ones it uses. The genfilelist tool resolves these symlinks from the build-type directory, NOT directly from `rtl_cfg/`.

### The Inclusion Chain

```
.model.cfg.mako
  └─ analysis_opts: global_<prefix>_pkg_<model>_vlog_opts.f     ← per-model config
       └─ -f $MODEL_ROOT/verif/emu/rtl_cfg/global_<prefix>_vlog_opts.f  ← base opts
            └─ contains: -sverilog, -timescale=1ps/1ps, +define+..., etc.
```

The `analysis_opts` field in `.model.cfg.mako` names a file. The genfilelist tool looks for this file in `verif/emu/<BUILD_TYPE_DIR>/`. If the symlink is missing, the file is silently not found, and **vlogan runs without the global opts** — no `-sverilog`, no global defines, no global include paths.

### How vlogan Commands Are Built

Each library's vlogan command in the analysis Makefile has this structure:
```
vlogan -work <lib> -kdb -full64 +define+INTEL_EMULATION \
    -f <lib>.sv.sim.opts.f \          ← per-IP opts (from IP's RTL JSON)
    -f global_<prefix>_vlog_opts.f \  ← global analysis opts (from analysis_opts config)
    -f <lib>.sv.sim.f                 ← per-IP source files
```

When the symlink is missing, argument #2 disappears entirely — the vlogan command only gets the per-IP opts (which may have `-sv` for Xcelium, not `-sverilog` for VCS).

## Diagnosis Procedure

### Step 1: Confirm the Symptom — Mass Analysis Failures

```bash
LOGDIR=$MODEL_ROOT/output/$DUT/emu/<BUILD_DIRNAME>_emuvcs/$MODEL/vcs/log/<timestamp>
grep -c "FAILED" $LOGDIR/analyze_summary.log
grep -c "PASSED" $LOGDIR/analyze_summary.log
```

If FAILED >> PASSED (e.g., 1292 vs 6), this is a systemic issue — not individual IP problems.

### Step 2: Check a Failing Library's Errors

```bash
# Pick any failing library
grep "FAILED" $LOGDIR/analyze_summary.log | head -1
# Read its scrout log
cat $LOGDIR/<lib>.analyze.scrout | grep -i error | head -20
```

**Signature errors:**
- `Error-[SVS] SystemVerilog construct` — unsized literals (`'0`, `'1`) not recognized
- `Error-[SVSTS] SystemVerilog construct` — `typedef`, `enum`, `logic` outside modules
- `Warning-[UNKWN_OPTVSIM] Ignoring unknown option '-sv'` — Xcelium flag, not VCS

All of these indicate `-sverilog` is missing from the vlogan command.

### Step 3: Compare vlogan Commands — Failing vs Working

Check the **failing** target's vlogan command:
```bash
head -15 $LOGDIR/<failing_lib>.analyze.scrout
```

Check a **working** ZSE target's vlogan command:
```bash
# Find a ZSE scrout for comparison
ZSE_LOGDIR=$MODEL_ROOT/output/$DUT/emu/zebu_zebu/$ZSE_MODEL/zse5/analyzed_libs/
head -20 $ZSE_LOGDIR/Makefile
```

**Key difference to look for:**
```
# Working (ZSE) — has 3 -f arguments:
vlogan ... -f <lib>.sv.sim.opts.f -f genfilelist_dv/global_emu_pkg_chpr_vlog_opts.f -f <lib>.sv.sim.f

# Broken (new target) — missing the global opts file:
vlogan ... -f <lib>.sv.sim.opts.f -f <lib>.sv.sim.f
```

### Step 4: Confirm the Global Opts File is Missing from genfilelist_dv

```bash
ls $MODEL_ROOT/output/$DUT/emu/<BUILD_DIRNAME>_emuvcs/$MODEL/vcs/genfilelist_dv/global*
# Expected: No match (file is missing)

# Compare with working ZSE:
ls $MODEL_ROOT/output/$DUT/emu/zebu_zebu/$ZSE_MODEL/zse5/genfilelist_dv/global*
# Expected: global_emu_pkg_chpr_vlog_opts.f, global_emu_pkg_chpr_fast_elab_opts.f
```

### Step 5: Verify the Symlink is Missing

```bash
ls -la $MODEL_ROOT/verif/emu/<BUILD_TYPE_DIR>/
# Look for symlinks — if none exist for global_*_opts.f files, this is the problem
```

Compare with the working ZSE directory:
```bash
ls -la $MODEL_ROOT/verif/emu/zebu/ | grep '^l'
# Should show many symlinks: global_*_vlog_opts.f → ../rtl_cfg/global_*_vlog_opts.f
```

### Step 6: Verify the Source Files Exist in rtl_cfg

```bash
ls $MODEL_ROOT/verif/emu/rtl_cfg/global_<prefix>*
```

Confirm the files referenced by `analysis_opts` and `elab_opts` in `.model.cfg.mako` exist here.

## Fix Procedure

### Step 1: Identify Which Files Need Symlinks

Check `.model.cfg.mako` for the new model's `analysis_opts` and `elab_opts`:
```bash
grep -A20 '<model_name>:' $MODEL_ROOT/verif/emu/.model.cfg.mako | grep '_opts'
```

Example output:
```yaml
analysis_opts : global_emu_pkg_ch_vlog_opts.f
elab_opts: global_emu_pkg_ch_elab_opts.f
```

Then find ALL matching files in rtl_cfg:
```bash
ls $MODEL_ROOT/verif/emu/rtl_cfg/global_emu*
```

### Step 2: Create the Symlinks

```bash
cd $MODEL_ROOT/verif/emu/<BUILD_TYPE_DIR>/
# Create a symlink for each global opts file
for f in $(ls ../rtl_cfg/global_<prefix>*.f); do
    ln -s "../rtl_cfg/$(basename $f)" .
done
```

**Concrete example for a new emuvcs target:**
```bash
cd $MODEL_ROOT/verif/emu/emuvcs/
ln -s ../rtl_cfg/global_emu_elab_opts.f .
ln -s ../rtl_cfg/global_emu_pkg_ch_elab_opts.f .
ln -s ../rtl_cfg/global_emu_common_elab_opts.f .
ln -s ../rtl_cfg/global_emu_pkg_ch_vlog_opts.f .
ln -s ../rtl_cfg/global_emu_vlog_opts.f .
```

### Step 3: Verify Symlinks Resolve

```bash
ls -la $MODEL_ROOT/verif/emu/<BUILD_TYPE_DIR>/global_*.f
# Confirm all symlinks point to valid files
file $MODEL_ROOT/verif/emu/<BUILD_TYPE_DIR>/global_*_vlog_opts.f
# Should show "symbolic link to ../rtl_cfg/..."
```

Verify the critical flag is in the chain:
```bash
grep -- '-sverilog' $MODEL_ROOT/verif/emu/rtl_cfg/global_<prefix>_vlog_opts.f
# Must show: -sverilog
```

### Step 4: Rebuild

A full rebuild is required — the genfilelist tool needs to re-run to pick up the symlinks and generate the correct vlogan commands with the global opts file included.

## Common Mistakes

### Wrong Fix: Adding -sverilog to *_CHANGES.cfg
Adding `-sverilog` to the `add: vlog_opts:` section of `*_CHANGES.cfg` will technically work but is **inconsistent** with how other targets handle it. The `-sverilog` belongs in `global_*_vlog_opts.f` which is shared across all models for a given target type. The `*_CHANGES.cfg` is for model-specific overrides (defines, file additions/removals), not global compilation flags.

### Wrong Fix: Adding -sv removal to CHANGES.cfg
Adding `-sv` to `remove: vlog_opts:` is treating a symptom. The `-sv` flag in per-IP opts is harmless in VCS (it generates a warning, not an error). It comes from the IP's RTL JSON metadata which targets Xcelium. VCS correctly ignores it. The real problem is `-sverilog` not being present.

### Forgetting Elab Opts Symlinks
Don't only create the `vlog_opts` symlinks — also create the `elab_opts` symlinks. The elaboration phase has the same symlink requirement. Missing elab opts will cause failures at the next stage.

## Reference: ZSE zebu/ Symlink Pattern

The established `verif/emu/zebu/` directory provides the reference pattern. It contains symlinks for every `global_*` file it uses:

```
global_emu_elab_opts.f          → ../rtl_cfg/global_emu_elab_opts.f
global_emu_pkg_ch_vlog_opts.f   → ../rtl_cfg/global_emu_pkg_ch_vlog_opts.f
global_emu_pkg_ch_elab_opts.f   → ../rtl_cfg/global_emu_pkg_ch_elab_opts.f
global_emu_pkg_chpr_vlog_opts.f → ../rtl_cfg/global_emu_pkg_chpr_vlog_opts.f
global_emu_vlog_opts.f          → ../rtl_cfg/global_emu_vlog_opts.f
global_zebu_elab_opts.f         → ../rtl_cfg/global_zebu_elab_opts.f
... (and more)
```

When creating a new target type, mirror this pattern with the appropriate file prefix.

## Key Insight

The genfilelist tool discovers global opts files from `verif/emu/<BUILD_TYPE_DIR>/`, not from `verif/emu/rtl_cfg/` directly. When a new build target type is enabled, the build-type directory typically starts with only `Makefile` and `Makefile.cfg`. The symlinks must be **manually created** as part of the target enablement — they are not auto-generated by any tool.
