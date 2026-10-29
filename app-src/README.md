# app-src: snapshot of the Daily Riddle app version (PWA shell)

Imported 2026-10-29 from the team's local build folder for the share-loop merge (UPGRADE #2).
This is a reference snapshot to merge FROM, not the shipping build. Deploy scripts and screenshots
from the original folder are intentionally not included.

- `www/`: static PWA (index.html, riddles.js, sw.js, manifest.json, icon.svg). Riddle numbering here
  (START = Oct 16, 2026) is NOT the canonical one; the canonical numbering is `riddles.json` (#001 = Oct 12, 2026).
- `capacitor.config.json`, `package.json`: Capacitor wrapper config (no native project).
