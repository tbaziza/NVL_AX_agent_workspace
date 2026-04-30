# NVL-AX Compilation Agent

An AI agent that automates the compile → test → debug → fix cycle for NVL-AX ZeBu ZSE5 emulation models.

## Quick Start

```bash
cd /nfs/site/disks/ive_sle_zsc11_tbaziza/models/integrate_bundle1106
copilot
```

That's it. The agent loads automatically. Start with:

```
You: compile the model
You: run DOA tests
You: this test failed, debug it
```

## Run From Any Directory

Add this line to your `~/.bashrc`:

```bash
export COPILOT_CUSTOM_INSTRUCTIONS_DIRS="/nfs/site/disks/ive_sle_zsc11_tbaziza/models/integrate_bundle1106/.github/instructions"
```

Then reload and run from anywhere:

```bash
source ~/.bashrc
copilot
```

## Select the Agent Persona

Inside Copilot CLI:

```
/agent nvlax-compiler
```

## Verify It's Working

Inside Copilot CLI:

```
/instructions
```

You should see 4 loaded files: `nvlax-agent`, `nvlax-build`, `nvlax-testing`, `nvlax-debug`.

## What It Does

```
Step 1: COMPILE    → runs grdlbuild → checks 6 pass criteria
Step 2: POST-BUILD → runs post_zcui + fix_zse5_libs.sh
Step 3: DOA TEST   → runs simregress → checks 5 pass criteria
Step 4: IF FAIL    → detects phase → searches 57 known bugs → suggests fix
```

## Knowledge Base Structure

```
00_index.md                          ← Start here
01_agent_core/                       ← Identity, safety rules, AI guidelines
02_execution/                        ← Build commands, environment setup
03_testing_and_validation/           ← DOA tests, emulator setup, quality gates
04_monitoring/                       ← Metrics, alert thresholds
05_knowledge_and_debugging/          ← Debug workflow, 57 bug files, symptom rules
   known_bugs_and_fixes/             ← BUG-001 to BUG-057
   run_phase_detection_nvlax.sh      ← Automated bug matcher
   symptom_rules.txt                 ← Keyword expansion rules
copilot_cli_agent/                   ← Agent instruction files for Copilot CLI
```

## What You Should Know

- The agent knows **57 documented bugs** and will match your failure against them
- It will **never** use the showstopper queue or the `-local` flag
- It will **never** resubmit a test that's still running
- It always checks ALL logbook stages — emurun PASS does not mean overall PASS
- It will always ask you before committing to git
