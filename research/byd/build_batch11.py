#!/usr/bin/env python3
"""
Batch 11 - field evidence ingestion & model-year colour catalogue (BYD Group).  Reproducible build.

Research only.  No field evidence was supplied, so every verification slot is PENDING.  Official colour NAMES were extracted from
official BYD-hosted brochures (batch11/raw/official_colour_extracts.json); an official colour name is NOT paint-code evidence.
Codes are never copied between models; name-only associations are flagged, never deleted.

Inputs (read-only): catalog_union/*, batch5/oem_paint_codes.csv, batch6|7/discovered_codes.csv, batch8/verification_results.csv,
                    batch10/{model_year_consistency,colour_conflict_audit,evidence_requirements}.csv, batch11/raw/*.json
Outputs: batch11/{official_colour_tables, model_year_colour_catalog, field_evidence_register, code_link_quality_audit, priority_conflict_updates, source_audit}.csv, stats_batch11.json
"""
import csv, os, re, json, collections
from pypinyin import lazy_pinyin

HERE = os.path.dirname(os.path.abspath(__file__)); U = f"{HERE}/catalog_union"
B5, B6, B7, B8, B10, B11 = (f"{HERE}/batch{i}" for i in (5, 6, 7, 8, 10, 11)); RAW = f"{B11}/raw"
TODAY = "2026-11-24"


def rd(p):
    with open(p, encoding="utf-8", newline="") as f: return list(csv.DictReader(f))


def wr(name, rows, fields):
    with open(f"{B11}/{name}", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in fields})


brands = {b["brand_id"]: b["name"] for b in rd(f"{U}/brands_all.csv")}
models = {m["model_id"]: m for m in rd(f"{U}/models_all.csv")}
gens = {g["generation_id"]: g for g in rd(f"{U}/generations_all.csv")}
years = {y["model_year_id"]: y for y in rd(f"{U}/model_years_all.csv")}
cols = {c["color_id"]: c for c in rd(f"{U}/factory_colors_all.csv")}
trims = rd(f"{U}/trims_all.csv"); trim_by_spec = collections.defaultdict(list)
for t in trims: trim_by_spec[t["autohome_spec_id"]].append(t)
cands = rd(f"{U}/paint_code_candidates_all.csv")
docs = json.load(open(f"{RAW}/official_colour_extracts.json", encoding="utf-8")); cnp = json.load(open(f"{RAW}/cn_model_pages_fetch.json", encoding="utf-8"))
bp = json.load(open(f"{RAW}/brand_colour_pages.json", encoding="utf-8")); bpf = json.load(open(f"{RAW}/brand_pages_fetch.json", encoding="utf-8"))
REF_RE = re.compile(r"BYH[A-Z]-\d+|BYD\d{2,}[A-Z0-9]*")
def tokens(raw): return {t.strip().upper() for t in re.split(r"[;,/]+|\s+\|\s+", raw or "") if t.strip()}
def nk(s): return re.sub(r"[^a-z0-9]", "", (s or "").lower())
def iso(d):
    import datetime
    try: return datetime.datetime.strptime(" ".join(d.split()[1:]).replace(" UTC", ""), "%b %d %H:%M:%S %Y").strftime("%Y-%m-%d")
    except Exception: return d

# =============================================================================================== 1. OFFICIAL COLOUR TABLES
HANS = {"北冰藍": "北冰蓝", "極光白": "极光白", "亞特蘭蒂斯灰": "亚特兰蒂斯灰", "迷迭灰": "迷迭灰", "玄空黑": "玄空黑", "風卷草綠": "风卷草绿"}
MAP = {  # doc -> (catalog model id, priority rank, mapping basis)
    "D01": ("M020", 1, "model name SEAL = catalogue 海豹 (M020)"), "D02": ("M020", 1, "model name SEAL = catalogue 海豹 (M020)"), "D03": ("M020", 1, "model name SEAL (MY26 UK) = catalogue 海豹 (M020); UK palette differs from China's"),
    "D04": ("M020", 1, "model name SEAL = catalogue 海豹 (M020)"), "D05": ("M021", "", "title carries 海豹 -> Seal 05 DM-i (M021). NOT Destroyer 05 (M019): the catalogue alias table lists 'Seal 5 DM-i' under both M019 and M021; the Chinese title indicates M021"),
    "D06": ("M031", "", "title carries 海狮 -> Sealion 06 DM-i (M031). The catalogue alias table also lists 'Sealion 6 DM-i' under Song Plus DM-i (M034); not used"),
    "D07": ("M034", 4, "export name 'SEAL U DM-i' = Song Plus DM-i (M034) per catalogue alias table; no Chinese name in the document, so the mapping is by alias only"),
    "D08": ("M026", 6, "model name DOLPHIN = catalogue 海豚 (M026)"), "D09": ("M026", 6, "model name DOLPHIN = catalogue 海豚 (M026)"), "D10": ("M016", 5, "export name ATTO 3 = Yuan Plus (M016) per catalogue alias table"),
    "D11": ("M022", "", "model name SEAL 6 DM-i = Seal 06 DM-i (M022)"), "D12": ("M030", "", "model name SEALION 5 DM-i = Sealion 05 DM-i (M030)"), "D13": ("M036", 2, "HAN (France) = Han EV (M036) by name only; no colour text extractable")}
YEAR = {"D02": ("2025", "file name 'BYD-SEAL-2025.pdf'"), "D03": ("MY26", "title 'SEAL MY26 UK Leaflet'"), "D05": ("2026", "file name 'Final 2026'"), "D06": ("2026", "file name 'Final 2026'"), "D09": ("2025", "file name 'BYD-DOLPHIN-2025.pdf'"),
        "D10": ("2026", "file name 'BYD-ATTO-3-2026.pdf'")}
D01_PAIRS = {d["printed"].lower(): HANS[d["chinese"]] for d in docs[0]["colours"]}
D01_PAIRS.update({"atlantis grey": "亚特兰蒂斯灰", "shark grey": "迷迭灰"})
GLOSS = collections.defaultdict(set); PYK = collections.defaultdict(set)
CWORDS = ("black", "white", "grey", "gray", "blue", "green", "red", "pink", "purple", "yellow", "orange", "gold", "silver", "brown")
for c in cols.values():
    zh = re.sub(r"[^一-鿿]", "", c["color_name_zh"])
    if c["name_en_gloss_unofficial"]: GLOSS[nk(c["name_en_gloss_unofficial"])].add(c["color_name_zh"])
    if len(zh) >= 3:
        py = lazy_pinyin(zh); PYK["".join(py[:-1])].add(c["color_name_zh"])
