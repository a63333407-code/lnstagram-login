#!/usr/bin/env python3
"""
Batch 6 - China paint-code discovery (BYD Group).  Reproducible build.

Inputs (read-only): research/byd/catalog_union/*.csv (Batch 1-4 union), research/byd/batch5/oem_paint_codes.csv,
                    research/byd/batch6/raw/oematch_byd_products.json, crop_byd_products.json (harvested 2026-11-24).
Outputs: research/byd/batch6/{discovered_codes.csv, lookup_model_year_colour.csv, sources.csv, conflicts.csv,
         formula_identifier_investigation.csv, stats_batch6.json}

Rules: nothing is VERIFIED_OEM / CORROBORATED here (no OEM document or exact-vehicle label found); every code is
third-party (retailer / paint-system listing).  `code_type` describes the FORMAT/PROVENANCE CLASS, not correctness.
Requires pypinyin (pip install pypinyin) only to normalise supplier pinyin names against Chinese colour names.
"""
import csv, os, re, json, collections
from pypinyin import lazy_pinyin

HERE = os.path.dirname(os.path.abspath(__file__)); U = os.path.join(HERE, "catalog_union"); B5 = os.path.join(HERE, "batch5"); OUT = os.path.join(HERE, "batch6"); RAW = os.path.join(OUT, "raw")
TODAY = "2026-11-24"


def rd(p):
    with open(p, encoding="utf-8", newline="") as f: return list(csv.DictReader(f))


def wr(name, rows, fields):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in fields})


brands = {b["brand_id"]: b["name"] for b in rd(f"{U}/brands_all.csv")}
models = {m["model_id"]: m for m in rd(f"{U}/models_all.csv")}
years = {y["model_year_id"]: y for y in rd(f"{U}/model_years_all.csv")}
cols = {c["color_id"]: c for c in rd(f"{U}/factory_colors_all.csv")}
links = rd(f"{U}/color_paint_code_links_all.csv")
cands = {c["candidate_id"]: c for c in rd(f"{U}/paint_code_candidates_all.csv")}
srcs = {s["source_id"]: s for s in rd(f"{U}/sources_all.csv")}
b5 = rd(f"{B5}/oem_paint_codes.csv")
oem_raw = json.load(open(f"{RAW}/oematch_byd_products.json", encoding="utf-8"))
crop_raw = json.load(open(f"{RAW}/crop_byd_products.json", encoding="utf-8"))

# ------------------------------------------------------------------------------------------------ helpers
def tokens(raw):
    return {t.strip().upper() for t in re.split(r"[;,/]+|\s+\|\s+", raw or "") if t.strip()}


FINISH = {"metallic", "pearl", "mat", "solid", "m", "m.", "p.m.", "p.m", "p.x", "met", "met.", "pm", "pearlescent", "mica", "x"}
def norm_en(s):
    w = [x for x in re.split(r"[\s\-_/]+", (s or "").lower()) if x and x not in FINISH]
    return "".join(re.sub(r"[^a-z0-9]", "", x) for x in w)


def pinyin_key(zh):
    return "".join(re.sub(r"[^a-z0-9]", "", s.lower()) for s in lazy_pinyin(re.sub(r"[^一-鿿]", "", zh)))


def code_type(code):
    c = code.upper()
    if re.fullmatch(r"BYH[A-Z]-\d+|BYD\d{2,}[A-Z0-9]*", c): return "SUPPLIER_OR_PAINT_SYSTEM_STYLE_IDENTIFIER"
    if re.fullmatch(r"[A-Z]\d{3,5}", c): return "SUPPLIER_LISTED_NUMERIC_STYLE_CODE"
    if re.fullmatch(r"[A-Z]-\d{2}", c): return "SUPPLIER_LISTED_LEGACY_HYPHEN_CODE"
    if re.fullmatch(r"[A-Z]{2,3}|[A-Z]{1,2}\d{1,2}[A-Z]?|\d{2}[A-Z]{2}|[A-Z]{3}\d", c): return "SUPPLIER_LISTED_OEM_STYLE_CODE"
    return "UNCLASSIFIED_SUPPLIER_CODE"


SYSTEM = {  # source_id -> paint manufacturer/system (only what the source itself or the baseline notes state)
    "S29": "not stated (AU touch-up retailer: Colour Tubes)", "S30": "retailer states Axalta-sourced data (Cartouch AU)",
    "S31": "not stated (EU retailer: Carross)", "S32": "not stated (retailer: Touch Up Paint Factory)", "S226": "not stated (retailer: Touch Up Paint Factory)",
    "S227": "not stated (EU retailer: Carross)", "B6S02": "OEMatch mixed paint, vendor 'Alpha Automotive Paint' / The Spray Source (US retailer)",
    "B6S03": "CROP touch-up/aerosol paint (sold via NonPaints); site claims factory-original recipe",
}
URL = {"B6S02": "https://thespraysource.com/", "B6S03": "https://www.nonpaints.com/en/car-paint/car-paint-by-car-brand/byd"}

