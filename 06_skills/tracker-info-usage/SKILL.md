---
name: tracker-info-usage
description: >-
  Discover and analyze validation tracker files for debugging. Use tracker_info to find
  tracker files for PMC boot flows, GPIO signals, register access, sideband traffic,
  PCIe transactions. Use this skill when you need to find where tracker_info is located
  and how to run it.
  Triggers: tracker file, find tracker, IP status, boot flow tracker, sideband tracker,
  which tracker, analyze tracker, PMC tracker, GPIO tracker, PCIe tracker.
---

# tracker_info Tool Usage Guide

## When to Use tracker_info

Use `tracker_info` when you need to:
- **Find the right tracker** for a specific debug scenario (boot hang, GPIO issue, register problem, etc.)
- **Understand what trackers are available** in a test results directory
- **Extract cycle-specific data** from a tracker file around a timestamp
- **Search for a specific cycle** across all available trackers
- **Avoid manually searching** through 400+ files in a results directory

## Prerequisites

1. **Required Environment Variable**:
   $OPENAI_API_KEY: Get your key from: https://genai-proxy.intel.com/

2. **Tool Execution:**

   **CRITICAL: Use the pre-installed virtual environment!**
   - **NEVER run `pip install` - dependencies are pre-configured**
   - **ALWAYS use `.venv/bin/python` to run the tool**

   ```bash
   $PCD_VAL_AGENTS_TOOLS_DIR/tracker_info/.venv/bin/python $PCD_VAL_AGENTS_TOOLS_DIR/tracker_info/tracker_info.py [options]
   ```

3. **Required Argument:**
   - `--results_dir` is **mandatory** for all operations
   - Must point to a test results directory containing tracker files

## What are Tracker Files?

Tracker files capture different aspects of DUT behavior during test execution:
- **Register access** (RAL model)
- **Memory allocation** (system manager)
- **PMC firmware** boot flows and power management
- **GPIO signals** and transitions
- **Sideband traffic** between IPs
- **PCIe transactions** per controller/port
- **North complex interface** (CPU/GFX/memory)
- **Configuration** (fuses, straps)

**Key characteristics:**
- 400+ files per test result
- All gzipped (.gz extension)
- Different formats (no standard schema)
- Sizes: 50KB - 600KB compressed, 500KB - 47MB uncompressed

## Common Usage Patterns

**Important:** All commands require `--results_dir <path>` to specify the test results directory.

### 1. **Find Tracker for Debug Scenario**
When you encounter a failure and don't know which tracker to examine:

```bash
cd $PCD_VAL_AGENTS_TOOLS_DIR/tracker_info
./tracker_info.py --query "PMC boot hang" --results_dir /path/to/test/results
```

**Output:**
```
======================================================================
RECOMMENDED TRACKERS
======================================================================
Query: PMC boot hang

1. PMC Firmware Trace Log - 99% match
   File: pmc_fw_ahb_trace_mod.log.gz
   Why: Directly targets PMC firmware boot flow, explicitly called 
        out for boot hang and error debugging
   Use for:
      - PMC firmware flow debugging
      - Boot flow stage analysis
      - Boot hang and error debugging

2. PMSYNC/PMDOWN Interface Tracker - 85% match
   File: PMC_PM_DOWN_TRK.out.gz
   Why: Monitors PMC–Punit communication; useful to see if PMC boot 
        progress is blocked by power-management handshakes
```

**The tool:**
- Uses AI to understand your debug intent
- Matches against 12 tracker definitions
- Explains *why* each tracker is relevant
- Shows confidence scores
- Provides full path to actual files

### 2. **AI Agent Integration - Get JSON**
For automated triage or agent consumption:

```bash
./tracker_info.py --query "GPIO signal issue" --results_dir /path/to/results --api
```

**JSON Output:**
```json
{
  "operation": "query",
  "query": "GPIO signal issue",
  "results_dir": "/path/to/results",
  "recommended_trackers": [
    {
      "name": "GPIO Signal Tracker",
      "filename": "GPIO_SIG_TRK_3.out.gz",
      "full_path": "/path/to/results/GPIO_SIG_TRK_3.out.gz",
      "confidence": 1.0,
      "reason": "Explicitly targets GPIO behavior...",
      "metadata": {
        "use_for": ["GPIO signal state tracking", ...],
        "keywords": ["GPIO", "signal", "GPCOM", ...]
      }
    }
  ]
}
```

