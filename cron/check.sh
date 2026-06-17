#!/bin/bash
# Phase 1 cron health check.
#
# Run after the 5 plists have had a chance to fire:
#   - capstone.staleness-audit       (tonight 23:00 NY)
#   - capstone.kelly-audit           (tonight 23:15 NY)
#   - capstone.reflexion-retro       (tonight 23:30 NY)
#   - capstone.dgm-proposal-demo     (Sunday 22:00 NY)
#   - capstone-brier-weekly          (Sunday — separate cadence)
#
# Outputs a colored pass/fail per plist + per data snapshot.

set -u

GREEN="\033[32m"
RED="\033[31m"
YELLOW="\033[33m"
DIM="\033[2m"
RESET="\033[0m"

REPO_ROOT="$HOME/Desktop/capstone-orallexa-calibration"
SNAP_DIR="$REPO_ROOT/data-snapshots"
TODAY=$(date +%Y-%m-%d)

pass=0
fail=0
warn=0

ok()    { echo -e "${GREEN}✓${RESET} $1"; pass=$((pass + 1)); }
bad()   { echo -e "${RED}✗${RESET} $1"; fail=$((fail + 1)); }
maybe() { echo -e "${YELLOW}?${RESET} $1"; warn=$((warn + 1)); }
note()  { echo -e "${DIM}  $1${RESET}"; }

echo "Phase 1 cron health check — $(date '+%Y-%m-%d %H:%M %Z')"
echo

# ─────────────────────────────────────────────────────────────
# 1. Plist loaded into launchd
# ─────────────────────────────────────────────────────────────
echo "─── launchctl ───"
for label in \
    com.alexji.capstone.staleness-audit \
    com.alexji.capstone.kelly-audit \
    com.alexji.capstone.reflexion-retro \
    com.alexji.capstone.dgm-proposal-demo \
    com.alexji.capstone-brier-weekly; do
    row=$(launchctl list 2>/dev/null | awk -v L="$label" '$3 == L')
    if [ -z "$row" ]; then
        bad "$label  not loaded"
        note "fix: launchctl bootstrap gui/\$(id -u) ~/Library/LaunchAgents/$label.plist"
    else
        rc=$(echo "$row" | awk '{print $2}')
        pid=$(echo "$row" | awk '{print $1}')
        if [ "$rc" = "0" ] || [ "$rc" = "-" ]; then
            ok "$label  rc=$rc  pid=$pid"
        else
            bad "$label  exit_code=$rc — fired but non-zero"
            note "tail /tmp/${label#com.alexji.}.err"
        fi
    fi
done

echo

# ─────────────────────────────────────────────────────────────
# 2. /tmp out + err files (visible signal of last run)
# ─────────────────────────────────────────────────────────────
echo "─── /tmp logs ───"
for stem in capstone-staleness capstone-kelly capstone-reflexion capstone-dgm; do
    out=/tmp/${stem}.out
    err=/tmp/${stem}.err
    if [ -f "$out" ]; then
        size=$(wc -c < "$out" | tr -d ' ')
        mod=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$out" 2>/dev/null || stat -c "%y" "$out" 2>/dev/null)
        ok "$out  ${size}B  $mod"
    else
        maybe "$out  missing — cron may not have fired yet"
    fi
    if [ -s "$err" ]; then
        bad "$err  non-empty"
        note "tail -20 $err"
    fi
done

echo

# ─────────────────────────────────────────────────────────────
# 3. Today's data snapshots (real output, not just process running)
# ─────────────────────────────────────────────────────────────
echo "─── data snapshots dated $TODAY ───"
if [ ! -d "$SNAP_DIR" ]; then
    maybe "$SNAP_DIR  dir does not exist yet"
else
    for prefix in staleness kelly reflexion dgm; do
        f="$SNAP_DIR/${prefix}-${TODAY}.json"
        if [ -f "$f" ]; then
            ok "$(basename "$f")  $(wc -c < "$f" | tr -d ' ') bytes"
        else
            # Look back: did the previous fire produce one?
            latest=$(ls -t "$SNAP_DIR/${prefix}-"*.json 2>/dev/null | head -1)
            if [ -n "$latest" ]; then
                maybe "${prefix}-${TODAY}.json  missing — most recent: $(basename "$latest")"
            else
                bad "${prefix}-*.json  no snapshots ever produced"
            fi
        fi
    done
fi

echo
echo "─── summary ───"
echo -e "${GREEN}pass: $pass${RESET}  ${YELLOW}warn: $warn${RESET}  ${RED}fail: $fail${RESET}"
if [ "$fail" = "0" ] && [ "$warn" = "0" ]; then
    echo -e "${GREEN}Phase 1 healthy.${RESET}"
    exit 0
elif [ "$fail" = "0" ]; then
    echo -e "${YELLOW}Phase 1 mostly healthy — warnings are non-blocking.${RESET}"
    exit 0
else
    echo -e "${RED}Phase 1 has failures — investigate before tomorrow's plan.${RESET}"
    exit 1
fi
