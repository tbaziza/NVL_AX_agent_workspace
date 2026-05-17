---
name: skill-auto-extractor
description: >-
  Autonomous skill extraction system that captures reusable knowledge from work
  sessions.
  Triggers: (1) /skill-auto-extractor command to review session learnings, (2) "save
  this as a skill" or "extract a skill from this", (3) "what did we learn?", (4) After
  any task involving non-obvious debugging, workarounds, or trial-and-error discovery.
  Creates new Copilot skills when valuable, reusable knowledge is identified.
---

# Skill Auto-Extractor

A continuous learning system that extracts reusable knowledge from work sessions and saves them as new skills.

## Purpose

When Copilot discovers non-obvious solutions through debugging, investigation, or trial-and-error, this skill captures that knowledge as a reusable skill for future sessions. Instead of re-discovering the same solutions, future sessions can leverage previously learned patterns.

## When This Skill Activates

### Automatic Activation (via Hook)

The UserPromptSubmit hook injects a reminder after each user prompt, prompting evaluation of whether extractable knowledge was produced. This achieves higher activation rates than semantic matching alone.

### Manual Activation

- Use `/skill-auto-extractor` command
- Say "save this as a skill" or "extract a skill from this"
- Ask "what did we learn?"

## Evaluation Protocol

After completing a task, evaluate:

1. **Did this require non-obvious investigation or debugging?**
   - Hours spent on obscure errors
   - Trial-and-error discovery
   - Workarounds for undocumented behavior

2. **Was the solution something that would help in future similar situations?**
   - Reusable patterns
   - Common pitfalls to avoid
   - Configuration gotchas

3. **Did I discover something not immediately obvious from documentation?**
   - Undocumented behavior
   - Environment-specific issues
   - Tool quirks

If YES to any question, proceed with skill extraction.

## Skill Extraction Process

### Step 1: Identify the Knowledge

Determine what was learned:
- **Problem**: What issue was encountered?
- **Investigation**: What steps were taken to diagnose?
- **Root Cause**: What was the actual cause?
- **Solution**: How was it resolved?
- **Prevention**: How to avoid in the future?

### Step 2: Determine Skill Format

Choose the appropriate skill structure:

```
skill-name/
├── SKILL.md          # Required: Instructions and trigger conditions
├── scripts/          # Optional: Executable code for deterministic tasks
├── references/       # Optional: Documentation to load as needed
└── assets/           # Optional: Templates, files for output
```

### Step 3: Write the Skill

Create SKILL.md with:

```yaml
---
name: descriptive-skill-name
description: >-
  Specific trigger conditions that describe WHEN to use this skill.
  Include error messages, symptoms, or scenarios that should activate it.
  Example: "Fix for 'ECONNREFUSED' errors when connecting to PostgreSQL
  in Docker containers on Intel corporate network."
---
```

**Description Quality is Critical**: The description determines when Copilot loads the skill. Be specific:
- BAD: "Helps with database problems"
- GOOD: "Fix for PrismaClientKnownRequestError P2024 (connection pool exhaustion) in serverless environments with cold starts"

### Step 4: Write Actionable Instructions

The skill body should contain:
1. **Problem Statement**: Clear description of the issue
2. **Symptoms**: How to recognize this problem
3. **Root Cause**: Why it happens
4. **Solution**: Step-by-step fix
5. **Verification**: How to confirm it's resolved
6. **Prevention**: How to avoid in the future

### Step 5: Save the Skill

Save to the appropriate location:

**For PCD Validation skills:**
```bash
# In the pcd-val-agents repo
skills/<skill-name>/SKILL.md
```

**For user-level skills:**
```bash
~/.copilot/skills/<skill-name>/SKILL.md
```

## Quality Gates

Only extract knowledge that:

1. **Required actual discovery** - Not just documentation lookups
2. **Has clear trigger conditions** - Specific scenarios when it applies
3. **Is verified to work** - Solution was actually tested
4. **Is genuinely reusable** - Will help with future similar problems

## Examples of Extractable Knowledge

### Good Candidates

- "PostgreSQL connection timeouts in Docker require setting `connect_timeout=10` in connection string when on VPN"
- "UVM test hangs during boot phase indicate missing `+BOOT_TIMEOUT=300` plusarg"
- "tcsh profile files on Intel network are at `~/.cshrc.$USER` not `~/.tcshrc`"

### Poor Candidates

- "How to write a for loop in Python" (documentation)
- "Fixed typo in variable name" (not reusable)
- "Added missing import" (trivial)

## Integration with Hooks

This skill works with the UserPromptSubmit hook that injects reminders:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 MANDATORY SKILL EVALUATION REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Reminder text about evaluation protocol]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The hook ensures consistent evaluation after every task.

## Skill Template

Use this template when creating new skills:

```markdown
---
name: problem-specific-name
description: >-
  Specific trigger: error message, symptom, or scenario.
  Environment context if relevant.
---

# Problem Name

## Symptoms

- Symptom 1
- Symptom 2

## Root Cause

Explanation of why this happens.

## Solution

1. Step 1
2. Step 2
3. Step 3

## Verification

How to confirm the fix worked.

## Prevention

How to avoid this in the future.
```
