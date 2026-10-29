#!/usr/bin/env python3
"""Retired. This file used to pack the site into one Worker script.

That packer ignored _headers and _redirects and hardcoded a CSP with
unsafe-inline. Deploys go through wrangler.jsonc instead:

  python3 build.py
  npx wrangler dev --local
  npx wrangler deploy

Do not revive the packer.
"""
raise SystemExit('retired: use wrangler.jsonc (see NOTES-merge.md). This packer is not a deploy path.')
