---
doc: prd
status: approved
---
# Bit & Fathom Daily Riddle — Product Requirements

## The Core Journey
1. Kid opens the page; header shows Bit & Fathom, today's date label and the streak.
2. Today's riddle card shows the speaker robot, title, question and three or four choices (A–D).
3. Kid taps a choice. Choices lock.
4. Feedback appears: correct answer gets teal + ✓; a wrong pick is muted coral labelled "· your guess"; a kind message ("Nice try — robots learn from mistakes too!").
5. Explanation, a kid-safe "Try it" and a source link appear.
6. Streak updates once for today. Kid can browse past riddles in the archive.
7. Tomorrow, a new riddle appears; after 14 days riddles loop with an "Encore" badge.

## Screens and Layout
One page, mobile-first (390px) and scaling to desktop (1280px): header + streak, riddle card, feedback panel, archive list, footer with gold @RippleParade YouTube/X pills.

## Look and Feel
Navy background, gold accents, teal highlights, the shell's existing fonts. Exact Bit and Fathom SVGs from the logic-gates exhibit — never redrawn. Gold focus ring on choices. Encore badge navy text on gold.

## Features and Behavior
### Daily riddle
Riddle index = days since the launch date on the **device's local calendar**, modulo 14. Day 14+ shows Encore.
### Answering
One answer per riddle; right = teal ✓, wrong = coral "your guess" + correct shown.
### Streak
Rules in STREAK.md: playing today counts right or wrong; one change per local day; archive never changes it; a skipped day resets to 0 on next visit; best streak kept.
### Archive
Past riddles (up to today) can be replayed without affecting the streak.

## States and Boundaries
First visit: streak 0. Storage blocked: app still works, streak just isn't remembered. Reload same day: answer and streak kept. Reduced-motion users get no animation.

## Product Decisions
Wrong answers don't punish (kids shouldn't lose a streak for guessing). Local date not UTC so a riddle never flips mid-evening.

## What We're Building
The POC in scope.md, as one self-contained HTML file built from src.html + riddles.json.

## Deferred From the POC
Read-aloud, more riddles, installable app.

## Possible Later Enhancements
Classroom mode, printable cards.

## Non-Goals
Accounts, data collection, trackers, external loads, sharing, ads.

## Open Questions
None blocking. Content additions go through Rigel Lab's science check.