# ------------------------------------------------------------------------------------------------ parse new supplier products
def parse_oematch(title):
    t = re.sub(r"\s*\|\s*OEMatch.*$", "", title).strip()
    t = re.sub(r"\s+(Basecoat Paint|Complete Car Paint Kit|Touch Up Spray Paint)$", "", t, flags=re.I)
    t = re.sub(r"^BYD\s+", "", t, flags=re.I)
    toks = t.split()
    code = toks[-1].upper(); name = " ".join(toks[:-1])
    ok = bool(re.fullmatch(r"[A-Z0-9]{1,5}(-[A-Z0-9]{1,3})?", code))
    if not ok and toks and re.fullmatch(r"[A-Z]\d{1,3}C?", toks[0].upper()):   # title form '<CODE> <NAME> M.'
        code = toks[0].upper(); name = " ".join(toks[1:]); ok = True
    return code, name, ok


def parse_crop(slug):
    s = re.sub(r"^crop-byd-auto-", "", slug)
    s = re.sub(r"-(18ml-touch-up-pen|car-paint-.*|touch-up-pen.*|\d+ml.*)$", "", s)
    parts = s.split("-")
    if len(parts) > 1 and re.fullmatch(r"[a-z]", parts[0]) and re.fullmatch(r"\d{2}", parts[1]): code = (parts[0] + "-" + parts[1]).upper(); rest = parts[2:]
    else: code = parts[0].upper(); rest = parts[1:]
    return code, " ".join(w.capitalize() for w in rest)


new_products = {}   # (source, code, name) -> dict(urls=set())
for r in oem_raw:
    code, name, ok = parse_oematch(r["title"])
    k = ("B6S02", code, name.lower())
    d = new_products.setdefault(k, dict(source="B6S02", code=code, name=name, ok=ok, urls=set(), titles=set()))
    d["urls"].add(r["url"]); d["titles"].add(r["title"])
for r in crop_raw:
    code, name = parse_crop(r["slug"])
    k = ("B6S03", code, name.lower())
    d = new_products.setdefault(k, dict(source="B6S03", code=code, name=name, ok=True, urls=set(), titles=set()))
    d["urls"].add(r["url"]); d["titles"].add(r["slug"])

# ------------------------------------------------------------------------------------------------ name indexes
MATTE_EN = re.compile(r"\bmatt?e?\b", re.I)
zh_by_py = collections.defaultdict(set); gloss_by_en = collections.defaultdict(set)   # keys: (matte_flag, key)
for c in cols.values():
    zh = c["color_name_zh"]
    if zh:
        is_m = zh.startswith("哑光"); zh_by_py[(is_m, pinyin_key(zh[2:] if is_m else zh))].add(zh)
    g = c["name_en_gloss_unofficial"]
    if g: gloss_by_en[(bool(MATTE_EN.search(g)), norm_en(MATTE_EN.sub("", g)))].add(c["color_id"])
colours_by_zh = collections.defaultdict(list)
for cid, c in cols.items(): colours_by_zh[c["color_name_zh"]].append(cid)

# ------------------------------------------------------------------------------------------------ link set  (colour_id, code) -> evidence
LINK = {}   # key -> dict(sources:set, urls:set, bases:set, rec_ids:set, levels:set, names:set)
def add_link(cid, code, src, url, basis, rec, name=""):
    d = LINK.setdefault((cid, code), dict(sources=set(), urls=set(), bases=set(), recs=set(), names=set(), b5=None))
    d["sources"].add(src); d["urls"].add(url); d["bases"].add(basis); d["recs"].add(rec)
    if name: d["names"].add(name)
    return d

per_src = collections.defaultdict(lambda: collections.defaultdict(set))   # color -> source -> code set
for r in b5:   # carry Batch 5 links (baseline retailers)
    d = LINK.setdefault((r["color_id"], r["supplier_candidate_code"]), dict(sources=set(), urls=set(), bases=set(), recs=set(), names=set(), b5=r["record_id"]))
    d["sources"] |= set(r["source_ids"].split(";")); d["urls"] |= set(r["source_urls"].split()); d["bases"].add("baseline name equivalence (Batch 4/5 link " + r["link_id"] + ")")
    d["recs"].add(r["link_id"]); d["names"] |= {x for x in r["supplier_published_names"].split(" | ") if x}
for l in links:   # per-source code sets as in Batch 5
    for pid in l["candidate_ids"].split(";"):
        cd = cands.get(pid)
        if cd and l["oem_code"].upper() in tokens(cd["code_raw"]): per_src[l["color_id"]][cd["source_id"]] |= tokens(cd["code_raw"])

