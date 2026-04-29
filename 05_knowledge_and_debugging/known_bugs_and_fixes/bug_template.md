---
title: "Bug Report Template"
module: 05_knowledge_and_debugging
tags: [template, bug, report, standard]
---

# Bug Report Template

> Copy this template when creating a new bug file.
> Replace all `<placeholders>` with actual values.
> File naming: `BUG-NNN_short_description.md`

---

```yaml
---
bug_id: BUG-<NNN>
title: "<Short descriptive title>"
date_discovered: <YYYY-MM-DD>
status: <fixed | workaround | open | informational>
severity: <blocker | critical | non-critical | informational>
stage: "<build stage or test phase where error occurs>"
bundle: <bundle1068 | bundle1088 | bundle1106 | all>
category: <shebang | permissions | library | build-config | runtime | monitoring | infrastructure>
related_patterns: [<pattern_N>]
tags: [<tag1>, <tag2>, <tag3>]
---
```

## Symptom

<Exact error message text, copy-pasted from the log file.
Include the log file path where it was found.>

```
<paste error text here>
```

## Triggered By

```bash
<exact command that surfaced the error>
```

## Root Cause

<Technical explanation of WHY the error occurs.
Include the chain of events leading to the failure.>

## Fix / Solution

```bash
<Exact commands to run — must be copy-paste ready>
```

## Files Affected

- `<path/to/file1>` — <what was changed>
- `<path/to/file2>` — <what was changed>

## Verification

```bash
<commands to verify the fix worked>
```

## Notes

- <Additional context, caveats, prevention strategies>
- <Cross-references to related bugs>
- <Warnings about re-application after rebuilds>
