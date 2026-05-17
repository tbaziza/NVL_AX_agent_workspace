---
name: gk-turnin
description: >-
  Guide for turning in git commits using Intel's Gatekeeper (CTH) system. Use when users
  want to turnin commits, submit changes to gatekeeper, or run cth_psetup with turnin
  commands. Works with pcd cluster and ttl-h-main stepping.
  Triggers: gatekeeper turnin, cth_psetup, submit commit, git turnin, CTH turnin, gk
  turnin.
---

# Gatekeeper Turnin

## Overview

This skill helps you turn in git commits to Intel's Gatekeeper system using the CTH (Common Tool Helper) infrastructure. It ensures proper environment setup, validates turnin comment formatting, and executes the turnin workflow.

## Workflow Decision Tree

**When to use this skill:**
- User asks to "turnin" a commit
- User wants to submit changes to Gatekeeper
- User mentions "cth_psetup" with turnin
- User needs to turn in latest commit(s)

**Prerequisites:**
1. Must be in a git repository with commits to turn in
2. README file should exist with cth_psetup command
3. Must have access to CTH infrastructure

## Step-by-Step Workflow

### Step 1: Analyze Changes and Verify Environment

**CRITICAL: Understand what you're turning in before proceeding!**

#### 1a. Check Environment

**Check if $WORKAREA is set:**
```bash
echo $WORKAREA
```
- If not set or empty, set it:
  ```bash
  export WORKAREA=$PWD
  ```

#### 1b. Analyze the Changes Being Turned In

**Get commit information:**
```bash
# View latest commit with full message
git --no-pager log -1

# View last N commits if turning in multiple commits
git --no-pager log -5 --oneline

# See detailed commit info
git --no-pager show HEAD --stat
```

**Understand what files changed:**
```bash
# List all changed files in the commit
git --no-pager diff-tree --no-commit-id --name-only -r HEAD

# Group files by directory to identify affected areas
git --no-pager diff-tree --no-commit-id --name-only -r HEAD | cut -d'/' -f1-2 | sort | uniq -c

# See actual changes (use carefully for large diffs)
git --no-pager show HEAD
```

**Analyze the type of changes:**

Use the file paths and diff content to determine:

| File Pattern | Likely Category | Suggested Tag |
|--------------|----------------|---------------|
| `verif/tests/`, `verif/testslists/`, `verif/sequences/` | Test/sequence changes | `VAL` type |
| `src/<IP>/`, `subsystems/<IP>/` | IP integration | `INT` type, use IP name |
| `cfg/ace/`, `scripts/`, `Makefile`, `.gitignore` | Environment/tooling | `ENV` type, `ENV` or `GK` chapter |
| `power/`, `*.upf` | Power-related | `INT` or `VAL`, `PWR` or `UPF` chapter |
| `dfx/`, `verif/tests/dfx/` | DFX-related | `INT` or `VAL`, `DFX` chapter |
| `flows/`, `cfg/` | Flow/config changes | `ENV` type, `ENV` chapter |
| `*_waiver.txt`, `lint/`, `cdc/` | Static checks | `SChk` type, `LINT`/`CDC` chapter |
| `integration/`, `handoff/` | IP integration | `INT` type |
| ROM files, `pmc_fw/` | Firmware/ROM | `INT` type, `ROM` chapter |
| `emu/`, emulation-related | Emulation | `VAL` type, `EMU` chapter |
| `fpga/`, FPGA-related | FPGA | `VAL` type, `FPGA` chapter |

**Example analysis workflow:**
```bash
# 1. Get the commit message
git --no-pager log -1 --pretty=format:"%s"

# 2. List changed files
git --no-pager diff-tree --no-commit-id --name-only -r HEAD

# 3. Categorize by analyzing paths
# If you see mostly verif/tests/* -> VAL type
# If you see src/ip_name/* -> INT type, use ip_name for chapter
# If you see scripts/* or cfg/* -> ENV type
```

