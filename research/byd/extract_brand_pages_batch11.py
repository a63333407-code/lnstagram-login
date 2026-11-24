#!/usr/bin/env python3
"""
Batch 11 helper: record the exterior-colour NAMES that official Denza / Yangwang / Fangchengbao model pages embed in their static HTML.

Usage: python3 extract_brand_pages_batch11.py <dir-with-fetched-html> <brand_pages_fetch.json>
Writes research/byd/batch11/raw/brand_colour_pages.json.  Only names found inside the pages' own structured data are kept
(Denza: "colorName"; Yangwang: image entries with "text" whose image path says waiguan = exterior / interior; Fangchengbao: "color":{...,"name":{"text":...}}).
No script/API behind the pages is called; the HTML is not stored, only its sha256 and the extracted names.
"""
import os, re, sys, json, hashlib, html

SRC, META = sys.argv[1], sys.argv[2]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batch11", "raw"); os.makedirs(OUT, exist_ok=True)
meta = json.load(open(META, encoding="utf-8"))
res = []
for m in meta:
    if m["http"] != "200": continue
    f = os.path.join(SRC, re.sub(r"[^A-Za-z0-9]", "_", m["url"]) + ".dat")
    data = open(f, "rb").read(); raw = html.unescape(data.decode("utf-8", "ignore")); names = []
    if m["brand"] == "denza":
        for mm in re.finditer(r'"colorName":"([^"]+)"(?:,"colorIcon":"[^"]*")?(?:,"staticImage":"([^"]*)")?', raw): names.append((mm.group(1), "exterior (rendered sequence frames)", (mm.group(2) or "")[-60:]))
    elif m["brand"] == "yangwang":
        for mm in re.finditer(r'"imgPc":"([^"]*)","imgMob":"[^"]*","text":"([^"]+)","paginationImg"', raw):
            p = mm.group(1); kind = "exterior" if "waiguan" in p else ("interior" if "interior" in p else "unclassified")
            names.append((mm.group(2), kind, p[-60:]))
    else:
        for mm in re.finditer(r'"color":\{"img":"([^"]*)","name":\{"text":"([^"]+)"\}', raw): names.append((mm.group(2), "body colour section (车色)", mm.group(1)[-60:]))
    seen = set(); uniq = []
    for n, k, p in names:
        if (n, k) not in seen: seen.add((n, k)); uniq.append(dict(name=n, kind=k, path_hint=p))
    res.append(dict(brand=m["brand"], url=m["url"], http=m["http"], bytes=m["bytes"], title=m["title"], sha256=hashlib.sha256(data).hexdigest(), colour_entries=uniq, retrieved="2026-11-24"))
json.dump(res, open(os.path.join(OUT, "brand_colour_pages.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for r in res: print(r["brand"], r["url"].split("/")[-1], len(r["colour_entries"]), [(e["name"], e["kind"][:3]) for e in r["colour_entries"]][:14])