def cand_zh(printed):
    p = printed.lower().strip(); out = []
    if p in D01_PAIRS: out.append((D01_PAIRS[p], "INFERRED: same English name as the official Chinese pairing in D01 (Macau Seal brochure)"))
    g = GLOSS.get(nk(printed), set())
    for z in sorted(g): out.append((z, "INFERRED: equals the researcher's unofficial English gloss of a catalogue colour"))
    words = [w for w in re.split(r"\s+", p) if w and w not in CWORDS]
    key = nk("".join(words))
    for z in sorted(PYK.get(key, set())): out.append((z, "INFERRED: transliteration equals the pinyin of the catalogue name"))
    seen = set(); res = []
    for z, b in out:
        if z not in seen: seen.add(z); res.append((z, b))
    return res
OC = []
TWO_TONE = {"D08": [("Atlantis Grey + Delan Black", "pair printed as stacked names joined by '+'"), ("Ski White + Urban Grey", "pair printed as stacked names joined by '+'")], "D09": [("Ski White + Harbour Grey", "printed in the document as a two-tone option")]}
for d in docs:
    did = d["doc_id"]; mid, prio, basis = MAP[did]; yv, yb = YEAR.get(did, ("not stated", "no model year in the text, title or file name"))
    base = dict(doc_id=did, source_url=d["url"], host_class=d["host_class"], document_date=iso(d["pdf_metadata"].get("CreationDate", "")), document_date_basis="PDF metadata CreationDate (not necessarily a publication date)" + (f"; ModDate {iso(d['pdf_metadata'].get('ModDate', ''))}" if d["pdf_metadata"].get("ModDate") else ""),
                model_as_printed=d["model_as_printed"], catalog_model_id=mid, catalog_model=models[mid]["model_key"], mapping_basis=basis, priority_rank=prio, market=d["market"], model_year_stated=yv, model_year_basis=yb,
                production_range="not stated", contains_paint_code="NO", status_effect="colour NAME only - not paint-code evidence; no model-year, trim or finish applicability beyond what is stated")
    if not d["colours"]:
        OC.append(dict(base, row_type="DOCUMENT_NO_COLOURS", colour_as_printed="", chinese_name_printed="", chinese_name_basis="", catalogue_candidate_zh="", finish_explicit="n/a", finish_text="", evidence_excerpt="Document fetched; no exterior-colour names are extractable from its text (colour pages are images; no OCR available)", two_tone="")); continue
    for c in d["colours"]:
        cz = cand_zh(c["printed"]); printed_zh = c["chinese"]
        per_colour_finish = (did == "D11")
        OC.append(dict(base, row_type="COLOUR", colour_as_printed=c["printed"], chinese_name_printed=printed_zh or "", chinese_name_basis="PRINTED in the document (Traditional Chinese)" if printed_zh else "NOT STATED in this document",
                       catalogue_candidate_zh=" | ".join(f"{z} [{b}]" for z, b in cz) if not printed_zh else HANS[printed_zh] + " [simplified form of the printed Chinese name]",
                       finish_explicit=("YES - 'metallic' stated for this colour" if per_colour_finish else "NO"), finish_text=(d["finish_note"] if (per_colour_finish or d["finish_note"]) else ""), two_tone="",
                       evidence_excerpt=" // ".join(l for l in d["excerpt_lines"] if c["printed"].lower() in l.lower() or (printed_zh and printed_zh in l))[:300] or " // ".join(d["excerpt_lines"][:2])[:300]))
    for name, note in TWO_TONE.get(did, []):
        OC.append(dict(base, row_type="COLOUR", colour_as_printed=name, chinese_name_printed="", chinese_name_basis="NOT STATED in this document", catalogue_candidate_zh="", finish_explicit="NO", finish_text="", two_tone="YES",
                       evidence_excerpt=note + " (layout read from text extraction)"))
# China-site model pages
CNMAP = {"/han/han-ev-zhijia": ("M036", 2), "/han/han-ev-shan": ("M036", 2), "/han/han-dm-i-zhijia": ("M002", 2), "/qin/2-qinplus-ev-zhijia": ("M039", 3), "/qin/26-qin-plus-dm-i": ("M007", 3), "/qin/3-qin-plus-DM-i": ("M007", 3), "/yuan/2-yuan-plus": ("M016", 5), "/yuan/3-yuan-plus": ("M016", 5),
         "/haitun/2025haitun": ("M026", 6), "/haitun/haitun-zhijia": ("M026", 6)}
for p in cnp:
    key = next((k for k in CNMAP if p["path"].endswith(k)), None)
    mid, prio = CNMAP.get(key, ("", ""))
    OC.append(dict(row_type="CN_MODEL_PAGE_DYNAMIC", doc_id="CN-" + p["path"].split("/")[-1], source_url="https://www.byd.com" + p["path"], host_class="BYD official website (China)", document_date="(page; no date)", document_date_basis="live web page fetched 2026-11-24",
                   model_as_printed=p["title"], catalog_model_id=mid, catalog_model=models[mid]["model_key"] if mid else "", mapping_basis="page title; mapping by model name only" if mid else "not a priority model", priority_rank=prio, market="China", model_year_stated="in title" if re.search(r"20\d\d款", p["title"]) else "not stated",
                   model_year_basis=p["title"], production_range="not stated", colour_as_printed="", chinese_name_printed="", chinese_name_basis="", catalogue_candidate_zh="", finish_explicit="n/a", finish_text="", contains_paint_code="NO",
                   evidence_excerpt=f"HTTP {p['http']}, {p['bytes']} bytes; the static HTML contains {p['colour_words']} colour words - colours are loaded by the page's scripts (the API behind it was NOT called)", two_tone="", status_effect="official page exists; colour table not extractable from static HTML"))
BPMAP = {"26-z9gt.html": ("M063;M064", "Denza"), "D9-2.html": ("M075;M076", "Denza"), "u8.html": ("M084", "Yangwang"), "u9-detail-page.html": ("M086", "Yangwang"), "u7-detail-page.html": ("M082;M083", "Yangwang"), "c-u8-l.html": ("M085", "Yangwang"),
         "bao5": ("M090", "Fangchengbao"), "bao8": ("M091", "Fangchengbao"), "tai7": ("M093;M094", "Fangchengbao"), "tai3": ("M092", "Fangchengbao"), "fangchengS": ("M087", "Fangchengbao")}
