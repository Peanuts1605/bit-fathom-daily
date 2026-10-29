#!/usr/bin/env python3
"""__BF is a build flag, and the service worker cache is capped and versioned."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
fail = 0


def check(name, cond, detail=''):
    global fail
    fail += 0 if cond else 1
    print(('PASS ' if cond else 'FAIL ') + name + (f' ({detail})' if detail else ''))


src = (ROOT / 'src' / 'app.js').read_text()
built = (ROOT / 'dist' / 'index.html').read_text()
sw = (ROOT / 'src' / 'sw.js').read_text()
check('source uses the test-hook placeholder', 'if(%%TESTHOOK%%)' in src)
check('source does not gate the hook on hostname', 'location.hostname' not in src and '127.0.0.1' not in src)
check('built hook is the explicit flag', 'if(true)' in built and 'if(%%TESTHOOK%%)' not in built)
check('built page has no hostname gate', 'location.hostname' not in built)
check('sw cache is versioned', "const C='bf-riddle-share-v4'" in sw and 'caches.delete' in sw)
check('sw cache is capped', 'const MAX=8' in sw and 'shellRequest' in sw and 'keys.slice' in sw)
print('RESULT', 'PASS' if fail == 0 else f'FAIL ({fail})')
raise SystemExit(1 if fail else 0)
