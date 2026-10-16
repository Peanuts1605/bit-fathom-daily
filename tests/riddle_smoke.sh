#!/bin/bash
# Usage: riddle_smoke.sh <index.html> [live_url]  -> prints PASS/FAIL lines, exit 0 pass / 1 fail
f=${1:-/workspace/work/rigel-creative-lab/bit-fathom-riddle-001/index.html}; rc=0
[ -s "$f" ] && echo "PASS exists ($(wc -c <"$f") bytes)" || { echo "FAIL missing/empty $f"; exit 1; }
grep -qiE 'bit (&|&amp;) fathom' "$f" && echo "PASS name" || { echo "FAIL no 'Bit & Fathom'"; rc=1; }
yt=$(grep -oiE 'https?://(www\.)?(youtube\.com|youtu\.be)[^"'"'"' <>]*' "$f" | sort -u)
xl=$(grep -oiE 'https?://(www\.)?(x\.com|twitter\.com)[^"'"'"' <>]*' "$f" | sort -u)
[ -n "$yt" ] && echo "PASS youtube: $yt" || { echo "FAIL no YouTube link"; rc=1; }
[ -n "$xl" ] && echo "PASS x: $xl" || { echo "FAIL no X link"; rc=1; }
bad=$(grep -oiwE 'crypto|bitcoin|btc|eth|coinbase|kalshi|robinhood|wallet|token|maggy|maggie|rent|therapist|jennifer|juniper|naumio\.com|password|secret' "$f" | sort | uniq -c)
[ -z "$bad" ] && echo "PASS no banned strings" || { echo "FAIL banned strings:"; echo "$bad"; rc=1; }
python3 - "$f" <<'P' || rc=1
import sys,html.parser
class C(html.parser.HTMLParser):
    def __init__(s): super().__init__(); s.t=False
    def handle_starttag(s,t,a): s.t |= t=='title'
c=C(); c.feed(open(sys.argv[1]).read()); print("PASS parses" + ("" if c.t else " (warn: no <title>)"))
P
URL=${2:-}
if [ -n "$URL" ]; then
  code=$(curl -s -o /tmp/riddle_live.html -w '%{http_code}' -L --max-time 20 "$URL")
  if [ "$code" = 200 ] && grep -qiE 'bit (&|&amp;) fathom' /tmp/riddle_live.html && grep -qi RippleParade /tmp/riddle_live.html; then echo "PASS live $URL (200, content ok)"; else echo "FAIL live $URL (HTTP $code or content mismatch)"; rc=1; fi
fi
[ $rc = 0 ] && echo "RESULT PASS" || echo "RESULT FAIL"; exit $rc
