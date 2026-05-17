---
name: sle-folsom-path-check
description: >-
  Verify that a project / model / workarea path is accessible from the
  Folsom (FM) site. Useful before sharing a path with a Folsom-based
  teammate, or before submitting a cross-site job. The skill classifies
  the path by its NFS prefix (site-local vs multi-site replicated), and
  — if a Folsom probe host is configured — actually SSHes there and
  runs `test -e` on the path. Returns a clear ACCESSIBLE /
  NOT_ACCESSIBLE / UNCERTAIN verdict with reasoning.
  Triggers: folsom accessible, fm site, cross-site path, accessible from
  Folsom, can Folsom see this, fm reachability, can FM see, multi-site
  path, /nfs/site path check.
---

# SLE Folsom Path Check

## Why this exists

The SLE agent runs on zsc11 (Santa Clara). When you ask a Folsom-based
colleague to look at your model, or when a cross-site job needs to
read your workarea, the path you give them must actually be visible
under the same name on the Folsom side.

Intel NFS uses multi-site replication for some disk classes, but not
all — and even replicated disks can lag or be excluded from FM. This
skill answers the question **"can a Folsom host see this path?"**
without you having to ssh manually.

## When to use

- Before pasting a path into a chat / ticket for an FM teammate.
- Before submitting a cross-site simregress / grdlbuild job that
  expects the workarea to be readable from the FM cluster.
- Whenever the user asks: "is X accessible from Folsom?" / "can FM
  see this?" / "what site is this disk on?"

## How to run

```bash
~/.copilot/skills/sle-folsom-path-check/scripts/folsom_path_check.sh [PATH]
```

If `[PATH]` is omitted, the script uses `$MODEL_ROOT` if set, else
`$PWD`.

## What it checks

The script runs three checks in order. **Step 3 is the only one that
gives a definitive YES** — but it requires the optional
`FOLSOM_PROBE_HOST` env var (see below).

| # | Check | Outcome |
|---|-------|---------|
| 1 | Path exists on the **local** host (zsc11) | If not even local, abort with FAIL |
| 2 | Classify by NFS prefix (heuristic) | `/nfs/site/...` → multi-site (LIKELY ACCESSIBLE), `/nfs/zsc*` → ZSC-local (NOT FM), `/nfs/fm*` → FM-local (DEFINITELY FM), other → UNCERTAIN |
| 3 | If `FOLSOM_PROBE_HOST` is set: ssh `<host>` `test -e <path>` | Definitive verdict |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | ACCESSIBLE — confirmed by probe, or classification says multi-site |
| 1 | NOT_ACCESSIBLE — path is site-local to a non-FM site, or probe failed `test -e` |
| 2 | UNCERTAIN — cannot classify and no probe host configured |
| 3 | LOCAL_MISSING — path does not exist on the current host (bad input) |

## Configuring the probe host

For a definitive answer, set the env var **before launching
copilot-cli**:

```tcsh
setenv FOLSOM_PROBE_HOST fmlogin01.fm.intel.com   # or your team's FM gateway
```

(The hostname is **not hardcoded** — every team uses different FM
bastions. Ask your group's admin for one you can `ssh BatchMode=yes`
into without a password prompt, i.e. with kerberos or an SSH agent
ticket already in place.)

If `FOLSOM_PROBE_HOST` is unset, the script still gives a heuristic
classification (Step 2), but the verdict will be `LIKELY` rather than
`CONFIRMED`.

## Output format

```
sle-folsom-path-check
  path:          /nfs/site/disks/ive_sle_zsc11_tbaziza/models/integrate_bundle1101
  local check:   OK (exists on this host)
  classification: multi-site replicated (/nfs/site/...)
  probe host:    fmlogin01.fm.intel.com
  ssh probe:     OK — path exists on FM
  VERDICT:       ACCESSIBLE (CONFIRMED)
```

## Use from the SLE agent

The agent should call this skill in two situations:

1. **Step 0 of any cross-site workflow** — before quoting a path to a
   Folsom user.
2. **On user demand** when they ask any of the trigger phrases above.

```bash
~/.copilot/skills/sle-folsom-path-check/scripts/folsom_path_check.sh "$MODEL_ROOT"
case $? in
  0) echo "Path is accessible from Folsom. Proceeding." ;;
  1) echo "Path is NOT accessible from Folsom — STOP and ask user." ;;
  2) echo "Cannot determine. Set FOLSOM_PROBE_HOST or ask the user." ;;
  3) echo "Path doesn't exist locally. Check the input." ;;
esac
```

## Notes / caveats

- The script never copies or modifies anything. It only `stat`s and
  optionally `ssh`s with `test -e`.
- SSH probe uses `BatchMode=yes` and `ConnectTimeout=10` — it will
  never hang for more than ~10 s.
- "Multi-site replication" of `/nfs/site/` is the *typical* Intel
  policy, but specific disks can be excluded. The CONFIRMED verdict
  from the SSH probe is the only source of truth.
