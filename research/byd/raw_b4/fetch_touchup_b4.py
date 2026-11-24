#!/usr/bin/env python3
"""Batch 4: collect colour-code swatches from every BYD model page of touchuppaintfactory.com (retailer catalog).
Records exactly what the page lists: code string(s) (data-details), colour name(s) (swatch title), swatch hex (display colour), page URL and fetch time.
No year information is exposed on the page.  Usage: python3 fetch_touchup_b4.py <out_json>"""
import re, json, subprocess, sys, time, datetime, html
OUT = sys.argv[1]
UA = "research-bot/1.0 (catalog research)"
now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def get(u):
    for i in range(4):
        p = subprocess.run(["curl", "-sS", "-m", "60", "-L", "-A", UA, u], capture_output=True)
        if p.returncode == 0 and len(p.stdout) > 20000: return p.stdout.decode("utf-8", "ignore")
        time.sleep(5 * (i + 1))
    return ""
brand = get("https://touchuppaintfactory.com/brands/byd/")
slugs = sorted(set(re.findall(r'https://touchuppaintfactory\.com/brands/byd/([a-z0-9-]+)/', brand)))
slugs = [s for s in slugs if s in ("all-models",) or not re.search(r'-(?:[a-z]{2,4}|[a-z0-9]{3}(?:-[a-z0-9]+)*)$', s) or True]
model_pages = []
# model slugs are the ones listed in the model selector (short slugs); colour slugs are long.  Take slugs without a hex-like code tail.
for s in slugs:
    if len(s) <= 22: model_pages.append(s)
out = []
for slug in model_pages:
    url = f"https://touchuppaintfactory.com/brands/byd/{slug}/"; page = get(url); t = now()
    items = re.findall(r'<a href="([^"]*)" class="[^"]*swatch-item"[^>]*?data-details="([^"]*)">(.*?)</a>', page, re.S)
    for href, det, inner in items:
        name = re.search(r'<h6[^>]*>(.*?)</h6>', inner, re.S); hx = re.search(r'background:\s*(#[0-9a-fA-F]{3,6})', inner)
        out.append(dict(model_slug=slug, page_url=url, code_raw=html.unescape(det), names_raw=html.unescape(re.sub(r'\s+', ' ', name.group(1)).strip()) if name else None, swatch_hex=hx.group(1) if hx else None, swatch_page_url=href, fetched_utc=t))
    print(slug, len(items), file=sys.stderr, flush=True); time.sleep(1.5)
json.dump(dict(model_pages=model_pages, rows=out), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