unmatched, near = [], []
CROSS_BRAND = []
for k, p in sorted(new_products.items()):
    is_matte = bool(MATTE_EN.search(p["name"])); p["matte"] = is_matte
    pk = (is_matte, norm_en(MATTE_EN.sub("", p["name"])))   # matte (哑光) variants carry their own codes: match matte only to matte names
    matched = set(); basis = ""
    if pk in zh_by_py:   # pinyin of a Chinese colour name equals the supplier's romanised name
        for zh in zh_by_py[pk]:
            matched |= set(colours_by_zh[zh]); basis = "PINYIN_EQUALS_CHINESE_NAME"
    if not matched and pk in gloss_by_en:
        matched = set(gloss_by_en[pk]); basis = "ENGLISH_NAME_EQUALS_RESEARCHER_GLOSS (unofficial)"
    cross = {cid for cid in matched if models[cols[cid]["model_id"]]["brand_id"] != "B2"}
    if cross: CROSS_BRAND.append((p["source"], p["code"], p["name"], len(cross)))
    matched -= cross   # supplier lists these under 'BYD'; a shared colour NAME is not evidence for Denza/Yangwang/Fangchengbao/Linghui
    if matched:
        for cid in matched:
            add_link(cid, p["code"], p["source"], sorted(p["urls"])[0], f"{p['source']} product '{p['name']}' {p['code']}: {basis}", "|".join(sorted(p["titles"]))[:200], p["name"])
            per_src[cid][p["source"]].add(p["code"])
        p["matched"] = sorted(matched); p["basis"] = basis
    else:
        p["matched"] = []; p["basis"] = ""; unmatched.append(p)
        # near pinyin match review (same length, <=1 differing syllable, >=5 syllables): never auto-linked
        sy = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in re.split(r"[\s\-_/]+", p["name"]) if w and w.lower() not in FINISH]
        for (km, key), zhs in zh_by_py.items():
            if km == is_matte and len(key) >= 8 and len(key) == len("".join(sy)):
                diff = sum(1 for a, b in zip(key, "".join(sy)) if a != b)
                if 0 < diff <= 2: near.append((p, sorted(zhs)[0], key, diff))

# ------------------------------------------------------------------------------------------------ colour-level status
col_status = {}
for cid in {k[0] for k in LINK}:
    sets = {frozenset(v) for v in per_src[cid].values()}
    codes = sorted({k[1] for k in LINK if k[0] == cid})
    if len(sets) > 1:
        nested = all(a <= b or b <= a for a in sets for b in sets)
        col_status[cid] = ("CONFLICTED", "SOURCES_DISAGREE_NESTED" if nested else "SOURCES_DISAGREE_NOT_NESTED")
    elif len(codes) > 1: col_status[cid] = ("POSSIBLE", "MULTI_CODE_ALIAS_GROUP")
    else: col_status[cid] = ("POSSIBLE", "SINGLE_CODE")

# ------------------------------------------------------------------------------------------------ discovered_codes.csv
F = ["record_id", "link_scope", "brand", "chinese_model_name", "international_model_name", "model_id", "production_year", "trim", "color_id", "original_chinese_color_name",
     "english_color_name", "english_color_name_basis", "paint_code", "code_type", "paint_manufacturer_system", "source_ids", "source_url", "evidence_description", "confidence_status",
     "code_ambiguity", "supplier_count", "name_match_basis", "source_record_ids", "date_accessed", "notes"]
rows = []
def mk(**k): rows.append(k)
for (cid, code), d in sorted(LINK.items(), key=lambda kv: (kv[0][0], kv[0][1])):
    c = cols[cid]; m = models[c["model_id"]]; st, amb = col_status[cid]
    srcset = sorted(d["sources"]); yr = years.get(c["model_year_id"], {}).get("year", "")
    mk(link_scope="COLOUR_RECORD", brand=brands[m["brand_id"]], chinese_model_name=m["name_zh"], international_model_name=m["model_key"] + (f" (aka {m['alt_names']})" if m["alt_names"] else ""),
       model_id=m["model_id"], production_year=yr, trim="", color_id=cid, original_chinese_color_name=c["color_name_zh"],
       english_color_name=c["name_en_gloss_unofficial"], english_color_name_basis="researcher gloss (UNOFFICIAL)" if c["name_en_gloss_unofficial"] else "", paint_code=code,
       code_type=code_type(code), paint_manufacturer_system="; ".join(sorted({SYSTEM.get(s, "not stated") for s in srcset})), source_ids=";".join(srcset),
       source_url=" ".join(sorted(d["urls"])), evidence_description="Third-party listing(s) give this code for a colour name matched to this colour record (" + "; ".join(sorted(d["bases"]))[:300] +
       "). Not an OEM document or vehicle label.", confidence_status=st, code_ambiguity=amb, supplier_count=len(srcset), name_match_basis="; ".join(sorted(d["bases"]))[:120],
       source_record_ids=";".join(sorted(d["recs"]))[:300], date_accessed=TODAY if any(s.startswith("B6") for s in srcset) else "see Batch 2-5 sources",
       notes="Model-year applicability is NOT confirmed: matching is by colour name." + ("" if yr else " No model year assigned in the baseline colour table."))

# type B: baseline candidates with a model listing that never produced a link
used = {(pid, l["oem_code"].upper()) for l in links for pid in l["candidate_ids"].split(";")}
alias = {}
for mid, m in models.items():
    for nm in [m["model_key"]] + [a.strip() for a in m["alt_names"].split(";") if a.strip()]:
        alias.setdefault((m["brand_id"], re.sub(r"[^a-z0-9]", "", nm.lower())), mid)
def map_model(listed):
    s = re.sub(r"^BYD\s+", "", listed.strip(), flags=re.I); key = re.sub(r"[^a-z0-9]", "", s.lower())
    for pref in ("B4", "B5", "B2", "B3", "B6"):
        for k in (key, re.sub(r"^yangwang", "", key), re.sub(r"^leopard", "bao", key)):
            if (pref, k) in alias: return alias[(pref, k)]
    return ""
