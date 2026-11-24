#!/usr/bin/env python3
"""
Batch 7 - OEM paint-code deep discovery (BYD Group).  Reproducible build.

Adds one new supplier source (DipYourCar 'Luna OEM Basecoat', 92 BYD titles) to the Batch 6 matching pipeline, re-derives
statuses, reports ONLY the rows that are new/changed versus Batch 6, and writes the VIN-method research tables.
Self-check: running the pipeline WITHOUT the new source must reproduce Batch 6's discovered_codes.csv exactly (keys + statuses).

Inputs (read-only): catalog_union/*.csv, batch5/oem_paint_codes.csv, batch6/discovered_codes.csv, batch6/raw/*.json, batch7/raw/*.json
Outputs: batch7/{discovered_codes.csv, sources.csv, vin_research.csv, conflicts.csv, source_lineage_analysis.csv,
         verification_sample_plan.csv, vin_evidence_template.csv, stats_batch7.json}
Requires pypinyin.
"""
import csv, os, re, json, collections, itertools
from pypinyin import lazy_pinyin

HERE = os.path.dirname(os.path.abspath(__file__)); U = f"{HERE}/catalog_union"; B5 = f"{HERE}/batch5"; B6 = f"{HERE}/batch6"; B7 = f"{HERE}/batch7"
TODAY = "2026-11-24"


def rd(p):
    with open(p, encoding="utf-8", newline="") as f: return list(csv.DictReader(f))


def wr(name, rows, fields):
    with open(f"{B7}/{name}", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in fields})


brands = {b["brand_id"]: b["name"] for b in rd(f"{U}/brands_all.csv")}
models = {m["model_id"]: m for m in rd(f"{U}/models_all.csv")}
years = {y["model_year_id"]: y for y in rd(f"{U}/model_years_all.csv")}
cols = {c["color_id"]: c for c in rd(f"{U}/factory_colors_all.csv")}
links = rd(f"{U}/color_paint_code_links_all.csv")
cands = {c["candidate_id"]: c for c in rd(f"{U}/paint_code_candidates_all.csv")}
srcs = {s["source_id"]: s for s in rd(f"{U}/sources_all.csv")}
b5 = rd(f"{B5}/oem_paint_codes.csv"); b6rows = rd(f"{B6}/discovered_codes.csv")
RAWS = {"B6S02": json.load(open(f"{B6}/raw/oematch_byd_products.json", encoding="utf-8")), "B6S03": json.load(open(f"{B6}/raw/crop_byd_products.json", encoding="utf-8")),
        "B7S02": json.load(open(f"{B7}/raw/dipyourcar_byd_products.json", encoding="utf-8"))}

LINEAGE = {"S29": "ColourTubes", "S30": "Cartouch", "S31": "Carross", "S227": "Carross", "S32": "TouchUpPaintFactory", "S226": "TouchUpPaintFactory",
           "B6S02": "US-Luna/OEMatch (shared names)", "B7S02": "US-Luna/OEMatch (shared names)", "B6S03": "CROP"}
SYSTEM = {"S29": "not stated (AU touch-up retailer: Colour Tubes)", "S30": "retailer states Axalta-sourced data (Cartouch AU)", "S31": "not stated (EU retailer: Carross)", "S32": "not stated (retailer: Touch Up Paint Factory)",
          "S226": "not stated (retailer: Touch Up Paint Factory)", "S227": "not stated (EU retailer: Carross)", "B6S02": "OEMatch mixed paint (The Spray Source / Alpha Automotive Paint)",
          "B6S03": "CROP touch-up/aerosol paint (NonPaints)", "B7S02": "'Luna OEM Basecoat' (DipYourCar, US retailer)"}


# ---------------------------------------------------------------------------------------------- helpers (as Batch 6)
def tokens(raw): return {t.strip().upper() for t in re.split(r"[;,/]+|\s+\|\s+", raw or "") if t.strip()}
FINISH6 = {"metallic", "pearl", "mat", "solid", "m", "m.", "p.m.", "p.m", "p.x", "met", "met.", "pm", "pearlescent", "mica", "x"}                       # Batch 6 normalisation
FINISH7 = FINISH6 | {"matt", "matte", "p", "p.", "p.x.", "x.", "s1"}                                                                                        # Batch 7: also strips 'P.', 'X.', 'S1' abbreviations
FINISH = FINISH6
MATTE_EN = re.compile(r"\bmatt?e?\b", re.I)
def norm_en(s):
    w = [x for x in re.split(r"[\s\-_/]+", (s or "").lower()) if x and x not in FINISH]
    return "".join(re.sub(r"[^a-z0-9]", "", x) for x in w)
def pinyin_key(zh): return "".join(re.sub(r"[^a-z0-9]", "", s.lower()) for s in lazy_pinyin(re.sub(r"[^一-鿿]", "", zh)))
def code_type(code):
    c = code.upper()
    if re.fullmatch(r"BYH[A-Z]-\d+|BYD\d{2,}[A-Z0-9]*", c): return "SUPPLIER_OR_PAINT_SYSTEM_STYLE_IDENTIFIER"
    if re.fullmatch(r"[A-Z]\d{3,5}", c): return "SUPPLIER_LISTED_NUMERIC_STYLE_CODE"
    if re.fullmatch(r"[A-Z]-\d{2}", c): return "SUPPLIER_LISTED_LEGACY_HYPHEN_CODE"
    if re.fullmatch(r"[A-Z]{2,3}|[A-Z]{1,2}\d{1,2}[A-Z]?|\d{2}[A-Z]{2}|[A-Z]{3}\d", c): return "SUPPLIER_LISTED_OEM_STYLE_CODE"
    return "UNCLASSIFIED_SUPPLIER_CODE"
def code_role(ct): return "FORMULA_SYSTEM_REFERENCE_CANDIDATE" if ct == "SUPPLIER_OR_PAINT_SYSTEM_STYLE_IDENTIFIER" else ("UNCLASSIFIED" if ct.startswith("UNCLASSIFIED") else "VEHICLE_PAINT_CODE_CANDIDATE")


def parse_title(src, rec):
    """-> (code, name, variant, ok)"""
    if src == "B6S03":
        s = re.sub(r"^crop-byd-auto-", "", rec["slug"]); s = re.sub(r"-(18ml-touch-up-pen|car-paint-.*|touch-up-pen.*|\d+ml.*)$", "", s); parts = s.split("-")
        if len(parts) > 1 and re.fullmatch(r"[a-z]", parts[0]) and re.fullmatch(r"\d{2}", parts[1]): code = (parts[0] + "-" + parts[1]).upper(); rest = parts[2:]
        else: code = parts[0].upper(); rest = parts[1:]
        return code, " ".join(w.capitalize() for w in rest), "", True, rec["url"], rec["slug"]
    t = rec["title"]
    t = re.sub(r"\s*\|\s*(OEMatch|Luna OEM Basecoat).*$", "", t).strip()
    t = re.sub(r"\s+(Basecoat Paint|Complete Car Paint Kit|Touch Up Spray Paint)$", "", t, flags=re.I); t = re.sub(r"^BYD\s+", "", t, flags=re.I)
    toks = t.split(); variant = ""
    code = toks[-1].upper(); name = " ".join(toks[:-1]); ok = bool(re.fullmatch(r"[A-Z0-9]{1,5}(-[A-Z0-9]{1,3})?", code))
    if not ok and toks and re.fullmatch(r"[A-Z]\d{1,3}C?", toks[0].upper()): code = toks[0].upper(); name = " ".join(toks[1:]); ok = True
    if len(toks) > 2 and toks[-2].upper() == "S1": variant = "S1"
    return code, name, variant, ok, rec["url"], rec["title"]


