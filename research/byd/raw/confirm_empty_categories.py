#!/usr/bin/env python3
"""For every (trim, category) whose tab is ABSENT on the Autohome landing page (expected count None), request the category list
URL without following redirects and record the HTTP status + UTC time.  HTTP 301/302 (redirect to the trim landing page) = Autohome
serves no photo list = category confirmed empty.  This is evidence of ABSENCE, never counted as a successful harvest.
A 200 with photos would be flagged as a mismatch.   Usage: python3 confirm_empty_categories.py <dir with expected_counts.json> <out jsonl>"""
import json, re, subprocess, sys, os, time, datetime
from concurrent.futures import ThreadPoolExecutor
D, OUT = sys.argv[1], sys.argv[2]; HERE = os.path.dirname(os.path.abspath(__file__))
RAW = json.load(open(os.path.join(HERE, "autohome_specs.json"), encoding="utf-8")); EXP = json.load(open(os.path.join(D, "expected_counts.json"), encoding="utf-8"))
KEY = {"exterior": "1", "official": "53", "cockpit": "10", "seats": "3"}
sid = {sp["spec_id"]: b["series_id"] for s, b in RAW.items() for sp in b["specs"]}
now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def one(job):
    spec, kind = job; url = f"https://car.autohome.com.cn/pic/series-s{spec}/{sid[spec]}-{KEY[kind]}.html"
    for attempt in range(1, 4):
        p = subprocess.run(["curl", "-sS", "-m", "40", "-A", "Mozilla/5.0", "-o", "-", "-w", "\n%{http_code}|%{redirect_url}", url], capture_output=True)
        body, _, tail = p.stdout.rpartition(b"\n"); code, _, loc = tail.decode().partition("|"); code = int(code or 0)
        n = len(re.findall(rb'<li><a href="https://www\.autohome\.com\.cn/cars/imgs-', body))
        if code in (301, 302, 200): break
        time.sleep(3)
    time.sleep(0.15)
    return dict(spec_id=spec, kind=kind, url=url, http=code, redirect_to=loc or None, photo_links_in_body=n, utc=now(), attempts=attempt,
                outcome=("confirmed_empty_redirect" if code in (301, 302) else ("MISMATCH_photos_served" if code == 200 and n else ("empty_page_200" if code == 200 else "failed"))))
jobs = [(sp, k) for sp, e in EXP.items() if "error" not in e for k in KEY if e.get(k) is None]
with ThreadPoolExecutor(max_workers=4) as ex: res = list(ex.map(one, jobs))
with open(OUT, "w", encoding="utf-8") as f:
    for r in res: f.write(json.dumps(r, ensure_ascii=False) + "\n")
import collections; print(len(res), collections.Counter(r["outcome"] for r in res))
