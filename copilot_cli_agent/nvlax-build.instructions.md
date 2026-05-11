---
applyTo: "**"
---

# Step 1: Compile the Model

## Command — Start Fresh Build

```bash
cd $MODEL_ROOT   # your model workarea (set by cth_psetup or manually)
grdlbuild :emu_build:zebu:pkg_ghpf_model_zse5 -Penv=immediate
```

## Command — Resume Build (skip completed stages)

```bash
grdlbuild :emu_build:zebu:pkg_ghpf_model_zse5 -id
```

Use `-id` ONLY when analyze/fe_be stages already completed. NEVER on first build.

## Build Stages (14 stages, ~50 hrs total)

prerequisite → spark_co → override_vcs_home → gen_dv_flist → c_compile → dw_gen → gen_analyze_make → zse_lint → pre_analyze → gen_elab_src → analyze (~45m) → fe_be (~25h) → zebu_tb → emu_gen

## How to Verify Compilation Passed — ALL 7 Must Pass

> **Note:** the technology subdir under `<EMU_MODEL>/` may be `zse5` **or** `zse4` depending on the build platform. Replace `zse5` in the paths below with the actual subdir.

```bash
# 1. .build_info.yml reports VALID = YES  ← GATE: if this fails, do NOT run checks 2–7
grep -qE "^\s*VALID\s*[:=]\s*YES\b" output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/.build_info.yml \
  && echo "CHECK-1: PASS" || { echo "CHECK-1: FAIL — STOP, do not run remaining checks"; }

# 2. Shadow files = 19
[ $(ls .shadow/ | wc -l) -eq 19 ] && echo "CHECK-2: PASS" || echo "CHECK-2: FAIL"

# 3. U0-U3 backend directories exist
ls output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/zcui.work/backend_default/ | grep -c "^U[0-9]"

# 4. MuDb info non-empty
[ -s output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/zcui.work/backend_default/MuDb/equis/info ] && echo "CHECK-4: PASS" || echo "CHECK-4: FAIL"

# 5. No missing shared libraries
ldd output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/simics_workspace/linux64/lib/zse_engine.so 2>/dev/null | grep -c "not found"

# 6. readmem.dump is a regular file
[ -f output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/readmem.dump ] && echo "CHECK-6: PASS" || echo "CHECK-6: FAIL"

# 7. No failure_info.log in latest log dir
LATEST=$(ls -t output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/log/ | head -1)
[ ! -f "output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/log/$LATEST/failure_info.log" ] && echo "CHECK-7: PASS" || echo "CHECK-7: FAIL"
```

**Quick check (gate on VALID first):**
```bash
grep -qE "^\s*VALID\s*[:=]\s*YES\b" output/nvlsi7_n2p/emu/zebu_zebu/pkg_ghpf_model/zse5/.build_info.yml \
  && [ $(ls .shadow/ | wc -l) -eq 19 ] \
  && echo "COMPILATION PASSED" || echo "COMPILATION INCOMPLETE"
```

## Step 2: Post-Build (on demand only — DO NOT auto-run)

**Do NOT run `post_zcui` automatically after a successful compilation.**

Only run it as a recovery step when the `zcui` / `zebu_tb` stage failed during the build, and ONLY after asking the user for permission:

> "The `zcui` / `zebu_tb` stage appears to have failed. May I run `post_zcui` to retry that stage only?"

If approved:

```bash
grdlbuild :emu_build:zebu:pkg_ghpf_model_zse5_post_zcui  # post_zcui
```

## If Compilation Fails → Go to debug instructions
