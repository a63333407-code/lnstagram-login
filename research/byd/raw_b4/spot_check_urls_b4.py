#!/usr/bin/env python3
"""Live check of a seeded random sample of stored batch-4 image URLs (run AFTER build_batch4_visual.py). Appends a section to
batch4/images/image_verification_report_b4.md and writes batch4/images/url_spot_check_b4.csv."""
import csv, gzip, os, random, subprocess, collections, datetime, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(HERE, "batch4", "images")
with gzip.open(os.path.join(D, "vehicle_images_b4.csv.gz"), "rt", encoding="utf-8") as f: img = list(csv.DictReader(f))
random.seed(20261124); jobs = []
for cat in ("exterior", "official_press", "interior_cockpit", "interior_seats"):
    pool = [r for r in img if r["image_category"] == cat]
    for r in random.sample(pool, min(25, len(pool))): jobs.append(("image_url", cat, r["image_id"], r["image_url"]))
    for r in random.sample(pool, min(10, len(pool))): jobs.append(("source_page_url", cat, r["image_id"], r["source_page_url"]))
for r in random.sample([r for r in img if r["color_gallery_photo_page_url"]], 10): jobs.append(("color_gallery_photo_page_url", "exterior", r["image_id"], r["color_gallery_photo_page_url"]))
def chk(j):
    kind, cat, ident, url = j
    for attempt in range(1, 6):
        p = subprocess.run(["curl", "-sS", "-m", "40", "-A", "research-bot/1.0 (catalog research)", "-L", "-o", "/dev/null", "-w", "%{http_code}|%{content_type}|%{size_download}", url], capture_output=True, text=True)
        code, ct, size = (p.stdout.split("|") + ["", "", ""])[:3]
        if code not in ("429", "000"): break
        time.sleep(15 * attempt)
    ok = code == "200" and ((ct.startswith("image/")) if kind == "image_url" else ("html" in ct))
    return dict(kind=kind, category=cat, id=ident, url=url, http=code, content_type=ct, bytes=size, status="OK" if ok else ("RATE_LIMITED_NOT_VERIFIED_LIVE" if code == "429" else "FAILED"), utc=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
with ThreadPoolExecutor(max_workers=4) as ex: res = list(ex.map(chk, jobs))
with open(os.path.join(D, "url_spot_check_b4.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(res[0])); w.writeheader(); w.writerows(res)
sec = "\n## Live URL spot check (seeded random sample, run after the build)\n\n| URL type | sampled | resolved OK (HTTP 200 + expected content type) | rate-limited, not verified live | failed |\n|---|---|---|---|---|\n"
for k in ("image_url", "source_page_url", "color_gallery_photo_page_url"):
    rs = [r for r in res if r["kind"] == k]; sec += f"| {k} | {len(rs)} | {sum(r['status']=='OK' for r in rs)} | {sum(r['status']=='RATE_LIMITED_NOT_VERIFIED_LIVE' for r in rs)} | {sum(r['status']=='FAILED' for r in rs)} |\n"
sec += "\nDetail per URL: `url_spot_check_b4.csv`.\n"
rp = os.path.join(D, "image_verification_report_b4.md"); t = open(rp, encoding="utf-8").read()
if "## Live URL spot check" in t: t = t[:t.index("\n## Live URL spot check")]
open(rp, "w", encoding="utf-8").write(t.rstrip("\n") + "\n" + sec); print(sec)
