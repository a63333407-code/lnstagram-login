#!/usr/bin/env python3
"""
Harvest image METADATA (URLs only, no image files) from Autohome picture galleries for every trim in
raw/autohome_specs.json.  Output: raw/autohome_images.jsonl and raw/autohome_interior_colors.json

For each spec (exact 款型 = exact model year + trim):
  category 1  外观      exterior gallery
  category 10 中控方向盘 dashboard / steering wheel / centre console area
  category 3  车厢座椅   seats / cabin
  category 53 官图      official press images
  colour-filtered exterior gallery for each observed exterior colour (spec-<spec>-<colorId>-1-<page>)
  interior-colour-filtered cockpit gallery for each interior colour option (spec-<spec>-i<id>-10-<page>)
Pages are GBK-encoded; decoded with gb18030.  Politeness: 8 workers, short delay per request. Interior-colour-filtered galleries are skipped unless HARVEST_INTERIOR_COLOR_GALLERIES=1 (interior colour facets are still recorded).

Usage: python3 harvest_images.py <out_dir>
"""
import re, json, sys, os, time, subprocess, html, threading
from concurrent.futures import ThreadPoolExecutor

OUT = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = json.load(open(os.path.join(HERE, "autohome_specs.json"), encoding="utf-8"))
UA = "Mozilla/5.0"
LOCK = threading.Lock()
MAXPAGES = 12

def get(url):
    for i in range(3):
        p = subprocess.run(["curl", "-sS", "-m", "40", "-A", UA, url], capture_output=True)
        if p.returncode == 0 and len(p.stdout) > 3000:
            time.sleep(0.15)
            return p.stdout.decode("gb18030", "ignore")
        time.sleep(1.5)
    return ""

LI = re.compile(r'<li><a href="(https://www\.autohome\.com\.cn/cars/imgs-[^"]*?/(\d+)\.html)[^"]*"[^>]*>\s*<img([^>]*)>', re.S)
def parse_photos(page):
    out = []
    for m in LI.finditer(page):
        attrs = m.group(3)
        t = re.search(r'(?:data-webp|data-original|src)="(//[^"]*autoimg[^"]*)"', attrs)
        alt = re.search(r'alt="([^"]*)"', attrs)
        out.append(dict(photo_id=m.group(2), photo_page_url=m.group(1), thumb_url=("https:" + t.group(1)) if t else None,
                        alt=html.unescape(alt.group(1)) if alt else None))
    return out

def FACET(page, spec, prefix):
    # facet links: /pic/spec-<spec>-<prefix><id>-<cat>-1.html ... class="color-cont" with swatch hex and (N张)
    res = []
    for m in re.finditer(r'<a href="/pic/spec-%s-%s(\d+)-[^"]*" class="color-cont[^"]*"[^>]*><em style="background-color:(#[0-9A-Fa-f]{3,6});?"></em><em class="carcolor-bg"></em>([^<]*)<span[^>]*>\((\d+)' % (spec, prefix), page):
        res.append(dict(facet_id=prefix + m.group(1), hex=m.group(2), name_zh=m.group(3).strip(), photos=int(m.group(4))))
    return res

def paged(url_for_page, series, spec, kind, key, sink):
    seen = set(); pos = 0
    for pg in range(1, MAXPAGES + 1):
        url = url_for_page(pg)
        page = get(url)
        if not page:
            sink.append(dict(error="fetch_failed", spec_id=spec, kind=kind, key=key, url=url)); break
        photos = [p for p in parse_photos(page) if p["photo_id"] not in seen]
        if not photos: break
        for p in photos:
            seen.add(p["photo_id"]); pos += 1
            sink.append(dict(spec_id=spec, series=series, kind=kind, key=key, position=pos, list_url=url, **p))
        if pg == 1:
            first_page = page
    return pos

def do_spec(args):
    series, sid, sp = args
    spec = sp["spec_id"]; recs = []; inner = {}
    for cat, kind in ((1, "exterior"), (53, "official"), (10, "cockpit"), (3, "seats")):
        base = f"https://car.autohome.com.cn/pic/series-s{spec}/{sid}-{cat}"
        n = paged(lambda pg, b=base: b + (".html" if pg == 1 else f"-p{pg}.html"), series, spec, kind, str(cat), recs)
        if cat in (10, 3):
            page1 = get(base + ".html")
            inner[kind] = FACET(page1, spec, "i")
    for c in sp["colors"]:
        cid = c["color_id"]
        paged(lambda pg, cid=cid: f"https://car.autohome.com.cn/pic/spec-{spec}-{cid}-1-{pg}.html", series, spec, "exterior_color", cid, recs)
    for ic in (inner.get("cockpit", []) if os.environ.get("HARVEST_INTERIOR_COLOR_GALLERIES") == "1" else []):
        iid = ic["facet_id"]
        paged(lambda pg, iid=iid: f"https://car.autohome.com.cn/pic/spec-{spec}-{iid}-10-{pg}.html", series, spec, "interior_color_cockpit", iid, recs)
    with LOCK:
        with open(os.path.join(OUT, "autohome_images.jsonl"), "a", encoding="utf-8") as f:
            for r in recs: f.write(json.dumps(r, ensure_ascii=False) + "\n")
        icf = os.path.join(OUT, "autohome_interior_colors.json")
        cur = json.load(open(icf, encoding="utf-8")) if os.path.exists(icf) else {}
        cur[spec] = inner
        json.dump(cur, open(icf, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"{series} spec {spec}: {len(recs)} records", file=sys.stderr, flush=True)
    return len(recs)

if __name__ == "__main__":
    done = set()
    jl = os.path.join(OUT, "autohome_images.jsonl")
    if os.path.exists(jl):
        for line in open(jl, encoding="utf-8"):
            try: done.add(json.loads(line)["spec_id"])
            except Exception: pass
    jobs = []
    for series, blk in RAW.items():
        for sp in blk["specs"]:
            if re.search(r"概念|Concept|ocean-X", sp["label"], re.I): continue
            if sp["spec_id"] in done: continue
            jobs.append((series, blk["series_id"], sp))
    print("jobs", len(jobs), "already done", len(done), file=sys.stderr, flush=True)
    with ThreadPoolExecutor(max_workers=int(os.environ.get('HARVEST_WORKERS', '8'))) as ex:
        total = sum(ex.map(do_spec, jobs))
    print("TOTAL records", total, file=sys.stderr)
