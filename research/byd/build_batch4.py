#!/usr/bin/env python3
"""
BYD research dataset, batch 4 (DATA part): the remaining BYD-group models.

Reads (never modifies): batch-1/2/3 CSVs in this folder.  Reads raw_b4/: autohome_specs_b4.json, autohome_series_inventory.json,
wikipedia_infoboxes_b4.json, touchup_b4.json, carross_b4.json, color_gloss_zh_en.tsv.
Writes (staging -> validated -> published): batch4/*.csv and catalog_union/*.csv.

PRINCIPLES
 * Years: only years that a source lists (Autohome 款 labels, Wikipedia list/infobox). No year is derived or estimated.
 * Assignments: a trim goes to a model only on an explicit label token, a single-row series, a documented intro-year uniqueness rule,
   or a cited range rule.  Everything else is written to unmapped_specs_b4.csv (never guessed).
 * Generation: single-row models take all specs (flagged when outside the documented range); multi-generation rows are assigned by documented
   intro year, and boundary years are left in an 'unspecified' generation bucket instead of being guessed.
 * Paint codes: retailer-catalog evidence only -> POSSIBLE at best; never VERIFIED.  Links need a model match, a year match (when the retailer
   gives years) and an exact normalized name match with a literal translation of the Chinese name.
 * Chinese colour names are exact; English glosses are my literal translations and are labelled UNOFFICIAL.
Run: python3 build_batch4.py
"""
import csv, json, os, re, collections, shutil, sys, datetime, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__)); R4 = os.path.join(HERE, "raw_b4")
STAGE = os.path.join(HERE, ".stage_batch4");
if os.path.exists(STAGE): shutil.rmtree(STAGE)
os.makedirs(os.path.join(STAGE, "batch4")); os.makedirs(os.path.join(STAGE, "catalog_union"))

