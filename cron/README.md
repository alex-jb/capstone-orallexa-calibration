# Capstone launchd cron jobs

Four nightly + one weekly job that exercise Phase 1 #3-#6 wire-up scripts.

| Plist | Schedule (NY local) | Script |
|---|---|---|
| `com.alexji.capstone.reflexion-retro` | daily 23:00 | `scripts/reflexion_retro.py --worst-n 3` |
| `com.alexji.capstone.staleness-audit` | daily 23:15 | `scripts/staleness_audit.py` |
| `com.alexji.capstone.kelly-audit` | daily 23:30 | `scripts/kelly_audit.py --top-n 30` |
| `com.alexji.capstone.dgm-proposal-demo` | weekly Sunday 22:00 | `scripts/dgm_proposal_demo.py` |

## Install

```bash
cd ~/Desktop/capstone-orallexa-calibration/cron
for plist in com.alexji.capstone.*.plist; do
  cp "$plist" ~/Library/LaunchAgents/
  launchctl unload ~/Library/LaunchAgents/"$plist" 2>/dev/null
  launchctl load ~/Library/LaunchAgents/"$plist"
done
launchctl list | grep com.alexji.capstone
```

## Verify

```bash
# next-fire times
launchctl list | grep com.alexji.capstone

# logs after a run
tail -50 /tmp/capstone-reflexion-retro.out
tail -50 /tmp/capstone-staleness-audit.out
tail -50 /tmp/capstone-kelly-audit.out
tail -50 /tmp/capstone-dgm-proposal-demo.out
```

## Uninstall

```bash
for label in reflexion-retro staleness-audit kelly-audit dgm-proposal-demo; do
  launchctl unload ~/Library/LaunchAgents/com.alexji.capstone.$label.plist 2>/dev/null
  rm -f ~/Library/LaunchAgents/com.alexji.capstone.$label.plist
done
```

## Why these specific times

- **23:00 reflexion** — runs after the day's brier_audit has resolved overnight outcomes; pulls worst-Brier rows into structured Reflexion entries before the JSONL log "closes" the day.
- **23:15 staleness** — 15 min after reflexion to avoid file lock contention on shared decision_log.
- **23:30 kelly** — needs the latest ECE snapshot, which `scripts/ece_audit.py` produces earlier in the day (manual or its own cron).
- **Weekly D-G proposal** — synthetic proposals exercise the merge gate, not the live agent. Daily is overkill; Sunday lets the week's data accumulate before the gate fires.
