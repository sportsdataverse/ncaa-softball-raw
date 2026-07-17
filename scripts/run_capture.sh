#!/usr/bin/env bash
# Live NCAA baseball/softball pbp capture launcher.
#
#   SPORT=MBA YEAR=2025 OUT=./raw MAX=200 \
#     NCAA_PROXY_POOL="$(cat proxies.txt)" bash scripts/run_capture.sh
#
# Watch live:  tail -f capture.log
set -euo pipefail
cd "$(dirname "$0")/.."

: "${SPORT:=MBA}"
: "${YEAR:?set YEAR, e.g. 2025}"
: "${OUT:=./raw}"
: "${MAX:=}"
: "${NCAA_PROXY_POOL:?set NCAA_PROXY_POOL to a US-residential pool}"
: "${PY:=python}"

export PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8
ARGS=(--sport "$SPORT" --year "$YEAR" --out "$OUT")
[ -n "$MAX" ] && ARGS+=(--max "$MAX")

echo "$(date -Is) START $SPORT $YEAR -> $OUT" >> capture.log
"$PY" python/run.py "${ARGS[@]}" >> capture.log 2>&1
echo "$(date -Is) EXIT=$?" >> capture.log
