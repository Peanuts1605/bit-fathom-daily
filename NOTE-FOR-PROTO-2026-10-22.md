# Note for Proto — Bit & Fathom Daily, 2026-10-22 (from Tinker 🐼, Rigel Lab)

Done at **Max's request**, after a **Lens PASS** (`/workspace/lens/f1f3-review-20261022/REVIEW.md`). Branch **`tinker/lensF3-streak`**, made from `mag84-hd7-48px` at 159557e. No force push and no history rewritten; `master` was not touched.

## What changed and why
1. **Streak dates (commit `e531d04`).**
   - **The bug:** the streak compared saved dates as text. A saved `last` of `2027-03-12` (zero-padded) did not match `2027-3-12`, so a kid who played yesterday got reset to 1.
   - **The fix:** dates are now compared as day numbers (`kday()`), so both spellings count as the same day.
   - **Junk dates:** an unreadable or junk saved date (e.g. `not-a-date` or an ISO timestamp) now counts as *very old*. The streak resets to 1 on the next play instead of quietly keeping the old number.
   - **Compatibility:** the storage key `bf-riddle-v1` and the saved format are unchanged.
2. **check.sh could never fail; now it can (commit `f8b75d6`).**
   - **The bug:** every step was piped through `| tail -1` without `pipefail`. The default Python (`/workspace/proto-bot/venv/bin/python`) does not exist, so the streak and multi-tab tests never ran, yet the script still printed CHECK PASS.
   - **Now:**
     - It uses `set -euo pipefail` and checks each step's exit code.
     - Python comes from `PYTHON=${PYTHON:-python3}`. If that has no Playwright, it falls back to `/workspace/lens/.venv/bin/python`.
     - Any failing step gives `CHECK FAIL` and exit 1.
   - **New test** `tests/streak_padded_test.py`: padded, unpadded, DST, gap, junk and ISO dates. The old `streak_date_test.py` passed even on the buggy app.
   - **Flaky test fixed** in `tests/multitab_test.py`. Its "next day" case set storage and then reloaded at once, which raced Chrome's storage flush. It failed 3 of 8 runs on 159557e as well. It now seeds before page scripts run, and passed 10 of 10 runs.
   - **Source links:** `validate_riddles.py` has `BF_SKIP_LINKS=1`. check.sh skips the network source-link check by default and prints that it did; `LINKS=1 ./check.sh` runs it. **Open item for you/Max:** riddle 005's LoC link still returns HTTP 403 to curl (it was already open in MAG-84).

## Deployed
- **Worker:** `bit-fathom-daily-preview` only (same account; no other worker, zone or DNS touched). URL: https://bit-fathom-daily-preview.gigantic-stranger.workers.dev/
- **Also shipped:** this deploy includes Max's MAG-84 48px tap-target commit (7f55a84), which was not live before. The previous live build matched cd6353d.
- **Live index.html sha256:** `41069231c60fe614025362a7e9a769d21ec2ec48bdf1fa7edf1b7ab9de2182f2`. This equals the local `index.html`.

## How to verify
```bash
cd /workspace/proto-bot/bit-fathom-daily
./check.sh                # expect: CHECK PASS, exit 0
curl -s https://bit-fathom-daily-preview.gigantic-stranger.workers.dev/ | sha256sum   # expect 41069231…
```

**Proof files:**
- `/workspace/work/grok-pilot/rigel-lab/experiments/lensF3-check-proof/`: check.sh FAIL on a deliberately broken copy, PASS on the real code, and the old check.sh printing CHECK PASS on the broken copy.
- `/workspace/work/grok-pilot/rigel-lab/experiments/lensF3-deploy/`: the deploy script, a backup of the previous deploy script, and the live check. On the live URL, a padded yesterday seed with streak 4 went to streak 5. The screenshot is there too.

Backups of every file I edited (before the edit) are in `/workspace/work/grok-pilot/rigel-lab/experiments/lensF3-check-proof/backups/`.
