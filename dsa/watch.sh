#!/bin/bash
# Live-interviewer watcher for /dsa. Watches one practice file and prints an
# event line when there's something worth looking at. Each line wakes Claude.
#
#   SAVE <n> lines   content changed (at most one every MIN_GAP seconds)
#   IDLE <m>m        no change for IDLE_AFTER seconds (once per quiet spell)
#
# Usage: dsa/watch.sh <file> [min_gap_s=30] [idle_after_s=180]
f="$1"; MIN_GAP="${2:-30}"; IDLE_AFTER="${3:-180}"
[ -n "$f" ] || { echo "usage: $0 <file>" >&2; exit 2; }

hash() { [ -f "$f" ] && md5 -q "$f" 2>/dev/null || echo none; }
last_hash=$(hash); last_emit=0; last_change=$(date +%s); idle_sent=0; pending=0

while true; do
  now=$(date +%s); h=$(hash)
  if [ "$h" != "$last_hash" ]; then
    last_hash=$h; last_change=$now; idle_sent=0; pending=1
  fi
  if [ $pending -eq 1 ] && [ $((now - last_emit)) -ge "$MIN_GAP" ]; then
    echo "SAVE $(wc -l < "$f" | tr -d ' ') lines"
    last_emit=$now; pending=0
  fi
  if [ $idle_sent -eq 0 ] && [ $((now - last_change)) -ge "$IDLE_AFTER" ]; then
    echo "IDLE $((IDLE_AFTER / 60))m"
    idle_sent=1
  fi
  sleep 1
done