LISTING_MODEL = {"LEOPARD 5": "M090", "LEOPARD 8": "M091", "YANGWANG U8": "M084", "YANGWANG U9": "M086"}   # Carross names for Fangchengbao Bao 5/8 and Yangwang U8/U9
for pid, cd in sorted(cands.items()):
    if cd["source_id"] in ("S33", "S34") or not cd["model_as_listed"] or cd["listing_level"] == "REJECTED": continue
    for tk in sorted(tokens(cd["code_raw"])):
        if (pid, tk) in used: continue
        lm = re.sub(r"^BYD\s+", "", cd["model_as_listed"].strip(), flags=re.I).upper()
        mid = LISTING_MODEL.get(lm) or map_model(cd["model_as_listed"]); m = models.get(mid)
        mk(link_scope="MODEL_LEVEL_LISTING", brand=brands[m["brand_id"]] if m else "BYD Group (listed under BYD)", chinese_model_name=m["name_zh"] if m else "",
           international_model_name=(m["model_key"] if m else cd["model_as_listed"]), model_id=mid, production_year=cd["year_as_listed"], trim="", color_id="", original_chinese_color_name="",
           english_color_name=cd["names_raw"], english_color_name_basis="supplier-published (NOT official)", paint_code=tk, code_type=code_type(tk), paint_manufacturer_system=SYSTEM.get(cd["source_id"], "not stated"),
           source_ids=cd["source_id"], source_url=cd["evidence_url"], evidence_description=f"Supplier listing ({cd['listing_level']}) gives {tk} for '{cd['names_raw']}' on '{cd['model_as_listed']}' {cd['year_as_listed']}; no Chinese colour record matched.",
           confidence_status="POSSIBLE", code_ambiguity="SINGLE_LISTING", supplier_count=1, name_match_basis="none (model-level supplier row)", source_record_ids=pid,
           date_accessed=(cd["fetched_utc"][:10] if cd["fetched_utc"] else "see Batch 2-4"), notes="Production year is the supplier's listed range, not verified. Chinese colour name not matched." + ("" if mid else " Supplier model not mapped to a catalog model."))
# type C: new-supplier products without any Chinese/English colour match
for p in unmatched:
    mk(link_scope="CODE_ONLY", brand="BYD Group (supplier lists under BYD; sub-brand not stated)", chinese_model_name="", international_model_name="", model_id="", production_year="", trim="", color_id="",
       original_chinese_color_name="", english_color_name=p["name"], english_color_name_basis="supplier romanisation/translation (NOT official)", paint_code=p["code"], code_type=code_type(p["code"]),
       paint_manufacturer_system=SYSTEM[p["source"]], source_ids=p["source"], source_url=" ".join(sorted(p["urls"])), evidence_description=f"Supplier product '{sorted(p['titles'])[0]}' gives {p['code']} for '{p['name']}'; supplier gives no model or year and no catalog colour name matched.",
       confidence_status="POSSIBLE", code_ambiguity="SINGLE_LISTING", supplier_count=1, name_match_basis="none", source_record_ids="|".join(sorted(p["titles"]))[:300], date_accessed=TODAY,
       notes="Code-only discovery: usable as a lead; model/year unknown." + ("" if p["ok"] else " Code token parsed from title may not be a code (format check failed)."))
for i, r in enumerate(rows, 1): r["record_id"] = f"B6D{i:05d}"
rows.sort(key=lambda r: (r["link_scope"], r["brand"], r["model_id"], r["production_year"], r["original_chinese_color_name"], r["paint_code"]))
wr("discovered_codes.csv", rows, F)

# ------------------------------------------------------------------------------------------------ lookup_model_year_colour.csv (practical pivot)
piv = collections.OrderedDict()
for r in rows:
    if r["link_scope"] == "CODE_ONLY" or (r["link_scope"] == "MODEL_LEVEL_LISTING" and not r["model_id"]): continue
    k = (r["brand"], r["model_id"], r["production_year"], r["original_chinese_color_name"] or ("(supplier name) " + r["english_color_name"]))
    d = piv.setdefault(k, dict(codes=[], types=set(), status=set(), srcs=set(), chinese_model=r["chinese_model_name"], intl=r["international_model_name"], eng=r["english_color_name"], amb=set(), cid=set()))
    d["codes"].append(r["paint_code"]); d["types"].add(r["code_type"]); d["status"].add(r["confidence_status"]); d["srcs"] |= set(r["source_ids"].split(";")); d["amb"].add(r["code_ambiguity"]); d["cid"].add(r["color_id"])