NOISE = re.compile(r"英寸|屏|套件|标|大灯|轮毂|方向盘|铝合金|\*|拖挂")
BRAND_ROWS = 0
for p in bp:
    key = p["url"].rstrip("/").split("/")[-1]; mids, bname = BPMAP[key]
    for e in p["colour_entries"]:
        if NOISE.search(e["name"]): continue
        ext = e["kind"].startswith("exterior") or e["kind"].startswith("body colour")
        OC.append(dict(row_type="COLOUR", doc_id="BP-" + bname[:3].upper() + "-" + key.replace(".html", "")[:14], source_url=p["url"], host_class=f"{bname} official website (live model page)", document_date="(live page fetched 2026-11-24; no publication date)", document_date_basis="live web page; HTML sha256 " + p["sha256"][:16] + "...",
                       model_as_printed=p["title"], catalog_model_id=mids, catalog_model=" | ".join(models[x]["model_key"] for x in mids.split(";")), mapping_basis="page title/URL name = catalogue model name; page may cover several catalogue variants", priority_rank="", market="China",
                       model_year_stated="in title" if re.search(r"20\d\d款", p["title"]) else "not stated", model_year_basis=p["title"], production_range="not stated", colour_as_printed=e["name"], chinese_name_printed=e["name"] if ext else "",
                       chinese_name_basis="PRINTED on the official page (Simplified Chinese), exterior/body-colour data entry" if ext else "printed on the official page but exterior vs interior NOT established (image path unclassified/interior)",
                       catalogue_candidate_zh="", two_tone="YES" if re.search(r"[/配双]", e["name"]) else "", finish_explicit="NO", finish_text="", contains_paint_code="NO",
                       evidence_excerpt=f"{e['kind']}; path ...{e['path_hint'][-50:]}", status_effect="colour NAME only - not paint-code evidence; live page, no model-year applicability"))
        BRAND_ROWS += 1
NF = [("Han EV (M036)", 2, "No static colour list: D13 (France Han brochure) has image-only colour pages; China pages han-ev-zhijia / han-ev-shan load colours dynamically; EU Han PDFs returned by search (byd.com/content/dam/byd-site/eu/product/han/han.pdf, BYD HAN V5.pdf) returned HTTP 404"),
      ("Qin PLUS EV / DM-i (M039, M007)", 3, "No official document with a colour list was fetched; China pages load colours dynamically; no export Qin PLUS brochure PDF with colours was retrievable"),
      ("Song PLUS EV / DM-i (M049, M034)", 4, "Only the export 'SEAL U DM-i' guide (D07) for the DM-i; no China-market colour table (the China site lists 宋Ultra/宋Pro/宋L pages, not 宋PLUS); no EV document"),
      ("e2 (M027)", 7, "No official document found; the China site's model list has no e2 page"),
      ("Destroyer 05 (M019)", 8, "No official document found. D05 (Cambodia 'Seal 5 DM-i 海豹') is catalogue Seal 05 DM-i (M021), not Destroyer 05")]
for m, pr, why in NF:
    OC.append(dict(row_type="NOT_FOUND", doc_id="NF-" + re.sub(r"[^A-Za-z0-9]+", "", m)[:12], source_url="", host_class="", document_date="", document_date_basis="", model_as_printed=m, catalog_model_id="", catalog_model="", mapping_basis="", priority_rank=pr, market="", model_year_stated="", model_year_basis="",
                   production_range="", colour_as_printed="", chinese_name_printed="", chinese_name_basis="", catalogue_candidate_zh="", finish_explicit="", finish_text="", contains_paint_code="NO", evidence_excerpt=why, two_tone="", status_effect="no official colour table obtained for this priority model"))
OCF = ["row_type", "doc_id", "source_url", "host_class", "document_date", "document_date_basis", "model_as_printed", "catalog_model_id", "catalog_model", "mapping_basis", "priority_rank", "market", "model_year_stated", "model_year_basis", "production_range", "colour_as_printed",
       "chinese_name_printed", "chinese_name_basis", "catalogue_candidate_zh", "two_tone", "finish_explicit", "finish_text", "contains_paint_code", "evidence_excerpt", "status_effect"]
wr("official_colour_tables.csv", OC, OCF)
colour_rows = [r for r in OC if r["row_type"] == "COLOUR"]

# official support lookup: (model id, zh) -> list of (doc, basis)
OFF = collections.defaultdict(list)
for r in colour_rows:
    if r["two_tone"] == "YES": continue
    if r["chinese_name_printed"]:
        for mid_ in r["catalog_model_id"].split(";"): OFF[(mid_, HANS.get(r["chinese_name_printed"], r["chinese_name_printed"]))].append((r["doc_id"], "OFFICIAL_CHINESE_NAME_PRINTED"))
    else:
        for part in r["catalogue_candidate_zh"].split(" | "):
            z = part.split(" [")[0].strip()
            if z: OFF[(r["catalog_model_id"], z)].append((r["doc_id"], "OFFICIAL_ENGLISH_NAME_INFERRED_CHINESE"))

# =============================================================================================== 2. CODE STATE + SUPPLIER SUPPORT (as Batch 10)
b5 = rd(f"{B5}/oem_paint_codes.csv"); b6 = [r for r in rd(f"{B6}/discovered_codes.csv") if r["link_scope"] == "COLOUR_RECORD"]; b7 = [r for r in rd(f"{B7}/discovered_codes.csv") if r["link_scope"] == "COLOUR_RECORD"]
b10 = {r["color_id"]: r for r in rd(f"{B10}/model_year_consistency.csv")}
state = {}
for r in b6 + b7: state[(r["color_id"], r["paint_code"])] = dict(sources=set(r["source_ids"].split(";")), status=r["confidence_status"], text=r["evidence_description"])
hist = collections.defaultdict(dict)
for r in b5: hist[(r["color_id"], r["supplier_candidate_code"])]["B5"] = r["evidence_status"]
for r in b6: hist[(r["color_id"], r["paint_code"])]["B6"] = r["confidence_status"]
for r in b7: hist[(r["color_id"], r["paint_code"])]["B7"] = r["confidence_status"]
by_col = collections.defaultdict(dict)
for (cid, code), v in state.items(): by_col[cid][code] = v
def finish_tags(text):
    t = text or ""; tags = set()
    if re.search(r"\bmatt?e?\b|¤MAT|哑光", t, re.I): tags.add("MATTE")
    if re.search(r"\bmet\b|met\.|metallic", t, re.I): tags.add("METALLIC")
    if re.search(r"\bpearl\b|\bp\.m\.?\b|\bpm\b|\bp\.x\b", t, re.I): tags.add("PEARL")
    if re.search(r"\bsolid\b", t, re.I): tags.add("SOLID")
    return tags
code_support = collections.defaultdict(list); code_finish = collections.defaultdict(set)
for c in cands:
    if c["source_id"] in ("S33", "S34") or c["listing_level"] == "REJECTED": continue
    for tk in tokens(c["code_raw"]):
        code_finish[tk] |= finish_tags(c["names_raw"]); code_support[tk].append(dict(source=c["source_id"], market=c["market"], level=c["listing_level"], model=c["model_as_listed"], year=c["year_as_listed"]))
