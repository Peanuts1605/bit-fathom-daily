#!/usr/bin/env python3
"""Validate riddles.json for the Bit & Fathom daily-riddle app."""
import json, re, sys, subprocess, pathlib
P = pathlib.Path(__file__).with_name("riddles.json")
KEYS = ["id","title","question","choices","answer_index","explainer","try_it","source_title","source_url","speaker"]
BANNED = r"\b(crypto\w*|bitcoin|ethereum|blockchain|nft|token|wallet|money|dollars?|cash|price|buy|sell|invest\w*|stocks?|maggy|jennifer|naumio|password|kill|die|blood)\b|\$"
errs = []
d = json.load(open(P))
if not isinstance(d, list) or len(d) != 14: errs.append(f"expected list of 14, got {len(d)}")
ids = [r.get("id") for r in d]
if ids != [f"{i:03d}" for i in range(1,15)]: errs.append(f"ids wrong: {ids}")
titles = [r.get("title","").strip().lower() for r in d]
if len(set(titles)) != len(titles): errs.append("duplicate titles")
for r in d:
    i = r.get("id")
    if list(r.keys()) != KEYS: errs.append(f"{i}: keys {list(r.keys())}")
    for k in KEYS:
        if k == "answer_index": continue
        if k == "choices":
            if not (isinstance(r[k], list) and 3 <= len(r[k]) <= 4 and all(isinstance(c,str) and c.strip() for c in r[k])): errs.append(f"{i}: bad choices")
            elif len(set(r[k])) != len(r[k]): errs.append(f"{i}: duplicate choices")
        elif not (isinstance(r[k], str) and r[k].strip()): errs.append(f"{i}: empty/non-string {k}")
    a = r.get("answer_index")
    if not (type(a) is int and 0 <= a < len(r.get("choices",[]))): errs.append(f"{i}: bad answer_index")
    if r.get("speaker") not in ("bit","fathom"): errs.append(f"{i}: bad speaker")
    n = len([s for s in re.split(r"(?<=[.!?])\s+", r.get("explainer","").strip()) if s])
    if n > 3: errs.append(f"{i}: explainer has {n} sentences")
    text = " ".join(str(v) for k,v in r.items() if k != "source_url")
    m = re.findall(BANNED, text, re.I)
    if m: errs.append(f"{i}: banned words {m}")
    code = subprocess.run(["curl","-sL","-A","Mozilla/5.0","-o","/dev/null","-w","%{http_code}","--max-time","25",r["source_url"]],capture_output=True,text=True).stdout
    print(f"{i} {code} {r['source_url']}")
    if code != "200": errs.append(f"{i}: source_url returned {code}")
print("answer_index distribution:", {k: [r['answer_index'] for r in d].count(k) for k in range(4)})
if errs:
    print("FAIL"); [print(" -", e) for e in errs]; sys.exit(1)
print("PASS: 14 riddles valid")