LF = ["brand", "chinese_model_name", "international_model_name", "model_id", "production_year", "original_chinese_color_name", "english_color_name_unofficial", "candidate_codes", "n_candidate_codes", "confidence_status", "code_ambiguity", "code_types", "supplier_source_ids", "color_ids", "row_scope", "how_to_use"]
lk = []
for (b, mid, yr, zh), d in sorted(piv.items()):
    lk.append(dict(brand=b, chinese_model_name=d["chinese_model"], international_model_name=d["intl"], model_id=mid, production_year=yr, original_chinese_color_name=zh, english_color_name_unofficial=d["eng"],
                   candidate_codes=" | ".join(sorted(set(d["codes"]))), n_candidate_codes=len(set(d["codes"])), confidence_status="/".join(sorted(d["status"])), code_ambiguity="/".join(sorted(d["amb"])),
                   code_types="/".join(sorted(d["types"])), supplier_source_ids=";".join(sorted(d["srcs"])), color_ids=";".join(sorted(d["cid"])), row_scope="COLOUR_RECORD" if d["cid"] - {""} else "MODEL_LEVEL_LISTING (supplier name; Chinese name not matched; years are supplier-listed)",
                   how_to_use="Candidate supplier codes only - confirm against the vehicle's own label, a VIN lookup at a BYD service centre, or a refinish system with BYD data before mixing paint."))
wr("lookup_model_year_colour.csv", lk, LF)

# ------------------------------------------------------------------------------------------------ conflicts.csv
CF = []
def cf(**k): CF.append(k)
agg = collections.OrderedDict()
for cid, (st, amb) in sorted(col_status.items()):
    c = cols[cid]; m = models[c["model_id"]]
    if amb.startswith("SOURCES_DISAGREE") or amb == "MULTI_CODE_ALIAS_GROUP":
        sig = json.dumps({s_: sorted(v) for s_, v in sorted(per_src[cid].items())}, ensure_ascii=False)
        a = agg.setdefault((amb, c["color_name_zh"] or c["name_en_gloss_unofficial"] or "(no Chinese name)", sig), dict(cids=[], brands=set(), models=set()))
        a["cids"].append(cid); a["brands"].add(brands[m["brand_id"]]); a["models"].add(m["model_key"])
for (amb, nm, sig), a in agg.items():
    dis = amb.startswith("SOURCES_DISAGREE")
    cf(conflict_type=amb, subject_scope=f"{len(a['cids'])} colour record(s) with this name and identical supplier code sets", brand="; ".join(sorted(a["brands"])), model="; ".join(sorted(a["models"]))[:200],
       color_id=";".join(a["cids"]), original_chinese_color_name=nm, values_in_conflict=sig if dis else " / ".join(sorted({k[1] for k in LINK if k[0] in a["cids"]})),
       sources_involved=";".join(sorted(json.loads(sig))), status_effect="CONFLICTED" if dis else "none (POSSIBLE with ambiguity flag)",
       resolution="OPEN - no OEM evidence to choose; no code selected", note="Suppliers list different code sets for this colour name." if dis else "Several codes listed for one alias group; which applies to the exact vehicle is unknown.")
# named, cross-source conflicts
WHITE = collections.defaultdict(set)
for r in rows:
    if r["original_chinese_color_name"] == "雪域白": WHITE[r["paint_code"]] |= set(r["source_ids"].split(";"))
cf(conflict_type="CODE_VS_CODE_SAME_NAME", subject_scope="Chinese colour name", brand="BYD", model="various", color_id="", original_chinese_color_name="雪域白",
   values_in_conflict=json.dumps({k: sorted(v) for k, v in sorted(WHITE.items())}, ensure_ascii=False), sources_involved="S31;S32;S226;S227;B6S02;B6S03", status_effect="colour records CONFLICTED/POSSIBLE per rule",
   resolution="OPEN", note="CROP lists W36C, OEMatch lists WA2, Carross lists 'W36C, WA2', TUPF lists BYHB-00001;W36C;WA2;WA8 for the same white. Possibly different years/markets or different systems; not resolvable from these sources.")
cf(conflict_type="FINISH_TYPE", subject_scope="Chinese colour name", brand="BYD", model="BYD Song (Autohome Q&A)", color_id="", original_chinese_color_name="雪域白",
   values_in_conflict="Autohome Q&A (B6S04): 普通漆 (solid, not metallic) | OEMatch/CROP: 'Xue Yu Bai Pearl' | Carross: 'SNOW WHITE-MET.'", sources_involved="B6S04;B6S02;B6S03;S227", status_effect="none",
   resolution="OPEN", note="Finish class differs between weak Q&A (unsourced) and retailers; finish affects which paint-system formula applies.")
cf(conflict_type="CODE_VS_CODE_SAME_NAME", subject_scope="Chinese colour name", brand="BYD", model="Seal", color_id="", original_chinese_color_name="亚特兰蒂斯灰",
   values_in_conflict="CROP (B6S03): HB5 'Atlantis Grey Metallic' | Carross (S31): HB6 | TUPF (S32): HB5, HB6", sources_involved="B6S03;S31;S32", status_effect="CONFLICTED",
   resolution="OPEN", note="Carried from Batch 5 and now supported by a further supplier for HB5.")
MATTE_PAIRS = []
byname_ = collections.defaultdict(dict)
for p in new_products.values():
    if p["source"] != "B6S02": continue
    byname_[norm_en(MATTE_EN.sub("", p["name"]))].setdefault(p["matte"], set()).add(p["code"])
for k_, v in sorted(byname_.items()):
    if True in v and False in v: MATTE_PAIRS.append(f"{k_}: gloss {'/'.join(sorted(v[False]))} vs matt {'/'.join(sorted(v[True]))}")