for fn, src in ((f"{HERE}/batch6/raw/oematch_byd_products.json", "B6S02"), (f"{HERE}/batch7/raw/dipyourcar_byd_products.json", "B7S02"), (f"{HERE}/batch6/raw/crop_byd_products.json", "B6S03")):
    for p in json.load(open(fn, encoding="utf-8")):
        title = p.get("title") or p["slug"].replace("-", " ")
        t = re.sub(r"\s*\|\s*(OEMatch|Luna OEM Basecoat).*$", "", title).strip(); t = re.sub(r"\s+(Basecoat Paint|Complete Car Paint Kit|Touch Up Spray Paint)$", "", t, flags=re.I); t = re.sub(r"^(BYD|Byd)\s+", "", t); toks = t.split()
        if not toks: continue
        cd = toks[-1].upper() if re.fullmatch(r"[A-Za-z0-9]{1,5}(-[A-Za-z0-9]{1,3})?", toks[-1]) else (toks[0].upper() if re.fullmatch(r"[A-Za-z]\d{1,3}[cC]?", toks[0]) else "")
        if src == "B6S03": cd = (toks[0] + "-" + toks[1]).upper() if len(toks) > 1 and re.fullmatch(r"[a-zA-Z]", toks[0]) and re.fullmatch(r"\d{2}", toks[1]) else toks[0].upper()
        if cd: code_finish[cd] |= finish_tags(t); code_support[cd].append(dict(source=src, market="(no market stated)", level="name-only", model="", year=""))
model_keys = {mid: {nk(m["model_key"])} | {nk(a) for a in m["alt_names"].split(";") if a.strip()} for mid, m in models.items()}
def listed_matches(listed, mid):
    l = nk(re.sub(r"^BYD\s+", "", listed or "", flags=re.I))
    if not l or l == "allmodels": return False
    return any(k == l or (k.startswith(l) and len(l) >= 3 and k[len(l):] in ("dmi", "ev", "dm", "dmp", "dmiev", "plus", "pro")) for k in model_keys[mid] if k)
def parse_range(y):
    m = re.findall(r"(20\d\d)", y or ""); return (int(m[0]), int(m[-1])) if m else None

# =============================================================================================== 3. CODE LINK QUALITY AUDIT (all existing colour/code links)
LQ = []; cnt = collections.Counter()
for i, ((cid, code), v) in enumerate(sorted(state.items(), key=lambda kv: (kv[0][0], kv[0][1])), 1):
    c = cols[cid]; m = models[c["model_id"]]; y = years.get(c["model_year_id"], {}); my = int(y["year"]) if y.get("year", "").isdigit() else None
    sup = code_support.get(code, []); rows_ = [s for s in sup if s["level"] in ("model", "model+year") and listed_matches(s["model"], c["model_id"])]
    srcs = sorted(v["sources"]); is_ref = bool(REF_RE.fullmatch(code.upper()))
    support = "MODEL_LISTED_APPROX" if rows_ else "NAME_ONLY"
    rng = [parse_range(s["year"]) for s in rows_ if parse_range(s["year"])]
    if rows_ and rng and my: yc = "YEAR_LISTED_MATCH" if any(a <= my <= b for a, b in rng) else "MODEL_YEAR_MISMATCH"
    elif rows_ and not rng: yc = "YEAR_UNKNOWN (model listed, no year given)"
    else: yc = "YEAR_UNKNOWN (name-only)"
    if not my: yc = "YEAR_UNKNOWN (no model year on the colour record)"
    tags = sorted(code_finish.get(code, set())); is_matte_rec = c["color_name_zh"].startswith("哑光")
    if is_matte_rec and "MATTE" not in tags: fc = "FINISH_MISMATCH (matte colour record, code never labelled matte by suppliers)"
    elif (not is_matte_rec) and "MATTE" in tags: fc = "FINISH_UNRESOLVED (a supplier labels this code matte; record finish unknown)"
    elif tags: fc = "NO_FINISH_CONFLICT_VISIBLE (supplier labels: " + "/".join(tags) + "; record finish unknown)"
    else: fc = "FINISH_UNKNOWN"
    mk = sorted({s["market"] for s in sup if s["market"]}); explicit = [x for x in mk if x not in ("unspecified (multi-market names)", "unspecified", "(no market stated)")]
    mc = "MARKET_UNKNOWN (supplier gives no market)" if not explicit else ("MARKET_NON_CHINA_SUPPLIER (" + "; ".join(explicit) + ")" if "China" not in explicit else "MARKET_INCLUDES_CHINA")
    pp = "PRODUCTION_PERIOD_LISTED (" + "/".join(sorted({s["year"] for s in rows_ if s["year"]})) + ")" if any(s["year"] for s in rows_) else "PRODUCTION_PERIOD_UNKNOWN"
    flags = []
    if support == "NAME_ONLY": flags.append("NAME_ONLY_PROPAGATED")
    if yc == "MODEL_YEAR_MISMATCH": flags.append("MODEL_YEAR_MISMATCH")
    if fc.startswith("FINISH_MISMATCH") or fc.startswith("FINISH_UNRESOLVED"): flags.append("FINISH_" + ("MISMATCH" if fc.startswith("FINISH_MISMATCH") else "UNRESOLVED"))
    if mc.startswith("MARKET_UNKNOWN") or mc.startswith("MARKET_NON_CHINA"): flags.append("MARKET_NOT_CHINA_CONFIRMED")
    if pp == "PRODUCTION_PERIOD_UNKNOWN": flags.append("PRODUCTION_PERIOD_UNKNOWN")
    for f in flags: cnt["flag:" + f] += 1
    primary = "MODEL_YEAR_MISMATCH" if yc == "MODEL_YEAR_MISMATCH" else ("FINISH_MISMATCH" if fc.startswith("FINISH_MISMATCH") else ("NAME_ONLY_PROPAGATED" if support == "NAME_ONLY" else ("MODEL_LISTED_YEAR_MATCH" if yc == "YEAR_LISTED_MATCH" else "MODEL_LISTED_YEAR_UNKNOWN")))
    cnt["primary:" + primary] += 1
    h = hist[(cid, code)]; first = "5 (baseline link)" if "B5" in h else ("6" if "B6" in h else "7")
    status = "PAINT_SYSTEM_REFERENCE" if is_ref else b10[cid]["status"]
    hs = "; ".join(f"{k}:{h[k]}" for k in ("B5", "B6", "B7") if k in h) + ("; B8:PAINT_SYSTEM_REFERENCE" if is_ref else "") + f"; B10(colour record):{b10[cid]['status']}; B11:{status} (unchanged)"
    LQ.append(dict(audit_id=f"LQ{i:04d}", color_id=cid, brand=brands[m["brand_id"]], model_id=m["model_id"], model=m["model_key"], model_year=y.get("year", "") or "UNKNOWN", colour_name_zh=c["color_name_zh"], record_market=c["market"] or "UNKNOWN", paint_code=code,
                   code_class="PAINT_SYSTEM_REFERENCE" if is_ref else "VEHICLE_PAINT_CODE_CANDIDATE", link_basis=v["text"][:240], supplier_sources=";".join(srcs), model_support=support, name_only_flag="YES" if support == "NAME_ONLY" else "NO", year_check=yc,
                   supplier_finish_labels="/".join(tags) or "none", finish_check=fc, market_check=mc, production_period_check=pp, flags=" | ".join(flags), primary_quality_class=primary, first_seen_batch=first, status_history=hs, current_status=status,
                   audit_note="historical record preserved; classification added in Batch 11; no code removed or re-assigned"))
