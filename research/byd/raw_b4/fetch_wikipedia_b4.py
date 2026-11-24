#!/usr/bin/env python3
"""Batch 4: fetch the English-Wikipedia article of every model linked from the 'List of BYD Auto vehicles' table and parse infoboxes.
Output: wikipedia_infoboxes_b4.json (+ wikitext cached in <cache_dir>, not committed).  Usage: python3 fetch_wikipedia_b4.py <cache_dir> <out_json>"""
import re, json, subprocess, sys, os, time, datetime, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); CACHE, OUT = sys.argv[1], sys.argv[2]; os.makedirs(CACHE, exist_ok=True)
lst = open(os.path.join(HERE, "wikipedia_list_wikitext.txt"), encoding="utf-8").read()
pages = {}
for t, d in re.findall(r'\[\[([^\]|#]+)(?:\|([^\]]+))?\]\]', lst):
    t = t.strip()
    if ":" in t or not re.search(r'^(BYD|Denza|Yangwang|Fangchengbao|Linghui)', t): continue
    if t in ("BYD Auto", "Denza", "Fangchengbao", "Linghui", "Yangwang", "BYD Seal (nameplate)"): continue
    if re.search(r'BYD (8TT|B series|C9|K9|E-Vali|T3|V3)$', t): continue   # commercial
    pages.setdefault(t, set()).add(re.sub(r'\{\{nowrap\|([^}]*)\}\}', r'\1', d or t).strip())
def raw(t):
    p = os.path.join(CACHE, urllib.parse.quote(t, safe="") + ".txt")
    if os.path.exists(p): return open(p, encoding="utf-8").read(), None
    for i in range(7):
        s = subprocess.run(["curl", "-sS", "-m", "60", "-A", "research-bot/1.0 (catalog research)", f"https://en.wikipedia.org/w/index.php?title={urllib.parse.quote(t.replace(' ', '_'))}&action=raw"], capture_output=True).stdout.decode("utf-8", "ignore")
        if s and not s.lstrip().startswith("<!DOCTYPE") and "Too Many Requests" not in s[:300] and "rate" not in s[:120].lower():
            open(p, "w", encoding="utf-8").write(s); return s, datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        time.sleep(8 * (i + 1))
    return None, None
def boxes(s):
    res = []
    for m in re.finditer(r'\{\{\s*Infobox (?:automobile|car|electric vehicle)', s, re.I):
        i = m.start(); depth = 0; j = i
        while j < len(s):
            if s.startswith("{{", j): depth += 1; j += 2
            elif s.startswith("}}", j):
                depth -= 1; j += 2
                if depth == 0: break
            else: j += 1
        res.append(s[i:j])
    return res
def fields(b):
    d = {}; cur = None
    for line in b.split("\n"):
        m = re.match(r'\|\s*([a-z_0-9 ]+?)\s*=(.*)', line)
        if m: cur = m.group(1).strip(); d[cur] = m.group(2)
        elif cur: d[cur] += " " + line
    return {k: re.sub(r'\s+', ' ', v).strip() for k, v in d.items()}
def clean(v):
    if not v: return None
    def cv(m):
        p = [x for x in m.group(1).split("|") if "=" not in x]; units = {"mm", "m", "cm", "kg", "lb", "in", "km", "kW", "PS", "hp"}; nums = []; unit = ""
        for x in p:
            if x in units: unit = x; break
            nums.append(x)
        return "".join(nums) + (" " + unit if unit else "")
    v = re.sub(r'\{\{\s*(?:convert|cvt)\s*\|([^{}]*)\}\}', cv, v, flags=re.I)
    v = re.sub(r'\{\{\s*(?:unbulleted list|ubl|plainlist|flatlist)\s*\|?', "", v, flags=re.I)
    v = re.sub(r'<ref[^>]*>.*?</ref>|<ref[^>]*/>', '', v, flags=re.S)
    v = re.sub(r'\}\}|\{\{|\[\[|\]\]|<br\s*/?>|<[^>]*>', "; ", v); v = re.sub(r'\|', "; ", v); v = re.sub(r'(;\s*)+', "; ", v).strip("; ").strip()
    return v or None
out = []; failed = []; redirects = []
def resolve(t):
    """fetch article, following up to 2 #REDIRECTs; returns (final_title, text, fetched_utc)"""
    s, ts = raw(t); hops = 0
    while s is not None and re.match(r'\s*#redirect', s, re.I) and hops < 2:
        m = re.search(r'\[\[([^\]|#]+)(?:#([^\]|]*))?', s); tgt = m.group(1).replace("_", " ").strip(); sec = m.group(2)
        redirects.append(dict(page=t, redirect_to=tgt, redirect_section=sec, wikitext=re.sub(r'\s+', ' ', s[:200])))
        t = tgt; s, ts2 = raw(t); ts = ts2 or ts; hops += 1; time.sleep(1.5)
    return t, s, ts
for t0 in sorted(pages):
    t, s, ts = resolve(t0)
    if s is None: failed.append(t0); continue
    sd = re.search(r'\{\{\s*Short description\s*\|([^}]*)\}\}', s, re.I)
    for bi, b in enumerate(boxes(s)):
        f = fields(b); rec = dict(requested_page=t0, page=t, page_url="https://en.wikipedia.org/wiki/" + urllib.parse.quote(t.replace(" ", "_")), listed_as=sorted(pages[t0]), infobox_index=bi, fetched_utc=ts, short_description=sd.group(1).strip() if sd else None)
        for k in ["name", "production", "model_years", "body_style", "class", "layout", "wheelbase", "length", "width", "height", "weight", "assembly", "predecessor", "successor"]: rec[k] = clean(f.get(k))
        out.append(rec)
    if not boxes(s): out.append(dict(requested_page=t0, page=t, page_url="https://en.wikipedia.org/wiki/" + urllib.parse.quote(t.replace(" ", "_")), listed_as=sorted(pages[t0]), infobox_index=None, fetched_utc=ts, short_description=sd.group(1).strip() if sd else None, note="no infobox found"))
    time.sleep(1.5)
json.dump(dict(pages=len(pages), failed=failed, redirects=redirects, infoboxes=out), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("pages", len(pages), "infoboxes", len(out), "failed", failed, file=sys.stderr)