### 3. **List All Available Trackers**
See what trackers exist in a results directory:

```bash
./tracker_info.py --list --results_dir /path/to/results
```

**Output:**
```
Found 12 tracker types in directory:

1. RAL Register Model
   Files: RegModel.out.gz
   Use for: High-level register access flow analysis

2. PMC Firmware Trace Log
   Files: pmc_fw_ahb_trace_mod.log.gz
   Use for: PMC firmware flow debugging, Boot flow stage analysis

3. GPIO Signal Tracker
   Files: GPIO_SIG_TRK_0.out.gz, GPIO_SIG_TRK_3.out.gz, ...
   Use for: GPIO signal state tracking
```

### 4. **Extract Data Around a Timestamp**
Once you know which tracker, extract cycle-specific context:

```bash
./tracker_info.py --extract pmc_fw_ahb_trace_mod.log.gz --timestamp 12345 --context 20 --results_dir /path/to/results
```

**Output:** 20 lines before and after timestamp 12345 from the tracker

### 5. **Search for Specific Cycle Across All Trackers**
Find where a cycle appears in multiple trackers:

```bash
./tracker_info.py --find_cycle timestamp=12345 --results_dir /path/to/results
```

**Use case:** When you see a failure at a specific timestamp and want to know what was happening across all interfaces

### 6. **Query with JSON for Automation**
Combine query and extraction in agent workflow:

```bash
# Step 1: Find tracker
TRACKER=$(./tracker_info.py --query "register timeout" --results_dir $RESULTS --api | jq -r '.recommended_trackers[0].filename')

# Step 2: Extract cycle context
./tracker_info.py --extract $TRACKER --timestamp 98765 --results_dir $RESULTS --api
```

## Debugging Workflow with tracker_info

### Standard Debug Flow:

**Step 1: Identify Debug Scenario**
From test failure logs, identify what failed:
- Boot hang → Query "PMC boot hang" or "boot flow"
- GPIO issue → Query "GPIO signal" or "GPIO toggle"
- Register timeout → Query "register access" or "RAL"
- Memory problem → Query "memory allocation" or "address space"
- PCIe error → Query "PCIe transaction" or "PCIe link"

**Step 2: Find Relevant Tracker**
```bash
./tracker_info.py --query "your debug scenario" --results_dir $RESULTS
```

**Step 3: Extract Cycle Context**
```bash
./tracker_info.py --extract <tracker_file> --timestamp <cycle> --results_dir $RESULTS
```

**Step 4: Analyze with Other Tools**
- Use `loggr` to correlate with test log
- Use `reg_info` to understand registers seen in tracker
- Use `find_passing` to compare with passing run

### Example: Debugging PMC Boot Hang

```bash
# Test fails with: "PMC boot timeout at timestamp 45678"

# Step 1: Find PMC tracker
./tracker_info.py --query "PMC boot hang" --results_dir /path/to/failing/test
# → Returns: pmc_fw_ahb_trace_mod.log.gz

# Step 2: Extract cycle context
./tracker_info.py --extract pmc_fw_ahb_trace_mod.log.gz --timestamp 45678 --context 30 --results_dir /path/to/failing/test
# → Shows PMC boot flow 30 lines before/after failure

# Step 3: Check if PMC-Punit communication issue
./tracker_info.py --query "PMC Punit" --results_dir /path/to/failing/test
# → Returns: PMC_PM_DOWN_TRK.out.gz

# Step 4: Cross-reference
./tracker_info.py --extract PMC_PM_DOWN_TRK.out.gz --timestamp 45678 --context 20 --results_dir /path/to/failing/test
# → Shows PMSYNC/PMDOWN activity at failure time
```

## Available Tracker Types

### 1. **RAL Register Model** (`RegModel.out`)
- **Use for:** High-level register access flow
- **Query terms:** "register access", "RAL", "read write"
- **Contains:** Register operation sequence, timing, parent sequences

### 2. **System Manager Log** (`sm.out`)
- **Use for:** Memory and address space allocation
- **Query terms:** "memory allocation", "MMIO", "address space"
- **Contains:** Region assignments, SRAM, MSI addresses