LQF = ["audit_id", "color_id", "brand", "model_id", "model", "model_year", "colour_name_zh", "record_market", "paint_code", "code_class", "link_basis", "supplier_sources", "model_support", "name_only_flag", "year_check", "supplier_finish_labels", "finish_check", "market_check",
       "production_period_check", "flags", "primary_quality_class", "first_seen_batch", "status_history", "current_status", "audit_note"]
wr("code_link_quality_audit.csv", LQ, LQF)
lq_by_col = collections.defaultdict(list)
for r in LQ: lq_by_col[r["color_id"]].append(r)

# =============================================================================================== 4. MODEL-YEAR COLOUR CATALOGUE (all 1,223 colour records)
MC = []; off_cnt = collections.Counter(); model_year_support = set()
for cid, c in cols.items():
    m = models[c["model_id"]]; y = years.get(c["model_year_id"], {}); g = gens.get(c["generation_id"], {}); b = b10[cid]
    sids = [x for x in c["gallery_spec_ids"].split(";") if x]; tn = []
    for s in sids:
        for t in trim_by_spec.get(s, []): tn.append(t["trim_name_zh"] or t["trim_name_en"])
    tn = sorted(set(x for x in tn if x))
    lqs = lq_by_col.get(cid, [])
    scopes = "; ".join(f"{r['paint_code']}[{r['model_support']}]" for r in lqs if r["code_class"] == "VEHICLE_PAINT_CODE_CANDIDATE")
    refs = "; ".join(f"{r['paint_code']}[{r['model_support']}]" for r in lqs if r["code_class"] != "VEHICLE_PAINT_CODE_CANDIDATE")
    flg = sorted({f for r in lqs for f in r["flags"].split(" | ") if f})
    off = OFF.get((c["model_id"], c["color_name_zh"]), [])
    if off:
        lev = "OFFICIAL_CHINESE_NAME_PRINTED" if any(b_ == "OFFICIAL_CHINESE_NAME_PRINTED" for _, b_ in off) else "OFFICIAL_ENGLISH_NAME_INFERRED_CHINESE"
        off_cnt[lev] += 1
        if y.get("year"): model_year_support.add((c["model_id"], y["year"]))
    else: lev = "NONE"
    MC.append(dict(color_id=cid, manufacturer="BYD Group", brand=brands[m["brand_id"]], model_id=m["model_id"], model=m["model_key"], chinese_model_name=m["name_zh"], generation_id=c["generation_id"], generation_label=g.get("generation_label", "") or g.get("source_row_name", ""),
                   generation_intro_year=g.get("intro_year", ""), generation_discontinued_year=g.get("discontinued_year", ""), model_year=y.get("year", "") or "UNKNOWN", model_year_basis=b["model_year_basis"], production_year="UNKNOWN (the catalogue records model years only)",
                   market=c["market"] or "UNKNOWN", trim_scope=(f"observed in {len(sids)} trim page(s): " + " | ".join(tn[:4]) + (" ..." if len(tn) > 4 else "")) if sids else "no trim recorded", finish_catalogue="MATTE" if c["color_name_zh"].startswith("哑光") else "UNKNOWN",
                   colour_name_zh=c["color_name_zh"], pinyin_translit=b["pinyin_translit"], english_name_unofficial=c["name_en_gloss_unofficial"], official_doc_support=lev, official_doc_ids=";".join(sorted({d for d, _ in off})),
                   candidate_vehicle_codes_with_support=scopes, paint_system_references=refs, code_association_flags=" | ".join(flg), status=b["status"], evidence_type=b["evidence_type"],
                   unresolved_questions=b["unresolved_questions"] + (" Official document support names the colour for this model but states no year, finish or code." if off else "")))
MCF = ["color_id", "manufacturer", "brand", "model_id", "model", "chinese_model_name", "generation_id", "generation_label", "generation_intro_year", "generation_discontinued_year", "model_year", "model_year_basis", "production_year", "market", "trim_scope", "finish_catalogue",
       "colour_name_zh", "pinyin_translit", "english_name_unofficial", "official_doc_support", "official_doc_ids", "candidate_vehicle_codes_with_support", "paint_system_references", "code_association_flags", "status", "evidence_type", "unresolved_questions"]
wr("model_year_colour_catalog.csv", MC, MCF)