def run(new_sources, finish, merge_lineage=False):
    """Batch 6 pipeline with the given new supplier sources. Returns dict of results."""
    global FINISH
    FINISH = finish
    products = {}
    for src in new_sources:
        for rec in RAWS[src]:
            code, name, variant, ok, url, title = parse_title(src, rec)
            k = (src, code, name.lower()); d = products.setdefault(k, dict(source=src, code=code, name=name, ok=ok, variant=set(), urls=set(), titles=set()))
            d["urls"].add(url); d["titles"].add(title)
            if variant: d["variant"].add(variant)
    zh_by_py = collections.defaultdict(set); gloss_by_en = collections.defaultdict(set); colours_by_zh = collections.defaultdict(list)
    for cid, c in cols.items():
        zh = c["color_name_zh"]; colours_by_zh[zh].append(cid)
        if zh: is_m = zh.startswith("哑光"); zh_by_py[(is_m, pinyin_key(zh[2:] if is_m else zh))].add(zh)
        g = c["name_en_gloss_unofficial"]
        if g: gloss_by_en[(bool(MATTE_EN.search(g)), norm_en(MATTE_EN.sub("", g)))].add(cid)
    LINK = {}; per_src = collections.defaultdict(lambda: collections.defaultdict(set))
    for r in b5:
        d = LINK.setdefault((r["color_id"], r["supplier_candidate_code"]), dict(sources=set(), urls=set(), bases=set(), recs=set(), names=set(), b5=r["record_id"]))
        d["sources"] |= set(r["source_ids"].split(";")); d["urls"] |= set(r["source_urls"].split()); d["bases"].add("baseline name equivalence (Batch 4/5 link " + r["link_id"] + ")"); d["recs"].add(r["link_id"])
    for l in links:
        for pid in l["candidate_ids"].split(";"):
            cd = cands.get(pid)
            if cd and l["oem_code"].upper() in tokens(cd["code_raw"]): per_src[l["color_id"]][cd["source_id"]] |= tokens(cd["code_raw"])
    def add_link(cid, code, src, url, basis, rec):
        d = LINK.setdefault((cid, code), dict(sources=set(), urls=set(), bases=set(), recs=set(), names=set(), b5=None)); d["sources"].add(src); d["urls"].add(url); d["bases"].add(basis); d["recs"].add(rec)
    unmatched, near, cross = [], [], []
    for k, p in sorted(products.items()):
        is_matte = bool(MATTE_EN.search(p["name"])); p["matte"] = is_matte
        pk = (is_matte, norm_en(MATTE_EN.sub("", p["name"]))); matched = set(); basis = ""
        if pk in zh_by_py:
            for zh in zh_by_py[pk]: matched |= set(colours_by_zh[zh]); basis = "PINYIN_EQUALS_CHINESE_NAME"
        if not matched and pk in gloss_by_en: matched = set(gloss_by_en[pk]); basis = "ENGLISH_NAME_EQUALS_RESEARCHER_GLOSS (unofficial)"
        cr = {cid for cid in matched if models[cols[cid]["model_id"]]["brand_id"] != "B2"}
        if cr: cross.append((p["source"], p["code"], p["name"], len(cr)))
        matched -= cr
        if matched:
            for cid in matched:
                add_link(cid, p["code"], p["source"], sorted(p["urls"])[0], f"{p['source']} product '{p['name']}' {p['code']}: {basis}", "|".join(sorted(p["titles"]))[:200]); per_src[cid][p["source"]].add(p["code"])
            p["matched"] = sorted(matched); p["basis"] = basis
        else:
            p["matched"] = []; p["basis"] = ""; unmatched.append(p)
            sy = "".join(re.sub(r"[^a-z0-9]", "", w.lower()) for w in re.split(r"[\s\-_/]+", p["name"]) if w and w.lower() not in FINISH)
            for (km, key), zhs in zh_by_py.items():
                if km == is_matte and len(key) >= 8 and len(key) == len(sy):
                    diff = sum(1 for a, b in zip(key, sy) if a != b)
                    if 0 < diff <= 2: near.append((p, sorted(zhs)[0], key, diff))
    per_eff = collections.defaultdict(lambda: collections.defaultdict(set))   # code sets per independent-opinion unit (lineage when merging)
    for cid, d_ in per_src.items():
        for s_, v in d_.items(): per_eff[cid][LINEAGE.get(s_, s_) if merge_lineage else s_] |= v
    col_status = {}
    for cid in {k[0] for k in LINK}:
        sets = {frozenset(v) for v in per_eff[cid].values()}; codes = sorted({k[1] for k in LINK if k[0] == cid})
        if len(sets) > 1: col_status[cid] = ("CONFLICTED", "SOURCES_DISAGREE_NESTED" if all(a <= b or b <= a for a in sets for b in sets) else "SOURCES_DISAGREE_NOT_NESTED")
        elif len(codes) > 1: col_status[cid] = ("POSSIBLE", "MULTI_CODE_ALIAS_GROUP")
        else: col_status[cid] = ("POSSIBLE", "SINGLE_CODE")
    return dict(products=products, LINK=LINK, per_src=per_src, per_eff=per_eff, unmatched=unmatched, near=near, cross=cross, col_status=col_status)


def build_rows(R, new_sources):
    rows = []; LINK, col_status, products = R["LINK"], R["col_status"], R["products"]
    for (cid, code), d in sorted(LINK.items()):
        c = cols[cid]; m = models[c["model_id"]]; st, amb = col_status[cid]; ss = sorted(d["sources"]); yr = years.get(c["model_year_id"], {}).get("year", "")
        var = sorted({v for p in products.values() if p["code"] == code and p["source"] in ss for v in p["variant"]})
        rows.append(dict(link_scope="COLOUR_RECORD", key=("C", cid, code), brand=brands[m["brand_id"]], chinese_model_name=m["name_zh"], international_model_name=m["model_key"] + (f" (aka {m['alt_names']})" if m["alt_names"] else ""),
                         model_id=m["model_id"], production_year=yr, color_id=cid, original_chinese_color_name=c["color_name_zh"], english_color_name=c["name_en_gloss_unofficial"],
                         english_color_name_basis="researcher gloss (UNOFFICIAL)" if c["name_en_gloss_unofficial"] else "", paint_code=code, variant_marker=" ".join(var), source_ids=ss, source_url=" ".join(sorted(d["urls"])),
                         evidence_description="Third-party listing(s) give this code for a colour name matched to this colour record (" + "; ".join(sorted(d["bases"]))[:260] + "). Not an OEM document or vehicle label.",
                         confidence_status=st, code_ambiguity=amb, notes="Model-year applicability NOT confirmed: matching is by colour name." + ("" if yr else " No model year assigned in the baseline colour table.")))
    for p in R["unmatched"]:
        if p["source"] not in new_sources: continue
        rows.append(dict(link_scope="CODE_ONLY", key=("O", p["source"], p["code"], norm_en(p["name"])), brand="BYD Group (supplier lists under BYD; sub-brand not stated)", chinese_model_name="", international_model_name="", model_id="", production_year="", color_id="",
                         original_chinese_color_name="", english_color_name=p["name"], english_color_name_basis="supplier romanisation/translation (NOT official)", paint_code=p["code"], variant_marker=" ".join(sorted(p["variant"])), source_ids=[p["source"]],
                         source_url=" ".join(sorted(p["urls"])), evidence_description=f"Supplier product '{sorted(p['titles'])[0]}' gives {p['code']} for '{p['name']}'; no model/year and no catalog colour name matched.",
                         confidence_status="POSSIBLE", code_ambiguity="SINGLE_LISTING", notes="Code-only lead; model/year unknown." + ("" if p["ok"] else " Code token parsed from title may not be a code.")))
    return rows