### 3. **North Complex Interface** (`IOSFP_NORTH_INTF_*.trk`)
- **Use for:** CPU/GFX/memory communication
- **Query terms:** "north complex", "CPU access", "memory access", "MMIO"
- **Contains:** MemRd/MemWr cycles, MSI messages, PCIe parameters

### 4. **IOSF-Sideband Interface** (`chs_sbnode_*.log`)
- **Use for:** IP sideband traffic
- **Query terms:** "sideband", "IOSF", "IP traffic"
- **Contains:** Messages to/from IPs, opcodes, packet contents

### 5. **PMC Firmware Trace** (`pmc_fw_ahb_trace_mod.log`)
- **Use for:** Boot hangs, power management issues
- **Query terms:** "PMC boot", "boot hang", "power management"
- **Contains:** Boot flow stages, PMC activities, timestamps with comments

### 6. **PMC PM Down Tracker** (`PMC_PM_DOWN_TRK.out`)
- **Use for:** PMC-Punit communication
- **Query terms:** "PMSYNC", "PMDOWN", "PMC Punit"
- **Contains:** Upstream/downstream cycles, power handshaking

### 7. **GPIO Signal Tracker** (`GPIO_SIG_TRK_*.out`)
- **Use for:** GPIO signal transitions
- **Query terms:** "GPIO", "signal toggle", "GPCOM"
- **Contains:** Signal names, previous/current values, timestamps

### 8. **Fuse Configuration** (`fuse_print.log`, `fuseosse_print.log`)
- **Use for:** Hardware configuration verification
- **Query terms:** "fuse", "configuration", "hardware settings"
- **Contains:** Fuse names, values, addresses

### 9. **Soft Strap Configuration** (`strap_print.log`)
- **Use for:** Platform configuration
- **Query terms:** "strap", "soft strap", "platform config"
- **Contains:** Strap names, sizes, values

### 10. **PCIe Transaction Tracker** (`PCIe*_*_trk.out`)
- **Use for:** PCIe link/device issues
- **Query terms:** "PCIe", "PCI Express", "device transaction"
- **Contains:** Per-controller/port transactions, TLP details, credits

### **JEM PP Logs** (`jem_pp_logs/*.log`)
- **Use for:** When other trackers don't have info
- **Query terms:** "emulation", "jem", "alternative tracker"
- **Contains:** Various interface data in emulation-friendly formats

## Integration with Other Tools

### With loggr (Test Log Analysis)
```bash
# Find failure timestamp in test log
loggr /path/to/test.log | grep FATAL
# → "FATAL at 12345: Boot timeout"

# Find relevant tracker
tracker_info.py --query "boot timeout" --results_dir /path/to/results

# Extract tracker context at that timestamp
tracker_info.py --extract pmc_fw_ahb_trace_mod.log.gz --timestamp 12345 --results_dir /path/to/results
```

### With reg_info (Register Details)
```bash
# Tracker shows register access: GEN_PMCON_A
# Look up register meaning
reg_info.py --register GEN_PMCON_A

# Or search for related registers
reg_info.py --search "power management after AC"
```

### With find_passing (Passing Reference)
```bash
# Find passing run
find_passing.py --test test_name

# Compare tracker from passing vs failing
tracker_info.py --extract pmc_fw_ahb_trace_mod.log.gz --timestamp 12345 --results_dir /path/to/passing
tracker_info.py --extract pmc_fw_ahb_trace_mod.log.gz --timestamp 12345 --results_dir /path/to/failing

# Diff the outputs
```

## Query Tips

### Be Specific But Flexible
- ✅ Good: "PMC boot hang", "GPIO toggle", "register timeout"
- ❌ Too vague: "error", "failure", "problem"

### Use Domain Terms
- ✅ "sideband traffic", "PMSYNC", "AHB transaction"
- ❌ "communication issue", "data transfer"

### Describe the Interface/IP
- ✅ "PMC power management", "PCIe controller 0"
- ❌ "power", "controller"

### Multiple Queries for Complex Issues
If first query doesn't give expected tracker, try related terms:
```bash
./tracker_info.py --query "boot hang" --results_dir $RESULTS
./tracker_info.py --query "PMC firmware" --results_dir $RESULTS
./tracker_info.py --query "power management" --results_dir $RESULTS
```

