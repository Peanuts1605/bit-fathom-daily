# Devpost submission draft — Bit & Fathom Daily Riddle

## What it does
A one-page web app that serves one science riddle a day, asked by two friendly robots, Bit and Fathom. Kids pick an answer and always get a warm explanation, a safe at-home "try it" experiment and a link to the real source the fact was checked against. A daily streak (saved only on the device) invites them back tomorrow; past riddles can be replayed, and after 14 days the riddles return as Encores.

## Who it's for
Curious kids about 7–12 and the grown-ups beside them — parents on a phone, teachers on a classroom screen. It's private by design: no accounts, no cookies, no trackers, nothing loaded from outside.

## What we learned
- Writing scope → PRD → spec *before* building kept the app small and focused; "Explicitly Cut" stopped us adding accounts and leaderboards a kids' app doesn't need.
- Kid-friendly rules are product decisions: a wrong guess still counts toward the streak, and wrong answers are coral, not gold, so they never look like a reward.
- Dates are tricky: using the device's local calendar, not UTC, keeps today's riddle from changing mid-evening.
- Science content needs a real checker; every riddle cites a source that was fetched and confirmed.
- Screenshots catch what tests miss — reviewing them made us fix our own docs.

## How we used the Devpost Learn Skill Pack
We installed the pack into the repo and ran its six skills in order inside a coding agent. **1-start** captured the learner's goals and kept that profile out of git. **2-scope** turned a brain dump into a kernel — one science-checked riddle a day plus a try-it — and a cut list. **3-prd** walked the journey screen by screen and defined the streak, archive and edge states. **4-spec** chose a single static HTML file with a local-date day mapper and device-only storage, citing each PRD behavior. **5-build** split the work into three thin slices, each verified with a validator, automated streak/date tests and a smoke check, plus screenshot reviews; when a review showed riddles have 3–4 choices, we corrected the PRD and spec to match. **6-ship** guided the privacy check, license, README and this write-up. All planning docs are in `devpost/`, and the details are in SKILLPACK_LOG.md.

## Video script (about 2 minutes)
1. **0:00–0:10** — Title card, then the live page on a phone. "Bit & Fathom Daily Riddle: one science riddle a day for curious kids."
2. **0:10–0:35** — Read today's actual riddle and choices (they change with the local date). Tap one of its incorrect answers. Show the coral "your guess", the teal ✓ on the correct choice and "Nice try — robots learn from mistakes too!"
3. **0:35–0:55** — Scroll: the robot's explanation, today's Try It and the fact-check link. "Every answer ends in something to try at home, and a real source."
4. **0:55–1:15** — Streak, Best and Stats. Tap 📤 Share: a shareable result with emoji, no answer spoilers. "A wrong guess still counts. Everything stays on this device; no accounts or trackers."
5. **1:15–1:35** — Tap ‹ to replay a past riddle; the streak doesn't change. Open ❓ How to play.
6. **1:35–1:52** — The repo: `devpost/scope.md`, `prd.md`, `spec.md`, `checklist.md`. "We planned it with the Devpost Learn Skill Pack before building."
7. **1:52–2:00** — Closing card: MIT licensed, @RippleParade.
