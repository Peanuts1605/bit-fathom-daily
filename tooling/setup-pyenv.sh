#!/bin/bash
# tooling/setup-pyenv.sh: make this repo's own Python for check.sh at tooling/pyenv (git-ignored).
# Why "pyenv" and not .venv: on a box restart the store sync drops folders named venv/.venv/build/out/
# target/.cache/node_modules/__pycache__/dist, so a project env with one of those names silently vanishes.
# Usage:
#   bash tooling/setup-pyenv.sh                       # pip install the pinned Playwright (network: PyPI)
#   bash tooling/setup-pyenv.sh --offline-from DIR    # no network: copy the pinned packages out of an
#                                                     #   existing site-packages DIR that has playwright==1.64.0
# Browsers: the tests launch /usr/bin/google-chrome, so no `playwright install` is needed.
set -euo pipefail
cd "$(dirname "$0")"
PW=1.64.0
ENV=pyenv
[ -x "$ENV/bin/python" ] || python3 -m venv --without-pip "$ENV"
SP=$("$ENV/bin/python" -c 'import sysconfig;print(sysconfig.get_paths()["purelib"])')
if [ "${1:-}" = --offline-from ]; then
  src=${2:?usage: --offline-from /path/to/site-packages}
  [ -d "$src/playwright-$PW.dist-info" ] || { echo "FAIL $src has no playwright==$PW"; exit 2; }
  for p in playwright greenlet pyee typing_extensions.py playwright-$PW.dist-info greenlet-*.dist-info pyee-*.dist-info typing_extensions-*.dist-info; do
    cp -a "$src"/$p "$SP/"; done
  find "$SP" -name __pycache__ -type d -prune -exec rm -rf {} +
else
  "$ENV/bin/python" -m ensurepip -q && "$ENV/bin/python" -m pip install -q "playwright==$PW"
fi
PYTHONDONTWRITEBYTECODE=1 "$ENV/bin/python" -c "import importlib.metadata as m,playwright;print('OK tooling/pyenv playwright',m.version('playwright'))"