if MATTE_PAIRS:
    cf(conflict_type="GLOSS_VS_MATTE_CODE_PAIR", subject_scope="OEMatch name pairs", brand="BYD", model="various", color_id="", original_chinese_color_name="",
       values_in_conflict=" | ".join(MATTE_PAIRS), sources_involved="B6S02", status_effect="none (hypothesis only; used to stop matte codes being linked to gloss colours)", resolution="OPEN",
       note="OEMatch gives matte (Mat/Matt) variants their own codes (e.g. HB5 vs HB6, HA4 vs HC2, UAM vs UAN, LAT vs LAV). Hypothesis: part of the HB5/HB6-style conflicts are gloss-vs-matte variants, but Carross lists HB6 for the plain grey, so it stays unresolved.")
for p, zh, key, diff in near:
    cf(conflict_type="NAME_MATCH_REVIEW", subject_scope="unmatched supplier name (NOT linked)", brand="BYD", model="", color_id="", original_chinese_color_name=zh,
       values_in_conflict=f"supplier '{p['name']}' ({p['code']}, {p['source']}) vs catalog '{zh}' - romanisations differ in {diff} letter(s)", sources_involved=p["source"], status_effect="none (not linked)",
       resolution="OPEN - needs human review", note="Possible spelling/romanisation difference; deliberately not auto-linked.")
cf(conflict_type="LABEL_LOCATION", subject_scope="where the code is printed", brand="BYD", model="all", color_id="", original_chinese_color_name="",
   values_in_conflict="see Batch 5 conflicts B5C (OEM manuals vs retailer guidance vs Autohome Q&A S34)", sources_involved="B5S01-B5S07;S34", status_effect="none", resolution="OPEN (carried over)", note="Unchanged since Batch 5; no new label evidence found.")
for i, r in enumerate(CF, 1): r["conflict_id"] = f"B6C{i:04d}"
CFF = ["conflict_id", "conflict_type", "subject_scope", "brand", "model", "color_id", "original_chinese_color_name", "values_in_conflict", "sources_involved", "status_effect", "resolution", "note"]
wr("conflicts.csv", CF, CFF)

# ------------------------------------------------------------------------------------------------ formula_identifier_investigation.csv
def occ(tok):
    hits = [r for r in rows if r["paint_code"] == tok]
    base = [c for c in cands.values() if tok in tokens(c["code_raw"])]
    return hits, base
FI = []
spec = [("WA2", "雪域白 / Snow White", "OEM-style 3-char code on retailer lists; same white also listed as W36C (CROP) and WA8, BYHB-00001 (TUPF). Appears with Carross 'W36C, WA2' and OEMatch 'Xue Yu Bai Pearl WA2'. Reads like a BYD factory-style short code, but no OEM document confirms it and a competing code (W36C) exists for the same name."),
        ("HA4", "时光灰 / Time Grey (also 'Boulder Grey' / 'Harbour Grey' in some lists)", "OEM-style 3-char code; listed by Cartouch, TUPF and OEMatch ('Shi Guang Hui Metallic HA4') for 时光灰; Cartouch also lists it for 'Harbour Grey, Boulder Grey' alongside another code - alias-group ambiguity."),
        ("B9", "no colour name found", "Searched all baseline candidates, 167 OEMatch BYD titles and 9 CROP products: B9 does not occur. Cannot be classified; request the source (screenshot/URL/vehicle) where it was seen."),
        ("BYD007WA2", "no colour name found", "Not found in any source (baseline retailers, OEMatch, CROP, web searches for 'BYD007'). Structure is consistent with a paint-system style identifier that concatenates a maker prefix + index + a short code ending in the known retailer code WA2 - this is a HYPOTHESIS about format only, not evidence of what it is."),
        ("BYHB-00001", "white group (Snow/Great/Polar White etc.)", "Appears only in Touch Up Paint Factory lists, always bundled with W36C;WA2;WA8 for a multi-name white group. The 'BYHB-<digits>' format differs from the OEM-style short codes; it is more likely a supplier/paint-system internal identifier than a factory code, but this is unverified."),
        ("W36C", "雪域白 / Xue Yu Bai Pearl", "OEM-style 4-char code with a digit pattern different from the 3-letter codes; listed by CROP ('W36C Xue Yu Bai Pearl'), Carross and TUPF. Competes with WA2 for the same colour name.")]
for tok, nm, assess in spec:
    hits, base = occ(tok)
    srcset = sorted({s for r in hits for s in r["source_ids"].split(";")} | {c["source_id"] for c in base})
    for p in new_products.values():
        if p["code"] == tok: srcset = sorted(set(srcset) | {p["source"]})
    FI.append(dict(identifier=tok, associated_colour=nm, occurrences_in_discovered_codes=len(hits), occurrences_in_baseline_listings=len(base), sources=";".join(srcset),
                   code_type_by_format=code_type(tok), oem_status="UNVERIFIED (never VERIFIED_OEM)" if srcset else "NOT_FOUND_IN_ANY_SOURCE", assessment=assess))
wr("formula_identifier_investigation.csv", FI, ["identifier", "associated_colour", "occurrences_in_discovered_codes", "occurrences_in_baseline_listings", "sources", "code_type_by_format", "oem_status", "assessment"])

