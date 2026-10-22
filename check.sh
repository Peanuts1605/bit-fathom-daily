#!/bin/bash
# check.sh: build + all tests. Exits non-zero if ANY step fails (pipefail; each step's exit code is checked).
# PYTHON: an interpreter with Playwright. Default python3; if that has no Playwright, falls back to
#   /workspace/lens/.venv/bin/python when present. Override: PYTHON=/path/to/python ./check.sh
# LINKS=1 also checks every riddle source_url over the network (riddle 005 currently gets HTTP 403).
# Usage: ./check.sh [live_url]
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
PYTHON=${PYTHON:-python3}
if ! "$PYTHON" -c 'import playwright' 2>/dev/null; then
  if [ -x /workspace/lens/.venv/bin/python ] && /workspace/lens/.venv/bin/python -c 'import playwright' 2>/dev/null; then
    echo "NOTE $PYTHON has no Playwright; using /workspace/lens/.venv/bin/python"; PYTHON=/workspace/lens/.venv/bin/python
  else
    echo "FAIL no Python with Playwright (set PYTHON=/path/to/python)"; exit 1
  fi
fi
fails=0
step(){ # step <label> <cmd...>: run, keep the full log, print its last line, record failure
  local label=$1; shift; local log; log=$(mktemp)
  if "$@" >"$log" 2>&1; then echo "PASS $label: $(tail -1 "$log")"
  else local rc=$?; echo "FAIL $label (exit $rc): $(tail -1 "$log")"; sed 's/^/    | /' "$log" | tail -15; fails=$((fails+1)); fi
  rm -f "$log"
}
step build python3 build.py
if [ "${LINKS:-0}" = 1 ]; then step riddles python3 validate_riddles.py
else echo "SKIP source-link network check (set LINKS=1 to run it)"; step riddles env BF_SKIP_LINKS=1 python3 validate_riddles.py; fi
step smoke bash tests/riddle_smoke.sh index.html ${1:-}
step streak-date "$PYTHON" tests/streak_date_test.py
step streak-padded "$PYTHON" tests/streak_padded_test.py index.html
step multitab "$PYTHON" tests/multitab_test.py
if grep -q 'fetch(' index.html; then echo "FAIL network fetch present"; fails=$((fails+1)); else echo "PASS no runtime fetch"; fi
if [ "$fails" -ne 0 ]; then echo "CHECK FAIL ($fails step(s))"; exit 1; fi
echo "CHECK PASS"