def rd(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f: return list(csv.DictReader(f))
def w(sub, name, rows, cols):
    with open(os.path.join(STAGE, sub, name), "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); wr.writeheader()
        for r in rows: wr.writerow(r)
def nz(v): return None if v in ("", None) else v
def idnum(s): return int(re.sub(r"\D", "", s))

# ---------------------------------------------------------------- base tables (read only)
brands = rd("brands.csv"); models = rd("models.csv"); gens = rd("generations.csv"); mys = rd("model_years.csv"); trims0 = rd("trims.csv")
colors0 = rd("factory_colors.csv"); cands0 = rd("paint_code_candidates.csv"); pcs0 = rd("paint_codes.csv"); links0 = rd("color_paint_code_links.csv")
ver0 = rd("verification_records.csv"); srcs0 = rd("sources.csv"); body_types = rd("body_types.csv")
BR = {"BYD": "B2", "Denza": "B3", "Yangwang": "B4", "Fangchengbao": "B5", "Linghui": "B6"}
model_by_key = {m["model_key"]: m for m in models}; model_by_id = {m["model_id"]: m for m in models}
model_by_bk = {(m["brand_id"], m["model_key"]): m for m in models}   # brand-aware lookup (model_key alone is NOT unique: BYD e5 vs Linghui e5)
gens_of = collections.defaultdict(list)
for g in gens: gens_of[g["model_id"]].append(g)
my_by_key = {(m["generation_id"], int(m["year"])): m for m in mys}
nxt = dict(M=max(idnum(m["model_id"]) for m in models) + 1, G=max(idnum(g["generation_id"]) for g in gens) + 1, Y=max(idnum(m["model_year_id"]) for m in mys) + 1,
           T=max(idnum(t["trim_id"]) for t in trims0) + 1, C=max(idnum(c["color_id"]) for c in colors0) + 1, P=max(idnum(c["candidate_id"]) for c in cands0) + 1,
           PC=max(idnum(c["paint_code_id"]) for c in pcs0) + 1, L=max(idnum(c["link_id"]) for c in links0) + 1, V=max(idnum(c["verification_id"]) for c in ver0) + 1,
           S=max(idnum(c["source_id"]) for c in srcs0) + 1)
def new_id(k, width):
    v = nxt[k]; nxt[k] += 1; return f"{k}{v:0{width}d}"

SPECS = json.load(open(os.path.join(R4, "autohome_specs_b4.json"), encoding="utf-8"))
INV = json.load(open(os.path.join(R4, "autohome_series_inventory.json"), encoding="utf-8"))
WIKI = json.load(open(os.path.join(R4, "wikipedia_infoboxes_b4.json"), encoding="utf-8"))
TU = json.load(open(os.path.join(R4, "touchup_b4.json"), encoding="utf-8")); CR = json.load(open(os.path.join(R4, "carross_b4.json"), encoding="utf-8"))
GLOSS = {a: b for a, b in (l.rstrip("\n").split("\t") for l in open(os.path.join(R4, "color_gloss_zh_en.tsv"), encoding="utf-8") if l.strip())}

# ---------------------------------------------------------------- sources (new ids)
sources_b4 = []
def add_source(title, url, stype, retrieval, notes, reliability):
    sid = new_id("S", 2); sources_b4.append(dict(source_id=sid, title=title, url=url, source_type=stype, retrieval=retrieval, reliability=reliability, notes=notes)); return sid
SRC_BRAND = {b["brand_autohome_id"]: add_source(f"Autohome picture gallery - brand page {b['brand']} (series inventory)", b["brand_page_url"], "secondary-catalog (Chinese auto portal)", "FULL", "Lists every series of the brand with photo counts; used to build the series inventory.", "secondary") for b in {r["brand_autohome_id"]: r for r in INV}.values()}
series_src = {}
for key, b in SPECS.items():
    series_src[str(b["series_id"])] = add_source(f"Autohome picture gallery - {b['brand']} {b['series_name']} (series {b['series_id']}), per-spec exterior pages", f"https://car.autohome.com.cn/pic/series-t/{b['series_id']}.html",
        "secondary-catalog (Chinese auto portal)", "FULL (GBK-decoded; spec lists from series-t + series pages; per-spec exterior pages)",
        "Lists 款 (model year), 款型 (trim) and colours with photos for each exact trim. A colour listed means a photo of that trim in that colour exists; not an official availability list.", "secondary (exact-trim photographic evidence)")
wiki_src = {}
for ib in WIKI["infoboxes"]:
    if ib["page"] not in wiki_src:
        wiki_src[ib["page"]] = add_source(f"Wikipedia - {ib['page']}", ib["page_url"], "secondary-encyclopedia", f"infobox + short description parsed from raw wikitext ({ib.get('fetched_utc') or 'cached'})", "Production dates, body style, doors, dimensions.", "secondary")
S_TU = add_source("Touch Up Paint Factory - BYD model pages", "https://touchuppaintfactory.com/brands/byd/", "retailer catalog", "27 model pages parsed", "code | names per model; years not shown; names mix markets/languages.", "retailer (secondary)")
S_CR = add_source("Carross (EU) - BYD model pages", "https://www.carross.eu/en/paint-byd-b221", "retailer catalog", "30 model pages parsed", "code | name | year range per model (as stated by the retailer).", "retailer (secondary)")

# ---------------------------------------------------------------- series policy
def R(rules=None, default=None, candidates=None, note=None): return dict(rules=rules or [], default=default, candidates=candidates, note=note)
NEW_MODELS = {  # key: (brand, series label, powertrain, reason)
 "Tang DM-p": ("BYD", "Dynasty", "PHEV", "Autohome 唐 series has DM-p trims; no row in the Wikipedia list"),
 "Tang (ICE)": ("BYD", "Dynasty", "ICE", "Autohome 唐 (4802) is the 2018-2021 petrol Tang; no row in the Wikipedia list"),
 "Song Plus (ICE)": ("BYD", "Dynasty", "ICE", "Autohome 宋PLUS (5760) is the 2020 petrol Song Plus; list rows cover DM-i/EV only"),
 "Song Pro (ICE)": ("BYD", "Dynasty", "ICE", "Autohome 宋Pro (5178) petrol; list row 'Song Pro' is PHEV"),
 "Song Pro EV": ("BYD", "Dynasty", "BEV", "Autohome 宋Pro新能源 EV trims; no row in the list"),
 "e9 (BYD brand, 2021)": ("BYD", "Dynasty", "BEV", "Autohome 比亚迪e9 (2021-2025) predates the Linghui e9 (2026) list row; kept separate to avoid a wrong association"),
 "U9 Xtreme": ("Yangwang", None, "BEV", "Autohome 仰望U9 Xtreme is its own series; no row in the list"),
 "Ti6": ("Fangchengbao", None, None, "Autohome 钛6 (1 trim, 3 photos); no row in the list"),
}
SERIES = {
 3430: R([(r"DM-p", "Tang DM-p", None, None), (r"DM-i", "Tang DM-i", None, None), (r"(?<![A-Za-z])EV(?![A-Za-z])", "Tang EV", None, None), (r"DM", "Tang", None, 2017), (r"DM", "Tang DM-i", 2018, None), (r".", "Tang", None, 2017)], note="Autohome 唐新能源 spans Tang DM/DM-i/DM-p/EV 2015-2027; token-less 2015-2017 trims (2.0T) go to the first-generation Tang row (Wikipedia: first generation 2015-2018)"),
 4802: R(default="Tang (ICE)"), 5371: R(default="e3"), 7981: R(default="Seal 05 DM-i"), 2761: R(default="Qin"), 8015: R(default="Linghui:e7", note="Autohome lists 2025; Wikipedia list intro 2026"),
 7588: R([(r"(?<![A-Za-z])EV(?![A-Za-z])", "Seal 06 EV", None, None), (r"DM-i", "Seal 06 DM-i", None, None)]), 8201: R(default="Seal 06 DM-i Touring"), 7694: R(default="Seal 06 GT"),
 7578: R([(r"(?<![A-Za-z])EV(?![A-Za-z])", "Qin L EV", None, None), (r"DM-i", "Qin L DM-i", None, None)]), 8463: R([(r"(?<![A-Za-z])EV(?![A-Za-z])", "Qin Max EV", None, None), (r"DM-i", "Qin Max DM-i", None, None)]),
 5955: R(default="e9 (BYD brand, 2021)"), 7822: R([(r"(?<![A-Za-z])EV(?![A-Za-z])", "Seal 07 EV", None, None), (r"DM-i", "Seal 07 DM-i", None, None)]), 8485: R([(r"(?<![A-Za-z])EV(?![A-Za-z])", "Seal 08 EV", None, None), (r"DM-i", "Seal 08 DM-i", None, None)]),
 7859: R([(r"(?<![A-Za-z])EV(?![A-Za-z])", "Han L EV", None, None), (r"DM", "Han L DM", None, None)]), 8517: R(default="Dahan EV"), 7538: R([(r"DM-i", "Yuan Up (PHEV)", None, None)], default="Yuan Up (BEV)"),
 7807: R(default="Sealion 05 DM-i"), 7982: R(default="Sealion 05 EV"), 5279: R([(r"(?<![A-Za-z])EV(?![A-Za-z])", "Song Pro EV", None, None)], default="Song Pro"),
 8087: R([(r"(?<![A-Za-z])EV(?![A-Za-z])", "Sealion 06 EV", None, None), (r"DM-i", "Sealion 06 DM-i", None, None)]), 7815: R(default="Song L DM-i"), 7220: R(default="Song L EV"),
 8511: R([(r"(?<![A-Za-z])EV(?![A-Za-z])", "Song Ultra EV", None, None), (r"DM-i", "Song Ultra DM-i", None, None)]), 8484: R([(r"(?<![A-Za-z])EV(?![A-Za-z])", "Sealion 08 EV", None, None), (r"DM-i", "Sealion 08 DM-i", None, None)]),
 8005: R([(r"(?<![A-Za-z])EV(?![A-Za-z])", "Tang L EV", None, None), (r"DM", "Tang L DM", None, None)]), 8102: R(default="Datang EV", note="all Autohome trims are 纯电"), 831: R(default="e6"), 8184: R(default="Linghui:M9", note="Autohome lists 2025; Wikipedia list intro 2026"),
 7851: R(default="Xia"), 7977: R(default="Sealion 07 DM-i"), 6851: R(default="Sealion 07 EV"), 8397: R(default="Racco"), 7257: R(default="Shark 6"), 5009: R(default="e1"), 579: R(default="F0"), 417: R(default="Flyer"),
 4073: R(default="e5"), 407: R(default="F3"), 940: R(default="F3R"), 4333: R(default="F3DM"), 927: R(default="G3"), 997: R(default="G3R"), 3283: R(default="G5"), 2085: R(default="L3 / New F3"), 5365: R(default="Qin"),
 4900: R(default="Qin Pro"), 4972: R(default="Qin Pro"), 2806: R(default="Surui"), 540: R(default="F6"), 2091: R(default="G6"), 2944: R(default="Sirui"), 5064: R(default="S2"), 3781: R(default="Yuan"), 6073: R(default="Yuan", note="Yuan Pro is part of the 'Yuan / Yuan Pro' row"),
 4353: R(default="Yuan"), 3780: R(default="Song"), 5760: R(default="Song Plus (ICE)"), 5178: R(default="Song Pro (ICE)"), 4394: R(default="Song"), 2088: R(default="S6"), 6531: R(default="S6"), 3059: R(default="S7"), 6671: R(default="Frigate 07"),
 5825: R(default="D1"), 4279: R(default="Song Max"), 4831: R(default="Song Max"), 798: R(default="M6 (2010)"), 489: R(default="S8"), 3376: R(default=None, note="BYD C6: 1 trim, 3 photos, no catalogue row (likely a show car)"),
 8107: R([(r"硬顶", "Z Coupe", None, None), (r"敞篷", "Z Spider", None, None)]), 7659: R([(r"^630", "Z9 GT EV", None, None), (r"^1100", "Z9 GT PHEV", None, None)], note="range rule: Wikipedia Denza Z9: EV 630-1036 km CLTC; PHEV 1100 km total range"),
 8758: R(default="Z9S"), 7179: R([(r"超混|插混|PHEV", "N8 PHEV", None, None), (r"EV|纯电", "N8 EV", None, None)]), 8159: R([(r"纯电", "N8L EV", None, None), (r"插混", "N8L PHEV", None, None)], candidates=["N8L PHEV", "N8L EV"]),
 7839: R(default="N9"), 6669: R([(r"DM-i", "D9 DM-i", None, None), (r"(?<![A-Za-z])EV(?![A-Za-z])", "D9 EV", None, None)]), 7838: R(default="Z9"), 2805: R(default="400/500/EV"), 6898: R(default="N7"), 5323: R(default="X", note="PHEV and 纯电 trims both under the 'X' row"),
 8811: R(default="Altior"), 7391: R([(r"(?<![A-Za-z])EV(?![A-Za-z])", "U7 EV", None, None), (r"PHEV", "U7 PHEV", None, None)]), 7003: R(default="U8"), 8266: R(default="U8L"), 7116: R(default="U9"), 8649: R(default="U9 Xtreme"),
 8734: R(default="Shark"), 8596: R([(r"^GT", "Formula S GT", None, None), (r"^SL", "Formula SL", None, None)], default="Formula S", note="Formula S GT / SL trims share this series; identified by the GT/SL label prefix"), 7356: R(default="Tai 3"), 7177: R(default="Bao 5"), 7353: R(default="Bao 8"),
 8171: R([(r"(?<![A-Za-z])EV(?![A-Za-z])", "Ti7 (BEV)", None, None)], candidates=["Ti7 (PHEV)", "Ti7 (BEV)"]), 8708: R(default="Ti9"), 8857: R(default="Ti6"),
}
# ---------------------------------------------------------------- new models / generations
models_b4, gens_b4 = [], []
def ensure_model(key, brand_name):
    if (BR[brand_name], key) in model_by_bk: return model_by_bk[(BR[brand_name], key)]
    brand, series, pt, why = NEW_MODELS[key]
    m = dict(model_id=new_id("M", 3), brand_id=BR[brand], series=series, model_key=key, name_zh=None, alt_names=None, powertrain=pt, source_id=None, discovered_note=why)
    models_b4.append(m); model_by_key[key] = m; model_by_bk[(BR[brand], key)] = m; model_by_id[m["model_id"]] = m; return m
def ensure_unspecified_gen(m, src):
    for g in gens_of[m["model_id"]]:
        if g["source_row_name"] == m["model_key"] + " [generation unspecified]": return g
    g = dict(generation_id=new_id("G", 3), model_id=m["model_id"], source_row_name=m["model_key"] + " [generation unspecified]", generation_label="UNSPECIFIED", status="unknown", intro_year=None, facelift_year=None, discontinued_year=None,
             body_type_id=None, body_raw=None, size_class=None, doors=None, doors_source_id=None, body_style_text=None, production_start_text=None, production_end_text=None, generation_facts_note="Bucket for Autohome trims whose generation cannot be determined without guessing (boundary or out-of-range years).",
             facts_source_id=None, exterior_design=None, note="created in batch 4 from Autohome evidence", source_id=src)
    gens_b4.append(g); gens_of[m["model_id"]].append(g); return g
def ensure_single_gen(m, src, stopsale):
    if gens_of[m["model_id"]]: return
    g = dict(generation_id=new_id("G", 3), model_id=m["model_id"], source_row_name=m["model_key"], generation_label=None, status="discontinued" if stopsale else "current", intro_year=None, facelift_year=None, discontinued_year=None,
             body_type_id=None, body_raw=None, size_class=None, doors=None, doors_source_id=None, body_style_text=None, production_start_text=None, production_end_text=None, generation_facts_note=None, facts_source_id=None,
             exterior_design=None, note="model and generation created in batch 4 from Autohome evidence; years come from the listed 款 only", source_id=src)
    gens_b4.append(g); gens_of[m["model_id"]].append(g)

def assign_gen(m, year, src):
    gl = [g for g in gens_of[m["model_id"]] if "[generation unspecified]" not in g["source_row_name"]]
    if len(gl) == 1:
        g = gl[0]; lo = int(g["intro_year"]) if g["intro_year"] else None; hi = int(g["discontinued_year"]) if g["discontinued_year"] else None
        flag = None
        if lo and year < lo: flag = f"year {year} is before the documented intro year {lo}"
        if hi and year > hi: flag = f"year {year} is after the documented discontinued year {hi}"
        return g, "single_generation_row", flag
    dated = sorted([(int(g["intro_year"]), g) for g in gl if g["intro_year"]], key=lambda x: x[0])
    cands = [(y, g) for y, g in dated if y <= year]
    if not cands: return ensure_unspecified_gen(m, src), "unresolved_before_first_documented_generation", f"year {year} precedes every documented generation intro"
    y0, g = cands[-1]
    if len(dated) > 1 and y0 == year and cands[-1] != dated[0]: return ensure_unspecified_gen(m, src), "unresolved_generation_boundary_year", f"{year} is the intro year of '{g['source_row_name']}' and may belong to the previous generation"
    return g, "inferred_from_documented_intro_year", None

FORCE_UNSPECIFIED = {'Sealion 05 DM-i': "Wikipedia: first-generation Sealion 05 DM-i (Sept 2024-2025) and the compact 'Sealion 05' (from March 2025) overlap in 2025, while the list row gives the second generation an intro of 2026; Autohome's 海狮05 DM-i trims cannot be attributed to either row"}

def spec_kind(lab):
    if re.search(r"概念|Concept|ocean-X", lab, re.I): return "concept"
    if "试装车" in lab: return "pre_production_trial_fit"
    if "欧洲版" in lab: return "europe_export_spec"
    if "香港车展" in lab or "车展版" in lab: return "auto_show_edition"
    if lab.endswith("基本型"): return "placeholder_few_photos"
    if "原型车" in lab: return "prototype"
    if re.search(r"联名|定制版|限量版|国漫版|战神版|特别版|纪念版|首发版|创始版", lab): return "special_edition"
    return "standard"

def resolve(sid, label, year, brand_name="BYD"):
    P = SERIES.get(sid)
    if P is None: return None, "no_policy"
    for rx, mk, y0, y1 in P["rules"]:
        if re.search(rx, label) and (y0 is None or year >= y0) and (y1 is None or year <= y1): return mk, "label_token_or_cited_rule"
    if P["default"]: return P["default"], "single_row_series_default"
    if P["candidates"]:
        ok = []
        for mk in P["candidates"]:
            g0 = gens_of[model_by_bk[(BR[brand_name], mk)]["model_id"]]; ins = [int(g["intro_year"]) for g in g0 if g["intro_year"]]
            if ins and min(ins) <= year: ok.append(mk)
        if len(ok) == 1: return ok[0], "unique_row_by_documented_intro_year"
    return None, "ambiguous_or_no_rule"

# ---------------------------------------------------------------- main mapping loop
trims_b4, colors_b4, color_by_trim, unmapped, excluded, my_new, my_evidence, conflicts = [], [], [], [], [], {}, collections.defaultdict(lambda: dict(ev=set(), src=set())), []
trim_flags = []
agg = {}; spec_to_model = {}; series_models = collections.defaultdict(set)
for key, b in SPECS.items():
    sid = b["series_id"]; ssrc = series_src[str(sid)]
    for sp in b["specs"]:
        year = int(sp["year"][:4]); lab = sp["label"]; kind = spec_kind(lab)
        base = dict(series=key, series_id=sid, year=year, spec_id=sp["spec_id"], label=lab, photos=sp["photos"], url=sp["url"], kind=kind)
        if kind == "concept": excluded.append(dict(base, reason="concept/show vehicle, not a production model-year")); continue
        brand_name = b["brand"]
        mk, how = resolve(sid, lab, year, brand_name)
        if mk and ":" in mk: brand_name, mk = mk.split(":", 1)
        if not mk:
            unmapped.append(dict(base, reason={"no_policy": "series has no mapping policy", "ambiguous_or_no_rule": "label has no powertrain token / rule and documented intro years do not decide it"}.get(how, how))); continue
        if (BR[brand_name], mk) not in model_by_bk and mk not in NEW_MODELS: raise SystemExit(f"unknown model key {mk} for series {sid}")
        m = ensure_model(mk, brand_name); ensure_single_gen(m, ssrc, all(s.get("stopsale") for s in b["specs"]))
        marker = re.search(r"第[二三四五]代", lab)
        if m["model_key"] in FORCE_UNSPECIFIED:
            g, gassign, gflag = ensure_unspecified_gen(m, ssrc), "unresolved_documented_generations_overlap", FORCE_UNSPECIFIED[m["model_key"]]
        elif marker:
            g, gassign, gflag = ensure_unspecified_gen(m, ssrc), "unresolved_label_states_" + marker.group(0), f"trim label states '{marker.group(0)}' (a later generation) but the catalogue cannot place it without guessing"
        else: g, gassign, gflag = assign_gen(m, year, ssrc)
        key2 = (g["generation_id"], year)
        if key2 in my_by_key: myrow = my_by_key[key2]; myid = myrow["model_year_id"]
        elif key2 in my_new: myid = my_new[key2]["model_year_id"]
        else:
            myid = new_id("Y", 4); my_new[key2] = dict(model_year_id=myid, model_id=m["model_id"], generation_id=g["generation_id"], year=year, label_zh=sp["year"], generation_assignment=gassign, evidence_class="SOURCED",
                                                       evidence="autohome_gallery_spec_listing", source_ids=ssrc)
        e = my_evidence[myid]; e["ev"].add("autohome_gallery_spec_listing"); e["src"].add(ssrc)
        if gflag: trim_flags.append((m["model_key"], year, sp["spec_id"], lab, gflag))
        tid = new_id("T", 4); series_models[sid].add(m["model_id"]); spec_to_model[sp["spec_id"]] = (m["model_id"], g["generation_id"], myid, tid)
        trims_b4.append(dict(trim_id=tid, model_year_id=myid, model_id=m["model_id"], generation_id=g["generation_id"], market="China", year=year, trim_name_zh=lab, trim_name_en=None, autohome_spec_id=sp["spec_id"], spec_kind=kind,
                             gallery_photos=sp["photos"], on_sale_status="discontinued (停售)" if sp.get("stopsale") else "on sale per Autohome", evidence_url=sp["url"], source_id=ssrc, model_assignment_basis=how, generation_assignment_basis=gassign, year_range_flag=gflag))
        for c in sp["colors"]:
            k = (g["generation_id"], year, c["name_zh"])
            a = agg.setdefault(k, dict(m=m, g=g, myid=myid, year=year, name=c["name_zh"], hexes=[], photos=0, specs=[], url=sp["url"], kinds=set(), ssrc=ssrc))
            a["hexes"].append(c["hex"]); a["photos"] += c["photos"]; a["specs"].append(sp["spec_id"]); a["kinds"].add(kind)
            color_by_trim.append(dict(trim_id=tid, autohome_spec_id=sp["spec_id"], year=year, trim_name_zh=lab, color_name_zh=c["name_zh"], swatch_hex=c["hex"], photos=c["photos"], spec_kind=kind, evidence_url=sp["url"], source_id=ssrc))
for (gid, year, nm), a in sorted(agg.items(), key=lambda kv: (idnum(kv[1]["m"]["model_id"]), kv[1]["year"], -kv[1]["photos"])):
    hx = collections.Counter(a["hexes"]).most_common(1)[0][0]
    colors_b4.append(dict(color_id=new_id("C", 4), model_id=a["m"]["model_id"], generation_id=gid, model_year_id=a["myid"], year_text=None, market="China", color_name_zh=nm, color_name_en=None, name_en_is_official=None,
                          supplier_published_en_names=None, color_role="two-tone" if ("双色" in nm or "/" in nm) else "body", swatch_hex=hx, evidence_class="GALLERY_OBSERVED", gallery_photo_count=a["photos"], gallery_spec_ids=";".join(sorted(set(a["specs"]))),
                          spec_kinds=";".join(sorted(a["kinds"])), source_id=a["ssrc"], retrieval="FULL", evidence_url=a["url"],
                          note="Observed in photos of %d trim(s) of this model year; absence of a colour does NOT mean it was not offered." % len(set(a["specs"])),
                          name_en_gloss_unofficial=GLOSS.get(nm), gloss_basis="literal translation by researcher; NOT an official name"))
missing_gloss = sorted({c["color_name_zh"] for c in colors_b4 if not c["name_en_gloss_unofficial"]})
trim_by_spec_b4 = {t["autohome_spec_id"]: t for t in trims_b4}

UNM = {
 8107: ("Z Coupe; Z Spider", "Autohome 腾势Z (8107) lists 硬顶版 (hard-top), 敞篷版 (convertible) and 赛道版 (track edition). Wikipedia 'Denza Z' states coupe and convertible only; the track edition's body style is not stated.", "a source stating the track edition's body style"),
 7659: ("Z9 GT PHEV; Z9 GT EV", "The 2024 trims were mapped by the cited range rule (630 = EV, 1100 = PHEV). These 2026 labels carry no range figure or powertrain token (闪充 = flash charging only) and both rows can exist in 2026 (list: Z9 GT PHEV 2024; Z9 GT EV intro not shown).", "an official Denza trim list, or an Autohome parameter value that is readable (its config table is obfuscated)"),
 6669: ("D9 DM-i; D9 EV", "Both D9 powertrains were sold 2022-2026 (Autohome lists DM-i and EV trims for most years). This label has no powertrain token.", "a source stating the powertrain of this edition"),
 8171: ("Ti7 (PHEV); Ti7 (BEV)", "Ti7 PHEV is documented from 2025 and Ti7 BEV from 2026; both exist in 2026. The '315KM'/'300KM' figures are not tied to a powertrain by any source read, so no inference is made.", "an official Ti7 trim list stating the powertrain of the 315 KM / 300 KM trims"),
 7859: ("Han L EV; Han L DM", "Autohome 汉L lists EV, DM-i and DM-p trims; the special edition label states no powertrain.", "a source stating the special edition's powertrain"),
 8005: ("Tang L EV; Tang L DM", "Autohome 唐L lists EV and DM trims; the special edition label states no powertrain.", "a source stating the special edition's powertrain"),
 3376: ("none (no catalogue row)", "Autohome 比亚迪C6 (3376): one 2014 trim '基本型' with 3 photos and no matching row in the Wikipedia list; probably a show car but no source says so.", "a source identifying the vehicle"),
}
for u in unmapped:
    c_, e_, r_ = UNM.get(u["series_id"], (None, "no mapping policy", None))
    if u["kind"] == "auto_show_edition": e_ = "Auto-show edition (" + str(u["year"]) + "): the label states no powertrain. " + (e_ or "")
    u["candidate_models"] = c_; u["evidence"] = e_; u["what_would_resolve_it"] = r_

inv_rows = []
for r in INV:
    sid = int(r["series_id"]); mids = sorted(series_models.get(sid, [])); mks = sorted(model_by_id[i]["model_key"] for i in mids)
    nspecs = len(SPECS[[k for k, b in SPECS.items() if b["series_id"] == sid][0]]["specs"]) if r["batch4_scope"] == "HARVEST" else None
    inv_rows.append(dict(brand=r["brand"], series_id=sid, series_name=r["series_name"], photos_listed_all=r["photos_all"], stopsale=r["stopsale"], batch4_scope=r["batch4_scope"], scope_note=r.get("scope_note"), specs_found=nspecs,
                         mapped_model_keys=";".join(mks) or None, mapped_model_ids=";".join(mids) or None, policy_note=(SERIES.get(sid) or {}).get("note"), source_id=SRC_BRAND[r["brand_autohome_id"]], brand_page_url=r["brand_page_url"], fetched_utc=r["fetched_utc"]))

# ---------------------------------------------------------------- Wikipedia facts / dimensions
def norm_name(s): return re.sub(r"[^a-z0-9]+", "", re.sub(r"\((?:1st|2nd|3rd)(?: gen)?\)|\(\d{4}\)", "", s.lower().replace("{{nowrap|", "").replace("}}", "")))
page_for = {}   # model_key -> wiki page (final article title)
alias_pages = collections.defaultdict(set)
for ib in WIKI["infoboxes"]:
    for disp in ib["listed_as"]: alias_pages[norm_name(disp)].add(ib["page"])
OVERRIDE_PAGE = {"Ti 7": "Fangchengbao Ti7", "Ti7 (PHEV)": "Fangchengbao Ti7", "Ti7 (BEV)": "Fangchengbao Ti7", "Shark": "BYD Shark 6", "Shark 6": "BYD Shark 6", "Bao 5": "Denza B5", "Bao 8": "Denza B8", "Seal 07 DM-i": "BYD Seal 07", "Seal 07 EV": "BYD Seal 07",
                 "Seal 06 DM-i Touring": "BYD Seal 6 DM-i", "Z9 GT PHEV": "Denza Z9", "Z9 GT EV": "Denza Z9", "Z9S": "Denza Z9S", "Z Coupe": "Denza Z", "Z Spider": "Denza Z", "Tang DM-i": "BYD Tang", "Tang EV": "BYD Tang", "Tang": "BYD Tang",
                 "N8 PHEV": "Denza N8", "N8 EV": "Denza N8", "N8L PHEV": "Denza N8L", "N8L EV": "Denza N8L", "X": "Denza N8", "400/500/EV": "Denza 500", "D9 DM-i": "Denza D9", "D9 EV": "Denza D9", "U7 PHEV": "Yangwang U7", "U7 EV": "Yangwang U7",
                 "e1": "BYD F0", "e3": "BYD e2", "Qin Pro": "BYD Qin", "Qin": "BYD Qin", "S1": "BYD Yuan", "S2": "BYD Yuan", "S7": "BYD S6", "Sirui": "BYD G6", "Surui": "BYD F3", "F3R": "BYD F3", "G3R": "BYD G3", "Tai 3": "Fangchengbao Tai 3",
                 "Formula S GT": "Fangchengbao Formula S", "Formula SL": "Fangchengbao Formula S", "Sealion 05 EV": "BYD Sealion 05 (2025)", "Sealion 05 DM-i": "BYD Sealion 05 (2025)", "Han L EV": "BYD Han L", "Han L DM": "BYD Han L", "Qin Max EV": "BYD Qin Max",
                 "Qin Max DM-i": "BYD Qin Max", "Seal 06 EV": "BYD Seal 06", "Seal 06 DM-i": "BYD Seal 06", "Seal 08 EV": "BYD Seal 08", "Seal 08 DM-i": "BYD Seal 08", "Sealion 06 EV": "BYD Sealion 06", "Sealion 06 DM-i": "BYD Sealion 06", "Sealion 08 EV": "BYD Sealion 08",
                 "Sealion 08 DM-i": "BYD Sealion 08", "Song Ultra EV": "BYD Song Ultra", "Song Ultra DM-i": "BYD Song Ultra", "Song L DM-i": "BYD Song L DM-i", "Song L EV": "BYD Song L EV", "Tang L DM": "BYD Tang L", "Tang L EV": "BYD Tang L",
                 "Datang DM": "BYD Datang", "Datang EV": "BYD Datang", "Dahan EV": "BYD Dahan", "Yuan Up (PHEV)": "BYD Atto 2", "Yuan Up (BEV)": "BYD Atto 2", "B2:e5": "BYD e5", "Yuan": "BYD Yuan", "Xia": "BYD Xia", "e7": "BYD e7",
                 "Qin L DM-i": "BYD Qin L DM-i", "Qin L EV": "BYD Qin L EV", "Seal 05 DM-i": "BYD Seal 05 DM-i", "Seal 06 GT": "BYD Seal 06 GT", "Sealion 07 EV": "BYD Sealion 7", "Sealion 07 DM-i": "BYD Sealion 07 DM", "e6": "BYD e6", "F3DM": "BYD F3DM",
                 "L3 / New F3": "BYD L3", "Song Pro": "BYD Song Pro", "Song Pro (ICE)": "BYD Song Pro", "Song Max": "BYD Song Max", "Song": "BYD Song", "Frigate 07": "BYD Frigate 07", "Flyer": "BYD Flyer", "U8": "Yangwang U8", "U8L": "Yangwang U8", "U9": "Yangwang U9",
                 "Altior": "Yangwang Altior", "N7": "Denza N7", "N9": "Denza N9", "Z9": "Denza Z9", "B5": "Denza B5", "B8": "Denza B8", "Ti9": "Fangchengbao Ti9", "Racco": "BYD Racco", "Mako": "BYD Mako", "Dolphin G DM-i": "BYD Dolphin G"}
by_page = collections.defaultdict(list)
for ib in WIKI["infoboxes"]: by_page[ib["page"]].append(ib)
def page_of(mk, brand_id=None):
    p = OVERRIDE_PAGE.get(f"{brand_id}:{mk}") or OVERRIDE_PAGE.get(mk)
    if p and p in by_page: return p
    ps = alias_pages.get(norm_name(mk), set())
    return sorted(ps)[0] if len(ps) == 1 else None
def doors_of(txt):
    m = re.search(r"(\d)-door", txt or ""); return int(m.group(1)) if m else None
dims_b4, facts_b4 = [], []
all_models_now = list(models) + models_b4
for m in all_models_now:
    mk = m["model_key"]; p = page_of(mk, m["brand_id"])
    if not p: continue
    boxes = [ib for ib in by_page[p] if ib.get("infobox_index") is not None]
    with_dims = [ib for ib in boxes if ib.get("length")]
    gl = [g for g in gens_of[m["model_id"]] if "[generation unspecified]" not in g["source_row_name"]]
    doors = {doors_of(ib.get("body_style")) for ib in boxes} - {None}
    sd = boxes[0].get("short_description") if boxes else None
    for g in gl:
        facts_b4.append(dict(generation_id=g["generation_id"], model_id=m["model_id"], doors=(sorted(doors)[0] if len(doors) == 1 else None), doors_basis=("Wikipedia infobox body_style" if len(doors) == 1 else ("infoboxes disagree: %s" % sorted(doors) if doors else "not stated")),
                             body_style_text=(boxes[0].get("body_style") if boxes else None), exterior_design_text=sd, exterior_design_basis="Wikipedia short description (body class only; not a styling description)" if sd else None,
                             production_text=(boxes[0].get("production") if len(boxes) >= 1 and len(with_dims) <= 1 else None), model_years_text=(boxes[0].get("model_years") if boxes else None), wikipedia_page=p, wikipedia_url=boxes[0]["page_url"] if boxes else None,
                             source_id=wiki_src[p], note=None if len(with_dims) <= 1 else "page has several generation infoboxes; production text not attributed to a single catalog generation"))
    for ib in with_dims:
        single = len(with_dims) == 1 and len(gl) == 1
        dims_b4.append(dict(dimension_id=None, model_id=m["model_id"], generation_id=gl[0]["generation_id"] if single else None, model_key=mk, infobox_name=ib["name"], production_text=ib.get("production"), length_text=ib["length"], width_text=ib["width"], height_text=ib["height"],
                            wheelbase_text=ib["wheelbase"], weight_text=ib["weight"], source_id=wiki_src[p], evidence_url=ib["page_url"], fetched_utc=ib.get("fetched_utc"),
                            note="Wikipedia infobox text; ranges/variants/markets as stated; not split by model year." + ("" if single else " Several infoboxes/generations: not attributed to one catalog generation.")))
seen = set(); dd = []
for d in dims_b4:
    k = (d["model_id"], d["infobox_name"], d["length_text"], d["width_text"], d["height_text"], d["wheelbase_text"])
    if k in seen: continue
    seen.add(k); d["dimension_id"] = f"DM{len(dd) + 100 + 1:03d}"; dd.append(d)
dims_b4 = dd

# ---------------------------------------------------------------- paint-code candidates / codes / links
cand_key0 = {(c["source_id"], (c["model_as_listed"] or "").upper(), c["code_raw"], c["names_raw"]) for c in cands0}
TU_MAP = {"atto-2": ["Yuan Up (BEV)"], "han": ["Han EV", "Han DM-i", "Han DM", "Han DM-p"], "king": ["Seal 05 DM-i", "Destroyer 05"], "m9": ["Xia", "M9"], "qin-l": ["Qin L DM-i", "Qin L EV"], "qin-plus": ["Qin Plus DM-i", "Qin Plus EV"],
          "seal-07": ["Seal 07 DM-i", "Seal 07 EV"], "seal-u": ["Song Plus DM-i", "Song Plus EV"], "sealion-05-ev": ["Sealion 05 EV"], "sealion-7": ["Sealion 07 EV"], "shark": ["Shark 6", "Shark"], "song-l": ["Song L DM-i", "Song L EV"],
          "song-plus": ["Song Plus DM-i", "Song Plus EV"], "song-pro": ["Song Pro"], "tang": ["Tang DM-i", "Tang EV", "Tang", "Tang DM-p"], "tang-l": ["Tang L DM", "Tang L EV"], "u9": ["U9"], "xia": ["Xia"], "e2": ["e2"],
          "fang-cheng-bao-5": ["Bao 5"], "fang-cheng-bao-8": ["Bao 8"], "fang-cheng-bao-ti3": ["Tai 3"]}
TU_SKIP = {"seal", "dolphin", "atto-3"}      # already collected in batch 2 (S32)
CR_MAP = {"atto-3": ["Yuan Plus"], "e2": ["e2"], "f0": ["F0"], "f3": ["F3"], "f3r": ["F3R"], "f6": ["F6"], "flyer": ["Flyer"], "g3": ["G3"], "han-ev": ["Han EV"], "han": ["Han DM", "Han DM-i"], "l3": ["L3 / New F3"], "leopard-5": ["Bao 5"],
          "leopard-8": ["Bao 8"], "phocidae-06dm-i": ["Seal 06 DM-i"], "qin": ["Qin"], "s6": ["S6"], "s7": ["S7"], "seal": ["Seal"], "sirui": ["Sirui"], "song": ["Song"], "surui": ["Surui"], "tang-ev": ["Tang EV"], "tang": ["Tang", "Tang DM-i"],
          "yangwang-u8": ["U8"], "yangwang-u9": ["U9"], "yuan-ev": ["Yuan"], "yuan": ["Yuan"], "yuan-plus": ["Yuan Plus"], "yuan-up": ["Yuan Up (BEV)", "Yuan Up (PHEV)"]}
cands_b4 = []; cand_models = {}
def add_cand(src, market, model_listed, year, code, names, level, url, note, mks, extra=None):
    cid = new_id("P", 3); cands_b4.append(dict(candidate_id=cid, source_id=src, market=market, model_as_listed=model_listed, year_as_listed=year, code_raw=code, names_raw=names, listing_level=level, evidence_url=url, note=note, swatch_hex=(extra or {}).get("hex"), fetched_utc=(extra or {}).get("t")))
    cand_models[cid] = mks; return cid
for r in TU["rows"]:
    slug = r["model_slug"]
    if slug in TU_SKIP: continue
    if ("S32", slug.upper(), r["code_raw"], r["names_raw"]) in cand_key0: continue
    add_cand(S_TU, "unspecified (multi-market names)", slug.upper(), None, r["code_raw"], r["names_raw"], "name-only" if slug == "all-models" else "model", r["page_url"],
             "Years not shown per row; one code may carry names from several markets/languages." if slug != "all-models" else "all-models list: no model attribution", TU_MAP.get(slug, []), dict(hex=r["swatch_hex"], t=r["fetched_utc"]))
for r in CR["rows"]:
    slug = r["model_slug"].rsplit("-m", 1)[0].replace("paint-byd-", "")
    yrs = f"{r['year_from']}-{r['year_to']}" if r["year_from"] and r["year_to"] else (r["year_from"] or None)
    if ("S31", (r["model_label"] or "").upper(), r["code_raw"], r["name_raw"]) in cand_key0: continue
    add_cand(S_CR, "Europe", r["model_label"], yrs, r["code_raw"], r["name_raw"], "model+year" if yrs else "model", r["page_url"], "Retailer model page; year range as stated by the retailer.", CR_MAP.get(slug, []), dict(hex=r["swatch_hex"], t=r["fetched_utc"]))
def tokens(code_raw): return [t.strip() for t in re.split(r"[;,]", code_raw or "") if t.strip()]
def nname(s): return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", re.sub(r"-MET\.?|¤MAT|\bMETALLIC\b|\bMATT?\b", " ", (s or "").upper()))).strip()
pc_by_tok = {p["oem_code"]: p for p in pcs0}; pcs_b4 = []; tok_cands = collections.defaultdict(lambda: dict(c=set(), s=set(), n=set()))
for c in cands0 + cands_b4:
    if c["listing_level"] in ("REJECTED", "location-only") or not c["code_raw"] or c["code_raw"] == "9010": continue
    for t in tokens(c["code_raw"]):
        d = tok_cands[t]; d["c"].add(c["candidate_id"]); d["s"].add(c["source_id"]); d["n"].update(n.strip() for n in (c["names_raw"] or "").split(","))
for t in sorted(tok_cands):
    if t in pc_by_tok: continue
    d = tok_cands[t]; pid = new_id("PC", 3)
    p = dict(paint_code_id=pid, oem_code=t, code_status="POSSIBLE", supplier_sources=";".join(sorted(d["s"])), n_independent_suppliers=len(d["s"]), candidate_ids=";".join(sorted(d["c"])), names_published=" | ".join(sorted(x for x in d["n"] if x))[:600],
             evidence_tier="RETAILER_CATALOG_UNVERIFIED", format_note="long part-number style (BYHA-/BYHB-)" if t.startswith("BYH") and "-" in t else None, note="Supplier-catalog code; not confirmed on any exact vehicle label."); pcs_b4.append(p); pc_by_tok[t] = p
# the token table of batch 2 keeps its own n_independent_suppliers; new suppliers for old tokens are recorded in links only.
colors_all = colors0 + colors_b4; col_by_model = collections.defaultdict(list)
for c in colors_all: col_by_model[model_by_id[c["model_id"]]["model_key"] if c["model_id"] in model_by_id else None].append(c)
assert not [k for k in col_by_model if k == "e5" and len({model_by_id[c["model_id"]]["brand_id"] for c in col_by_model[k]}) > 1], "ambiguous model_key in colour map"
my_year = {m["model_year_id"]: int(m["year"]) for m in mys}; my_year.update({v["model_year_id"]: v["year"] for v in my_new.values()})
links0_set = {(l["color_id"], l["oem_code"]) for l in links0}; links_b4 = []; ver_b4 = []
def vr(stype, sid, status, evidence, srcs, urls):
    ver_b4.append(dict(verification_id=new_id("V", 4), subject_type=stype, subject_id=sid, status=status, evidence=evidence, source_ids=";".join(sorted(set(srcs))), evidence_urls=" ".join(sorted(set(u for u in urls if u))), editor_approved="false", reviewed_on=None))
linked_colors = set(); cand_by_id = {c["candidate_id"]: c for c in cands0 + cands_b4}
for cid, mks in cand_models.items():
    c = cand_by_id[cid]; names = {nname(n) for n in (c["names_raw"] or "").split(",") if n.strip()}
    if not mks or not names: continue
    yf = yt = None
    if c["year_as_listed"] and re.fullmatch(r"\d{4}(-\d{4})?", c["year_as_listed"]): yf = int(c["year_as_listed"][:4]); yt = int(c["year_as_listed"][-4:])
    for mk in mks:
        for col in col_by_model.get(mk, []):
            gl = nname(GLOSS.get(col["color_name_zh"])) if col["color_name_zh"] else None
            if not gl or gl not in names: continue
            yr = my_year.get(col["model_year_id"])
            if yf and yr and not (yf <= yr <= yt): continue
            for t in tokens(c["code_raw"]):
                if (col["color_id"], t) in links0_set or any(l["color_id"] == col["color_id"] and l["oem_code"] == t for l in links_b4): continue
                srcs = tok_cands[t]["s"]
                conf = "medium" if (c["listing_level"] == "model+year" and yf and len(names) <= 2) else "low"
                basis = ("retailer lists this model with a year range that includes the model year and a name list of <=2 names; still unverified (no OEM evidence)" if conf == "medium"
                         else "retailer listing is model-level, name-only or a multi-name alias group; repetition across retailers is NOT counted as corroboration (retailers may share upstream data and none cites an OEM source)")
                lid = new_id("L", 4); pid = pc_by_tok[t]["paint_code_id"]
                links_b4.append(dict(link_id=lid, color_id=col["color_id"], paint_code_id=pid, oem_code=t, link_basis=f"exact normalized name match between a literal translation of '{col['color_name_zh']}' ('{GLOSS.get(col['color_name_zh'])}') and the retailer name list", confidence=conf, candidate_ids=cid,
                                     year_specificity="retailer gives a year range that includes the model year" if yf else "retailer listing is model-level; year not matched", confidence_basis=basis,
                                     conflict_note="Retailer name list is a multi-name alias group (%d names); treat as unreliable until a label is seen." % len(names) if len(names) > 2 else None, status="POSSIBLE"))
                linked_colors.add(col["color_id"])
                vr("color_paint_code_link", col["color_id"], "POSSIBLE", f"Code {t} listed by {len(srcs)} retailer catalog(s) for a name matching this colour. Not confirmed on an exact-vehicle label; no editor approval.", srcs, [c["evidence_url"]])
for p in pcs_b4: vr("paint_code", p["paint_code_id"], "POSSIBLE", f"Appears in {p['n_independent_suppliers']} retailer catalog(s): {p['supplier_sources']}. No OEM document or exact-vehicle label evidence.", p["supplier_sources"].split(";"), [cand_by_id[x]["evidence_url"] for x in p["candidate_ids"].split(";")])
for c in colors_b4:
    if c["color_id"] not in linked_colors: vr("factory_color", c["color_id"], "NOT FOUND", "No reliable paint code located for this colour on this model; retailer catalogs checked do not list this model/colour combination.", [c["source_id"]], [c["evidence_url"]])

# attach supplier-published names to colours (never as official names)
pub = collections.defaultdict(set)
for l in links_b4:
    pub[l["color_id"]].update(n.strip() for n in (cand_by_id[l["candidate_ids"]]["names_raw"] or "").split(",") if n.strip())
for c in colors_b4: c["supplier_published_en_names"] = " | ".join(sorted(pub[c["color_id"]])) or None


_fl = collections.defaultdict(list)
for mk_, yr_, sp_, lab_, fl_ in trim_flags: _fl[(mk_, re.sub(r"\d{4}", "YYYY", fl_))].append((yr_, sp_, lab_, fl_))
for (mk_, kind_), lst in sorted(_fl.items()):
    yrs_ = sorted({x[0] for x in lst})
    conflicts.append(dict(subject=mk_, field="Autohome trim years vs documented generation range", source_a=f"Autohome lists {len(lst)} trim(s) in {yrs_} (e.g. spec {lst[0][1]} '{lst[0][2]}')", source_b=lst[0][3] if len(set(x[3] for x in lst)) == 1 else kind_.replace("YYYY", "<year>") + " (see trims_b4.csv year_range_flag)",
                          handling="trims kept under the model (or its 'generation unspecified' bucket); not corrected; flagged for editor review"))

# ---------------------------------------------------------------- aliases / duplicates
alias_rows = []
allm = list(models) + models_b4
byalias = collections.defaultdict(set)
for m in allm:
    for a in [x.strip() for x in (m.get("alt_names") or "").split(";") if x.strip()]: byalias[a.lower()].add(m["model_key"])
for a, ks in sorted(byalias.items()):
    if len(ks) > 1: alias_rows.append(dict(alias_type="export/alt name shared by several model rows", key=a, model_keys=" | ".join(sorted(ks)), evidence="models.csv alt_names (Wikipedia list)", handling="editor decision needed before import"))
byzh = collections.defaultdict(set)
for m in allm:
    if m.get("name_zh"): byzh[m["name_zh"]].add(m["model_key"])
for z, ks in sorted(byzh.items()):
    if len(ks) > 1: alias_rows.append(dict(alias_type="same Chinese name on several model rows", key=z, model_keys=" | ".join(sorted(ks)), evidence="models.csv name_zh", handling="rows differ by powertrain/generation; keep separate, never merge on name alone"))
byname = collections.defaultdict(set)
for m in allm: byname[re.sub(r"[^a-z0-9]", "", m["model_key"].lower())].add(m["model_id"])
for n, ids in byname.items():
    if len(ids) > 1: alias_rows.append(dict(alias_type="identical normalized model name", key=n, model_keys=" | ".join(sorted(model_by_id[i]["model_key"] + "(" + i + ")" for i in ids)), evidence="model_key", handling="duplicate risk: check brand/generation"))
for m in allm:
    for g in gens_of[m["model_id"]]:
        n = g.get("note") or ""
        mm = re.search(r"(?:Exported as|Rebadged|Export rebadge of)\s+(.+?)(?: for export)?$", n.strip())
        if mm: alias_rows.append(dict(alias_type="export rebadge pair (Wikipedia list note)", key=m["model_key"], model_keys=f"{m['model_key']} <-> {mm.group(1)}", evidence=n[:120], handling="same vehicle sold under two names; keep both rows, link by this table, never merge"))
for r in WIKI.get("redirects", []):
    alias_rows.append(dict(alias_type="Wikipedia redirect (name is an alias of another article)", key=r["page"], model_keys=r["redirect_to"] + (f" #{r['redirect_section']}" if r["redirect_section"] else ""), evidence=r["wikitext"][:120], handling="alias evidence; not merged"))
for sid, mks in sorted(series_models.items()):
    if len(mks) > 1: alias_rows.append(dict(alias_type="one Autohome series covers several model rows", key=f"series {sid}", model_keys=" | ".join(sorted(mks)), evidence="Autohome series vs powertrain-split model rows", handling="trims split by label token / documented rule"))

# ---------------------------------------------------------------- conflicts against documented years / status
gen_of_id = {g["generation_id"]: g for g in gens + gens_b4}
for m in allm:
    yrs = [t["year"] for t in trims_b4 if t["model_id"] == m["model_id"]]
    if not yrs: continue
    g0 = [g for g in gens_of[m["model_id"]] if g["intro_year"]]
    if g0:
        lo = min(int(g["intro_year"]) for g in g0)
        if min(yrs) < lo: conflicts.append(dict(subject=m["model_key"], field="earliest year", source_a=f"Wikipedia list: intro {lo}", source_b=f"Autohome lists a {min(yrs)}款 trim", handling="both kept; model-year rows come from Autohome listings only"))
    st = [g["status"] for g in gens_of[m["model_id"]]]
    stops = [t["on_sale_status"] for t in trims_b4 if t["model_id"] == m["model_id"]]
    if st and all(s == "current" for s in st) and all(x.startswith("discontinued") for x in stops):
        conflicts.append(dict(subject=m["model_key"], field="sales status", source_a="Wikipedia list: current", source_b="Autohome marks every listed trim 停售 (discontinued)", handling="both kept"))
    if st and all(s == "discontinued" for s in st):
        disc = max((int(g["discontinued_year"]) for g in gens_of[m["model_id"]] if g["discontinued_year"]), default=None)
        if disc and max(yrs) > disc: conflicts.append(dict(subject=m["model_key"], field="last year", source_a=f"Wikipedia list: discontinued {disc}", source_b=f"Autohome lists a {max(yrs)}款 trim", handling="both kept"))
for ib in WIKI["infoboxes"]:
    pass
for m in allm:
    p = page_of(m["model_key"], m["brand_id"]); g = gens_of[m["model_id"]]
    if not p or not g or not g[0]["intro_year"]: continue
    boxes = [ib for ib in by_page[p] if ib.get("production")]
    if len(boxes) != 1: continue
    ys = re.findall(r"(?<!\d)(19|20)(\d\d)(?!\d)", boxes[0]["production"] or "")
    if not ys: continue
    first = int("".join(ys[0]))
    if first != int(g[0]["intro_year"]) and len(g) == 1:
        conflicts.append(dict(subject=m["model_key"], field="production start year", source_a=f"Wikipedia list intro {g[0]['intro_year']}", source_b=f"Wikipedia article infobox production '{boxes[0]['production'][:60]}'", handling="both kept (list value stays in generations.csv)"))
for r in INV:
    if r["batch4_scope"] == "HARVEST" and not series_models.get(int(r["series_id"])) and r["series_id"] not in ("3376",):
        conflicts.append(dict(subject=f"Autohome series {r['series_name']} ({r['series_id']})", field="series mapping", source_a="Autohome series with trims", source_b="no trim could be mapped to a catalogue model", handling="all trims listed in unmapped_specs_b4.csv"))

# ---------------------------------------------------------------- model coverage: models with no Autohome mapping
mapped_models = {i for ids in series_models.values() for i in ids}
remaining_ids = {x["model_id"] for x in rd("image_coverage_by_model.csv") if x["status"] == "NOT_YET_RESEARCHED"} | {m["model_id"] for m in models_b4}
WK = "https://en.wikipedia.org/wiki/"
BRAND_PAGE = {r["brand"]: (r["brand_page_url"], r["fetched_utc"], sum(1 for x in INV if x["brand"] == r["brand"])) for r in INV}
NOMAP_EV = {
 ("B2", "Datang DM"): ("PHEV variant not listed on Autohome", "Autohome series 大唐 (8102) lists 8 trims and every label is 纯电 (EV); Wikipedia list: Datang DM = PHEV 2026 (article BYD Datang).", "a 大唐 DM trim on Autohome or an official BYD trim list", WK + "BYD_Datang"),
 ("B2", "Dolphin G DM-i"): ("upcoming / not on Autohome", "Wikipedia list: Dolphin G DM-i 2026 (article BYD Dolphin G, Europe unveiling May 2026); no 海豚G series on the Autohome BYD brand page.", "an Autohome series or official trim list", WK + "BYD_Dolphin_G"),
 ("B2", "Ti 7"): ("export rebadge of a mapped model", "Wikipedia redirect 'BYD Ti 7' -> 'Fangchengbao Ti7'; list note 'Export rebadge of Fangchengbao Ti7'. The Chinese-market vehicle is Autohome series 钛7 (8171), mapped to Ti7 (PHEV)/(BEV).", "n/a - alias, not a separate vehicle (see alias_collisions_b4.csv)", WK + "Fangchengbao_Ti7"),
 ("B2", "M6 DM"): ("export-market model not on Autohome", "Wikipedia list: M6 DM 2026, three-row MPV based on Song Max. Autohome series 比亚迪M6 (798) is the 2010 M6 (mapped to 'M6 (2010)'); no later M6 series on the BYD brand page.", "an Autohome series or official trim list", WK + "List_of_BYD_Auto_vehicles"),
 ("B2", "M6 EV"): ("export-market model not on Autohome", "Wikipedia list: M6 EV 2024 (eMax 7), based on e6 and Song Max. Autohome 比亚迪M6 (798) is the 2010 M6; Autohome 比亚迪e6 (831) is mapped to e6.", "an Autohome series or official trim list", WK + "List_of_BYD_Auto_vehicles"),
 ("B2", "Mako"): ("upcoming / not on Autohome", "Wikipedia list status 'Upcoming'. Autohome has an unnamed 混动皮卡 (hybrid pickup, series 7075, 3 photos): it is not assumed to be the Mako.", "an official Mako announcement tied to an Autohome series", WK + "BYD_Mako"),
 ("B6", "e9"): ("different Autohome vehicle under the same name", "Autohome 比亚迪e9 (5955) lists 2021-2025 BYD-brand e9 trims, catalogued separately as 'e9 (BYD brand, 2021)'. Wikipedia: Linghui e9 (2026) is a later model (redirect 'Linghui e9' -> 'BYD Han#BYD e9 (2021) / Linghui e9 (2026)'); no 2026 trims listed.", "Autohome trims dated 2026 or an official Linghui e9 trim list", WK + "BYD_Han"),
 ("B6", "e5"): ("upcoming / name collision with the old BYD e5", "Wikipedia list: Linghui e5 upcoming, based on Qin Plus EV (redirect 'Linghui e5' -> 'BYD Qin#Linghui e5'). Autohome 比亚迪e5 (4073) is the 2015-2020 BYD e5, mapped to the BYD-brand row (same model_key, different brand).", "an Autohome 领汇e5 series", WK + "BYD_Qin"),
 ("B3", "B5"): ("export name of a mapped model", "List note: rebadged Fangchengbao Bao 5 for export; Wikipedia redirect 'Fangchengbao Bao 5' -> 'Denza B5'. Autohome lists the Chinese-market 豹5 (7177), mapped to 'Bao 5'.", "n/a - alias (see alias_collisions_b4.csv)", WK + "Denza_B5"),
 ("B3", "B8"): ("export name of a mapped model", "List note: rebadged Fangchengbao Bao 8 for export; Wikipedia redirect 'Fangchengbao Bao 8' -> 'Denza B8'. Autohome 豹8 (7353) is mapped to 'Bao 8'.", "n/a - alias (see alias_collisions_b4.csv)", WK + "Denza_B8"),
 ("B3", "B3"): ("export name of a mapped model", "List note: rebadged Fangchengbao Tai 3 for export. Autohome 钛3 (7356) is mapped to 'Tai 3'.", "n/a - alias (see alias_collisions_b4.csv)", WK + "Fangchengbao_Tai_3"),
 ("B2", "S1"): ("no separate Autohome series", "Wikipedia redirect 'BYD S1' -> 'BYD Yuan#BYD S1'; list row S1 (2015-2016). The Autohome BYD brand page has S2, S6, S7 and S8 but no S1 series.", "an Autohome S1 series", WK + "BYD_Yuan"),
}
nomap = []
for m in allm:
    if m["model_id"] in remaining_ids and m["model_id"] not in mapped_models:
        rsn, ev, res, url = NOMAP_EV.get((m["brand_id"], m["model_key"]), ("no Autohome series/trims mapped", "not individually reviewed", None, None))
        bn = [k for k, v in BR.items() if v == m["brand_id"]][0]; bp = BRAND_PAGE.get("BYD" if bn == "Linghui" else bn)
        nomap.append(dict(model_id=m["model_id"], model_key=m["model_key"], brand_id=m["brand_id"], reason=rsn, evidence=ev, evidence_url=url,
                          autohome_absence_check=(f"not among the {bp[2]} series listed on {bp[0]} (fetched {bp[1]})" if bp else None), what_would_resolve_it=res))

# ---------------------------------------------------------------- model years / unions
my_rows_new = list(my_new.values())
my_evid_rows = []
for myid, e in my_evidence.items():
    my_evid_rows.append(dict(model_year_id=myid, evidence="autohome_gallery_spec_listing", source_ids=";".join(sorted(e["src"])), is_new_row=any(v["model_year_id"] == myid for v in my_rows_new)))
gen_cols = ["generation_id","model_id","source_row_name","generation_label","status","intro_year","facelift_year","discontinued_year","body_type_id","body_raw","size_class","doors","doors_source_id","body_style_text","production_start_text","production_end_text","generation_facts_note","facts_source_id","exterior_design","note","source_id"]
model_cols = ["model_id","brand_id","series","model_key","name_zh","alt_names","powertrain","source_id","discovered_note"]
trim_cols = ["trim_id","model_year_id","model_id","generation_id","market","year","trim_name_zh","trim_name_en","autohome_spec_id","spec_kind","gallery_photos","on_sale_status","evidence_url","source_id","model_assignment_basis","generation_assignment_basis","year_range_flag"]
col_cols = ["color_id","model_id","generation_id","model_year_id","year_text","market","color_name_zh","color_name_en","name_en_is_official","supplier_published_en_names","color_role","swatch_hex","evidence_class","gallery_photo_count","gallery_spec_ids","spec_kinds","source_id","retrieval","evidence_url","note","name_en_gloss_unofficial","gloss_basis"]
cand_cols = ["candidate_id","source_id","market","model_as_listed","year_as_listed","code_raw","names_raw","listing_level","evidence_url","note","swatch_hex","fetched_utc"]
pc_cols = ["paint_code_id","oem_code","code_status","evidence_tier","supplier_sources","n_independent_suppliers","candidate_ids","names_published","format_note","note"]
link_cols = ["link_id","color_id","paint_code_id","oem_code","link_basis","confidence","confidence_basis","candidate_ids","year_specificity","conflict_note","status","confidence_audited","audit_note"]
ver_cols = ["verification_id","subject_type","subject_id","status","evidence","source_ids","evidence_urls","editor_approved","reviewed_on"]
my_cols = ["model_year_id","model_id","generation_id","year","label_zh","generation_assignment","evidence_class","evidence","source_ids"]
src_cols = ["source_id","title","url","source_type","retrieval","reliability","notes"]

w("batch4", "series_inventory_b4.csv", inv_rows, ["brand","series_id","series_name","photos_listed_all","stopsale","batch4_scope","scope_note","specs_found","mapped_model_keys","mapped_model_ids","policy_note","source_id","brand_page_url","fetched_utc"])
w("batch4", "series_sources_b4.csv", [dict(series_id=k, source_id=v) for k, v in series_src.items()], ["series_id", "source_id"])
w("batch4", "models_b4.csv", models_b4, model_cols); w("batch4", "generations_b4.csv", gens_b4, gen_cols); w("batch4", "model_years_b4.csv", my_rows_new, my_cols)
w("batch4", "model_year_evidence_b4.csv", my_evid_rows, ["model_year_id", "evidence", "source_ids", "is_new_row"])
w("batch4", "generation_facts_b4.csv", facts_b4, ["generation_id","model_id","doors","doors_basis","body_style_text","exterior_design_text","exterior_design_basis","production_text","model_years_text","wikipedia_page","wikipedia_url","source_id","note"])
w("batch4", "vehicle_dimensions_b4.csv", dims_b4, ["dimension_id","model_id","generation_id","model_key","infobox_name","production_text","length_text","width_text","height_text","wheelbase_text","weight_text","source_id","evidence_url","fetched_utc","note"])
w("batch4", "trims_b4.csv", trims_b4, trim_cols); w("batch4", "factory_colors_b4.csv", colors_b4, col_cols)
w("batch4", "color_by_trim_b4.csv", color_by_trim, ["trim_id","autohome_spec_id","year","trim_name_zh","color_name_zh","swatch_hex","photos","spec_kind","evidence_url","source_id"])
PINYIN = ("Xuan","Weiyang","Shangya","Falan","Chidi","Tianshan","Xizi","Xinghan","Muchuan","Para ","Ruiya","Rong","Fei Leng","Erhai","Kiln","Danxia","Yueji","Beibei","Pupu","Qinhai","Delan","Zhi")
PROPER = ("Atlantis","Marseilles","Athens","Mecca","Argyle","Bellini","Poseidon","Hera","Lafite","California","Iceland","Brazil","Danube","Le Mans","Mars","Florence","Tarim","Vatnajokull","Dolomites","Aegean","Portia","Rhea","Denza")
occ = collections.Counter(c["color_name_zh"] for c in colors0 + colors_b4 if c["color_name_zh"])
def gkind(zh, g):
    if "two-tone" in g: return "two-tone (literal)"
    if any(x in g for x in PINYIN): return "partly transliterated (pinyin) - weakest"
    if any(x in g for x in PROPER): return "proper name / place name"
    return "literal"
AMBIG = {"蓝辰银": "辰 can mean star, dawn or time; 'Blue Dawn Silver' is one reading", "际云青": "际 = boundary/edge; reading uncertain", "石影澜": "澜 = large waves; whole name poetic, translation approximate", "翡冷翠": "classical Chinese rendering of 'Florence'; the colour itself is not described",
         "紫瑢金": "瑢 is a rare character (no clear meaning); transliterated", "玄璟墨": "璟 = lustre of jade; name poetic, translation approximate", "悦己白": "悦己 = pleasing oneself; approximate", "暖萌黄白": "two colours implied (yellow-white) but not marked as two-tone by the source",
         "赤霞丹朱": "poetic; 'red glow vermilion' approximate", "法兰红": "法兰 may be a phonetic rendering of 'France' or 'Flange'; retailers use 'FLANGE RED' for a different code family", "晌雅蓝": "晌 = midday; approximate", "未央灰": "未央 = 'not yet ended' (classical); approximate"}
_idx = collections.defaultdict(set)
for c_ in cands0 + cands_b4:
    for n_ in (c_["names_raw"] or "").split(","):
        if n_.strip(): _idx[nname(n_)].add(n_.strip())
w("batch4", "color_name_glossary_b4.csv", [dict(name_zh=k, gloss_en_unofficial=v, gloss_kind=gkind(k, v), translation_note=AMBIG.get(k), retailer_english_names_equal_to_gloss=" | ".join(sorted(_idx.get(nname(v), []))) or None, review_status="REVIEWED_UNOFFICIAL_RESEARCHER_TRANSLATION", gloss_basis="researcher's translation of the Chinese name; NOT an official name and NOT taken from BYD; do not use as a marketing or paint-code name",
    occurrences_in_catalog=occ.get(k, 0), used_in_batch4=any(c["color_name_zh"] == k for c in colors_b4)) for k, v in sorted(GLOSS.items())], ["name_zh","gloss_en_unofficial","gloss_kind","translation_note","retailer_english_names_equal_to_gloss","review_status","gloss_basis","occurrences_in_catalog","used_in_batch4"])
w("batch4", "paint_code_candidates_b4.csv", cands_b4, cand_cols); w("batch4", "paint_codes_b4.csv", pcs_b4, pc_cols); w("batch4", "color_paint_code_links_b4.csv", links_b4, link_cols); w("batch4", "verification_records_b4.csv", ver_b4, ver_cols)
w("batch4", "sources_b4.csv", sources_b4, src_cols); w("batch4", "alias_collisions_b4.csv", alias_rows, ["alias_type","key","model_keys","evidence","handling"])
w("batch4", "source_conflicts_b4.csv", conflicts, ["subject","field","source_a","source_b","handling"])
w("batch4", "unmapped_specs_b4.csv", unmapped, ["series","series_id","year","spec_id","label","photos","kind","url","reason","candidate_models","evidence","what_would_resolve_it"]); w("batch4", "excluded_specs_b4.csv", excluded, ["series","series_id","year","spec_id","label","photos","kind","url","reason"])
w("batch4", "models_without_autohome_mapping_b4.csv", nomap, ["model_id","model_key","brand_id","reason","evidence","evidence_url","autohome_absence_check","what_would_resolve_it"])
w("batch4", "wikipedia_redirects_b4.csv", [dict(page=r["page"], redirect_to=r["redirect_to"], redirect_section=r["redirect_section"], wikitext=r["wikitext"]) for r in WIKI.get("redirects", [])], ["page","redirect_to","redirect_section","wikitext"])

# union tables ------------------------------------------------------------------
def union(sub, name, base_rows, new_rows, cols):
    w(sub, name, base_rows + new_rows, cols)
facts_by_gen = {f["generation_id"]: f for f in facts_b4}
gens_union = []
for g in gens + gens_b4:
    g = dict(g); f = facts_by_gen.get(g["generation_id"])
    if f:
        if not g.get("doors") and f["doors"]: g["doors"] = f["doors"]; g["doors_source_id"] = f["source_id"]
        if not g.get("body_style_text") and f["body_style_text"]: g["body_style_text"] = f["body_style_text"]
        if not g.get("exterior_design") and f["exterior_design_text"]: g["exterior_design"] = f["exterior_design_text"]
        if not g.get("production_start_text") and f["production_text"]: g["production_start_text"] = f["production_text"]
        if not g.get("facts_source_id"): g["facts_source_id"] = f["source_id"]
    if g.get("doors") and not g.get("doors_source_id"): g["doors_source_id"] = g["source_id"]   # batch-1 rows: the door count is stated in the list page's own body description (source S01)
    gens_union.append(g)
my_union = [dict(m) for m in mys]
evid = {e["model_year_id"]: e for e in my_evid_rows}
for m in my_union:
    e = evid.get(m["model_year_id"])
    if e and not e["is_new_row"]:
        m["evidence"] = ";".join(sorted(set((m["evidence"] or "").split(";")) | {e["evidence"]})); m["source_ids"] = ";".join(sorted(set((m["source_ids"] or "").split(";")) | set(e["source_ids"].split(";"))))
my_union += my_rows_new
col_union_cols = col_cols
def allcols(a, b):
    cs = list(a[0].keys()) if a else []
    for r in b:
        for k in r:
            if k not in cs: cs.append(k)
    return cs
w("catalog_union", "models_all.csv", models + models_b4, model_cols)
w("catalog_union", "generations_all.csv", gens_union, gen_cols); w("catalog_union", "model_years_all.csv", my_union, my_cols)
w("catalog_union", "trims_all.csv", trims0 + trims_b4, allcols(trims0, trims_b4)); w("catalog_union", "factory_colors_all.csv", colors0 + colors_b4, allcols(colors0, colors_b4))
cid_col = {c["color_id"]: c for c in colors_all}
def audit_conf(l):
    col = cid_col.get(l["color_id"]); yr = my_year.get(col["model_year_id"]) if col else None
    for cid_ in (l["candidate_ids"] or "").split(";"):
        cd = cand_by_id.get(cid_)
        if cd and cd["listing_level"] == "model+year" and cd["year_as_listed"] and re.fullmatch(r"\d{4}(-\d{4})?", cd["year_as_listed"]):
            yf_, yt_ = int(cd["year_as_listed"][:4]), int(cd["year_as_listed"][-4:]); nn_ = len([n for n in (cd["names_raw"] or "").split(",") if n.strip()])
            if yr and yf_ <= yr <= yt_ and nn_ <= 2: return "medium"
    return "low"
links_union = []
for l in links0 + links_b4:
    l = dict(l); a_ = "medium" if (l["confidence"] == "medium" and audit_conf(l) == "medium") else "low"   # the audit can only downgrade, never upgrade
    l["confidence_audited"] = a_
    l["audit_note"] = ("unchanged" if a_ == l["confidence"] else f"audit: '{l['confidence']}' -> '{a_}' (repetition across retailers, model-level or alias-group listings do not justify more than low; medium needs a retailer model+year listing with <=2 names)")
    links_union.append(l)
pcs_union = [dict(p, evidence_tier="RETAILER_CATALOG_UNVERIFIED") for p in pcs0] + pcs_b4
w("catalog_union", "paint_codes_all.csv", pcs_union, pc_cols); w("catalog_union", "color_paint_code_links_all.csv", links_union, link_cols)
w("catalog_union", "confirmed_oem_paint_codes.csv", [], ["paint_code_id","oem_code","verification_id","evidence_type","evidence_url","editor_id","approved_on"])
w("catalog_union", "paint_code_candidates_all.csv", cands0 + cands_b4, allcols(cands0, cands_b4)); w("catalog_union", "verification_records_all.csv", ver0 + ver_b4, ver_cols)
w("catalog_union", "sources_all.csv", srcs0 + sources_b4, src_cols); w("catalog_union", "brands_all.csv", brands, list(brands[0].keys()))

# ---------------------------------------------------------------- data validation
allspecs = sum(len(b["specs"]) for b in SPECS.values())
hard = []
def chk(name, ok, detail=""): hard.append((name, bool(ok), detail))
chk("every Autohome spec is a trim, unmapped or excluded (none lost)", allspecs == len(trims_b4) + len(unmapped) + len(excluded), f"{allspecs} specs = {len(trims_b4)} trims + {len(unmapped)} unmapped + {len(excluded)} excluded")
def uniq(rows, k): return len({r[k] for r in rows}) == len(rows)
chk("new ids unique and disjoint from batches 1-3", all([uniq(trims_b4, "trim_id"), uniq(colors_b4, "color_id"), uniq(my_rows_new, "model_year_id"), uniq(models_b4, "model_id"), uniq(gens_b4, "generation_id"), uniq(cands_b4, "candidate_id"), uniq(pcs_b4, "paint_code_id"), uniq(links_b4, "link_id"), uniq(ver_b4, "verification_id"), uniq(sources_b4, "source_id")])
    and not ({t["trim_id"] for t in trims_b4} & {t["trim_id"] for t in trims0}) and not ({c["color_id"] for c in colors_b4} & {c["color_id"] for c in colors0}) and not ({m["model_year_id"] for m in my_rows_new} & {m["model_year_id"] for m in mys})
    and not ({s["source_id"] for s in sources_b4} & {s["source_id"] for s in srcs0}) and not ({p["paint_code_id"] for p in pcs_b4} & {p["paint_code_id"] for p in pcs0}), "")
allm_ids = {m["model_id"] for m in allm}; allg = {g["generation_id"]: g for g in gens + gens_b4}; allmy = {m["model_year_id"]: m for m in mys + my_rows_new}
bad = [t["trim_id"] for t in trims_b4 if t["model_id"] not in allm_ids or allg.get(t["generation_id"], {}).get("model_id") != t["model_id"] or allmy.get(t["model_year_id"], {}).get("generation_id") != t["generation_id"] or str(allmy[t["model_year_id"]]["year"]) != str(t["year"])]
chk("trim -> model/generation/model-year consistent", not bad, f"{len(bad)} problems")
bad = [c["color_id"] for c in colors_b4 if not c["source_id"] or not c["evidence_url"] or allmy.get(c["model_year_id"], {}).get("generation_id") != c["generation_id"] or allg[c["generation_id"]]["model_id"] != c["model_id"]]
chk("every colour record has source + URL and a consistent model/generation/year", not bad, f"{len(colors_b4)} colours, {len(bad)} problems")
chk("all model-year rows are sourced (no estimates)", all(m["evidence_class"] == "SOURCED" and m["source_ids"] for m in my_rows_new), f"{len(my_rows_new)} new rows")
chk("no VERIFIED status anywhere", not any(v["status"] == "VERIFIED" for v in ver_b4) and not any(p["code_status"] == "VERIFIED" for p in pcs_b4) and not any(l["status"] == "VERIFIED" for l in links_b4), "")
chk("links reference existing colours and codes", all(l["color_id"] in {c["color_id"] for c in colors_all} and l["paint_code_id"] in {p["paint_code_id"] for p in pcs0 + pcs_b4} for l in links_b4), f"{len(links_b4)} links")
chk("all Chinese colour names have a glossary entry", not missing_gloss, str(missing_gloss[:5]))
chk("every new model/generation has a source or documented origin", all(m.get("discovered_note") for m in models_b4) and all(g["source_id"] for g in gens_b4), f"{len(models_b4)} new models, {len(gens_b4)} new generations")
chk("series inventory complete (every Autohome series has a scope)", all(r["batch4_scope"] for r in inv_rows) and len(inv_rows) == len(INV), f"{len(inv_rows)} series")
ok_all = all(ok for _, ok, _ in hard)
with open(os.path.join(STAGE, "batch4", "validation_report_batch4_data.md"), "w", encoding="utf-8") as f:
    f.write("# Batch 4 data validation report\n\n" + ("**RESULT: ALL HARD CHECKS PASSED**\n\n" if ok_all else "**RESULT: FAILED - nothing published**\n\n") + "| Check | Result | Detail |\n|---|---|---|\n")
    for n, ok, d in hard: f.write(f"| {n} | {'PASS' if ok else 'FAIL'} | {str(d)[:240].replace('|', '/')} |\n")
stats = dict(specs=allspecs, trims=len(trims_b4), unmapped=len(unmapped), excluded=len(excluded), new_models=len(models_b4), new_generations=len(gens_b4), new_model_years=len(my_rows_new), model_years_touched_existing=sum(1 for e in my_evid_rows if not e["is_new_row"]),
             colour_records=len(colors_b4), distinct_zh_colours=len({c["color_name_zh"] for c in colors_b4}), color_by_trim=len(color_by_trim), candidates=len(cands_b4), new_paint_codes=len(pcs_b4), links=len(links_b4), colours_linked=len(linked_colors),
             dims=len(dims_b4), facts=len(facts_b4), conflicts=len(conflicts), alias_rows=len(alias_rows), models_without_autohome_mapping=len(nomap), series=len(inv_rows), hard_checks=[(n, ok) for n, ok, _ in hard])
json.dump(stats, open(os.path.join(STAGE, "batch4", "stats_b4_data.json"), "w"), indent=1, ensure_ascii=False)
if not ok_all:
    print("VALIDATION FAILED - nothing published; see", os.path.join(STAGE, "batch4", "validation_report_batch4_data.md")); sys.exit(1)
for sub in ("batch4", "catalog_union"):
    os.makedirs(os.path.join(HERE, sub), exist_ok=True)
    for f in os.listdir(os.path.join(STAGE, sub)): shutil.move(os.path.join(STAGE, sub, f), os.path.join(HERE, sub, f))
shutil.rmtree(STAGE); print(json.dumps(stats, indent=1, ensure_ascii=False))