# ------------------------------------------------------------------------------------------------ sources.csv
SF = ["source_id", "title", "url_or_query", "publisher_or_type", "evidence_tier", "accessed", "retrieval_method", "access_result", "contains_paint_codes", "usable_as_oem_verification", "notes"]
SR = [
 dict(source_id="B6S01", title="BYD China - 售后服务 / maintenance protection page (精诚钣喷)", url_or_query="https://www.byd.com/cn/after-sales-service/maintenance-protection", publisher_or_type="BYD official website (OEM statement)",
      evidence_tier="PRIORITY_1 (OEM statement; no code table)", accessed=TODAY, retrieval_method="curl + text extraction", access_result="HTTP 200; page text read",
      contains_paint_codes="NO", usable_as_oem_verification="NO (no codes) - but authoritative on WHICH paint systems BYD's own service network uses",
      notes="States 精诚钣喷 selects three refinish brands - 阿克苏诺贝尔 (AkzoNobel), 巴斯夫 (BASF), 东来 (Donglai) - with '原厂数据、原厂配方' (OEM data, OEM formulas); some service shops cannot offer the service due to local environmental rules. Implies factory formulas are reached through those paint makers' systems, i.e. refinish 'formula identifiers' are paint-system references that map back to BYD factory data - not published as a public code table."),
 dict(source_id="B6S02", title="The Spray Source / Alpha Automotive Paint - BYD OEMatch product listings", url_or_query="https://thespraysource.com/search/suggest.json (query 'BYD ...'); product pages under https://thespraysource.com/products/byd-*",
      publisher_or_type="US retailer (mixed paint)", evidence_tier="PRIORITY_3_RETAILER", accessed=TODAY, retrieval_method="public Shopify search-suggest JSON, titles only (raw/oematch_byd_products.json)",
      access_result="167 BYD product titles (not exhaustive - suggest endpoint returns <=10 per query)", contains_paint_codes="YES (code + supplier romanised name in each title; no model or year)", usable_as_oem_verification="NO - POSSIBLE at most",
      notes="Uses pinyin names that can be matched to Chinese colour names. No Denza/Yangwang/Fangchengbao/Linghui entries found in probe queries (Xiaomi, Voyah and other Chinese brands exist)."),
 dict(source_id="B6S03", title="CROP via NonPaints - BYD AUTO touch-up/aerosol products", url_or_query="https://www.nonpaints.com/en/car-paint/car-paint-by-car-brand/byd (?p=1..3)", publisher_or_type="EU retailer of CROP paints",
      evidence_tier="PRIORITY_3_RETAILER", accessed=TODAY, retrieval_method="curl listing pages; product slugs parsed (raw/crop_byd_products.json)", access_result="9 colours x 2 formats; pages >=4 redirect to page 1 (listing is not exhaustive)",
      contains_paint_codes="YES (code in product name)", usable_as_oem_verification="NO", notes="Earlier baseline S03 (colour-code guidance page) had no codes; the product listings do."),
 dict(source_id="B6S04", title="Autohome Q&A 21849562 - 雪域白 paint type", url_or_query="https://www.autohome.com.cn/ask/21849562.html", publisher_or_type="Chinese automotive portal Q&A (unsourced, possibly machine-written)", evidence_tier="WEAK",
      accessed=TODAY, retrieval_method="curl, gb18030/utf-8 decode", access_result="HTTP 200", contains_paint_codes="NO", usable_as_oem_verification="NO", notes="Claims 雪域白 is 普通漆 (solid) not metallic; conflicts with 'Pearl'/'-MET.' in retailer names."),
 dict(source_id="B6S05", title="JD.com - 比亚迪漆 product/spec listing pages", url_or_query="https://www.jd.com/xinghao/6728c1a4185f131073de.html", publisher_or_type="Chinese e-commerce listing", evidence_tier="WEAK",
      accessed=TODAY, retrieval_method="curl", access_result="HTTP 200; colour names and fitment in titles only", contains_paint_codes="NO (no code found in page text)", usable_as_oem_verification="NO", notes="Chinese touch-up-pen listings name colours (德兰黑、时光灰、雪域白、亚特兰蒂斯灰、山脉灰) without codes."),
 dict(source_id="B6S06", title="Autohome chejiahao article 14912759 - 时光灰 touch-up colour mismatch", url_or_query="https://chejiahao.autohome.com.cn/info/14912759", publisher_or_type="Chinese user-generated article", evidence_tier="WEAK",
      accessed=TODAY, retrieval_method="curl (search snippet + page fetch)", access_result="HTTP 200", contains_paint_codes="NO", usable_as_oem_verification="NO", notes="Reports visible colour mismatch after dealer re-spray of Qin PLUS 时光灰 (and Yuan PLUS) - evidence that exact formula matters; no code."),
 dict(source_id="B6S07", title="Search record - Chinese paint-code terms", url_or_query="比亚迪原厂漆号 / 比亚迪车漆代码 / 比亚迪油漆配方 / 车身颜色编码 / 原厂颜色代码 / VIN油漆代码查询 / 比亚迪 补漆笔 颜色代码 / 汽车修补漆 色卡 配方查询系统",
      publisher_or_type="web search record", evidence_tier="n/a", accessed=TODAY, retrieval_method="web search (standard and extended)", access_result="NOT_FOUND - returned Autohome gallery pages, Tesla service docs, JD listings, no BYD code table",
      contains_paint_codes="NO", usable_as_oem_verification="NO", notes="No public Chinese-language page listing BYD factory paint codes was located."),
 dict(source_id="B6S08", title="Search record - VSM / 御华行 (Yuhuahang) / other Chinese formula databases", url_or_query="VSM 油漆配方 比亚迪; 御华行 汽车油漆 配方查询; 'BYD007'",
      publisher_or_type="web search record", evidence_tier="n/a", accessed=TODAY, retrieval_method="web search", access_result="NOT_FOUND - no VSM or Yuhuahang database page indexed; formula databases are login/app-gated",
      contains_paint_codes="NO", usable_as_oem_verification="NO", notes="Could not be investigated further without access; recorded as a gap, not as evidence of absence."),
 dict(source_id="B6S09", title="Search record - Denza / Yangwang / Fangchengbao / Linghui paint codes (Chinese + English)", url_or_query="仰望U8 OR 腾势N7 OR 方程豹豹5 车漆 颜色代码; 腾势 OR 仰望 OR 方程豹 OR 岚图 补漆 原厂色号; OEMatch probes 'Denza','Yangwang','Fangchengbao','Linghui'",
      publisher_or_type="web search / retailer probes", evidence_tier="n/a", accessed=TODAY, retrieval_method="web search + OEMatch suggest.json probes + Carross brand-page index", access_result="NOT_FOUND for Denza, Linghui; only Carross pages for Yangwang U8/U9 and Leopard (Bao) 5/8 (baseline S227)",
      contains_paint_codes="NO new", usable_as_oem_verification="NO", notes="Media articles give colour names only. Nonpaints has no Denza/Yangwang/Fangchengbao pages (404); Touch Up Paint Factory brand index returned 403."),
 dict(source_id="B6S10", title="Glasurit Color Online (BASF refinish colour database)", url_or_query="https://www.glasurit.com/uae/node/8034", publisher_or_type="Paint-manufacturer tool (login-gated)", evidence_tier="PRIORITY_3 pointer",
      accessed=TODAY, retrieval_method="search snippet", access_result="Tool exists; not publicly queryable", contains_paint_codes="UNKNOWN", usable_as_oem_verification="NO", notes="BASF is one of the three refinish brands BYD's service network names (B6S01); access would need a licensed account."),
 dict(source_id="B6S11", title="Online VIN decoders (vindecoder.eu, vincario, 7zap) - BYD", url_or_query="https://vindecoder.eu/byd ; https://vincario.com/vin-decoder/byd/ ; https://7zap.com/zh/vin-decoder/", publisher_or_type="Generic VIN decoders",
      evidence_tier="n/a", accessed=TODAY, retrieval_method="search snippet only", access_result="No colour code reported in snippets", contains_paint_codes="NO", usable_as_oem_verification="NO", notes="VIN structure does not encode paint; a colour code requires a manufacturer/dealer system."),
]
for sid, label in (("S29", "baseline"), ("S30", "baseline"), ("S31", "baseline"), ("S32", "baseline"), ("S226", "baseline"), ("S227", "baseline"), ("S34", "baseline")):
    s = srcs[sid]
    SR.append(dict(source_id=sid, title=s["title"], url_or_query=s["url"], publisher_or_type=s["source_type"], evidence_tier="PRIORITY_3_RETAILER" if sid != "S34" else "WEAK", accessed="Batches 2-5",
                   retrieval_method="carried over unchanged", access_result="see baseline", contains_paint_codes="YES (supplier codes)" if sid != "S34" else "NO (location claim only)", usable_as_oem_verification="NO", notes=s["notes"]))
