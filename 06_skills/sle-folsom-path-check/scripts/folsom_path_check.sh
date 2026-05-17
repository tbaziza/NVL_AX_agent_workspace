#!/bin/bash
# folsom_path_check.sh — verify a path is accessible from the Folsom (FM) site.
#
# Usage:
#   folsom_path_check.sh [PATH]
#
# If PATH is omitted, uses $MODEL_ROOT, else $PWD.
#
# Exit codes:
#   0  ACCESSIBLE   — confirmed by SSH probe, or classified as multi-site
#   1  NOT_ACCESSIBLE — path is site-local to a non-FM site, or probe failed
#   2  UNCERTAIN    — cannot classify and no probe host configured
#   3  LOCAL_MISSING — path does not exist on the current host

set -u

P="${1:-${MODEL_ROOT:-$PWD}}"

echo "sle-folsom-path-check"
echo "  path:          $P"

# ── Step 1: local existence ────────────────────────────────────────────
if [ ! -e "$P" ]; then
  echo "  local check:   MISSING — '$P' does not exist on $(hostname -s)"
  echo "  VERDICT:       LOCAL_MISSING"
  exit 3
fi
echo "  local check:   OK (exists on this host)"

# Resolve symlinks so we classify the real backing path
RP=$(readlink -f "$P" 2>/dev/null || echo "$P")
if [ "$RP" != "$P" ]; then
  echo "  resolved to:   $RP"
fi

# ── Step 2: classify by NFS prefix ─────────────────────────────────────
classification="UNKNOWN"
likely_fm="unknown"
case "$RP" in
  /nfs/site/*)
    classification="multi-site replicated (/nfs/site/...)"
    likely_fm="likely_yes"
    ;;
  /nfs/fm/*|/nfs/fm[0-9]*/*|/p/fm/*)
    classification="FM-local"
    likely_fm="definitely_yes"
    ;;
  /nfs/zsc*/*|/nfs/sc*/*)
    classification="site-local to Santa Clara (NOT FM)"
    likely_fm="no"
    ;;
  /nfs/hf/*|/nfs/hd/*)
    classification="Hillsboro-local (NOT FM)"
    likely_fm="no"
    ;;
  /p/*|/usr/intel/*|/opt/*)
    classification="globally exported tool path"
    likely_fm="likely_yes"
    ;;
  *)
    classification="unclassified prefix"
    likely_fm="unknown"
    ;;
esac
echo "  classification: $classification"

# ── Step 3: SSH probe (optional, definitive) ───────────────────────────
probe_host="${FOLSOM_PROBE_HOST:-}"
probe_result="skipped"
if [ -n "$probe_host" ]; then
  echo "  probe host:    $probe_host"
  if ssh -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new \
       "$probe_host" "test -e '$RP'" 2>/dev/null; then
    probe_result="confirmed_yes"
    echo "  ssh probe:     OK — path exists on FM"
  else
    rc=$?
    if [ "$rc" -eq 1 ]; then
      probe_result="confirmed_no"
      echo "  ssh probe:     FAIL — path does NOT exist on $probe_host"
    else
      probe_result="probe_error"
      echo "  ssh probe:     ERROR — could not reach $probe_host (rc=$rc)"
    fi
  fi
else
  echo "  probe host:    (unset — set FOLSOM_PROBE_HOST for a definitive check)"
fi

# ── Verdict ────────────────────────────────────────────────────────────
case "$probe_result" in
  confirmed_yes)
    echo "  VERDICT:       ACCESSIBLE (CONFIRMED)"
    exit 0
    ;;
  confirmed_no)
    echo "  VERDICT:       NOT_ACCESSIBLE (CONFIRMED)"
    exit 1
    ;;
  probe_error)
    # Fall through to heuristic
    ;;
esac

case "$likely_fm" in
  definitely_yes)
    echo "  VERDICT:       ACCESSIBLE (heuristic — FM-local path)"
    exit 0
    ;;
  likely_yes)
    echo "  VERDICT:       LIKELY ACCESSIBLE (heuristic — set FOLSOM_PROBE_HOST to confirm)"
    exit 0
    ;;
  no)
    echo "  VERDICT:       NOT ACCESSIBLE (heuristic — site-local to a non-FM site)"
    exit 1
    ;;
  unknown|*)
    echo "  VERDICT:       UNCERTAIN — cannot classify prefix; set FOLSOM_PROBE_HOST to confirm"
    exit 2
    ;;
esac
