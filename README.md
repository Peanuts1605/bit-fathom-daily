# Bit & Fathom Daily Riddle

One science riddle a day, asked by Bit and Fathom from the Ripple Parade world. Pick an answer, get a kind explanation, a kid-safe "try it" experiment and a real source — then come back tomorrow to grow your streak.

## Who it's for
Curious kids (about 7–12) with a grown-up nearby, at home or in class. No accounts, no cookies, no trackers, no external loads. The streak lives only in your browser's local storage.

## Run it
- Just open `index.html` in a browser, or `python3 -m http.server` and visit http://localhost:8000.
- Rebuild after editing riddles or the template: `python3 build.py` (inlines `riddles.json` into `src.html` → `index.html`, and writes `publish/` for wrangler).
- Validate riddles: `python3 validate_riddles.py`
- Tests (needs Python Playwright + Chrome): `./check.sh`
- Python for the check: `bash tooling/setup-pyenv.sh` (installs `requirements.txt` into `tooling/pyenv`). pngquant is a system package (`apt install pngquant`).

## Deploy
Config is `wrangler.jsonc` (Worker name `bit-fathom-daily-next`). `build.py` fills `publish/` with the HTML bundle plus `/og/` cards. `worker/share-routes.js` serves real `/r/NNN/` pages, the generic card for other `/r/` paths, and leaves every other missing path as a 404.

```
npx wrangler dev --local
npx wrangler deploy
```

`./check.sh` runs the local worker. It does not deploy. The old inline-worker packer (`review/gen.py`) is retired.

## How it works
- Today's riddle comes from the device's local date (riddle 001 = Oct 12, 2026), looping with an **Encore** badge after 14 days.
- Streak rules are in [STREAK.md](STREAK.md): playing counts right or wrong, once per day; past riddles never change it; a skipped day resets it.

## Built with the Devpost Learn Skill Pack
Planning docs live in [`devpost/`](devpost/): `scope.md`, `prd.md`, `spec.md`, `checklist.md`. See [SKILLPACK_LOG.md](SKILLPACK_LOG.md).

## Credits
- Riddles, science checks and try-it experiments: the content / science team
- Characters Bit & Fathom: Ripple Parade — [YouTube](https://www.youtube.com/@RippleParade) · [X](https://x.com/RippleParade)
- App build: the team's coding agent

MIT licensed — see [LICENSE](LICENSE).
