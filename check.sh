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
setup_fail(){ echo "FAIL setup: $1"; echo "    fix: ${2:-bash tooling/setup-pyenv.sh}"; exit 2; }
if [ -n "${PYTHON:-}" ]; then has_pw "$PYTHON" || setup_fail "PYTHON=$PYTHON cannot import playwright"
elif has_pw tooling/pyenv/bin/python; then PYTHON=tooling/pyenv/bin/python
elif has_pw "$(command -v python3 || true)"; then PYTHON=$(command -v python3)
else setup_fail "no Python with Playwright (no tooling/pyenv, and python3 has none)"; fi
echo "USING $PYTHON (playwright $("$PYTHON" -c 'import importlib.metadata as m;print(m.version("playwright"))'))"
command -v pngquant >/dev/null || setup_fail "pngquant is not installed" "apt install pngquant"
"$PYTHON" -c 'import PIL' >/dev/null 2>&1 || setup_fail "Pillow is missing (requirements.txt)" "bash tooling/setup-pyenv.sh"
"$PYTHON" -c 'import fontTools' >/dev/null 2>&1 || setup_fail "fonttools is missing (requirements.txt)" "bash tooling/setup-pyenv.sh"
command -v node >/dev/null || setup_fail "node is not installed" "install Node.js, then npm ci (wrangler is a devDependency)"
command -v npm >/dev/null || setup_fail "npm is not installed" "install Node.js, then npm ci (wrangler is a devDependency)"
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
if [ ! -x node_modules/.bin/wrangler ]; then step wrangler npm ci; fi
step build env BF_TEST_HOOK=1 "$PYTHON" build.py
if [ "${LINKS:-0}" = 1 ]; then step riddles "$PYTHON" validate_riddles.py
else echo "SKIP source-link network check (set LINKS=1 to run it)"; step riddles env BF_SKIP_LINKS=1 "$PYTHON" validate_riddles.py; fi
step smoke bash tests/riddle_smoke.sh index.html ${1:-}
step streak-date "$PYTHON" tests/streak_date_test.py
step streak-padded "$PYTHON" tests/streak_padded_test.py index.html
step multitab "$PYTHON" tests/multitab_test.py
step clock-skew "$PYTHON" tests/clock_skew_test.py
step og "$PYTHON" tests/og_check.py
step r-pages "$PYTHON" tests/r_pages_test.py
step csp "$PYTHON" tests/csp_check.py
step hook "$PYTHON" tests/hook_check.py
step share "$PYTHON" tests/share_check.py
step e2e "$PYTHON" tests/share_loop_e2e.py
# Tests need the hook. The files we leave behind are a release build, which omits it.
step release env BF_SKIP_OG=1 "$PYTHON" build.py
if grep -q 'if(true)' dist/index.html || grep -q 'if(true)' index.html; then echo "FAIL release build left the test hook on"; fails=$((fails+1)); else echo "PASS release build omits test hook"; fi
step review "$PYTHON" tests/capture_review.py
if grep -q 'fetch(' index.html || grep -q 'fetch(' dist/index.html; then echo "FAIL network fetch present"; fails=$((fails+1)); else echo "PASS no runtime fetch"; fi
dirty=$(git status --porcelain)
if [ -n "$dirty" ]; then echo "FAIL git status not clean after check"; echo "$dirty"; fails=$((fails+1)); else echo "PASS git status clean"; fi
if [ "$warns" -ne 0 ]; then echo "WARN $warns note(s) (listed above; not a failure)"; fi
if [ "$fails" -ne 0 ]; then echo "CHECK FAIL ($fails step(s))"; exit 1; fi
echo "CHECK PASS"