wr("sources.csv", SR, SF)

# ------------------------------------------------------------------------------------------------ stats
st = collections.Counter(r["confidence_status"] for r in rows); sc = collections.Counter(r["link_scope"] for r in rows)
brand_cov = collections.Counter(r["brand"] for r in rows)
brands_lookup = collections.Counter(r["brand"] for r in lk)
new_codes = sorted({p["code"] for p in new_products.values()} - {tk for c in cands.values() for tk in tokens(c["code_raw"])})
STATS = dict(discovered_rows=len(rows), by_scope=dict(sc), by_status=dict(st), by_brand=dict(brand_cov), lookup_rows=len(lk), lookup_by_brand=dict(brands_lookup),
             code_types=dict(collections.Counter(r["code_type"] for r in rows)), distinct_codes=len({r["paint_code"] for r in rows}),
             new_supplier_products=len(new_products), new_products_matched=sum(1 for p in new_products.values() if p["matched"]), new_products_unmatched=len(unmatched), codes_new_to_catalog=new_codes,
             new_links_added=len([1 for k, d in LINK.items() if not d["b5"]]), colour_records_with_candidate=len(col_status), conflicts=dict(collections.Counter(r["conflict_type"] for r in CF)),
             near_name_reviews=len(near), cross_brand_name_matches_not_linked=len(CROSS_BRAND), colour_status=dict(collections.Counter(v[0] for v in col_status.values())))
json.dump(STATS, open(os.path.join(OUT, "stats_batch6.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(STATS, ensure_ascii=False, indent=1))
