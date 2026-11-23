#!/usr/bin/env python3
"""
Retry pass for the image harvest.  Finds every (trim, category) or (trim, colour gallery) whose harvested photo count does
not equal the count Autohome itself states (expected_counts.json for categories, the colour-facet count for colour galleries)
and re-fetches the WHOLE list with full pagination.  Results supersede the earlier records for that list.

HTTP semantics:  200 + photos = harvested.  301/302 = Autohome redirects to the trim landing page when a list has no photos:
this is recorded as 'redirect_no_photos' and is NEVER counted as a successful harvest.  Anything else is retried (3x) and, if it
keeps failing, logged as 'failed' (trim then becomes PARTIAL or FAILED_RETRY_REQUIRED).
Usage: python3 retry_failures.py <dir with autohome_images.jsonl + expected_counts.json> [round]
Writes: retry_records_<round>.jsonl, retry_log_<round>.jsonl (one line per HTTP attempt, UTC timestamps)
"""
import json, re, subprocess, sys, os, time, html, datetime, collections
from concurrent.futures import ThreadPoolExecutor
D = sys.argv[1]; ROUND = sys.argv[2] if len(sys.argv) > 2 else "1"
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = json.load(open(os.path.join(HERE, "autohome_specs.json"), encoding="utf-8"))
EXP = json.load(open(os.path.join(D, "expected_counts.json"), encoding="utf-8"))
LI = re.compile(r'<li><a href="(https://www\.autohome\.com\.cn/cars/imgs-[^"]*?/(\d+)\.html)[^"]*"[^>]*>\s*<img([^>]*)>', re.S)
CATKEY = {"exterior": "1", "official": "53", "cockpit": "10", "seats": "3"}
now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
LOGF = open(os.path.join(D, f"retry_log_{ROUND}.jsonl"), "w", encoding="utf-8")
def fetch(url):
    last = (0, "")
    for attempt in range(1, 4):
        p = subprocess.run(["curl", "-sS", "-m", "40", "-A", "Mozilla/5.0", "-o", "-", "-w", "\n%{http_code}", url], capture_output=True)
        body, _, code = p.stdout.rpartition(b"\n"); code = int(code or 0); txt = body.decode("gb18030", "ignore")
        outcome = "redirect_no_photos" if code in (301, 302) else ("ok" if code == 200 and len(txt) > 3000 else "failed")
        LOGF.write(json.dumps(dict(utc=now(), url=url, http=code, bytes=len(body), attempt=attempt, outcome=outcome, curl_rc=p.returncode)) + "\n"); LOGF.flush()
        last = (code, txt)
        if outcome != "failed": return outcome, txt
        time.sleep(3 * attempt)
    return "failed", last[1]
def parse(page):
    out = []
    for m in LI.finditer(page):
        t = re.search(r'(?:data-webp|data-original|src)="(//[^"]*autoimg[^"]*)"', m.group(3)); alt = re.search(r'alt="([^"]*)"', m.group(3))
        out.append(dict(photo_id=m.group(2), photo_page_url=m.group(1), thumb_url=("https:" + t.group(1)) if t else None, alt=html.unescape(alt.group(1)) if alt else None))
    return out
def refetch(job):
    spec, series, sid, kind, key = job
    seen = {}; recs = []; res = "ok"
    for pg in range(1, 15):
        if kind == "exterior_color": url = f"https://car.autohome.com.cn/pic/spec-{spec}-{key}-1-{pg}.html"
        else: url = f"https://car.autohome.com.cn/pic/series-s{spec}/{sid}-{key}" + (".html" if pg == 1 else f"-p{pg}.html")
        outcome, page = fetch(url); time.sleep(0.2)
        if outcome == "redirect_no_photos":
            if pg == 1: res = "redirect_no_photos"
            break
        if outcome == "failed": res = "failed"; break
        new = [p for p in parse(page) if p["photo_id"] not in seen]
        if not new: break
        for p in new:
            seen[p["photo_id"]] = 1
            recs.append(dict(spec_id=spec, series=series, kind=kind, key=key, position=len(recs) + 1, list_url=url, collected_utc=now(), **p))
    return dict(job=job, result=res, records=recs)

def current_counts():
    """photo ids per (spec, kind, key): main harvest, with any list re-fetched in a retry round replaced by the LAST round's result."""
    main = collections.defaultdict(set); replaced = {}
    for line in open(os.path.join(D, "autohome_images.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        if "error" not in r: main[(r["spec_id"], r["kind"], r["key"])].add(r["photo_id"])
    for f in sorted(x for x in os.listdir(D) if re.fullmatch(r"retry_records_\d+\.jsonl", x)):
        cur = None
        for line in open(os.path.join(D, f), encoding="utf-8"):
            r = json.loads(line)
            if r.get("_supersede"): cur = (r["spec_id"], r["kind"], r["key"]); replaced[cur] = set()
            elif cur: replaced[cur].add(r["photo_id"])
    out = {k: len(v) for k, v in main.items()}
    out.update({k: len(v) for k, v in replaced.items()})
    return out
if __name__ == "__main__":
    have = current_counts(); jobs = []
    for series, b in RAW.items():
        for sp in b["specs"]:
            spec = sp["spec_id"]
            if spec not in EXP or "error" in EXP[spec]: continue
            e = EXP[spec]
            for kind, key in CATKEY.items():
                if (e.get(kind) or 0) != have.get((spec, kind, key), 0): jobs.append((spec, series, b["series_id"], kind, key))
            for c in sp["colors"]:
                if c["photos"] != have.get((spec, "exterior_color", c["color_id"]), 0): jobs.append((spec, series, b["series_id"], "exterior_color", c["color_id"]))
    print("mismatching lists to retry:", len(jobs), file=sys.stderr, flush=True)
    with ThreadPoolExecutor(max_workers=4) as ex: results = list(ex.map(refetch, jobs))
    with open(os.path.join(D, f"retry_records_{ROUND}.jsonl"), "w", encoding="utf-8") as f:
        for r in results:
            spec, series, sid, kind, key = r["job"]
            f.write(json.dumps(dict(_supersede=True, spec_id=spec, kind=kind, key=key, retry_result=r["result"], collected_utc=now()), ensure_ascii=False) + "\n")
            for rec in r["records"]: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(collections.Counter(r["result"] for r in results), file=sys.stderr)