**Determine the appropriate tags based on analysis:**

1. **Identify affected IP/Chapter:**
   - Single IP: Use IP name (e.g., `FIA`, `USB`, `CLK`)
   - Multiple IPs: Use `IP1/IP2/IP3` format
   - Test chapter: Use chapter name (e.g., `BOOT`, `DFX`)
   - Environment: Use `ENV` or `GK`

2. **Identify Type:**
   - RTL/IP integration → `INT`
   - Test/sequence/validation → `VAL`
   - Scripts/config/environment → `ENV`
   - Lint/CDC/static checks → `SChk`

3. **Identify Milestone:**
   - Check project status or ask user if uncertain
   - Common: `R0P5`, `R0P8`, `V1P0`, `ECO1`, etc.

#### 1c. Read README for CTH Setup Command

**Read the README to find the cth_psetup command:**
```bash
cat README
```
- Look for the `cth_psetup` command line (typically line 4)
- Extract the full command path and arguments
- Common pattern: `/p/cth/pu_tu/prd/liteinfra/<version>/commonFlow/bin/cth_psetup -p <project> -read_only -skip_prompt -nowash -force`
- Also note the cluster (`-c`) and stepping (`-s`) parameters from the turnin example (typically line 7)

### Step 2: Format Turnin Comment

**REQUIRED FORMAT:** The turnin comment MUST follow this strict pattern for indicator automation, turnin prioritization, and release note automation:

```
<proj>-<milestone>-<IP/chapter>-<Type>: actual comment
```

#### Project (`proj`)

Project name format: `<proj key><dut key1>/<dut key2>/<dut key3>`

Use `/<dut key>` for turnins containing changes for more than one DUT.

**TTL Project examples:**
- `TTLH` - TTL H-die
- `TTLS` - TTL S-die  
- `TTLH/S` - Changes affecting both H and S dies

**Other project examples:**
- CNP: `CNPLP`, `CNPH`, `CNPLP/H`
- ICP: `ICPLP`, `ICPH`, `ICPN`, `ICPLP/H`, `ICPLP/N`, `ICPN/H`, `ICPLP/N/H`
- TGP: `TGPLP`, `TGPH`, `TGPN`, `TGPLP/H`, `TGPLP/N`, `TGPN/H`, `TGPLP/N/H`

#### Milestone (`milestone`)

Target milestone for the changes. Starts with "R" for RTL milestone, "V" for Validation milestone, "ECO" for ECO turnins.

**Format patterns:**
- Pre-RTL 0P5: `Rpre0P5` (initial project startup if starting at 0P5)
- Pre-RTL 0P8: `Rpre0P8` (initial project startup if starting at 0P8)
- RTL 0P5: `R0P5`
- RTL 0P8: `R0P8`
- RTL 1P0: `R1P0` (for IP with no ECO, but has drop for RDL fix, lintra waiver, CDC waiver, etc)
- VAL 1P0: `V1P0` (for test/seq changes for VAL 1P0)
- ECO: `ECO1`, `ECO2`, `ECO3`, etc.

**Common milestones:**
- `R0P5`, `R0P8`, `R1P0` - RTL milestones
- `V1P0` - Validation milestone
- `Rpre0P5`, `Rpre0P8` - Pre-RTL milestones
- `ECO1`, `ECO2`, `ECO3` - ECO milestones (can be for RTL or VAL)

#### IP/Chapter (`IP/chapter`)

IP (or subsystem) name for IP integration, OR test chapter name for test/seq turnins.