# =============================================================================================== 5. FIELD EVIDENCE REGISTER
tg = rd(f"{B8}/verification_results.csv"); FE = []
def fe(**k): FE.append(k)
fe(row_type="INTAKE_CHECK", id="IC01", evidence_type="all", description="Git history since the Batch 10 commit 0baa8ac: no commits other than the research batches; working tree clean at the start of Batch 11", received="NO", received_date="", provider_role="", vin_handling="n/a", acceptance_checks="", classification_if_accepted="", status="NO_NEW_EVIDENCE", notes=f"checked {TODAY}")
fe(row_type="INTAKE_CHECK", id="IC02", evidence_type="all", description="Repository scan for image/PDF/document files newer than the Batch 10 report outside the research batches: none found (repository root holds only the unrelated static page files)", received="NO", received_date="", provider_role="", vin_handling="n/a", acceptance_checks="", classification_if_accepted="", status="NO_NEW_EVIDENCE", notes=f"checked {TODAY}")
fe(row_type="INTAKE_CHECK", id="IC03", evidence_type="all", description="User messages during Batch 11 contain instructions only; no label photograph, dealer reply, VIN-linked record or OEM paint document was supplied", received="NO", received_date="", provider_role="", vin_handling="n/a", acceptance_checks="", classification_if_accepted="", status="NO_NEW_EVIDENCE", notes=f"checked {TODAY}")
RULES = [("LABEL_PHOTO", "Photographs of a factory label on the owner's own vehicle (context, medium, close-up, field-name shots; VIN and personal data masked; GPS stripped)", "vehicle association (model, year, colour; first 9 VIN characters or owner's own hash); authenticity (in-situ context shots); meaning (field name states colour/paint)", "VERIFIED_LABEL (that vehicle only)"),
         ("DEALER_WRITTEN", "Written reply from an authorised service centre (screenshot, printout or stamped statement) showing colour name and code for the owner's own vehicle", "document shows VIN-equivalent identification (owner-supplied hash/prefix), colour name, code; code nature stated (factory colour code vs mixing formula); centre and date named", "VERIFIED_OEM (that vehicle only) if a factory colour code; PAINT_SYSTEM_REFERENCE if a formula number"),
         ("VIN_BUILD_RECORD_OWNER_SUPPLIED", "A factory/build record supplied by the vehicle owner for their own vehicle", "origin identifiable as a BYD-group system or document; colour name and code present; full VIN never stored (hash + 9-char prefix only)", "VERIFIED_OEM (that vehicle only)"),
         ("OEM_PAINT_DOCUMENT", "Official manufacturer paint-code documentation (repair manual page, parts/colour table) obtained through an authorised route", "document identity and date; model/year/market stated; no copying of licensed formula data; terms permit research use", "VERIFIED_OEM for the model-years the document states")]
for t, desc, chk_, cls in RULES:
    fe(row_type="EVIDENCE_TYPE_RULE", id="ER-" + t, evidence_type=t, description=desc, received="NO", received_date="", provider_role="", vin_handling="never store a full VIN; keep SHA-256 hash and first 9 characters only; originals in a private store", acceptance_checks=chk_, classification_if_accepted=cls, status="PENDING", notes="No item of this type has been received.")
for r in tg:
    fe(row_type="TARGET_SLOT", id="FS-" + r["target_id"], evidence_type="LABEL_PHOTO or DEALER_WRITTEN", target_id=r["target_id"], description=f"{r['international_model_name']} {r['original_chinese_color_name']} ({r['model_years_in_catalog']}); candidates {r['candidate_codes']}", received="NO", received_date="", provider_role="", vin_handling="hash + first 9 characters only",
       acceptance_checks="per rules ER-*", classification_if_accepted="see rule", status="PENDING", notes="PENDING - no evidence received; status of the catalogue records stays " + r["current_status"])
FEF = ["row_type", "id", "evidence_type", "target_id", "description", "received", "received_date", "provider_role", "vin_handling", "acceptance_checks", "classification_if_accepted", "status", "notes"]
wr("field_evidence_register.csv", FE, FEF)

# =============================================================================================== 6. PRIORITY CONFLICT UPDATES
ca = rd(f"{B10}/colour_conflict_audit.csv"); PU = []
def pu(colour, kind, item, text, source, basis):
    PU.append(dict(colour_zh=colour, row_type=kind, item=item, statement=text, source_or_basis=source, evidence_grade=basis))
cat_years = collections.defaultdict(lambda: collections.defaultdict(set))
for c in cols.values():
    if c["color_name_zh"] in ("雪域白", "攀岩灰", "亚特兰蒂斯灰", "苍穹蓝"): cat_years[c["color_name_zh"]][models[c["model_id"]]["model_key"]].add(years.get(c["model_year_id"], {}).get("year", "?"))
def catline(z): return "; ".join(f"{k}: {','.join(sorted(v))}" for k, v in sorted(cat_years[z].items()))
for g in [r for r in ca if r["row_type"] == "GROUP"]:
    z = g["colour_zh"]
    for r in [x for x in ca if x["row_type"] == "CODE" and x["colour_zh"] == z]:
        pu(z, "COMPETING_CODE", r["code"], f"{r['code_class']} - lineages {r['n_lineages']} ({r['supporting_lineages']}); finish labels: {r['finish_tags_in_supplier_text']}; supplier year ranges: {r['listed_years'] or 'none'}; supplier models: {r['listed_models'] or 'none'}; markets: {r['listing_markets'] or 'none stated'}", r["supporting_sources"], "RETAILER (not OEM)")
    pu(z, "CATALOGUE_FACT", "colour records", f"Catalogue (gallery-observed) records by model: {catline(z)}", "model_year_colour_catalog.csv", "CATALOGUE (Autohome gallery evidence)")
