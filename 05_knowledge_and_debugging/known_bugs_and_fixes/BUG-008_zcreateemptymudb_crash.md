---
bug_id: BUG-008
title: "zCreateEmptyMuDb crashes with assertion error"
date_discovered: 2026-03-29
status: open
severity: non-critical
stage: "MuDb recovery attempt"
bundle: bundle1068
category: build-config
related_patterns: []
tags: [zCreateEmptyMuDb, MuDb, assertion, PropertySchema, equis]
---

# BUG-008: zCreateEmptyMuDb crashes with assertion error

## Symptom
zCreateEmptyMuDb: PropertySchema.cc:25: MUDB::PropertySchema::PropertySchema(const MUDB::Properties&, MUDB::Properties::SchemaMode): Assertion `v != nullptr' failed.

## Triggered By
```bash
export LD_LIBRARY_PATH="$ZEBU_ROOT/lib:$ZEBU_ROOT/tcl:$LD_LIBRARY_PATH"
export TCL_LIBRARY="$ZEBU_ROOT/tcl/tcl8.6"
$ZEBU_ROOT/bin/zCreateEmptyMuDb --platform SEM --top tb_top_config --zebu-work /tmp/test_dir
```

## Root Cause
`zCreateEmptyMuDb` crashes during property schema initialization because it cannot
find the design's property schema (needed to create a properly-typed MuDb). It crashes BEFORE
creating the `equis/info` file but AFTER creating `version`, `properties`, `crcs`, `upf`.
The crash does NOT produce a valid MuDb — it is incomplete and non-functional.

## Fix / Solution
No simple workaround. The tool needs a valid property schema from the design.
The correct flow is: `FpgaPostProc` (creates MuDb from bitstreams) → `zMuDbMerge` (merges per-part data).
Both depend on FPGA bitstreams being present.

## Files Affected
None (temporary test directories only)

## Verification
N/A — tool bug or missing design context; not blocking if fe_be is re-run.

## Notes
Status: open (tool bug or missing design context; not blocking if fe_be is re-run)
