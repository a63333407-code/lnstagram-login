#!/usr/bin/env python3
"""Batch 4: list every trim (spec) and its exterior colour facets for each Autohome series in raw_b4/autohome_series_inventory.json
with batch4_scope == HARVEST.  Same output schema as raw/autohome_specs.json; series key = '<Brand>:<series name>'.
Usage: python3 scrape_specs_b4.py <out_json>"""
import re, json, subprocess, sys, time, html, os, datetime
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = sys.argv[1]
INV = [r for r in json.load(open(os.path.join(HERE, "autohome_series_inventory.json"), encoding="utf-8")) if r["batch4_scope"] == "HARVEST"]
def get(url):
    for i in range(3):
        p = subprocess.run(["curl", "-sS", "-m", "40", "-A", "Mozilla/5.0", url], capture_output=True)
        if p.returncode == 0 and len(p.stdout) > 5000: return p.stdout.decode("gb18030", "ignore")
        time.sleep(2)
    return ""
def list_specs(page):
    specs = []
    for m in re.finditer(r'<dt>([^<]*)</dt><dd>(.*?)</dd>', page, re.S):
        for a in re.finditer(r'<a href="/pic/series-s(\d+)/(\d+)\.html[^"]*"[^>]*>\s*([^<]*)<span[^>]*>\(?(\d+)([^<]*)</span>(.*?)</a>', m.group(2), re.S):
            specs.append(dict(year=m.group(1), spec_id=a.group(1), label=html.unescape(a.group(3)).strip(), photos=int(a.group(4)), stopsale=("icon-stopsale" in a.group(6)), color_view=("icon16-rainbow" in a.group(6))))
    return specs
def one(r):
    sid = r["series_id"]; seen = {}; urls = {}
    for tag, url in (("series-t", f"https://car.autohome.com.cn/pic/series-t/{sid}.html"), ("series", f"https://car.autohome.com.cn/pic/series/{sid}.html")):
        pg = get(url); urls[tag] = url; time.sleep(0.3)
        for s in list_specs(pg):
            s["listed_on"] = [tag]
            if s["spec_id"] in seen: seen[s["spec_id"]]["listed_on"].append(tag)
            else: seen[s["spec_id"]] = s
    for sp in seen.values():
        u = f"https://car.autohome.com.cn/pic/series-s{sp['spec_id']}/{sid}-1.html"; pg = get(u); time.sleep(0.25)
        t = re.search(r'<title>([^<]*)', pg); sp["title"] = t.group(1).strip() if t else None; sp["url"] = u
        sp["colors"] = [dict(color_id=c.group(1), hex=c.group(2), name_zh=c.group(3).strip(), photos=int(c.group(4)))
            for c in re.finditer(r'<a href="/pic/spec-%s-(\d+)-[^"]*" class="color-cont[^"]*"[^>]*><em style="background-color:(#[0-9A-Fa-f]{3,6});?"></em><em class="carcolor-bg"></em>([^<]*)<span[^>]*>\((\d+)' % sp["spec_id"], pg)]
    print(r["brand"], r["series_name"], sid, "specs:", len(seen), file=sys.stderr, flush=True)
    return (f"{r['brand']}:{r['series_name']}", dict(brand=r["brand"], series_id=int(sid), series_name=r["series_name"], series_urls=urls, stopsale_series=r["stopsale"], specs=list(seen.values())))
with ThreadPoolExecutor(max_workers=6) as ex: res = dict(ex.map(one, INV))
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("series", len(res), "specs", sum(len(v["specs"]) for v in res.values()), file=sys.stderr)