FACTS = {
 "雪域白": [("FACT", "official names", "No fetched official document prints the Chinese name 雪域白. Official Seal documents print 極光白 / Aurora White (D01, D02, D04) for the white, so a Seal is not a 雪域白 car and retailer listings of the 'Snow White' code group under SEAL are not evidence for 极光白.", "D01 (Macau, 2024-03 metadata), D02, D04", "OFFICIAL_DOCUMENT_NAME_ONLY"),
           ("FACT", "official English names", "Official export documents list 'Snow white' for Seal U DM-i (D07, Croatia importer guide, 2024-05 metadata) and 'Snowy White' for Seal 5 DM-i / 海豹 (D05, Cambodia, 2025-07 metadata). The documents give no Chinese name, finish or code.", "D05, D07", "OFFICIAL_DOCUMENT_NAME_ONLY"),
           ("HYPOTHESIS", "H1 name equivalence", "'Snow white' (D07) is the export name of the Chinese 雪域白 on Song PLUS DM-i. Not stated by BYD; supported only by catalogue alias and retailer naming.", "D07 + catalogue alias table", "HYPOTHESIS"),
           ("HYPOTHESIS", "H2 two codes, one colour", "W36C and WA2 may both belong to the same colour (Carross lists them in the same row for 'SNOW WHITE-MET.', 2017-2024) - e.g. two systems or two production periods. No source separates them by year or model.", "S31, S227 (batch 10 audit)", "HYPOTHESIS"),
           ("HYPOTHESIS", "H3 WA8 and BYHB-00001", "WA8 may be a different white and BYHB-00001 a paint-system reference; only the Touch Up Paint Factory lineage lists them, for a seven-name white group.", "S32, S226", "HYPOTHESIS")],
 "攀岩灰": [("FACT", "official English names", "Official Australian documents list 'Harbour Grey' for the ATTO 3 (D10, 2026) and for the Dolphin (D09, 2025). Neither prints a Chinese name, finish or code.", "D09, D10", "OFFICIAL_DOCUMENT_NAME_ONLY"),
            ("FACT", "retailer grouping", "Cartouch (AU) lists 'HARBOUR GREY, BOULDER GREY' with HAN, HA4 for ATTO 3 2023-2025 and 'BOULDER GREY, TIME GREY' with HAN, HA4 for Dolphin 2024; other lineages tie HA4 to 时光灰.", "S30; S32; B6S02; B7S02", "RETAILER (not OEM)"),
            ("HYPOTHESIS", "H1 HA4 belongs to 时光灰", "HA4 is the 时光灰 code and Cartouch lumped it into Boulder-Grey rows; 攀岩灰 = HAN. Unverified.", "batch 10 audit", "HYPOTHESIS"),
            ("HYPOTHESIS", "H2 贝贝灰 and 攀岩灰 share a paint", "Dolphin 贝贝灰 and Atto 3 攀岩灰 are both sold in Australia as 'Harbour Grey' and share HAN in retailer lists. BYD states no equivalence; catalogue Chinese names differ.", "D09, D10, S30, S32", "HYPOTHESIS")],
 "亚特兰蒂斯灰": [("FACT", "official names", "Official documents print Atlantis Grey/Gray (Chinese 亞特蘭蒂斯灰 on the Macau Seal brochure D01) for Seal (D01, D02, D04), ATTO 3 (D10, 'only available on PREMIUM Model'), Dolphin (D08, D09). None states finish (matte/metallic) or a code. UK documents print 'Atlantis BLUE' (D03, D11, D12) and D05 prints 'Atlantic Grey' - different names, not to be equated.", "D01-D05, D08-D12", "OFFICIAL_DOCUMENT_NAME_ONLY"),
                  ("FACT", "retailer finish labels", "Every retailer text with a finish tag labels HB6 matte (¤MAT / MATT / Matt) and HB5 plain metallic (three lineages). HB6 is supported for Seal 2022 only by Carross.", "S31, S32, S226, S227, B6S02, B7S02, B6S03", "RETAILER (not OEM)"),
                  ("HYPOTHESIS", "H1 HB6 is a matte variant", "HB6 = matte Atlantis Grey, HB5 = metallic. No official statement that a matte Atlantis Grey exists in China; the catalogue has no finish evidence for 亚特兰蒂斯灰.", "retailer labels", "HYPOTHESIS"),
                  ("HYPOTHESIS", "H2 year split", "HB6 may apply to the 2022 launch Seal only (Carross 2022) and HB5 later.", "S31 (Seal 2022)", "HYPOTHESIS")],
 "苍穹蓝": [("FACT", "official names", "No fetched official document prints 苍穹蓝 / Firmament Blue / Sky Blue. Other official blues (北冰蓝 / Arctic Blue on Seal, Azure Blue on Sealion 6, Atlantis Blue in the UK) are different names.", "D01-D12", "OFFICIAL_DOCUMENT_NAME_ONLY"),
            ("FACT", "catalogue", "苍穹蓝 appears in the catalogue for e2 (2019-2021) and older models; no priority-model official document covers e2.", "model_year_colour_catalog.csv", "CATALOGUE"),
            ("HYPOTHESIS", "H1 code era", "BYL (2016-2017) and F2/L32C (2015-2019) are earlier codes and LAN a later one (Carross year ranges); the e2's 2019-2021 years sit at the boundary and no source assigns them.", "S31, S227, S226", "HYPOTHESIS"),
            ("HYPOTHESIS", "H2 name mix-up", "LAN may belong to 穹顶蓝 ('Dome Blue' in the Touch Up Paint Factory names), not 苍穹蓝.", "S226", "HYPOTHESIS")]}
MINEV = {"雪域白": "At least one document-grade record (dealer system/printout or label photo, owner's own vehicle) each for: a Han EV, a Qin PLUS (EV and DM-i), a Song PLUS (DM-i and EV) and a Destroyer 05, with one 2020-2022 and one 2023-2025 car of one model; BYD documentation of what BYHB-00001/WA8 are.",
         "攀岩灰": "A record from an Atto 3/Yuan PLUS in 攀岩灰, one from a Dolphin in 贝贝灰 and one 时光灰 car (any model), each with year and finish; or a BYD document pairing the Chinese and export names.",
         "亚特兰蒂斯灰": "A record from a Seal in 亚特兰蒂斯灰 stating year and finish; a BYD statement whether a matte Atlantis Grey exists in China; if both exist, one car of each finish.",
         "苍穹蓝": "A record from an e2 (2019-2021) in 苍穹蓝; a BYD document naming the colour's code or era; separate confirmation of what 穹顶蓝 is on the LAN listings."}
for z, items in FACTS.items():
    for kind, item, text, src, grade in items: pu(z, kind, item, text, src, grade)
    pu(z, "MINIMUM_EVIDENCE", "to resolve", MINEV[z], "evidence_requirements.csv (Batch 10)", "REQUIREMENT")
    pu(z, "BATCH11_STATUS", "conflict state", "OPEN - every competing code preserved; no majority vote; no status changed. New in Batch 11: official document names added; none states a code, finish or year.", "this batch", "UNCHANGED")
PUF = ["colour_zh", "row_type", "item", "statement", "source_or_basis", "evidence_grade"]
wr("priority_conflict_updates.csv", PU, PUF)

# =============================================================================================== 7. SOURCE AUDIT (new sources of Batch 11)
SA = []
def sa(key, cls, title, url, http, date, lineage, note, codes="NO", mc="YES"):
    SA.append(dict(source_key=key, first_batch="11", source_class=cls, manufacturer_controlled=mc, title=title, url_or_query=url, fetch_result=http, document_date=date, evidence_role="OFFICIAL_COLOUR_NAMES" if cls != "SEARCH_RECORD" else "SEARCH_RECORD", contains_vehicle_paint_codes=codes, lineage_id=lineage,
                   status_effect="colour names only; cannot verify a paint code" if cls != "SEARCH_RECORD" else "lead or negative result", note=note))
for d in docs:
    host = d["host_class"]; cls = "AUTHORISED_DEALER_HOSTED" if "dealer" in host else ("MANUFACTURER_CONTROLLED" if "importer" not in host.lower() and "BYD official" in host or "BYD UK" in host else "MANUFACTURER_CONTROLLED")
    lin = "L-DEALER-HOSTED-BYD" if "dealer" in host else ("L-OEM-BYD-IMPORTERS" if ("importer" in host.lower() or "Australia" in host) else "L-OEM-BYD")
    sa("B11-" + d["doc_id"], cls, f"{d['model_as_printed']} - {d['market']} ({d['title_in_url']})", d["url"], f"HTTP 200, {d['bytes']} bytes, sha256 {d['sha256'][:16]}...", iso(d["pdf_metadata"].get("CreationDate", "")), lin,
       f"{host}. " + (f"Prints Chinese names. " if any(c["chinese"] for c in d["colours"]) else "English names only. ") + d["finish_note"], mc="NO" if "dealer" in host else "YES")
