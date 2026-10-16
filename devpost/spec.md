---
doc: spec
status: approved
---
# Bit & Fathom Daily Riddle — Technical Spec

## How This Works, In Plain Language
All riddles live in a small data file. A build step pours that data into a page template, producing one HTML file that runs entirely in the browser. The page works out today's riddle from the device's calendar and remembers your streak in the browser's own storage.

## The Core Journey Through the System
Load index.html → read inlined riddle JSON → compute local day index → render card (implements `prd.md > Daily riddle`) → on tap, grade and render feedback (`prd.md > Answering`) → update streak object and save to localStorage (`prd.md > Streak`) → render archive (`prd.md > Archive`).

## Stack
Plain HTML/CSS/vanilla JS, no frameworks, no dependencies. Python 3 for build, validation and tests (Playwright + headless Chrome).

## Where It Runs and How Someone Tries It
Open index.html in any browser, or serve the folder (`python3 -m http.server`). Can be hosted as a static file anywhere.

## Look and Feel
Implements `prd.md > Look and Feel`: CSS variables for navy/gold/teal/coral; SVGs inlined verbatim; tap targets ≥48px; `@media (hover:hover)` for hover styles; `prefers-reduced-motion` disables animation.

## Components
### Riddle data — riddles.json
Array of 14 objects: id, title, question, choices[3–4], answer_index, explainer, try_it, source_title, source_url, speaker. Validated by validate_riddles.py.
### Template — src.html
Markup, styles, SVGs and script with a `%%INLINE%%` placeholder.
### Build — build.py
Inlines riddles.json (escaping `</`) into src.html → index.html.
### Day mapper
Local-date day count from launch (2026-10-12 → 001), modulo 14, encore flag when day ≥ 14.
### Streak engine
Implements STREAK.md; state `{ans:{date:choice}, streak, best, last}` in localStorage.

## Data Model
localStorage key holds `{"ans":{"YYYY-MM-DD":choiceIndex},"streak":n,"best":n,"last":"YYYY-MM-DD"}`. Nothing else stored; nothing leaves the device.

## File Structure
`src.html`, `riddles.json`, `build.py`, `index.html` (built), `validate_riddles.py`, `STREAK.md`, `tests/streak_date_test.py`, `tests/riddle_smoke.sh`, `shots/`, `devpost/`.

## External Services and Dependencies
None at runtime. Source links are plain outbound links only.

## Important Failure Modes
localStorage unavailable → in-memory fallback. Clock changes → mapping uses local date only. Riddles run out → encore loop.

## What Was Simplified and Why
Single file, no build tooling beyond Python, no server — fastest to review, host and keep private-by-design for kids.

## Decisions and Open Issues
Streak counts plays, not correctness (kid-friendly). No open issues.