# ---------------------------------------------------------------------------------------------- self-check vs Batch 6
RB6 = run(["B6S02", "B6S03"], FINISH6); rows_b6_re = [r for r in build_rows(RB6, ["B6S02", "B6S03"]) if r["link_scope"] != "MODEL_LEVEL_LISTING"]
b6_key = {}
for r in b6rows:
    if r["link_scope"] == "COLOUR_RECORD": b6_key[("C", r["color_id"], r["paint_code"])] = r["confidence_status"]
    elif r["link_scope"] == "CODE_ONLY": b6_key[("O", r["source_ids"], r["paint_code"], norm_en(r["english_color_name"]))] = r["confidence_status"]
re_key = {r["key"]: r["confidence_status"] for r in rows_b6_re}
SELF_CHECK = dict(batch6_keys=len(b6_key), reproduced_keys=len(re_key), identical=(b6_key == re_key))
assert SELF_CHECK["identical"], f"pipeline does not reproduce Batch 6: {SELF_CHECK} missing={list(set(b6_key)-set(re_key))[:3]} extra={list(set(re_key)-set(b6_key))[:3]}"

# ---------------------------------------------------------------------------------------------- Batch 7 run (adds DipYourCar)
NEW = ["B6S02", "B6S03", "B7S02"]; R7 = run(NEW, FINISH7, merge_lineage=True); rows7 = build_rows(R7, NEW)
b6_sources = {}
for r in b6rows:
    if r["link_scope"] == "COLOUR_RECORD": b6_sources[("C", r["color_id"], r["paint_code"])] = set(r["source_ids"].split(";"))
b6_codeonly = {r["paint_code"] for r in b6rows if r["link_scope"] == "CODE_ONLY"}
out = []
for r in rows7:
    k = r["key"]; srcset = set(r["source_ids"])
    if r["link_scope"] == "CODE_ONLY":
        if r["source_ids"] != ["B7S02"]: continue     # only DipYourCar code-only rows are new; OEMatch/CROP ones are Batch 6
        delta = "SOURCE_ADDED_SAME_LINEAGE" if r["paint_code"] in b6_codeonly else "NEW_ROW"; prev = ""
    else:
        if k not in b6_key: delta = "NEW_ROW"; prev = ""
        elif b6_key[k] != r["confidence_status"]: delta = "STATUS_CHANGED"; prev = b6_key[k]
        elif srcset != b6_sources.get(k, set()): delta = "SOURCE_ADDED"; prev = b6_key[k]
        else: continue
        prev = prev or b6_key.get(k, "")
    r["delta"] = delta; r["batch6_status"] = prev; out.append(r)

now_code_only = {(r["source_ids"][0], r["paint_code"]) for r in rows7 if r["link_scope"] == "CODE_ONLY"}
RESOLVED = sorted(k for k in b6_key if k[0] == "O" and (k[1], k[2]) not in now_code_only)
ENR = []
for i, r in enumerate(sorted(out, key=lambda r: (r["delta"], r["link_scope"], r["brand"], r["model_id"], r["production_year"], r["original_chinese_color_name"], r["paint_code"])), 1):
    ss = sorted(r["source_ids"]); lin = sorted({LINEAGE[s] for s in ss if s in LINEAGE}); ct = code_type(r["paint_code"])
    ENR.append(dict(record_id=f"B7D{i:05d}", delta=r["delta"], link_scope=r["link_scope"], brand=r["brand"], chinese_model_name=r["chinese_model_name"], international_model_name=r["international_model_name"], model_id=r["model_id"],
                    production_year=r["production_year"], color_id=r["color_id"], original_chinese_color_name=r["original_chinese_color_name"], english_color_name=r["english_color_name"], english_color_name_basis=r["english_color_name_basis"],
                    paint_code=r["paint_code"], code_type=ct, code_role=code_role(ct), variant_marker=r["variant_marker"], paint_manufacturer_system="; ".join(sorted({SYSTEM.get(s, "not stated") for s in ss})),
                    source_ids=";".join(ss), source_lineages=" | ".join(lin), independent_lineage_count=len(lin), source_url=r["source_url"], evidence_description=r["evidence_description"],
                    confidence_status=r["confidence_status"], batch6_status=r["batch6_status"], code_ambiguity=r["code_ambiguity"], date_accessed=TODAY if any(s.startswith("B7") for s in ss) else "Batches 2-6", notes=r["notes"]))
FD = ["record_id", "delta", "link_scope", "brand", "chinese_model_name", "international_model_name", "model_id", "production_year", "color_id", "original_chinese_color_name", "english_color_name", "english_color_name_basis", "paint_code",
      "code_type", "code_role", "variant_marker", "paint_manufacturer_system", "source_ids", "source_lineages", "independent_lineage_count", "source_url", "evidence_description", "confidence_status", "batch6_status", "code_ambiguity", "date_accessed", "notes"]
wr("discovered_codes.csv", ENR, FD)

# ---------------------------------------------------------------------------------------------- lineage analysis
def src_names(sid):    # source -> {code -> set(normalised english names)}
    d = collections.defaultdict(set)
    if sid in RAWS:
        for k, p in R7["products"].items():
            if p["source"] == sid: d[p["code"]].add(norm_en(MATTE_EN.sub("", p["name"])))
    else:
        for c in cands.values():
            if c["source_id"] != sid: continue
            for tk in tokens(c["code_raw"]):
                for nm in re.split(r"[,|]", c["names_raw"] or ""): d[tk].add(norm_en(re.sub(r"-MET\.?|¤MAT|\bMAT\b", "", nm.strip(), flags=re.I)))
    return d
SIDS = ["B6S02", "B7S02", "B6S03", "S29", "S30", "S31", "S32", "S226", "S227"]
SN = {s: src_names(s) for s in SIDS}; LA = []
for a, b in itertools.combinations(SIDS, 2):
    if LINEAGE[a] == LINEAGE[b] and a in ("S226", "S227", "S31", "S32"): continue
    sc = set(SN[a]) & set(SN[b]); sn = sum(1 for c_ in sc if (SN[a][c_] & SN[b][c_]) - {""})
    LA.append(dict(source_a=a, source_b=b, lineage_a=LINEAGE[a], lineage_b=LINEAGE[b], codes_a=len(SN[a]), codes_b=len(SN[b]), shared_codes=len(sc), shared_codes_with_identical_normalised_name=sn,
                   identical_name_share=f"{100*sn/len(sc):.0f}%" if sc else "n/a",
                   reading="SAME UPSTREAM (near-identical romanised names and abbreviations)" if sc and sn / len(sc) >= 0.6 and LINEAGE[a] == LINEAGE[b] else ("names differ - independence neither shown nor refuted" if sc else "no shared codes")))
wr("source_lineage_analysis.csv", LA, ["source_a", "source_b", "lineage_a", "lineage_b", "codes_a", "codes_b", "shared_codes", "shared_codes_with_identical_normalised_name", "identical_name_share", "reading"])
oem_dyc = next(r for r in LA if (r["source_a"], r["source_b"]) == ("B6S02", "B7S02"))

# ---------------------------------------------------------------------------------------------- conflicts.csv (full recompute)
per_src, per_eff, col_status, LINK = R7["per_src"], R7["per_eff"], R7["col_status"], R7["LINK"]; CF = []
def cf(**k): CF.append(k)
agg = collections.OrderedDict()
for cid, (st, amb) in sorted(col_status.items()):
    c = cols[cid]; m = models[c["model_id"]]
    if amb.startswith("SOURCES_DISAGREE") or amb == "MULTI_CODE_ALIAS_GROUP":
        sig = json.dumps({s_: sorted(v) for s_, v in sorted(per_eff[cid].items())}, ensure_ascii=False)
        a = agg.setdefault((amb, c["color_name_zh"] or c["name_en_gloss_unofficial"] or "(no Chinese name)", sig), dict(cids=[], brands=set(), models=set())); a["cids"].append(cid); a["brands"].add(brands[m["brand_id"]]); a["models"].add(m["model_key"])