**Common IP/Chapter tags:**
- `CLK` - ICC/ISCLK plus top level clock changes
- `USBx` - USB including usb2phy
- `BOOT` - Boot chapter
- `DFX` - DFX (can categorize as DFXMBIST, DFXVISA, DFXIDV - keep it short but retain DFX prefix)
- `ROM` - DFX Production ROM (use INT for type)
- `PWR` - Power (can categorize as PWRUSB, PWRDMI - keep it short but retain PWR prefix)
- `FPGA` - FPGA
- `EMU` - Emulation
- `GK` - Gatekeeper update
- `ENV` - ACE/HDK/Script update (for DA and script owner only, including fc.pp global cleanup - NOT verif env)
- `LINT` - Lintra
- `CDC` - CDC
- `SpyLP` - SpyglassLP
- `GLS` - Global GLS changes (not specific IP GLS fix)
- `UPF` - All other UPF turnins by UPF team
- **Multiple IPs:** `<IP1>/<IP2>/<IP3>` format (e.g., `FIA/USB/CLK`)

**Important:** Be consistent with naming - pick one name and stick with it (e.g., choose either CAVS or ADSP, not both).

#### Type (`Type`)

Type of turnin:

- `INT` - Integration turnin (including Production ROM integration)
- `VAL` - Validation turnin only (includes FC VAL, DFX VAL, POWER VAL, GLS, Emulation/FPGA)
- `ENV` - ENV/GK/script turnin (THIS IS NOT for VAL ENV)
- `SChk` - Static check (Lint/spyglass/CDC)

#### Actual Comment

Your regular meaningful comment. **Do not repeat what's already in the tagging.**

**Requirements:**
- For IP rev up: Include SHIP TAG and IP VERSION (IRR version or hotfix version)
- Comment should describe what changed in the **whole turnin**, not just last commit
- If turnin contains changes pulled from any inflight/active turnin, indicate it at the end
- Turnin comment with ONLY "resolve merge conflict with 12345" is **NOT acceptable**

#### Complete Examples

**ECO turnins:**
```
CNPLP-ECO1-FIA-INT: FIA ECO1 drop CNPA0P10RTL4V1 (IP drop: FIA_CNPLP_ECO1_WW02)
CNPLP-ECO1-CLK-INT: CLK connection fix signal ABC
```

**Integration turnins:**
```
CNPH-Rpre0P8-DFX-INT: Integrate dfx CNPHA0P08RTL1V1 (IP Drop: dfx-cnph-a0-16ww02)
TTLH-R0P5-ENV-ENV: copilot cli + pcd val agent setup script
CNPLP-R1P0-ROM-INT: PMC ROM version 123 update
```

**Validation turnins:**
```
CNPLP-V1P0-BOOT-VAL: boot scenarioXYZ update
CNPLP-V1P0-FPGA-VAL: enable backdoor for ISH
TTLS-V1P0-USBx-VAL: USB validation test fixes
```

**Environment/Tool turnins:**
```
CNPLP-R1P0-LINT-SChk: lintra waiver update for parpsf2
CNPH-R1P0-GK-ENV: update file lock owner
CNPLP-R1P0-ENV-ENV: add new switch ABC to local ivar
```

**Common mistake:** Missing the tag format will cause turnin to fail with:
```
Error : comment doesn't fufill the turnin comment tag!
```

### Step 3: Construct and Execute CTH Turnin

**Now that you understand the changes, construct the properly tagged turnin comment.**

**Command pattern:**
```bash
<cth_psetup_command_from_README> -cmd 'turnin -c <cluster> -s <stepping> -comments "<formatted_comment>"'
```

**Example based on change analysis:**

If analysis shows:
- Changed files: `scripts/bin/common/copilot_setup.sh`, `.gitignore`
- Type: Environment/tooling changes
- Category: ENV

Construct comment:
```bash
/p/cth/pu_tu/prd/liteinfra/1.20/commonFlow/bin/cth_psetup -p pcth -read_only -skip_prompt -nowash -force -cmd 'turnin -c pcd -s ttl-h-main -comments "TTLH-R0P5-ENV-ENV: copilot cli + pcd val agent setup script"'
```

**More examples matching analysis to tags:**

**Example 1: Single IP Integration**
- Files: `src/usb/usb_controller.sv`, `subsystems/usb/usb_top.sv`
- Analysis: USB IP integration → Type: `INT`, Chapter: `USBx`
```bash
# Comment: "TTLH-R0P5-USBx-INT: USB controller rev-up to version X.Y"
```

