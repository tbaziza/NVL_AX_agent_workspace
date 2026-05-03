---
title: "Environment — Paths, Tools & Variables"
module: 02_execution
tags: [environment, paths, tools, nfs, zebu, vcs, simics]
---

# Environment — Paths, Tools & Variables

## Workspace Paths

| Path | Description |
|------|-------------|
| `/nfs/site/disks/ive_sle_zsc11_tbaziza/models/integrate_bundle1106` | Current workspace root |
| `/nfs/site/disks/ive_nvl_efs_gk_002/GK4/integrate/sle_emu/integrate_bundle1106/output/` | GK build output (symlinked as `output/`) |
| `/nfs/site/disks/ive_sle_zsc11_tbaziza` | NFS disk (4.9TB total) |

## ZSE5 Model Path
```
# Replace <EMU_MODEL> with the model being built (e.g., pkg_ghpf_model)
ZSE5=output/nvlsi7_n2p/emu/zebu_zebu/<EMU_MODEL>/zse5
```

## Tool Installations

| Tool | Version | Path |
|------|---------|------|
| Zebu SDK | V21.09-2_B4_250617 | `/p/hdk/rtl/cad/x86-64_linux26/synopsys/z_zse/V21.09-2_B4_250617` |
| VCS | (from tool.cth) | `/p/hdk/rtl/cad/x86-64_linux26/synopsys/vcs/...` |
| Simics | 6.0.210 | `/p/hdk/cad/windriver/simics/6.0.210/` |
| GCC | 12.1.0 | `/usr/intel/pkgs/gcc/12.1.0/bin/gcc` |
| GCC (for RPATH) | 12.2.0 | `/usr/intel/pkgs/gcc/12.2.0/lib64` |
| Python3 | 3.11.1 | `/usr/intel/bin/python3` |
| Perl | 5.34.0+ | `/usr/intel/bin/perl` |
| utdb | 24.06_shOpt64 | `/p/hdk/rtl/cad/x86-64_linux44/dt/utdb/24.06_shOpt64` |
| Copilot CLI | latest | `/p/hdk/cad/copilot/latest/copilot` |

## Known-Bad Tool Paths (DO NOT USE)

| Bad Path | Replacement |
|----------|-------------|
| `/usr/intel/bin/python3.7.4` | `/usr/intel/bin/python3` |
| `/usr/intel/pkgs/python3/3.7.4/bin/python3` | `/usr/intel/bin/python3` |
| `/usr/intel/bin/python2.7` | `/usr/intel/bin/python3` |
| `/usr/intel/bin/python` | `/usr/intel/bin/python3` |
| `/usr/intel/pkgs/perl/5.14.1/bin/perl` | `/usr/intel/bin/perl` |
| `/usr/intel/pkgs/gcc/9.2.0/` | `/usr/intel/pkgs/gcc/12.1.0/` |
| `/p/com/eda/` | `/p/hdk/rtl/cad/x86-64_linux26/` |
| utdb `24.03_shOpt64` | utdb `24.06_shOpt64` |

## Environment Variables

```bash
# Zebu
export ZEBU_ROOT=/p/hdk/rtl/cad/x86-64_linux26/synopsys/z_zse/V21.09-2_B4_250617
export LD_LIBRARY_PATH="$ZEBU_ROOT/lib:$ZEBU_ROOT/tcl:$LD_LIBRARY_PATH"
export TCL_LIBRARY="$ZEBU_ROOT/tcl/tcl8.6"
export SNPSLMD_LICENSE_FILE="26586@synopsys07p.elic.intel.com:..."

# Workspace
export WORKAREA=/nfs/site/disks/ive_sle_zsc11_tbaziza/models/integrate_bundle1106
```

## NB/FM Configuration

| Setting | Value |
|---------|-------|
| NB Pool | `zsc11_express` |
| NB QSlot | `/IVE/NVL/emu` |
| FM QSlot | `/prj/sv/nvl/emu/interactive` (NOT `/prj/sv/nvl/showstopper`) |
| NB Feeder Host | `sccc14644327.zsc11.intel.com` |
| FM Board Queue | `fm_zse5_g503-g514_express` |

## Disk Management

```bash
# Check disk usage
df -h /nfs/site/disks/ive_sle_zsc11_tbaziza | tail -1

# Find large dirs
du -sh output/nvlsi7_n2p/emu/zebu_zebu/<EMU_MODEL>/zse5/zcui.work/* 2>/dev/null | sort -rh | head -15
```

### Safe-to-Delete (ONLY after corresponding stage passes)
- After analyze: `*.analyze.scrout` files (~1.6GB)
- After vcs_splitter: `elab.log` (~24GB), `vcs_splitter_VCS_Task_Builder.log` (~24GB), `analyzed_libs/` (~55GB)
- After FPGA P&R: `zCui/vcs_splitter/` (~57GB) — **CAUTION: see BUG-006**
- After all stages: `backend_default_*_zFpgaTiming.log` files

> ⚠️ **WARNING**: Do NOT delete `zcui.work/vcs_splitter/` until `zebu_tb` has completed.