for (amb, nm, sig), a in agg.items():
    dis = amb.startswith("SOURCES_DISAGREE")
    cf(conflict_type=amb, subject_scope=f"{len(a['cids'])} colour record(s), identical supplier code sets", brand="; ".join(sorted(a["brands"])), model="; ".join(sorted(a["models"]))[:200], color_id=";".join(a["cids"]), original_chinese_color_name=nm,
       values_in_conflict=sig if dis else " / ".join(sorted({k[1] for k in LINK if k[0] in a["cids"]})), sources_involved=";".join(sorted({x for c_ in a["cids"] for x in per_src[c_]})), status_effect="CONFLICTED" if dis else "none (POSSIBLE with ambiguity flag)",
       resolution="OPEN - no OEM evidence; no code selected", note="Independent supplier lineages (same-site and same-upstream sources merged) list different code sets." if dis else "Several codes for one alias group; which applies to the exact vehicle is unknown.")
WHITE = collections.defaultdict(set)
for (cid, code), d in LINK.items():
    if cols[cid]["color_name_zh"] == "雪域白": WHITE[code] |= d["sources"]
cf(conflict_type="CODE_VS_CODE_SAME_NAME", subject_scope="Chinese colour name", brand="BYD", model="various", color_id="", original_chinese_color_name="雪域白", values_in_conflict=json.dumps({k: sorted(v) for k, v in sorted(WHITE.items())}, ensure_ascii=False),
   sources_involved=";".join(sorted({s for v in WHITE.values() for s in v})), status_effect="CONFLICTED/POSSIBLE per rule", resolution="OPEN", note="W36C vs WA2 vs WA8 vs BYHB-00001 for the same colour name (Batch 6); DipYourCar adds its own WA2 listing but shares OEMatch's upstream, so it does not break the tie.")
cf(conflict_type="CODE_VS_CODE_SAME_NAME", subject_scope="Chinese colour name", brand="BYD", model="Seal", color_id="", original_chinese_color_name="亚特兰蒂斯灰", values_in_conflict="HB5 (CROP, OEMatch, TUPF) | HB6 (Carross, TUPF; OEMatch/DipYourCar label HB6 'Matt')",
   sources_involved="B6S03;B6S02;B7S02;S31;S32", status_effect="CONFLICTED", resolution="OPEN", note="Matte-variant hypothesis (Batch 6) now has two retailers from ONE lineage; still unverified.")
cf(conflict_type="RETAILER_LINEAGE", subject_scope="independence of retailer evidence", brand="BYD", model="all", color_id="", original_chinese_color_name="",
   values_in_conflict=f"OEMatch (B6S02) vs DipYourCar (B7S02): {oem_dyc['shared_codes']} shared codes, {oem_dyc['shared_codes_with_identical_normalised_name']} with identical normalised romanised names ({oem_dyc['identical_name_share']})", sources_involved="B6S02;B7S02",
   status_effect="none (reinforces rule: repetition is not corroboration)", resolution="OPEN", note="Two US retailers carry the same romanisations, abbreviations and 'Doctor Black'-style translations: one upstream database. Counted as ONE lineage in independent_lineage_count.")
cf(conflict_type="COLOUR_CLASS_VS_CODE", subject_scope="vehicle certificate", brand="BYD Group", model="all", color_id="", original_chinese_color_name="",
   values_in_conflict="GB/T 21085-2020 certificate field: body colour as one of 10 classes (白灰黄粉红紫绿蓝棕黑) | retailer lists: 154+ distinct codes", sources_involved="B7S05", status_effect="none",
   resolution="OPEN (limit, not error)", note="The Chinese 合格证 can only narrow a colour to a class; it cannot choose between e.g. WA2 and W36C.")
cf(conflict_type="LABEL_LOCATION", subject_scope="where a BYD colour code is printed", brand="BYD", model="all", color_id="", original_chinese_color_name="", values_in_conflict="see Batch 5/6: OEM manuals (nameplate without paint item) vs retailer guidance vs Autohome Q&A S34",
   sources_involved="B5S01;B5S02;B5S03;B5S04;B5S05;B5S06;B5S07;B7S12;B7S13;B7S14;B7S15;S34;B6S10", status_effect="none", resolution="OPEN (carried over)", note="No new label evidence in Batch 7.")
cf(conflict_type="FINISH_TYPE", subject_scope="Chinese colour name", brand="BYD", model="BYD Song (Autohome Q&A)", color_id="", original_chinese_color_name="雪域白", values_in_conflict="Autohome Q&A: 普通漆 (solid) | retailers: Pearl / -MET.", sources_involved="B6S04;B6S02;B6S03;B7S02;S227", status_effect="none", resolution="OPEN (carried over)", note="")
mp = collections.defaultdict(dict)
for k_, p in R7["products"].items():
    if p["source"] in ("B6S02", "B7S02"): mp[norm_en(MATTE_EN.sub("", p["name"]))].setdefault(p["matte"], set()).add(p["code"])
pairs = [f"{k_}: gloss {'/'.join(sorted(v[False]))} vs matt {'/'.join(sorted(v[True]))}" for k_, v in sorted(mp.items()) if True in v and False in v]
cf(conflict_type="GLOSS_VS_MATTE_CODE_PAIR", subject_scope="OEMatch + DipYourCar (one lineage)", brand="BYD", model="various", color_id="", original_chinese_color_name="", values_in_conflict=" | ".join(pairs), sources_involved="B6S02;B7S02",
   status_effect="none (hypothesis; matte codes never linked to gloss colours)", resolution="OPEN", note="Pairs are repeated by two retailers of the same lineage, so the hypothesis is not strengthened as independent evidence.")
for p, zh, key, diff in R7["near"]:
    cf(conflict_type="NAME_MATCH_REVIEW", subject_scope="unmatched supplier name (NOT linked)", brand="BYD", model="", color_id="", original_chinese_color_name=zh, values_in_conflict=f"supplier '{p['name']}' ({p['code']}, {p['source']}) vs catalog '{zh}' - differ in {diff} letter(s)",
       sources_involved=p["source"], status_effect="none (not linked)", resolution="OPEN - human review", note="Possible romanisation difference; not auto-linked.")
for i, r in enumerate(CF, 1): r["conflict_id"] = f"B7C{i:04d}"
wr("conflicts.csv", CF, ["conflict_id", "conflict_type", "subject_scope", "brand", "model", "color_id", "original_chinese_color_name", "values_in_conflict", "sources_involved", "status_effect", "resolution", "note"])

# ---------------------------------------------------------------------------------------------- verification sample plan
PRIO = {"M020": (1, "Seal"), "M026": (2, "Dolphin"), "M028": (3, "Seagull"), "M016": (4, "Atto 3 / Yuan PLUS"), "M002": (5, "Han"), "M036": (5, "Han"), "M128": (5, "Han"), "M129": (5, "Han"), "M007": (6, "Qin PLUS"), "M039": (6, "Qin PLUS"),
        "M034": (7, "Song PLUS"), "M049": (7, "Song PLUS"), "M019": (8, "Destroyer 05"), "M027": (9, "e2"), "M084": (10, "Yangwang U8"), "M086": (10, "Yangwang U9"), "M090": (11, "Fangchengbao Bao 5"), "M091": (11, "Fangchengbao Bao 8")}
