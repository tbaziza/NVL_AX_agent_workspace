---
name: intel-wiki-pat-setup
description: >-
  Step-by-step guide for generating an Intel Wiki (Confluence) Personal Access
  Token (PAT) and storing it on the local machine so tools like wiki_cli.py /
  intel-wiki-cli can authenticate. Use when the user needs to create a wiki
  PAT for the first time, when wiki_cli.py reports "NOT CONFIGURED", or when
  the user's existing token is invalid/expired.
  Triggers: intel wiki token, generate PAT, wiki PAT, confluence PAT, create
  wiki token, ~/.intel_wiki_pat, CONFLUENCE_PAT, wiki auth, wiki not
  configured, regenerate token, intel-wiki-cli setup.
---

# Intel Wiki Personal Access Token (PAT) — Setup Guide

This skill walks the user through generating a Personal Access Token (PAT) for
**wiki.ith.intel.com** (Atlassian Confluence) and saving it locally so tools
such as `wiki_cli.py` (skill: `intel-wiki-cli`) can authenticate as the user.

**Authoritative reference (must be kept in sync):**
[How to Generate Intel Wiki Personal Access Token](https://wiki.ith.intel.com/spaces/iMTA/pages/3943869530/How+to+Generate+Intel+Wiki+Personal+Access+Token)

## Why a PAT?

The Intel Wiki API does not accept your AD password. A PAT is a long-lived
opaque string the wiki issues on your behalf. Tools and scripts present this
token in an `Authorization: Bearer <PAT>` HTTP header instead of using your
SSO password — so credentials never leak into automation.

A PAT inherits **your** wiki permissions. It can read pages you can read,
edit pages you can edit, etc. **Treat it like a password — never commit it
to git, paste it in chat logs, or share it.**

## When to run this skill

- First time setup on a new host
- `wiki_cli.py check-setup` returns `NOT CONFIGURED`
- API calls return `401 Unauthorized` (token expired/revoked)
- User wants to rotate their token

## Step 1 — Generate the token (browser, ~1 minute)

1. Sign in to **<https://wiki.ith.intel.com>** with your Intel SSO if you
   are not already authenticated.
2. Click your **profile picture / avatar** in the **top-right corner** of
   any wiki page.
3. From the dropdown choose **Settings**.
4. In the left sidebar of the Settings page, scroll to the **lower left**
   and click **Personal Access Tokens**.
   - Direct link:
     <https://wiki.ith.intel.com/plugins/personalaccesstokens/usertokens.action>
5. Click **Create token**.
6. Fill the form:
   - **Token name:** anything memorable — purely a label for you (e.g.
     `copilot-cli`, `sle-emulation-agent`, `<user>-cli-<host>`). Confluence
     does not validate it.
   - **Automatic expiry:** **UNTICK** this box (per the upstream wiki
     instructions). If you leave it ticked the token will expire in 90 days
     and tools will start returning 401s.
7. Click **Create**.
8. **Copy the token string immediately.** It is shown only once — there is
   no way to retrieve it later. If you lose it you must generate a new one.

> Note: the token string looks like `MDg2NDA4...` — a random Base64-ish
> blob ~40+ characters long. It is **not** the same as the token name.

## Step 2 — Save the token on the host

Two supported ways, in order of preference:

### Option A — File at `~/.intel_wiki_pat` (recommended, persistent)

```bash
echo "PASTE_TOKEN_STRING_HERE" > ~/.intel_wiki_pat
chmod 600 ~/.intel_wiki_pat
```

This is the default location `wiki_cli.py` looks for. It persists across
shells and reboots.

### Option B — Environment variable `CONFLUENCE_PAT` (ephemeral)

```bash
export CONFLUENCE_PAT="PASTE_TOKEN_STRING_HERE"
```

Lives only in the current shell. Useful for one-off runs or shared boxes.
For a permanent export add the line to `~/.bashrc` / `~/.cshrc`, **but**
embedding secrets in a dotfile is less safe than the `chmod 600` file
above.

## Step 3 — Verify

```bash
~/.copilot/skills/intel-wiki-cli/wiki_cli.py check-setup
```

Expected output:

```
OK: PAT configured via /nfs/site/home/<user>/.intel_wiki_pat
```

(or `via CONFLUENCE_PAT environment variable` for Option B).

Then do a real API round-trip:

```bash
~/.copilot/skills/intel-wiki-cli/wiki_cli.py search -q "test" | head -20
```

If you see JSON page results, you are done. If you see `401 Unauthorized`
the token string was mistyped or already revoked — repeat Step 1.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `NOT CONFIGURED: PAT is not set up` | File missing / env var unset | Run Step 2 |
| `401 Unauthorized` | Token expired, revoked, or mistyped | Regenerate (Step 1) |
| `403 Forbidden` on a specific page | Your account lacks permission to that wiki space | Ask the space admin — PAT inherits your access |
| Token vanished from `~/.intel_wiki_pat` | File overwritten/cleaned | Regenerate (the original cannot be recovered) |
| Works on host A, fails on host B | PAT file was only on host A | Copy it (`scp -p ~/.intel_wiki_pat hostB:`) or regenerate on host B |

## Security checklist

- `chmod 600 ~/.intel_wiki_pat` — owner-only
- Never `git add ~/.intel_wiki_pat` or paste it into PRs / chat / Confluence
- Rotate the token if you suspect leakage: revoke at the same URL where you
  created it, then run this skill again
- Tokens without auto-expiry never rotate on their own — set a calendar
  reminder if your team requires periodic rotation

## Related skills

- **intel-wiki-cli** — uses the PAT this skill installs (`wiki_cli.py`
  search / get / create / update / comment).
- **intel-genai-api-setup** — analogous pattern (`~/.openai_api_key`) for
  the Intel GenAI proxy.
