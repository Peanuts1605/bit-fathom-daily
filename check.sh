#!/bin/bash
# Full local check: build, riddle data, smoke, streak/date, multi-tab regressions.
set -e; cd "$(dirname "$0")"; PY=${PY:-/workspace/proto-bot/venv/bin/python}
python3 build.py
$PY validate_riddles.py | tail -1
bash tests/riddle_smoke.sh index.html ${1:-} | tail -1
$PY tests/streak_date_test.py | tail -1
$PY tests/multitab_test.py | tail -1
grep -q 'fetch(' index.html && { echo "FAIL network fetch present"; exit 1; } || echo "PASS no runtime fetch"
echo "CHECK PASS"
