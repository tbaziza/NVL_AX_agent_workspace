---
title: "Documentation Rules &amp; Standards"
module: 05_knowledge_and_debugging
tags: [documentation, standards, rules, writing, bugs]
---

# Documentation Rules &amp; Standards

## Core Principle
> **Documentation is a byproduct of work, not a separate task.**
> Every fix you apply generates a document. Every command you discover gets recorded.
> The goal: the NEXT AI session should be able to apply any fix in under 60 seconds.

## Bug Documentation

### When to Create a Bug File
- Any new error you encounter and solve
- Any workaround you apply (even temporary)
- Any informational observation that prevents future mistakes (e.g., BUG-030)
- Any infrastructure issue that blocks work (e.g., BUG-034)

### File Naming Convention
```
BUG-NNN_short_snake_case_description.md
```
Examples:
- `BUG-035_new_shebang_error.md`
- `BUG-036_fm_board_timeout.md`

### Required Sections
Every bug file MUST use the template from `bug_template.md`:
1. **YAML Frontmatter** — metadata for RAG (bug_id, status, severity, category, tags)
2. **Symptom** — exact error message text (copy-paste from logs)
3. **Root Cause** — why it happens (technical explanation)
4. **Fix / Solution** — exact commands to run (copy-paste ready)
5. **Files Affected** — list of files changed
6. **Verification** — how to confirm the fix worked
7. **Notes** — additional context, caveats, prevention

## Command Documentation

### When to Add a Command
- Any shell command you discover that solves a problem
- Any command the user teaches you
- Any monitoring/diagnostic command that proves useful

### Format (in `commands_reference.md`)
| Command | What It Does | When To Use |

## Pattern Documentation

### When to Update `common_patterns.md`
- New bug matches an existing pattern → add bug reference
- New bug reveals a new category → create new Pattern entry
- Existing pattern needs updated advice → edit the pattern

### Pattern Format
```
## Pattern N: Short Name
- **Symptom**: What you see
- **Cause**: Why it happens
- **General Fix**: How to fix it
- **Related Bugs**: BUG-NNN, BUG-MMM
```

## Quality Checks
- [ ] Every bug file has YAML frontmatter
- [ ] Error messages are exact (copy-pasted, not paraphrased)
- [ ] Fix commands are copy-paste ready (absolute paths where needed)
- [ ] Verification step is included
- [ ] Related patterns are cross-referenced
