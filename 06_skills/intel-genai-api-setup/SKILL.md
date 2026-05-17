---
name: intel-genai-api-setup
description: >-
  Setup Intel GenAI API key for pcd-val-agents tools. Use when tools report
  "OPENAI_API_KEY not set", "API key not found", or when setting up formatr, loggr,
  bucketr, or other AI-powered tools.
  Triggers: OPENAI_API_KEY error, genai api key, setup api key, configure openai.
---

# Intel GenAI API Key Setup

## Problem

Many pcd-val-agents tools (formatr, loggr, bucketr, etc.) require the `OPENAI_API_KEY` environment variable to use AI-powered analysis features. Without it, you'll see errors like:

```
ERROR: OPENAI_API_KEY environment variable not set.
Please set it before running formatr:
  setenv OPENAI_API_KEY 'your-api-key-here'
```

## Solution: API Key Already Exists!

**Good news**: Your API key is likely already stored in `~/.openai_api_key`

### Quick Setup (One-Time per Shell Session)

**For tcsh (Intel default):**
```tcsh
setenv OPENAI_API_KEY `cat ~/.openai_api_key`
```

**For bash:**
```bash
export OPENAI_API_KEY=$(cat ~/.openai_api_key)
```

### Permanent Setup (Recommended)

Add to your shell profile so it's automatically loaded:

**For tcsh:**
```tcsh
# Add to ~/.cshrc or ~/.cshrc.$USER
if ( -f ~/.openai_api_key ) then
    setenv OPENAI_API_KEY `cat ~/.openai_api_key`
endif
```

**For bash:**
```bash
# Add to ~/.bashrc
if [ -f ~/.openai_api_key ]; then
    export OPENAI_API_KEY=$(cat ~/.openai_api_key)
fi
```

### Verification

Check if the key is loaded:
```bash
echo ${OPENAI_API_KEY}
# Should output: genai_xxxxx...
```

## If ~/.openai_api_key Doesn't Exist

1. **Get your API key** from: https://genai-proxy.intel.com/
2. **Save it to the file**:
   ```tcsh
   echo "genai_your_api_key_here" > ~/.openai_api_key
   chmod 600 ~/.openai_api_key  # Secure the file
   ```
3. **Load it** using the commands above

## Tools That Use This

The following pcd-val-agents tools require OPENAI_API_KEY:

- **formatr** - Test intent interpretation with `--interpret_intent`
- **loggr** - Log analysis and error summarization (if using AI features)
- **bucketr** - Intelligent failure bucketing with embeddings
- **repo_diff** - AI-powered code change summarization
- Any other tool using Intel GenAI proxy for LLM calls

## Security Note

The `~/.openai_api_key` file contains your personal Intel GenAI API key:
- Keep permissions restricted: `chmod 600 ~/.openai_api_key`
- Never commit this file to git
- Don't share the key in logs or screenshots

## Troubleshooting

### "OPENAI_API_KEY still not set after export"

**Cause**: You exported in one shell but are running the tool in a different shell/session

**Solution**: 
- Export in the same shell where you'll run the tool
- OR add to your profile (permanent solution)

### "API key file doesn't exist"

**Check common locations**:
```bash
ls -la ~/.openai_api_key
ls -la ~/.config/openai/api_key
```

If neither exists, create one using the instructions above.

### "Invalid API key" error from tools

**Cause**: Key format incorrect or expired

**Solution**:
1. Get a fresh key from https://genai-proxy.intel.com/
2. Update `~/.openai_api_key` with the new key
3. Reload: `setenv OPENAI_API_KEY \`cat ~/.openai_api_key\``

## Integration with Copilot Agents

When Copilot agents run pcd-val-agents tools, they should:

```bash
# Always check and load API key before running AI-powered tools
if [ -z "$OPENAI_API_KEY" ] && [ -f ~/.openai_api_key ]; then
    export OPENAI_API_KEY=$(cat ~/.openai_api_key)
fi

# Then run the tool
TOOLS_DIR="${PCD_VAL_AGENTS_TOOLS_DIR:-$HOME/.copilot/copilot_agent_tools}"
$PCD_VAL_AGENTS_TOOLS_DIR/formatr/.venv/bin/python $PCD_VAL_AGENTS_TOOLS_DIR/formatr/formatr.py --interpret_intent test.sv
```

## Related Skills

- **formatr-usage** - Uses this for test intent interpretation
- **loggr-usage** - May use this for AI-powered log analysis
- **bucketr-usage** - Uses this for failure bucketing with embeddings
