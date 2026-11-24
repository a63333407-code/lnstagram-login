#!/usr/bin/env python3
"""Batch 4: collect the colour cards of every BYD model page of carross.eu (retailer catalog).  Records code(s), name, year range
(data-year-from/to, as stated by the retailer), swatch hex (display), card URL, page URL and fetch time.  Usage: python3 fetch_carross_b4.py <out_json>"""
import re, json, subprocess, sys, time, datetime, html
OUT = sys.argv[1]; UA = "research-bot/1.0 (catalog research)"
now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def get(u):
    for i in range(4):
        p = subprocess.run(["curl", "-sS", "-m", "60", "-L", "-A", UA, u], capture_output=True)
        if p.returncode == 0 and len(p.stdout) > 20000: return p.stdout.decode("utf-8", "ignore")
        time.sleep(5 * (i + 1))
    return ""
main = get("https://www.carross.eu/en/paint-byd-b221")
models = sorted(set(re.findall(r'href="(/en/paint-byd-[a-z0-9-]+-m\d+)"', main)))
rows = []
for m in models:
    url = "https://www.carross.eu" + m; p = get(url); t = now()
    h = re.search(r'All original colors <strong>([^<]*)</strong>', p)
    n = 0
    for codes, name, yf, yt, card in re.findall(r'<li data-family="[^"]*" data-codes="([^"]*)" data-name="([^"]*)"(?: data-year-from="(\d*)")?(?: data-year-to="(\d*)")?>(.*?)</li>', p, re.S):
        hx = re.search(r'background:\s*(#[0-9a-fA-F]{3,6})', card); href = re.search(r'href="([^"]*)"', card)
        rows.append(dict(model_slug=m.rsplit("/", 1)[1], model_label=html.unescape(h.group(1)) if h else None, page_url=url, code_raw=html.unescape(codes), name_raw=html.unescape(name),
                         year_from=yf or None, year_to=yt or None, swatch_hex=hx.group(1) if hx else None, card_url="https://www.carross.eu" + href.group(1) if href else None, fetched_utc=t)); n += 1
    print(m, n, file=sys.stderr, flush=True); time.sleep(1.5)
json.dump(dict(model_pages=models, rows=rows), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
