#!/usr/bin/env python3
"""For every trim, read Autohome's OWN per-category photo totals from the trim landing page
(车身外观/中控方向盘/车厢座椅/其它细节/官图/车展/全部图片).  Used to judge harvest completeness.
Usage: python3 expected_counts.py <out_dir>   -> expected_counts.json  (failures recorded, retried 3x)"""
import json, re, subprocess, sys, os, time
from concurrent.futures import ThreadPoolExecutor
OUT = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
RAW = json.load(open(os.path.join(HERE, "autohome_specs.json"), encoding="utf-8"))
NAMES = {"车身外观": "exterior", "中控方向盘": "cockpit", "车厢座椅": "seats", "其它细节": "details", "官图": "official", "车展": "show"}
def get(url):
    p = subprocess.run(["curl", "-sS", "-m", "40", "-A", "Mozilla/5.0", "-o", "-", "-w", "\n%{http_code}", url], capture_output=True)
    body, _, code = p.stdout.rpartition(b"\n"); return int(code or 0), body.decode("gb18030", "ignore")
def one(a):
    series, sid, sp = a; spec = sp["spec_id"]; url = f"https://car.autohome.com.cn/pic/series-s{spec}/{sid}.html"
    for i in range(3):
        code, s = get(url)
        if code == 200 and len(s) > 5000:
            d = {}
            for k, v in NAMES.items():
                m = re.search(r'%s(?:<span[^>]*>)?\s*[\(（](\d+)张[\)）]' % k, s)
                d[v] = int(m.group(1)) if m else None
            m = re.search(r'全部图片\s*(?:<[^>]*>\s*)*[\(（](\d+)[\)）]', s)
            d["all"] = int(m.group(1)) if m else None
            d.update(spec_id=spec, series=series, url=url, http=code); time.sleep(0.2); return d
        time.sleep(2)
    return dict(spec_id=spec, series=series, url=url, http=code, error="landing page not retrieved")
jobs = [(s, b["series_id"], sp) for s, b in RAW.items() for sp in b["specs"] if not re.search(r"概念|Concept|ocean-X", sp["label"], re.I)]
with ThreadPoolExecutor(max_workers=3) as ex: res = list(ex.map(one, jobs))
json.dump({r["spec_id"]: r for r in res}, open(os.path.join(OUT, "expected_counts.json"), "w"), ensure_ascii=False, indent=1)
print(len(res), "errors:", sum(1 for r in res if "error" in r))