for p in cnp:
    sa("B11-CN-" + p["path"].split("/")[-1], "MANUFACTURER_CONTROLLED", f"BYD China model page: {p['title']}", "https://www.byd.com" + p["path"], f"HTTP {p['http']}, {p['bytes']} bytes", "(live page)", "L-OEM-BYD", "Static HTML holds no colour names; colours are loaded dynamically; the underlying API was not called.")
for p in bp:
    key = p["url"].rstrip("/").split("/")[-1]; bname = BPMAP[key][1]
    sa("B11-BP-" + key.replace(".html", ""), "MANUFACTURER_CONTROLLED", f"{bname} official model page: {p['title']}", p["url"], f"HTTP {p['http']}, {p['bytes']} bytes, sha256 {p['sha256'][:16]}...", "(live page)", "L-OEM-" + bname.upper(),
       f"{len(p['colour_entries'])} colour/option entries embedded in the static HTML; names only; no codes; the scripts/API behind the page were not called.")
for p in bpf:
    if p["http"] != "200": sa("B11-BPF-" + p["url"].split("/")[-1].replace(".html", ""), "SEARCH_RECORD", f"{p['brand']} model page (link taken from the brand's own site configuration) - NOT retrievable", p["url"], f"HTTP {p['http']}", "", "L-SEARCH-RECORD", "Fetch failed on 2026-11-24; content not seen.", mc="NO")
FAILED = ["https://www.byd.com/content/dam/byd-site/hk/product/seal/pc/SPECS.pdf", "https://www.byd.com/content/dam/byd-site/hk/product/dolphin/pc/BROCHURE-zh.pdf", "https://www.byd.com/content/dam/byd-site/uk/product/BYD%20DOLPHIN%20v5.pdf", "https://www.byd.com/content/dam/byd-site/eu/product/han/han.pdf",
          "https://www.byd.com/content/dam/byd-site/eu/product/han/BYD%20HAN%20V5.pdf", "https://byd.com/content/dam/byd-site/mo/product/dolphin/BYDDOLPHINbrochure.pdf", "https://bydauto.be/media/pnzpbugo/seal-0723-bps-en-v1-web-1.pdf", "https://bydauto.be/media/000asdas/dolphin-en-ld.pdf",
          "https://byd.com/content/dam/byd-site/sg/product/pdf/BYD%20Dolphin%20Spec%20Sheet%20(Digital).pdf", "https://byd.com/content/dam/byd-site/hk/product/sealion7/BYD_SEALION_7_brochure", "https://denzel.at/sites/denzel.at/files/downloads/6735bd50381ad49eb065b686_BYD_Folder_Han.pdf"]
for i, u in enumerate(FAILED, 1):
    sa(f"B11-F{i:02d}", "SEARCH_RECORD", "URL returned by a web search; NOT retrievable", u, "HTTP 404", "", "L-SEARCH-RECORD", "Returned HTTP 404 on 2026-11-24; content not seen and not used (search-engine summaries of it are unverified).", mc="NO")
sa("B11-S01", "SEARCH_RECORD", "Search record - official BYD colour tables per model/year (China and export)", "queries: 比亚迪 官方 电子彩页 ...; BYD Seal brochure PDF exterior colours ...; BYD Dolphin brochure ...; BYD Han brochure ...; BYD Qin PLUS DM-i brochure ...; BYD Seal U DM-i / Song Plus / Sealion 6 brochure ...; byd.com ... 彩頁 (HK/Macau)", "web search", "", "L-SEARCH-RECORD",
   "Found official export brochures for Seal, Dolphin, ATTO 3, Seal U DM-i and others; no static China-market colour table; none for e2, Qin PLUS, Han EV or Destroyer 05.", mc="NO")
sa("B11-S02", "SEARCH_RECORD", "Search record - Denza, Yangwang, Fangchengbao, Linghui colour tables", "see unresolved_questions.md (Section F)", "web search + page reads", "", "L-SEARCH-RECORD", "No official colour table for these brands was obtained in Batch 11 (see unresolved_questions.md).", mc="NO")
SAF = ["source_key", "first_batch", "source_class", "manufacturer_controlled", "title", "url_or_query", "fetch_result", "document_date", "evidence_role", "contains_vehicle_paint_codes", "lineage_id", "status_effect", "note"]
wr("source_audit.csv", SA, SAF)

# =============================================================================================== STATS
st_c = collections.Counter(r["status"] for r in MC); n_name_only = sum(1 for r in LQ if r["name_only_flag"] == "YES"); n_mismatch = sum(1 for r in LQ if "MODEL_YEAR_MISMATCH" in r["flags"])
mismatch_cols = sorted({r["color_id"] for r in LQ if "MODEL_YEAR_MISMATCH" in r["flags"]})
docs_with_colours = [d for d in docs if d["colours"]]; models_cov = sorted({MAP[d["doc_id"]][0] for d in docs_with_colours})
STATS = dict(official_documents_fetched=len(docs), brand_pages_with_colour_names=len(bp), brand_colour_name_rows=BRAND_ROWS, official_documents_with_exterior_colour_names=len(docs_with_colours), docs_with_chinese_names=sum(1 for d in docs if any(c["chinese"] for c in d["colours"])), docs_with_per_colour_finish=1, docs_with_equipment_finish_line=sum(1 for d in docs if d["equipment_lines"] and d["doc_id"] != "D11" and d["doc_id"] != "D10"),
             docs_with_paint_code=0, colour_rows=len(colour_rows), cn_model_pages=len(cnp), failed_urls=len(FAILED), catalog_models_covered=models_cov, priority_models_with_official_table=sorted({MAP[d["doc_id"]][1] for d in docs_with_colours if MAP[d["doc_id"]][1] != ""}),
             model_year_combinations_with_official_name_support=len(model_year_support), colour_records_with_official_support=dict(off_cnt), colour_records=len(MC), status=dict(st_c), links=len(LQ), name_only_links=n_name_only, model_listed_links=len(LQ) - n_name_only, model_year_mismatch_links=n_mismatch,
             model_year_mismatch_colour_records=len(mismatch_cols), flag_counts={k[5:]: v for k, v in cnt.items() if k.startswith("flag:")}, primary_classes={k[8:]: v for k, v in cnt.items() if k.startswith("primary:")}, field_evidence_received=0, verified_oem=0, verified_label=0, corroborated=0, target_slots=len(tg))
json.dump(STATS, open(f"{B11}/stats_batch11.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(STATS, ensure_ascii=False, indent=1))
