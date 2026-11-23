#!/usr/bin/env python3
"""Live check of a seeded random sample of stored URLs (images by category, photo pages, all logos). Appends a section to
image_verification_report.md and writes url_spot_check.csv.  Run AFTER build_batch3_visual.py."""
import csv, os, random, subprocess, collections, datetime
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
img = list(csv.DictReader(open(os.path.join(HERE, "vehicle_images.csv"), encoding="utf-8")))
logos = list(csv.DictReader(open(os.path.join(HERE, "brand_logos.csv"), encoding="utf-8")))
random.seed(20261123); jobs = []
for cat in ("exterior", "official_press", "interior_cockpit", "interior_seats"):
    pool = [r for r in img if r["image_category"] == cat]
    for r in random.sample(pool, 25):
        jobs.append(("image_url", cat, r["image_id"], r["image_url"])); 
    for r in random.sample(pool, 10): jobs.append(("source_page_url", cat, r["image_id"], r["source_page_url"]))
for r in random.sample([r for r in img if r["color_gallery_photo_page_url"]], 10): jobs.append(("color_gallery_photo_page_url", "exterior", r["image_id"], r["color_gallery_photo_page_url"]))
for l in logos: jobs.append(("logo_url", "logo", l["logo_id"], l["logo_url"]))
logo_jobs = [j for j in jobs if j[0] == "logo_url"]; jobs = [j for j in jobs if j[0] != "logo_url"]
def chk(j):
    kind, cat, ident, url = j
    import time
    for attempt in range(1, 6):
        p = subprocess.run(["curl", "-sS", "-m", "40", "-A", "research-bot/1.0 (catalog research)", "-L", "-o", "/dev/null", "-w", "%{http_code}|%{content_type}|%{size_download}", url], capture_output=True, text=True)
        code, ct, size = (p.stdout.split("|") + ["", "", ""])[:3]
        if code not in ("429", "000"): break
        time.sleep(20 * attempt)   # 429 = rate limited by the host; 000 = connection reset: both are retried, neither means a broken URL
    ok = (code == "200") and ((ct.startswith("image/")) if kind in ("image_url", "logo_url") else ("html" in ct))
    status = "OK" if ok else ("RATE_LIMITED_NOT_VERIFIED_LIVE" if code == "429" else "FAILED")
    return dict(kind=kind, category=cat, id=ident, url=url, http=code, content_type=ct, bytes=size, ok=ok, status=status, utc=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
with ThreadPoolExecutor(max_workers=4) as ex: res = list(ex.map(chk, jobs))
res += [chk(j) for j in logo_jobs]   # logos one at a time: Wikimedia rate-limits parallel requests
with open(os.path.join(HERE, "url_spot_check.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(res[0])); w.writeheader(); w.writerows(res)
c = collections.Counter((r["kind"], r["ok"]) for r in res)
sec = "\n## Live URL spot check (seeded random sample, run after the build)\n\n| URL type | sampled | resolved OK (HTTP 200 + expected content type) | rate-limited, not verified live | failed |\n|---|---|---|---|---|\n"
for k in ("image_url", "source_page_url", "color_gallery_photo_page_url", "logo_url"):
    rs = [r for r in res if r["kind"] == k]; sec += f"| {k} | {len(rs)} | {sum(r['status']=='OK' for r in rs)} | {sum(r['status']=='RATE_LIMITED_NOT_VERIFIED_LIVE' for r in rs)} | {sum(r['status']=='FAILED' for r in rs)} |\n"
sec += f"\nDetail per URL: `url_spot_check.csv`. A 429 means the host throttled this machine; the URL itself was returned by the MediaWiki API (see brand_logos.csv) but could not be re-fetched live in this run.\n"
rp = os.path.join(HERE, "image_verification_report.md"); t = open(rp, encoding="utf-8").read()
if "## Live URL spot check" in t: t = t[:t.index("\n## Live URL spot check")]
open(rp, "w", encoding="utf-8").write(t.rstrip("\n") + "\n" + sec); print(sec)