## Common Scenarios

### Scenario 1: Test Fails with "Boot Timeout"
```bash
# Query for boot-related tracker
./tracker_info.py --query "boot timeout" --results_dir $RESULTS

# Likely returns: pmc_fw_ahb_trace_mod.log.gz
# Extract around failure time
./tracker_info.py --extract pmc_fw_ahb_trace_mod.log.gz --timestamp <failure_time> --results_dir $RESULTS
```

### Scenario 2: GPIO Signal Not Toggling
```bash
# Find GPIO tracker
./tracker_info.py --query "GPIO signal" --results_dir $RESULTS

# List all GPIO trackers (multiple GPCOMs)
./tracker_info.py --list --results_dir $RESULTS | grep GPIO

# Extract from specific GPCOM
./tracker_info.py --extract GPIO_SIG_TRK_3.out.gz --timestamp <cycle> --results_dir $RESULTS
```

### Scenario 3: Register Access Hang
```bash
# Find register tracker
./tracker_info.py --query "register access timeout" --results_dir $RESULTS

# Extract RAL model activity
./tracker_info.py --extract RegModel.out.gz --timestamp <hang_cycle> --results_dir $RESULTS

# Cross-check with sideband
./tracker_info.py --query "sideband register" --results_dir $RESULTS
```

### Scenario 4: Memory Allocation Conflict
```bash
# Find memory tracker
./tracker_info.py --query "memory allocation" --results_dir $RESULTS

# List system manager log
./tracker_info.py --extract sm.out.gz --results_dir $RESULTS
```

### Scenario 5: PCIe Device Not Enumerating
```bash
# Find PCIe tracker
./tracker_info.py --query "PCIe enumeration" --results_dir $RESULTS

# Extract PCIe controller activity
./tracker_info.py --extract PCIe0_0_trk.out.gz --timestamp <enum_time> --results_dir $RESULTS
```

## Error Handling

### "No trackers found matching query"
**Possible causes:**
- Query too specific or uses non-domain terms
- Tracker doesn't exist in this test results directory
- Typo in results directory path

**Solution:** Try broader query or use `--list` to see available trackers

### "Results directory not found"
**Solution:** Verify path to test results directory exists

### "Timestamp not found in tracker"
**Possible causes:**
- Timestamp outside tracker's range
- Tracker doesn't record that cycle
- Wrong tracker file

**Solution:** Use `--find_cycle` to search across all trackers

## Advanced Usage

### Custom Context Window
```bash
# Default is 10 lines before/after
./tracker_info.py --extract <file> --timestamp 12345 --context 50 --results_dir $RESULTS
```

### JSON for Scripting
```bash
# Get tracker filename programmatically
TRACKER=$(./tracker_info.py --query "PMC" --results_dir $RESULTS --api | jq -r '.recommended_trackers[0].filename')
echo "Using tracker: $TRACKER"
```

### Batch Analysis
```bash
# Analyze multiple timestamps
for ts in 1000 2000 3000; do
  ./tracker_info.py --extract pmc_fw_ahb_trace_mod.log.gz --timestamp $ts --results_dir $RESULTS
done
```

## Tips and Best Practices

1. **Start with --query** to find the right tracker before extracting
2. **Use --list** when unfamiliar with a test's results structure
3. **Cross-reference multiple trackers** for complex issues (e.g., PMC + PMSYNC)
4. **Use --api for automation** in agent workflows
5. **Check confidence scores** - lower confidence may mean query needs refinement
6. **Read the "Why"** explanation to understand tracker relevance
7. **Combine with loggr** to correlate tracker data with test log events


## Getting Help

For full command-line options:
```bash
./tracker_info.py --help
```

## Additional Resources

For complete documentation of all tracker_info capabilities, advanced options, output formats, and troubleshooting guidance, see:

- **TOOL_SPEC.md**: `$PCD_VAL_AGENTS_TOOLS_DIR/tracker_info/TOOL_SPEC.md` - Comprehensive tool specification with all options and use cases
- **README.md**: `$PCD_VAL_AGENTS_TOOLS_DIR/tracker_info/README.md` - Quick start guide and overview

Read these files when users need details beyond the common commands listed above.
