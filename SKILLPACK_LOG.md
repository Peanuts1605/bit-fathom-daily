# Devpost Learn Skill Pack — usage log

Installed into this repo on 2026-10-16 with `npx -p node@22 -p skills@1.7.2 skills add challengepost/learn-ai-basics --all -y` (the box's Node 20 was too old for `skills`; running the CLI on Node 22 via npx fixed it). Skills land in `.agents/skills/` (plus `agent/skills/` links); versions pinned in `skills-lock.json`.

Honest note: the pack is designed as an interview between the coding agent and a learner. Our coding agent ran each skill in order; interview answers came from the team's written instructions — the adult entrant's goals, the coordinator, and the content/science/QA reviewers — and the existing QA-approved riddle prototype. The adult entrant still needs to read and try the result before submitting (see "Still to do").

| Skill | What we did |
|---|---|
| 1-start | Ran the folder check, added `/devpost/learner-profile.md` to `.gitignore`, wrote a learner profile (kept out of git) recording goals ("learning is the point"), Markdown review format, fast build mode. |
| 2-scope | Brain-dumped the idea, found the kernel (one science-checked riddle a day + a try-it), defined "working", cut accounts/analytics/sharing → `devpost/scope.md`. |
| 3-prd | Walked the core journey screen by screen, named behaviors (daily pick, answering, streak, archive), states (first visit, storage blocked, reload, reduced motion) and non-goals → `devpost/prd.md`. |
| 4-spec | Chose plain HTML/JS + Python build, local-date day mapper, localStorage data model, failure modes; every component cites PRD headings → `devpost/spec.md`. |
| 5-build | Wrote `devpost/checklist.md` as 3 thin slices; built from the QA-approved v3 shell; verified each slice mechanically (validator, streak/date tests, smoke check) and visually (screenshots, two review passes). A screenshot review caught that riddles have 3–4 choices, so PRD/spec were corrected in the same pass, as the skill asks. |
| 6-ship | Followed its checklist: secrets/private-data review of tracked files, kept planning docs in the repo, MIT license, README, video script and description in DEVPOST.md. Video recording, public repo and form fields remain for the entrant. |
