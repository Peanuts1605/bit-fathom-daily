#!/bin/bash
# check.sh: build + all tests. Exits non-zero if ANY step fails (pipefail; each step's exit code is checked).
# PYTHON: an interpreter with Playwright, picked in this order (no other bot's venv, no silent fallback):
#   1. PYTHON=/path/to/python if you set it (it must import playwright, or the check stops)
#   2. tooling/pyenv/bin/python, this repo's own env (make it once: bash tooling/setup-pyenv.sh)
#   3. python3 on PATH, if it has Playwright
#   None has Playwright -> "FAIL setup: ..." with the fix, exit 2 (a setup problem, not a test result).
# LINKS=1 also checks every riddle source_url over the network: HTTP 403 = WARN (likely bot-blocking of curl,
#   listed with its URL; CHECK PASS still possible); 404, 5xx, DNS error or timeout = FAIL.
# Usage: ./check.sh [live_url]
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONDONTWRITEBYTECODE=1
has_pw(){ [ -n "$1" ] && "$1" -c 'import playwright' 2>/dev/null; }
setup_fail(){ echo "FAIL setup: $1"; echo "    fix: bash tooling/setup-pyenv.sh  (or: PYTHON=/path/to/python-with-playwright ./check.sh)"; exit 2; }
if [ -n "${PYTHON:-}" ]; then has_pw "$PYTHON" || setup_fail "PYTHON=$PYTHON cannot import playwright"
elif has_pw tooling/pyenv/bin/python; then PYTHON=tooling/pyenv/bin/python
elif has_pw "$(command -v python3 || true)"; then PYTHON=$(command -v python3)
else setup_fail "no Python with Playwright (no tooling/pyenv, and python3 has none)"; fi
echo "USING $PYTHON (playwright $("$PYTHON" -c 'import importlib.metadata as m;print(m.version("playwright"))'))"
fails=0; warns=0
step(){ # step <label> <cmd...>: run, keep the full log, print its last line, record failure
  local label=$1; shift; local log; log=$(mktemp)
  if "$@" >"$log" 2>&1; then echo "PASS $label: $(tail -1 "$log")"
    # WARN lines (e.g. a source link answering HTTP 403) are listed but do not fail the check
    local w; w=$(grep '^WARN' "$log" || true)
    if [ -n "$w" ]; then echo "$w" | sed 's/^/    /'; warns=$((warns+$(echo "$w" | wc -l))); fi
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
step clock-skew "$PYTHON" tests/clock_skew_test.py
if grep -q 'fetch(' index.html; then echo "FAIL network fetch present"; fails=$((fails+1)); else echo "PASS no runtime fetch"; fi
if [ "$warns" -ne 0 ]; then echo "WARN $warns link(s) (HTTP 403, listed above; not a failure)"; fi
if [ "$fails" -ne 0 ]; then echo "CHECK FAIL ($fails step(s))"; exit 1; fi
echo "CHECK PASS"
