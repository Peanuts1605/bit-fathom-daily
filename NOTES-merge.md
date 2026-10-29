# Merge notes — web + app into one Daily Riddle

The playable game is the repo-root build (`src.html` → `index.html` and `dist/`). `app-src/` stays in the tree as the reference shell we merged from. Do not treat `app-src/www/riddles.js` as canonical.

## What moved

- Layout ideas from the app: bottom tabs (Today / Journal / Grown-ups), grown-up math gate, sound toggle, manifest, icon, service worker.
- Rules from the web: local date, epoch 12 Oct 2026 = puzzle #001, Encore after 14 days, archive arrows, `sync()` multi-tab merge, clock-skew (`lday` / future dates count as today). `window.__BF` is compiled in only when the build is run with `BF_TEST_HOOK=1` (check.sh sets that). A normal `python build.py` leaves the hook out, including on localhost and in Capacitor.
- Capacitor config now lives at the repo root with `webDir` set to `dist`. No native build was run.

## Storage

New key `bf-riddle-v2`: `{v:2, plays:{'Y-M-D':{id, tries, ok, t, done}}, streak, best, last, sound, haptics}`.

One-time migration on load (idempotent; old keys are not deleted):

- `bf-riddle-v1` `{ans:{date: index}}` becomes a finished play with that single try. Streak, best, and last carry over. Padded and unpadded dates match the existing `kday` rules.
- `bfdr.v1` `{h:{date:{id,g,ok}}, sound, best}` becomes finished plays (`tries:[g]`, `ok` kept as stored). `best` is the max of every source. `sound` is kept when v2 does not already have a preference.

The page also mirrors finished plays back into `bf-riddle-v1` so the existing streak, multi-tab, and clock-skew tests can keep reading that key. A mirror write is not a deletion.

## Tries

Up to `choices.length - 1` guesses. A wrong pick strikes that option out. The explainer, share grid, and guess distribution update when the pick is right or when the last miss is used. Playing today counts on the first guess, right or wrong. Archive days never move the streak.

## Share numbers

`#NNN` and `/r/NNN/` are the 1-based local day from the epoch (12 Oct 2026 = #001). #018 is 29 Oct 2026. The riddle content loops every 14 days; the puzzle number does not. The archive label, the share text, and the URL all use that puzzle number. An encore adds a separate “Encore of #id” chip for the looping riddle.

Static `/r/NNN/` pages and og cards are generated for every day from **#001 through 31 Jan 2027** (#112), plus `og/today.png`. The screen label uses that same puzzle number, including on an encore day (`Today's riddle #018` plus `Encore of #004`).

Share text and `og:url` use the build-time origin `BF_ORIGIN` (default `https://bit-fathom-daily-next.gigantic-stranger.workers.dev`), including on localhost and in Capacitor.

`/r/*` is handled by `worker/share-routes.js`, not by `_redirects`. workerd rejects `/r/* /r/fallback/index.html 200` as a loop, and `_redirects` run before assets, so a catch-all would hide the real pages. The Worker runs first for `/r/*`: it serves the asset when it exists, redirects a later puzzle number to `/?d=NNN`, sends a non-canonical number such as `/r/0029` to `/r/029/`, and returns the generic card for `/r/abc` and `/r/000`.

## Deploy (Workers Static Assets)

`wrangler.jsonc` is the deploy config. Name: `bit-fathom-daily-next`. Main: `worker/share-routes.js`. Assets: `publish/`, with `run_worker_first` for `/r/*`.

```
python3 build.py
npx wrangler dev --local
npx wrangler deploy
```

`build.py` writes `dist/` (the 2.5 MB HTML budget) and then `publish/` by copying `dist/` and merging `static-assets/og/` at `publish/og/` so `/og/NNN.png` resolves. Do not deploy from `./check.sh`. The inline packer in `review/gen.py` is retired: it ignored `_headers` and hardcoded `unsafe-inline`.

`./check.sh` builds twice. The first build sets `BF_TEST_HOOK=1` so the tests can call `window.__BF`. The second build leaves `index.html` without that hook. `BF_SKIP_OG=1` on the second build reuses cards already written in that same check; it prints the skip and does not run unless the variable is set. A normal `python build.py` always renders the cards and always requires pngquant. Review screenshots from the check go to a temp directory, so the check does not rewrite `review/share-loop/`.

## App-only riddles — candidates for #015+

Not imported. They have no `source_title` / `source_url` and need a content and science review first. Topics below are the app's labels.

| App id | Topic | Question (short) |
|---|---|---|
| 1 | Robots | Camera says red — does the robot see red? (near-duplicate of web #001; do not add twice) |
| 2 | Electricity | Tiny gadget, one long leg (near-duplicate of web #002) |
| 3 | Space | Mars sunset color (near-duplicate of web #003) |
| 4 | Space | Text to Voyager 1 (near-duplicate of web #004) |
| 5 | Robots | Robot vacuum stops at the stairs (cliff sensors) |
| 6 | Electricity | Birds on a power line |
| 7 | Space | Sunlight travel time to Earth |
| 8 | Colors | Why the daytime sky is blue |
| 9 | Robots | How lidar measures distance |
| 10 | Electricity | How hot a lightning bolt gets |
| 11 | Space | Planet whose day is longer than its year (near-duplicate of web #006) |
| 12 | Colors | Red light plus green light |
| 13 | Robots | Why Mars rovers are not driven live |
| 14 | Electricity | Why house wires wear plastic |
| 15 | Space | Footprints left on the Moon |
| 16 | Colors | Why grown flamingos are pink |

Near-duplicates of the canonical 14 should be dropped, not renumbered. The rest can become #015+ after sources and review.