**Example 2: Multiple IP Integration**
- Files: `src/fia/`, `src/usb/`, `integration/clk/`
- Analysis: Multiple IPs → Type: `INT`, Chapter: `FIA/USB/CLK`
```bash
# Comment: "TTLH-R0P5-FIA/USB/CLK-INT: clock integration for FIA and USB IPs"
```

**Example 3: Validation Test**
- Files: `verif/tests/boot/pch_reset_test.sv`, `verif/sequences/boot_seq.sv`
- Analysis: Test changes → Type: `VAL`, Chapter: `BOOT`
```bash
# Comment: "TTLH-V1P0-BOOT-VAL: boot reset sequence test updates"
```

**Example 4: DFX Validation**
- Files: `verif/tests/dfx/mbist_test.sv`, `verif/testslists/dfx_mbist.list`
- Analysis: DFX test changes → Type: `VAL`, Chapter: `DFXMBIST`
```bash
# Comment: "TTLS-V1P0-DFXMBIST-VAL: MBIST coverage improvements"
```

**Example 5: Lintra Waiver**
- Files: `lint/usb_waiver.txt`, `scripts/lint/update_waivers.sh`
- Analysis: Static check waivers → Type: `SChk`, Chapter: `LINT`
```bash
# Comment: "TTLH-R1P0-LINT-SChk: lintra waiver updates for USB IP"
```

**Example 6: Environment/GK Update**
- Files: `cfg/ace/pchlp/fc.acerc`, `Makefile`, `.gitignore`
- Analysis: Config/environment → Type: `ENV`, Chapter: `ENV`
```bash
# Comment: "TTLH-R0P5-ENV-ENV: ACE config updates for new IP integration"
```

**Example 7: ECO Integration**
- Files: `src/fia/fia_eco1_fixes.sv`
- Analysis: ECO fix → Milestone: `ECO1`, Type: `INT`, Chapter: `FIA`
```bash
# Comment: "TTLH-ECO1-FIA-INT: FIA ECO1 drop TTLHA0P10RTL4V1 (IP drop: FIA_TTLH_ECO1_WW02)"
```

**Parameters explained:**
- `-p pcth`: Project type (from README)
- `-read_only`: Read-only mode
- `-skip_prompt`: Skip interactive prompts
- `-nowash`: Skip workspace washing
- `-force`: Force setup
- `-cmd`: Command to execute within CTH environment
- `-c pcd`: Cluster name
- `-s ttl-h-main`: Stepping name
- `-comments`: The formatted turnin comment

**Execution tips:**
- Use `initial_wait: 90` seconds for bash tool
- Use `mode: "sync"` to capture full output
- Watch for "Submission successful" message

### Step 4: Verify Turnin Success

**Success indicators:**
```
Submission successful.
Received turnin <ID>
```

**You'll receive:**
- Turnin ID number (e.g., 2609)
- Monitoring command: `turnininfo <ID>`
- Web URL: `https://scygatkpr410.zsc16.intel.com:10000/turnin/<ID>`

**Pre-turnin checks that run automatically:**
1. Turnin comment format validation
2. Softlinks pointer checks
3. File size validation (max 5MB)
4. Test portability rule checks
5. Merge conflict detection

**Common failure scenarios:**

| Issue | Symptom | Solution |
|-------|---------|----------|
| Bad comment format | "comment doesn't fufill the turnin comment tag" | Use proper format: `PROJ-MILESTONE-IP-TYPE: comment` |
| Missing $WORKAREA | Environment errors | Set `export WORKAREA=$PWD` |
| Wrong cth_psetup path | Command not found | Check README for correct path |
| File size too large | "File size > 5MB" check fails | Review large files, get waiver if needed |
| Merge conflicts | "merge failed" | Resolve conflicts first |

## Quick Reference

### Full Example Workflow

