---
name: intel-wiki-cli
description: >-
  Search and interact with Intel Wiki (Confluence) pages. Use this skill when you need
  to search for documentation on Intel Wiki, get page content by ID or title, create or
  update wiki pages, add comments, or navigate page hierarchies.
  Triggers: intel wiki, confluence, wiki search, wiki page, documentation search, find
  wiki, get wiki page, create wiki page, wiki.ith.intel.com.
---

# Intel Wiki CLI Tool Usage Guide

## Overview

The `wiki_cli.py` tool provides command-line access to Intel Wiki (Confluence) at wiki.ith.intel.com. It allows you to search, read, create, and update wiki pages programmatically.

## IMPORTANT: Check PAT Setup First

**Before using any wiki commands, ALWAYS run `check-setup` first:**

```bash
TOOL_PATH="${PCD_VAL_AGENTS_DIR:-$HOME/.copilot/iscp.pcd-val-agents}/skills/intel-wiki-cli/wiki_cli.py"
$TOOL_PATH check-setup
```

- If output starts with `OK:` - PAT is configured, proceed with commands
- If output starts with `NOT CONFIGURED:` - guide the user through the setup below

## First Time Setup (REQUIRED if PAT not configured)

**IMPORTANT:** Before using this tool, you MUST set up your Confluence Personal Access Token (PAT).

### Step 1: Generate your PAT

1. Visit: https://wiki.ith.intel.com/plugins/personalaccesstokens/usertokens.action
2. Click "Create token"
3. Give it a name (e.g., "CLI Access")
4. Copy the generated token (you won't see it again!)

### Step 2: Save your PAT

Save your PAT to `~/.intel_wiki_pat`:

```bash
echo "YOUR_PAT_TOKEN_HERE" > ~/.intel_wiki_pat
chmod 600 ~/.intel_wiki_pat
```

**Alternative:** Set the `CONFLUENCE_PAT` environment variable instead:
```bash
export CONFLUENCE_PAT="YOUR_PAT_TOKEN_HERE"
```

### Step 3: Verify setup

```bash
# Check if PAT file exists and has correct permissions
ls -la ~/.intel_wiki_pat

# Test the connection
./wiki_cli.py search "test"
```

If you see JSON results, you're all set!

## Tool Location

- Primary: `$PCD_VAL_AGENTS_DIR/skills/intel-wiki-cli/wiki_cli.py`
- Fallback: `~/.copilot/iscp.pcd-val-agents/skills/intel-wiki-cli/wiki_cli.py`

## Python Requirements

- Python 3.6+ with `requests` library (standard on most Intel systems)
- Uses `/usr/bin/python3` which has required dependencies

## Common Usage Patterns

### 1. Search for Content

Search wiki by text (searches both title and body):

```bash
./wiki_cli.py search "PCH boot sequence"
./wiki_cli.py search "PMC firmware debug"
```

### 2. Search with CQL (Confluence Query Language)

For advanced searches using CQL:

```bash
./wiki_cli.py search-pages -q 'space=fvcommon AND title~"boot"' -l 20
./wiki_cli.py search-pages -q 'creator=currentUser() AND created>now("-7d")'
```

### 3. Get Page by ID

When you have a page ID (from search results or URLs):

```bash
./wiki_cli.py get -i 2135216104
```

### 4. Get Page by Title

Find a page by its exact title:

```bash
./wiki_cli.py get -t "PCH Boot Sequence and Commands"
```

### 5. Get Child Pages

List all child pages under a parent:

```bash
./wiki_cli.py children -i 2135216104
```

Prefer using jq at /usr/intel/bin/jq for JSON parsing to avoid broken pipe issues:

```bash
/usr/intel/bin/jq -r '.results[].title'
```

### 6. Get Page Comments

Read comments on a page:

```bash
./wiki_cli.py comments -i 2135216104
```

### 7. Create a New Page

Create a page in a specific space:

```bash
./wiki_cli.py create -s MYSPACE -t "New Page Title" -b "<p>Page content in HTML</p>"

# With a parent page
./wiki_cli.py create -s MYSPACE -t "Child Page" -b "<p>Content</p>" -p 12345678
```

### 8. Create a Draft Page

Create a draft (unpublished) page:

```bash
./wiki_cli.py create-draft -s MYSPACE -t "Draft Title" -b "<p>Draft content</p>"
```

### 9. Update an Existing Page

Update page content (automatically handles versioning):

```bash
./wiki_cli.py update -i 12345678 -s MYSPACE -t "Updated Title" -b "<p>New content</p>"
```

### 10. Move a Page

Move a page to a new parent:

```bash
./wiki_cli.py move -i 12345678 -s MYSPACE -t "Page Title" -p 87654321
```

### 11. Add a Comment

Add a comment to a page:

```bash
./wiki_cli.py add-comment -i 12345678 -c "<p>This is my comment</p>"
```

## Output Format

All commands return JSON output, which can be piped to `jq` for processing:

```bash
# Get just the page titles from search results
./wiki_cli.py search "boot" | jq '.results[].title'

# Get page body content
./wiki_cli.py get -i 12345678 | jq '.body.storage.value'

# Pretty print with limited depth
./wiki_cli.py search "PMC" | jq -r '.results[:5] | .[].title'
```

## Common CQL Queries

```bash
# Pages in a specific space
./wiki_cli.py search-pages -q 'space=fvcommon'

# Pages modified recently
./wiki_cli.py search-pages -q 'lastModified>now("-7d")'

# Pages by a specific user
./wiki_cli.py search-pages -q 'creator="username"'

# Pages with specific label
./wiki_cli.py search-pages -q 'label="validation"'

# Combine conditions
./wiki_cli.py search-pages -q 'space=fvcommon AND title~"debug" AND lastModified>now("-30d")'
```

## Tips and Best Practices

1. **Start with text search** for general queries, use CQL for precise filtering
2. **Use `jq`** to extract specific fields from JSON output
3. **Page IDs** are found in search results under `content.id` or in page URLs
4. **HTML content** - Page bodies use Confluence storage format (HTML-like)
5. **Proxy bypass** - The tool automatically bypasses Intel proxy for internal wiki access

## Error Handling

Common errors and solutions:

- **403 Access Denied**: Check your PAT is valid and not expired
- **404 Not Found**: Verify page ID or title exists
- **Connection Error**: Ensure you're on Intel network (or VPN)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CONFLUENCE_PAT` | Personal Access Token | Read from `~/.intel_wiki_pat` |
| `CONFLUENCE_BASE_URL` | API base URL | `https://wiki.ith.intel.com/rest/api` |

## Getting Help

```bash
./wiki_cli.py --help
./wiki_cli.py search --help
./wiki_cli.py get --help
```
