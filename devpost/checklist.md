---
doc: checklist
status: approved
---
# Build Checklist

Build mode: fast (QA checkpoints by Rigel Lab)

## Slices

- [x] **1. Today's riddle shows from the data file**
  Becomes usable: index.html built from src.html + riddles.json shows today's riddle.
  Why now: proves the build path end to end.
  PRD ref: `prd.md > The Core Journey` (1-2)
  Spec ref: `spec.md > Components`, `spec.md > File Structure`
  Build: port QA-approved v3 shell; riddles.json copied unchanged; build.py inlines data.
  Verify (mechanical): `python3 build.py`; validate_riddles.py PASS; smoke RESULT PASS.
  Learner check: open the page and see today's riddle.
  Commit: `Port v3 shell and riddle data`

- [x] **2. Answering, feedback and streak**
  Becomes usable: tap an answer, see teal ✓ / coral guess, streak saved.
  Why now: the kernel.
  PRD ref: `prd.md > Answering`, `prd.md > Streak`
  Spec ref: `spec.md > Streak engine`, `spec.md > Data Model`
  Build: kept v3 logic; tests made repo-relative.
  Verify (mechanical): tests/streak_date_test.py RESULT PASS.
  Learner check: answer wrong, reload, streak still 1.
  Commit: `Make tests repo-relative`

- [x] **3. Encore loop, archive, screenshots**
  Becomes usable: day 14+ encore; archive replays; review shots.
  Why now: boundary behavior and visual QA.
  PRD ref: `prd.md > Daily riddle`, `prd.md > Archive`
  Spec ref: `spec.md > Day mapper`
  Build: Playwright shots at 390x844 and 1280x800.
  Verify (mechanical): encore tests PASS; shots reviewed twice.
  Learner check: look at shots/.
  Commit: `Add screenshots and submission docs`

## Hands-on Checkpoints
- [x] Rigel Lab QA rounds 1–3 on v1–v3 (approved v3).
- [ ] Adult entrant tries the page end to end before submitting.

## Final Review
Two self-review passes on shots and tests (see SKILLPACK_LOG.md).

## Code Tour and App Map
src.html (UI + logic) ← build.py ← riddles.json → index.html. Streak engine and day mapper are in src.html's script block.

## Revisions
- Tests changed from absolute path to repo-relative path.
- Docs corrected: riddles have 3–4 choices (screenshots showed 3), not always 4.