plan = collections.OrderedDict()
for (cid, code), d in LINK.items():
    c = cols[cid]; m = models[c["model_id"]]
    if m["model_id"] not in PRIO: continue
    k = (m["model_id"], c["color_name_zh"] or c["name_en_gloss_unofficial"] or "(colour record with no Chinese name - English-only source)")
    p = plan.setdefault(k, dict(codes=set(), years=set(), st=col_status[cid][0], amb=set(), srcs=set(), cids=set()))
    p["codes"].add(code); p["years"].add(years.get(c["model_year_id"], {}).get("year", "")); p["amb"].add(col_status[cid][1]); p["srcs"] |= d["sources"]; p["cids"].add(cid)
    if col_status[cid][0] == "CONFLICTED": p["st"] = "CONFLICTED"
PLAN = []
for (mid, nm), p in plan.items():
    m = models[mid]; lin = {LINEAGE[s] for s in p["srcs"] if s in LINEAGE}
    score = (3 if p["st"] == "CONFLICTED" else 0) + (2 if len(p["codes"]) > 1 else 0) + min(len(p["years"] - {""}), 3)
    PLAN.append(dict(priority_rank=PRIO[mid][0], priority_group=PRIO[mid][1], brand=brands[m["brand_id"]], model_id=mid, international_model_name=m["model_key"], chinese_model_name=m["name_zh"], original_chinese_color_name=nm,
                     model_years_in_catalog=" | ".join(sorted(y for y in p["years"] if y)), candidate_codes=" | ".join(sorted(p["codes"])), n_candidate_codes=len(p["codes"]), current_status=p["st"], independent_lineages=len(lin),
                     value_score=score, why_this_sample="Codes in dispute between suppliers - one dealer/label read decides it" if p["st"] == "CONFLICTED" else ("Several candidate codes for one colour" if len(p["codes"]) > 1 else "Single supplier code; confirm once per model-year family"),
                     capture_needed="Dealer VIN read-out (screenshot/photo) OR label photo with VIN plate in frame; see vin_evidence_template.csv"))
PLAN.sort(key=lambda r: (r["priority_rank"], -r["value_score"], r["original_chinese_color_name"]))
wr("verification_sample_plan.csv", PLAN, ["priority_rank", "priority_group", "brand", "model_id", "international_model_name", "chinese_model_name", "original_chinese_color_name", "model_years_in_catalog", "candidate_codes", "n_candidate_codes",
                                       "current_status", "independent_lineages", "value_score", "why_this_sample", "capture_needed"])

# ---------------------------------------------------------------------------------------------- vin_evidence_template.csv
TEMPLATE = ["submission_id", "vin_sha256_hex", "vin_wmi_vds_first_9", "model_id_or_name", "model_year", "market_country", "registration_or_certificate_body_colour_class_zh", "colour_name_zh_on_invoice_or_brochure",
            "evidence_type(DEALER_DMS_SCREENSHOT|DEALER_PRINTOUT|LABEL_PHOTO|OEM_REPAIR_DOC|OTHER)", "paint_code_as_shown", "text_next_to_code_on_source", "label_location_if_label", "vin_plate_in_same_photo(Y/N)",
            "dealer_or_shop_name_city", "staff_role_confirming", "date_of_observation", "vehicle_respray_history(Y/N/unknown)", "file_name_of_stored_evidence(kept_privately)", "researcher_notes"]
with open(f"{B7}/vin_evidence_template.csv", "w", encoding="utf-8", newline="") as f: csv.writer(f, lineterminator="\n").writerow(TEMPLATE)

# ---------------------------------------------------------------------------------------------- stats
st = collections.Counter(r["confidence_status"] for r in ENR); dl = collections.Counter(r["delta"] for r in ENR)
dyc = [p for p in R7["products"].values() if p["source"] == "B7S02"]
all_codes_b6 = {r["paint_code"] for r in b6rows}; new_codes = sorted({p["code"] for p in dyc} - all_codes_b6 - {tk for c in cands.values() for tk in tokens(c["code_raw"])})
STATS = dict(self_check=SELF_CHECK, delta_rows=len(ENR), by_delta=dict(dl), by_status=dict(st), by_scope=dict(collections.Counter(r["link_scope"] for r in ENR)), dyc_titles=len(RAWS["B7S02"]), dyc_distinct_pairs=len(dyc),
             dyc_matched=sum(1 for p in dyc if p["matched"]), dyc_unmatched=sum(1 for p in dyc if not p["matched"]), new_codes_from_dyc=new_codes, colour_status=dict(collections.Counter(v[0] for v in col_status.values())),
             colour_records_with_candidate=len(col_status), conflicts=dict(collections.Counter(r["conflict_type"] for r in CF)), sample_plan_rows=len(PLAN), lineage_oematch_vs_dyc=oem_dyc,
             status_changes=[(r["original_chinese_color_name"], r["paint_code"], r["batch6_status"], r["confidence_status"]) for r in ENR if r["delta"] == "STATUS_CHANGED"][:20],
             batch6_code_only_rows_now_matched=[list(k[1:]) for k in RESOLVED], independent_lineage_distribution=dict(collections.Counter(r["independent_lineage_count"] for r in ENR)))
