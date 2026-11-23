#!/usr/bin/env python3
"""Re-check harvest 'fetch_failed' records.  302 redirect to the trim landing page = category has no photos
(valid absence).  Anything else is retried and, if it works, parsed like harvest_images.py.
Usage: python3 retry_errors.py <dir containing autohome_images.jsonl>   -> autohome_images_retry.jsonl, category_status.json"""
import json, re, subprocess, sys, os, time, html
D = sys.argv[1]
LI = re.compile(r'<li><a href="(https://www\.autohome\.com\.cn/cars/imgs-[^"]*?/(\d+)\.html)[^"]*"[^>]*>\s*<img([^>]*)>', re.S)
def fetch(url):
    p = subprocess.run(["curl", "-sS", "-m", "40", "-A", "Mozilla/5.0", "-o", "-", "-w", "\n%{http_code}", url], capture_output=True)
    body, _, code = p.stdout.rpartition(b"\n")
    return int(code or 0), body.decode("gb18030", "ignore")
def parse(page):
    out = []
    for m in LI.finditer(page):
        t = re.search(r'(?:data-webp|data-original|src)="(//[^"]*autoimg[^"]*)"', m.group(3)); alt = re.search(r'alt="([^"]*)"', m.group(3))
        out.append(dict(photo_id=m.group(2), photo_page_url=m.group(1), thumb_url=("https:" + t.group(1)) if t else None, alt=html.unescape(alt.group(1)) if alt else None))
    return out
errs = {}
for line in open(os.path.join(D, "autohome_images.jsonl"), encoding="utf-8"):
    if '"error"' in line:
        e = json.loads(line); errs[(e["spec_id"], e["kind"], e["key"], e["url"])] = e
status = {}; new = []
for (spec, kind, key, url), e in errs.items():
    for attempt in range(3):
        code, body = fetch(url)
        if code in (301, 302): status[f"{spec}|{kind}|{key}"] = "empty_category (HTTP %d redirect to trim landing page)" % code; break
        if code == 200 and len(body) > 3000:
            ph = parse(body); status[f"{spec}|{kind}|{key}"] = "ok_page1_recovered" if ph else "empty_page"
            for i, p in enumerate(ph, 1): new.append(dict(spec_id=spec, series=None, kind=kind, key=key, position=i, list_url=url, **p))
            break
        time.sleep(3)
    else:
        status[f"{spec}|{kind}|{key}"] = "still_failing (last HTTP %s)" % code
    time.sleep(0.3)
with open(os.path.join(D, "autohome_images_retry.jsonl"), "w", encoding="utf-8") as f:
    for r in new: f.write(json.dumps(r, ensure_ascii=False) + "\n")
json.dump(status, open(os.path.join(D, "category_status.json"), "w"), ensure_ascii=False, indent=1)
import collections; print(collections.Counter(v.split(" ")[0] for v in status.values()), len(new))