```bash
# 1. Set WORKAREA if not set
export WORKAREA=$PWD

# 2. Analyze what you're turning in
git --no-pager log -1
git --no-pager diff-tree --no-commit-id --name-only -r HEAD

# Example output analysis:
# Changed files:
#   verif/tests/boot/pch_reset_test.sv
#   verif/sequences/boot_sequence.sv
# Analysis: Test changes in boot chapter → VAL type, BOOT chapter

# 3. Read README for cth_psetup command
cat README

# 4. Construct appropriate comment based on analysis
# Pattern: TTLH-<milestone>-<IP/Chapter>-<Type>: description
# For this example: TTLH-V1P0-BOOT-VAL: <description>

# 5. Execute turnin with analyzed tags
/p/cth/pu_tu/prd/liteinfra/1.20/commonFlow/bin/cth_psetup -p pcth -read_only -skip_prompt -nowash -force -cmd 'turnin -c pcd -s ttl-h-main -comments "TTLH-V1P0-BOOT-VAL: boot reset sequence test updates"'

# 6. Monitor turnin
turnininfo <ID>
```

### Decision Tree for Tag Selection

```
1. Analyze changed files (git diff-tree)
   ├─ Mostly in verif/tests/, verif/sequences/
   │  └─ Type: VAL
   │     └─ Identify test chapter (BOOT, DFX, PWR, etc.)
   │
   ├─ Mostly in src/<ip>/, subsystems/<ip>/
   │  └─ Type: INT
   │     └─ Identify IP name(s) - single or multiple (IP1/IP2/IP3)
   │
   ├─ Mostly in cfg/, scripts/, Makefile, .gitignore
   │  └─ Type: ENV
   │     └─ Chapter: ENV or GK
   │
   ├─ Mostly in lint/, cdc/, *_waiver.txt
   │  └─ Type: SChk
   │     └─ Chapter: LINT, CDC, or SpyLP
   │
   └─ Mixed changes
      └─ Identify primary purpose
         └─ Tag based on main intent

2. Ask user for milestone if uncertain
   └─ Common: R0P5, R0P8, V1P0, ECO1, etc.

3. Construct comment: <PROJ>-<MILESTONE>-<CHAPTER>-<TYPE>: description
```

### Comment Format Cheatsheet

**Integration (INT):**
```
TTLH-R0P5-ENV-ENV: environment setup changes
TTLH-R0P5-BOOT-INT: boot flow integration
TTLH-ECO1-FIA-INT: FIA ECO1 drop with IP version
TTLH-R1P0-ROM-INT: PMC ROM version update
TTLH-Rpre0P5-CLK-INT: clock integration for startup
```

**Validation (VAL):**
```
TTLH-V1P0-BOOT-VAL: boot scenario test updates
TTLH-V1P0-DFX-VAL: DFX validation updates
TTLS-V1P0-USBx-VAL: USB validation test fixes
TTLH-V1P0-FPGA-VAL: FPGA backdoor enablement
```

**Environment/Tools (ENV):**
```
TTLH-R1P0-GK-ENV: gatekeeper config update
TTLH-R0P5-ENV-ENV: ACE/HDK script changes
```

**Static Checks (SChk):**
```
TTLH-R1P0-LINT-SChk: lintra waiver updates
TTLH-R0P8-CDC-SChk: CDC waiver for IP XYZ
TTLS-R1P0-SpyLP-SChk: SpyglassLP fixes
```

**Multi-DUT/Multi-IP:**
```
TTLH/S-R0P5-ENV-ENV: changes affecting both dies
TTLH-R0P5-FIA/USB/CLK-INT: integration for multiple IPs
```

## Additional Resources

- Turnin comment tagging: https://sharepoint.gar.ith.intel.com/sites/HWENG_CNP/FE1/CNP%20FrontEnd%20Wiki/Turnin%20Comment%20Tagging.aspx
- Project wiki: https://wiki.ith.intel.com/display/pch/TTLPCD+Project+Env