json.dump(STATS, open(f"{B7}/stats_batch7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(STATS, ensure_ascii=False, indent=1))


# ================================================================================================ sources.csv / vin_research.csv
SF = ["source_id", "title", "url_or_query", "publisher_or_type", "evidence_tier", "accessed", "retrieval_method", "access_result", "contains_paint_codes", "usable_as_oem_verification", "notes"]
NEWSRC = []
def ns(sid, title, url, pub, tier, how, res, codes, oemv, notes, acc=TODAY): NEWSRC.append(dict(source_id=sid, title=title, url_or_query=url, publisher_or_type=pub, evidence_tier=tier, accessed=acc, retrieval_method=how, access_result=res, contains_paint_codes=codes, usable_as_oem_verification=oemv, notes=notes))
ns("B7S01", "AkzoNobel Car Refinishes puts color retrieval on mobile phones (FenderBender)", "https://www.fenderbender.com/running-a-shop/operations/article/33021252/akzonobel-car-refinishes-puts-color-retrieval-on-mobile-phones", "Trade press about a paint-system tool", "PRIORITY_3 (paint-system behaviour)", "curl + text", "HTTP 200; read", "NO", "NO",
   "Quote: users 'enter simple, straightforward search criteria (such as make, year, color code and/or color group)' and the AkzoNobel color retrieval system 'provides the formula for a perfect color match'. Shows the system takes the OEM colour code as an INPUT and returns a formula; it does not derive the code from a VIN. Article is old (mobile-phone era); current Chinese-market tool not verified.")
ns("B7S02", "DipYourCar - BYD 'Luna OEM Basecoat' product listings", "https://www.dipyourcar.com/search/suggest.json (query 'BYD ...'); product pages https://www.dipyourcar.com/products/byd-*", "US retailer (mixed paint)", "PRIORITY_3_RETAILER", "public Shopify search-suggest JSON, titles only (batch7/raw/dipyourcar_byd_products.json)",
   "92 BYD titles; not exhaustive (<=10 per query)", "YES (code in title, no model/year)", "NO", "Same romanisations and abbreviations as OEMatch (B6S02): treated as ONE lineage (see source_lineage_analysis.csv). Adds 19 code tokens new to the catalog (CA8, CAJ, EA5, EA7, EAF, EAP, EX, HCH, HDK, HE3, JN, L15C, R14C, S-01, UAK, UAY, UBG, UBM, YC8), all unverified.")
ns("B7S03", "BASF Baslac (百事利) 色卡 page + Formula Finder", "https://www.baslac.com/zh-apac/seka ; https://formula-finder.baslac.com", "Paint manufacturer (BASF refinish brand, Chinese-language page)", "PRIORITY_3 (paint-system behaviour)", "curl + text; Formula Finder landing page only",
   "Page read (HTTP 200). Formula Finder: landing page is a disclaimer click-through ('I agree'); not accepted/used", "NO (no BYD data seen)", "NO",
   "Quotes: chip tool of 3000+ chips, '每个色卡对应一个配方(标准配方)。按OEM分类' (each chip corresponds to one standard formula; sorted by OEM); deviation variants (偏差色) are checked in Formula Finder and are marked with direction (all darker than the standard). Shows formula VARIANTS exist per OEM colour: a formula identifier is not the OEM code. Whether the Formula Finder lists BYD is UNTESTED - acceptance of its terms is left to the user.")
ns("B7S04", "BASF Glasurit - colour competence (colour tools)", "https://www.glasurit.com/en-int/color-competence", "Paint manufacturer", "PRIORITY_3 (paint-system behaviour)", "curl + text", "HTTP 200; read", "NO", "NO",
   "Quote: colour chips 'coated with original paint. The front shows the color and on the back is the color code so you can easily find the correct mixing formula in our database.' Code -> formula direction again.")
ns("B7S05", "GB/T 21085-2020 Qualified Certificate of Vehicle (partial English preview)", "https://www.chinesestandard.net/PDF.aspx/GBT21085-2020", "Chinese national standard (commercial preview/translation)", "PRIORITY_1-adjacent (regulatory standard)", "curl + text", "HTTP 200; preview read",
   "NO", "NO (regulatory, not BYD-specific)", "Clause 7.2: 'Fill in the Chinese characters describing the color of the vehicle body. For single-color vehicles ... in accordance with the color classification of white, gray, yellow, pink, red, purple, green, blue, brown and black.' So the Chinese vehicle certificate (合格证) carries only a 10-class colour family, never a paint code.")
ns("B7S06", "GB/T 18411-2018 Power-driven vehicles manufacturer's plate (preview)", "https://www.chinesestandard.net/PDF.aspx/GBT18411-2018", "Chinese national standard (commercial preview)", "PRIORITY_1-adjacent", "curl + text", "HTTP 200; preview shows scope/TOC only (clause 5 content table not shown)", "NO", "NO",
   "Defines type, marking content, position and requirements of the manufacturer's plate; the required/optional item list is behind the paywall, so whether colour is allowed is UNKNOWN.")
ns("B7S07", "Axalta colour tools (Color Inspector, Acquire spectrophotometer, colour retrieval software, fan decks)", "https://www.axalta.com/id/in_ID/color-competency/color-tools.html", "Paint manufacturer", "PRIORITY_3 (paint-system behaviour)", "curl + text", "HTTP 200; read", "NO", "NO",
   "Quotes: colour tools 'linked to a global database'; Acquire spectrophotometer 'measure[s] colors directly from' the vehicle and checks them against the stored data; sample chips carry 'the code and the name of the colour shade' on the back. Confirms a measurement route that needs no OEM code.")
ns("B7S08", "17vin - VIN decoder, EPC-level parts data, repair-manual index (BYD)", "https://en.17vin.com/aboutus.html ; https://en.17vin.com/automotive_repair_manual_wiring_diagrams/BYD/2089.html", "Chinese VIN/parts-data platform (login, paid)", "PRIORITY_B (Chinese data ecosystem)", "curl + text (about page, repair-manual index); no VIN decoded", "HTTP 200; read",
   "NO", "NO", "Offers VIN decoding (web + API), 'EPC level' parts data and BYD repair-manual listings (e.g. 2017 BYD Qin Hybrid). Whether a decode returns body colour/paint code is UNKNOWN - needs a test with a VIN the user owns.")
ns("B7S09", "Onwings / 东来涂料技术(上海)股份有限公司 - company background (CNPP, Maigoo)", "https://m.maigoo.com/brand/14147.html ; https://www.cnpp.cn/china/paihang_11323.html", "Chinese brand-ranking portals (secondary)", "WEAK", "web search snippet", "Snippet only; onwings.com.cn connection reset", "NO", "NO",
   "Donglai (东来) = Onwings: Shanghai-based, STAR-market listed (688129), refinish brands onwings/onwaves/fixs. No public colour-retrieval or BYD formula page found.")
ns("B7S10", "PaintScratch and VinAudit - paint code by VIN guides", "https://www.paintscratch.com/pages/finding-your-color-code ; https://www.vinaudit.com/paint-code-by-vin", "US retailer / VIN-report vendor", "WEAK (generic, non-BYD)", "curl + text", "HTTP 200; read", "NO", "NO",
   "PaintScratch: 'The VIN identifies the vehicle, but it does not include the paint code.' Generic statement; supports the method point that a VIN is only a key to a database lookup.")
ns("B7S11", "DipYourCar - how to find your car's paint code (every major brand)", "https://www.dipyourcar.com/blogs/dipyourcar-daily/how-to-find-your-cars-paint-code-every-major-brand", "US retailer guide", "WEAK (generic)", "curl + text", "HTTP 200; read", "NO", "NO",
   "Generic: 'A main dealer - give them the VIN and they can usually look up the factory color in seconds.' Not BYD-specific, not verified for China.")
cnman = [("B7S12", "BYD 2025款海豹用户手册 (domestic, 260622)", "https://www.byd.com/material/domestic-official/user-manual/ocean/2025款海豹用户手册260622.pdf", 392, "385"),
         ("B7S13", "BYD 宋PLUS EV 冠军版＆荣耀版用户手册 (domestic, 260813)", "https://www.byd.com/material/__CN/domestic-official/user-manual/ocean/宋PLUS EV冠军版＆荣耀版用户手册260813.pdf", 300, "291"),
         ("B7S14", "BYD 汉L EV用户手册 (domestic, 1104)", "https://www.byd.com/material/domestic-official/user-manual/dynasty/汉L EV用户手册1104.pdf", 408, "401"),
         ("B7S15", "BYD 汉DM-i智驾版 长续航版 用户手册 (domestic, 20260410)", "https://www.byd.com/material/domestic-official/user-manual/dynasty/汉DM-i智驾版-长续航版 用户手册20260410.pdf", 412, "405")]
for sid, t, u, npg, pg in cnman:
    ns(sid, t, u, "BYD official website - Chinese-market owner's manual PDF (OEM document)", "PRIORITY_1_OEM_DOCUMENTATION (owner's manual)", "curl download + pdftotext; keyword search (车身颜色/油漆/涂装/漆色/色号/颜色代码/铭牌) + nameplate page read",
       f"HTTP 200; {npg} PDF pages; '整车铭牌' on PDF page {pg}", "NO", "NO - lists nameplate contents and labels; no colour-code item",
       "整车铭牌 (vehicle nameplate) is below the right B-pillar and lists: company name, brand, country of manufacture, model, seats, manufacture date, motor model, motor peak power, battery voltage and capacity, VIN, maximum mass (+ engine items for DM-i). No paint/colour field. (Seal 2025: VIN-label and warning-label inventories list no colour-code label.) Paint section only gives care advice (e.g. avoid unnecessary respray 'to prevent colour mismatch'); no colour-code instruction.")
ns("B7S16", "BYD App (App Store listing) - vehicle information across BYD brands", "https://apps.apple.com/cn/app/id493482713", "Vendor app-store listing (search snippet)", "PRIORITY_C (BYD service network)", "web search snippet", "Snippet only", "NO", "NO",
   "Listing says the app shows vehicle information for BYD, Fangchengbao, Denza, Yangwang vehicles. Whether it exposes body colour or a paint code is UNKNOWN (not accessed; needs an owner account).")
ns("B7S17", "Search record - Chinese VIN / EPC / collision-repair / paint-distributor platforms", "17vin 比亚迪 VIN 解析 车身颜色; 怎么查车漆色号 4S店 车架号; 4S店 钣喷 按车架号 查询 原厂色号; 东来 Onwings 色卡 配方 查询; 阿克苏诺贝尔 新劲 色卡 查询", "web search record", "n/a", "web search (standard)", "NOT_FOUND - no Chinese-language page documents a VIN -> BYD paint-code lookup", "NO", "NO", "Chinese forums/Zhihu did not surface; results were generic or English.")
ns("B7S18", "Search record - Denza / Yangwang / Fangchengbao / Linghui manuals and paint data", "腾势N7 用户手册 pdf 整车铭牌; 仰望U8 用户手册 pdf; 方程豹 豹5 用户手册", "web search record", "n/a", "web search (standard)", "NOT_FOUND - no domestic user-manual PDFs located for these brands; no paint-code data", "NO", "NO",
   "BYD hosts domestic manuals under byd.com/material/domestic-official/user-manual/ (dynasty/, ocean/ seen); Denza/Yangwang/Fangchengbao/Linghui paths were not found by search and were not guessed.")
b6s = {r["source_id"]: r for r in rd(f"{B6}/sources.csv")}; b5s = {r["b5_source_id"]: r for r in rd(f"{B5}/source_register.csv")}
CARRY = []
for sid in ("B6S01", "B6S02", "B6S03", "B6S04", "B6S05", "B6S10", "B6S11", "S29", "S30", "S31", "S32", "S226", "S227", "S34"):
    r = dict(b6s[sid]); r["notes"] = "[carried from Batch 6] " + r["notes"]; CARRY.append(r)
for sid in ("B5S01", "B5S02", "B5S03", "B5S04", "B5S05", "B5S06", "B5S07"):
    b = b5s[sid]; CARRY.append(dict(source_id=sid, title=b["title"], url_or_query=b["url_or_query"], publisher_or_type=b["publisher_or_type"], evidence_tier=b["evidence_tier"], accessed=b["accessed"], retrieval_method=b["retrieval_method"],
                                    access_result=b["access_result"], contains_paint_codes="NO", usable_as_oem_verification="NO", notes="[carried from Batch 5] " + b["notes"]))
# B6S02 is re-described: lineage note
for r in CARRY:
    if r["source_id"] == "B6S02": r["notes"] += " | Batch 7: same lineage as DipYourCar (B7S02)."
wr("sources.csv", NEWSRC + CARRY, SF)

# ---- vin_research.csv
VF = ["method_id", "method_group", "method", "input_needed", "output_obtained", "yields_factory_paint_code", "access", "evidence_basis", "finding", "source_ids", "verification_level", "limitations", "role_in_recommended_method"]
V = []
def vr(**k): V.append(k)
vr(method_id="V01", method_group="VIN", method="Decode the VIN itself (any online decoder)", input_needed="VIN", output_obtained="WMI/VDS/model-year/plant/serial only", yields_factory_paint_code="NO", access="public",
   evidence_basis="Vendor guides + VIN structure", finding="'The VIN identifies the vehicle, but it does not include the paint code.' Colour is stored in the maker's build record, not in the VIN characters. Generic BYD decoders (vindecoder.eu, vincario, 7zap) report no colour code in the snippets seen.",
   source_ids="B7S10;B6S11", verification_level="FETCHED_AND_READ (PaintScratch/VinAudit) + SEARCH_SNIPPET (decoders)", limitations="Generic, not BYD-specific; decoders not tested with a BYD VIN.", role_in_recommended_method="VIN is the KEY to a lookup (dealer/OEM system); never a source of the code itself")
vr(method_id="V02", method_group="Official document", method="Chinese vehicle certificate (机动车整车出厂合格证) body-colour field", input_needed="the car's certificate (or its data)", output_obtained="colour CLASS: one of 白/灰/黄/粉/红/紫/绿/蓝/棕/黑 (multi-colour: up to 3 colours in order)",
   yields_factory_paint_code="PARTIAL (colour family only)", access="owner's document", evidence_basis="GB/T 21085-2020 clause 7.2 (English preview)", finding="Certificate records the body colour only as a Chinese colour-class word; it cannot distinguish WA2 from W36C or a pearl white from a solid white.",
   source_ids="B7S05", verification_level="FETCHED_AND_READ (standard preview)", limitations="Standard text read from a commercial preview; BYD's actual certificates not inspected.", role_in_recommended_method="Step 1: narrows the candidate list to the right colour family; cross-check against the catalogue colour name")
vr(method_id="V03", method_group="OEM document", method="BYD Chinese-market owner's manual: vehicle nameplate (整车铭牌) and label inventory", input_needed="model-specific manual PDF (free on byd.com)", output_obtained="nameplate position and content list; VIN/warning/tyre-pressure label inventory",
   yields_factory_paint_code="NO", access="public", evidence_basis="4 Chinese-market manuals read (Seal 2025, Song PLUS EV, Han L EV, Han DM-i) + 7 export manuals (Batch 5)", finding="Five manuals list the nameplate's contents (ATTO 3 2022 + the four Chinese-market manuals): company, brand, country, model, seats, build date, motor/battery data, VIN, mass (+ engine data on DM-i) - no paint/colour item. The other six export manuals only state the nameplate's position. The Seal 2025 manual's VIN-label and warning-label inventories include no colour-code label (other manuals' inventories were not read in full). Absence from a manual is not proof that no colour label exists anywhere.",
   source_ids="B7S12;B7S13;B7S14;B7S15;B5S01;B5S02;B5S03;B5S04;B5S05;B5S06;B5S07", verification_level="FETCHED_AND_READ", limitations="Only BYD-brand models; Denza/Yangwang/Fangchengbao/Linghui manuals not found. Images not OCR'd.", role_in_recommended_method="Tells where NOT to expect the code; do not rely on the nameplate for a paint code")
vr(method_id="V04", method_group="Regulatory standard", method="GB/T 18411-2018 manufacturer's plate marking content", input_needed="standard text (paid)", output_obtained="required/optional plate items", yields_factory_paint_code="UNKNOWN", access="paid (US$135 translation)",
   evidence_basis="Preview shows scope and TOC only", finding="Clause 5 'marking content' (specified + optional items) is not visible; whether colour may appear on a plate is unknown.", source_ids="B7S06", verification_level="FETCHED_PREVIEW_ONLY", limitations="Paywalled.", role_in_recommended_method="Optional: buy/read clause 5 to close the question for plates")
vr(method_id="V05", method_group="Physical label", method="Locate a printed paint/colour-code label on the vehicle", input_needed="the vehicle", output_obtained="a code, if a label exists", yields_factory_paint_code="UNKNOWN (location undocumented for BYD)", access="owner/body shop",
   evidence_basis="Retailer guidance conflicts (under bonnet / driver door-B-pillar / door jamb / service booklet); BYD manuals list none; one weak Q&A (S34) says a bonnet plate with 'paintcolor'/'H/S'", finding="No BYD source documents a paint-code label. A photographed label with the VIN plate in the same frame is the only way to turn this into VERIFIED_LABEL evidence.",
   source_ids="B6S10;S34;B7S12;B7S13;B7S14;B7S15;B5S07", verification_level="SYNTHESIS", limitations="Needs physical inspection of several BYD models.", role_in_recommended_method="Step 2 (parallel): inspect and photograph; record location in vin_evidence_template.csv")
vr(method_id="V06", method_group="BYD service network", method="Ask a BYD service centre to read the factory colour code from the vehicle's build record by VIN", input_needed="VIN (+ ID/ownership as the shop requires)", output_obtained="expected: factory colour (name/code) from the dealer system - NOT documented by BYD",
   yields_factory_paint_code="LIKELY but UNVERIFIED for BYD", access="dealer / service centre (in person or phone)", evidence_basis="BYD's service page: 精诚钣喷 uses 原厂数据、原厂配方 with AkzoNobel/BASF/Donglai; generic dealer-VIN advice (DipYourCar); no BYD document describing the lookup",
   finding="The only OEM-sourced route. BYD's own repair network states it works from factory data/formulas, which implies the service system holds colour/formula data per vehicle, but no public document says that a code is shown or how staff retrieve it.", source_ids="B6S01;B7S11", verification_level="OEM STATEMENT (indirect) + generic advice",
   limitations="Outcome depends on what the dealer system displays (code vs formula number vs name); staff may refuse to disclose.", role_in_recommended_method="Step 3: PRIMARY route to VERIFIED_OEM evidence - capture a screenshot/photo of the system showing VIN + code + colour name; see protocol in the report")
vr(method_id="V07", method_group="BYD service network", method="BYD App / service-centre appointment records", input_needed="owner account", output_obtained="UNKNOWN (store listing mentions vehicle information only)", yields_factory_paint_code="UNKNOWN", access="owner login",
   evidence_basis="App Store listing snippet; BYD page mentions app booking for 8-hour 钣喷 quick repair", finding="Not shown to expose colour or code. Test with a real account before relying on it.", source_ids="B7S16;B6S01", verification_level="SEARCH_SNIPPET_ONLY", limitations="Not accessed.", role_in_recommended_method="Optional check by an owner")
vr(method_id="V08", method_group="Chinese data platform", method="17vin VIN decode / EPC-level data / BYD repair-manual index", input_needed="VIN; account/credits", output_obtained="vehicle configuration, parts, manuals; colour output UNKNOWN", yields_factory_paint_code="UNKNOWN", access="login + paid API",
   evidence_basis="About page and repair-manual index read; no decode run", finding="Plausible source of build-level data and BYD repair manuals (index lists e.g. 2017 Qin Hybrid). Never tested for colour; do not use another person's VIN.", source_ids="B7S08", verification_level="FETCHED_AND_READ (marketing/index pages)", limitations="No decode run.", role_in_recommended_method="Optional: test with a VIN the user owns; check the returned field list")
vr(method_id="V09", method_group="Paint system", method="AkzoNobel colour retrieval (make + year + colour code/group -> formula)", input_needed="make, year, OEM colour code or colour group", output_obtained="mixing formula", yields_factory_paint_code="NO (code is the INPUT)", access="licensed shop software",
   evidence_basis="FenderBender article", finding="The tool needs the OEM code or a colour group; it returns the formula. Formula identifiers belong to this output side.", source_ids="B7S01", verification_level="FETCHED_AND_READ (old article)", limitations="Chinese-market current tool not verified.", role_in_recommended_method="Step 4: after the OEM code is known, translate to a formula")
vr(method_id="V10", method_group="Paint system", method="BASF Baslac (百事利) chips + Formula Finder; Glasurit colour chips/online", input_needed="OEM code (chips are sorted by OEM, code on the back); or visual chip match", output_obtained="standard formula + deviation variants",
   yields_factory_paint_code="NO (formula side); chips carry the OEM code on the back", access="distributor / licensed (Formula Finder behind click-through)", evidence_basis="Baslac chip page; Glasurit competence page", finding="Each chip = one standard formula; variants (偏差色) are darker/finer/coarser than standard - so a formula variant ID is not the OEM code. A physical chip match could reveal the code printed on the chip back without a VIN.",
   source_ids="B7S03;B7S04", verification_level="FETCHED_AND_READ", limitations="BYD coverage of the chip sets UNTESTED; Formula Finder not accessed (terms acceptance).", role_in_recommended_method="Step 4 and a fallback: chip match gives a candidate code with a paint-maker's own data")
vr(method_id="V11", method_group="Paint system", method="Axalta colour retrieval + Acquire spectrophotometer + fan decks", input_needed="measurement of the car, or code", output_obtained="formula (code and name printed on chip backs)", yields_factory_paint_code="NO (formula); chip back shows code", access="licensed shop",
   evidence_basis="Axalta colour-tools page", finding="A spectrophotometer reading finds a formula for the paint actually on the car - works for resprayed or faded cars but returns no factory code.", source_ids="B7S07", verification_level="FETCHED_AND_READ", limitations="Measures current paint, not necessarily factory paint.", role_in_recommended_method="Step 5 fallback: when no code can be obtained")
vr(method_id="V12", method_group="Paint system", method="Onwings / Donglai (东来) colour retrieval", input_needed="unknown", output_obtained="unknown", yields_factory_paint_code="UNKNOWN", access="distributor/licensed", evidence_basis="Company background pages only; official site connection reset", finding="Donglai = Onwings (Shanghai, 688129); no public colour-lookup page found.", source_ids="B7S09", verification_level="SEARCH_SNIPPET_ONLY", limitations="Not accessed.", role_in_recommended_method="Ask a Donglai distributor which BYD colour codes/variants their system carries")
vr(method_id="V13", method_group="Retailer", method="Retailer colour finders by year/make/model (Chipex, CROP, DipYourCar, Carross, etc.)", input_needed="year, make, model", output_obtained="candidate codes (retailer database)", yields_factory_paint_code="NO (POSSIBLE only)", access="public",
   evidence_basis="Batches 2-7 listings", finding="OEMatch and DipYourCar share one upstream (95% identical romanised names across shared codes); other retailers' lineage unknown. Repetition is not corroboration.", source_ids="B6S02;B7S02;B6S03;S29;S30;S31;S32", verification_level="FETCHED_AND_READ", limitations="No OEM source cited by any retailer.", role_in_recommended_method="Step 0/5: source of candidate codes to test (lookup + sample plan), never of verification")
vr(method_id="V14", method_group="Chinese e-commerce", method="JD/Taobao touch-up-pen listings", input_needed="model + colour name", output_obtained="colour names and fitment in titles", yields_factory_paint_code="NO", access="public", evidence_basis="JD listing page (Batch 6)", finding="Chinese retail sells pens by colour NAME and model; no code seen.", source_ids="B6S05", verification_level="FETCHED_AND_READ", limitations="Marketplace content not exhaustive.", role_in_recommended_method="None (name only)")
vr(method_id="V15", method_group="Standards/OEM text", method="BYD repair guidance on respray", input_needed="owner's manual paint-care section", output_obtained="advice only", yields_factory_paint_code="NO", access="public", evidence_basis="Seal/Song PLUS/Han L/Han DM-i manuals",
   finding="Manual says not to respray without clear damage 'to prevent mismatched colour or poor adhesion' - confirms mismatch risk but gives no code or formula.", source_ids="B7S12;B7S13;B7S14;B7S15", verification_level="FETCHED_AND_READ", limitations="", role_in_recommended_method="Context for Step 5 (check respray history)")
vr(method_id="V16", method_group="Proposed protocol", method="Dealer confirmation protocol (PROPOSED, not a BYD procedure)", input_needed="VIN, model, MY, market, colour name from invoice, body-colour class from 合格证", output_obtained="evidence record for vin_evidence_template.csv",
   yields_factory_paint_code="DEPENDS on what the dealer system shows", access="in person / phone", evidence_basis="Synthesis of V02, V03, V06", finding="Ask: (1) what colour name/code does the build record show for this VIN? (2) is a paint-system formula number shown, and for which maker (AkzoNobel/BASF/Donglai)? (3) can the screen or printout be photographed with the VIN visible? (4) is there any respray/repair record?",
   source_ids="B6S01;B7S05;B7S12", verification_level="PROPOSED", limitations="Not validated with a BYD dealer.", role_in_recommended_method="Step 3 script")
wr("vin_research.csv", V, VF)
STATS["vin_methods"] = len(V); STATS["sources_rows"] = len(NEWSRC) + len(CARRY)
json.dump(STATS, open(f"{B7}/stats_batch7.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("vin methods", len(V), "sources", len(NEWSRC) + len(CARRY))
