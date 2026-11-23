#!/usr/bin/env python3
"""
BYD research dataset, batch 2 (priority models).

Inputs : batch1/*.csv (baseline), raw/autohome_specs.json (scraped, GBK-decoded),
         transcribed supplier tables below (copied from fetched pages; see sources.csv).
Outputs: *.csv in this folder (normalized), estimates_model_years.csv, REPORT_batch2.md,
         missing_data.csv.  Nothing is imported into any application.

RULES ENFORCED HERE
  * Sourced facts and estimates are in different files. model_years.csv contains only sourced years.
  * No paint code is VERIFIED. Supplier-catalog codes are POSSIBLE at best.
  * Codes are linked to a colour only on explicit name evidence (see LINKS). A colour name alone
    (e.g. "white") never inherits a code from another model.
Run:  python3 build_batch2.py
"""
import csv, json, os, re, collections, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
B1 = os.path.join(HERE, "batch1")

def rd(n):
    with open(os.path.join(B1, n), encoding="utf-8") as f:
        return list(csv.DictReader(f))

def nz(v):
    return None if v in ("", None) else v

def w(name, rows, cols):
    with open(os.path.join(HERE, name), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader()
        for r in rows:
            wr.writerow(r)

# ------------------------------------------------------------------ baseline
brands = rd("brands.csv")
models = rd("models.csv")
gens = rd("generations.csv")
b1_my = rd("model_years.csv")
b1_col = rd("factory_colors.csv")
body_types = rd("body_types.csv")
model_by_key = {m["model_key"]: m for m in models}  # keys unique inside BYD brand rows we use
gen_by_name = {g["source_row_name"]: g for g in gens}

# ------------------------------------------------------------------ sources
SRC = {}  # id -> dict
def S(i, title, url, stype, retrieval, notes, reliability):
    SRC[i] = dict(source_id=i, title=title, url=url, source_type=stype, retrieval=retrieval, notes=notes, reliability=reliability)

for r in rd("sources.csv"):
    SRC[r["source_id"]] = dict(r, reliability=None)
SRC["S01"]["reliability"] = "secondary"
for k in ("S02","S09","S10","S11"): SRC[k]["reliability"] = "OEM or OEM-importer"
for k in ("S03","S13"): SRC[k]["reliability"] = "retailer (no codes)"
for k in ("S04","S05","S06","S07","S08","S12","S14"): SRC[k]["reliability"] = "secondary"
SRC["S04"]["notes"] += " | batch 2: superseded by per-trim Autohome observations (S15-S23)."

SERIES_SRC = {"Seal": "S15", "Dolphin": "S16", "Seagull": "S17", "Yuan Plus": "S18", "Han": "S19",
              "Qin Plus": "S20", "Song Plus": "S21", "Destroyer 05": "S22", "e2": "S23"}
SERIES_ID = {"Seal": 6394, "Dolphin": 6139, "Seagull": 6762, "Yuan Plus": 6298, "Han": 5499,
             "Qin Plus": 5964, "Song Plus": 5761, "Destroyer 05": 6337, "e2": 5238}
for name, sid in SERIES_SRC.items():
    S(sid, f"Autohome picture gallery - {name} (series {SERIES_ID[name]}), per-spec exterior pages",
      f"https://car.autohome.com.cn/pic/series-t/{SERIES_ID[name]}.html",
      "secondary-catalog (Chinese auto portal)", "FULL (GBK-decoded; spec lists from series-t + series pages; per-spec exterior pages)",
      "Lists 款 (model year), 款型 (trim) and colours with photos for each exact trim. A colour listed means a photo of that trim in that colour exists; it is NOT an official availability list, so each trim shows only some colours.",
      "secondary (exact-trim photographic evidence)")
S("S24", "Autohome news - Seagull launch article (2023-04-07)", "https://www.autohome.com.cn/news/202304/1282756.html", "media article citing BYD announcement", "FULL", "Names four launch colours.", "secondary")
S("S25", "Autohome - e2 2019 launch buying guide", "https://www.autohome.com.cn/advice/201909/944699.html", "media article", "FULL", "Names 4 single + 2 two-tone colours for the 2019 launch line-up.", "secondary")
S("S26", "Autohome news - Song PLUS 2025 DM-i update (2024-07-25)", "https://www.autohome.com.cn/news/202407/1298857.html", "media article", "FULL", "States four exterior colours without naming them.", "secondary")
S("S27", "BYD official China site - Dahan EV (大汉EV) model page", "https://www.byd.com/cn/dynasty-home/models/han/da-han-ev", "OEM website", "FULL (extracted text; applicable trim/year not stated on page)", "Only official BYD China model page reached that lists exterior colours.", "OEM")
S("S29", "Colour Tubes (AU touch-up supplier) - BYD paint codes", "https://colourtubes.com.au/pages/byd-paint-code", "retailer catalog", "FULL", "Code|name table with NO model or year. Door-jamb label field 颜色/车身颜色. Source of data not stated.", "retailer (secondary)")
S("S30", "Cartouch Touch-up Paint (AU) - code lookup by year/make/model", "https://www.cartouchuppaint.com.au/your-color-code?txtYear=2024&txtmake=BYD+AUTO&txtModel=ATTO+3", "retailer catalog (paints from Axalta)", "PARTIAL (first rows only; 'Load More' not retrieved)", "Model+year pages for ATTO 3 (2022/23/24/25) and DOLPHIN 2024; SEAL and SEAGULL 2024 returned no rows.", "retailer (secondary)")
S("S31", "Carross (EU) - BYD colour codes (69 listed)", "https://www.carross.eu/en/paint-byd-b221", "retailer catalog", "FULL for main list; model pages Seal, Atto 3, Song only", "Code(s)|name|year-range; model shown only on model sub-pages. Says 'enter the code listed on the manufacturer's label'. Source of data not stated.", "retailer (secondary)")
S("S32", "Touch Up Paint Factory - BYD colour codes by model", "https://touchuppaintfactory.com/brands/byd/", "retailer catalog", "Seal, Dolphin, Atto 3 pages read; others not", "Per-model code|names lists; years not shown per row. Names mix markets/languages.", "retailer (secondary)")
S("S33", "Paint Calculators - BYD colour codes (REJECTED)", "https://www.paintcalculators.com/car-colour-codes/byd/", "unsourced catalog", "FULL", "REJECTED: sequential 'BYD-001..010' IDs, generic names (Rose Gold, Jade Green) matching no BYD/other-supplier name, claims 'Official BYD Codes' with no source. Not recorded as codes.", "rejected")
S("S34", "Autohome Q&A - 比亚迪车漆标编号在哪里 (2025-08-28)", "https://www.autohome.com.cn/ask/18504197.html", "forum Q&A (AI-disclaimed, author type not shown)", "FULL", "Says paint code is on a nameplate under the bonnet marked 'paintcolor' or 'H/S'. Weak source; contradicts door-jamb locations given by suppliers.", "weak")
S("S35", "Sina Tech / IT之家 - 第三代元PLUS six colours (2026-05-13)", "https://finance.sina.com.cn/tech/roll/2026-05-13/doc-inhxtqxm7600143.shtml", "media article citing BYD executive announcement", "FULL", "Six colours announced for new-generation Yuan PLUS.", "secondary")
wiki_pages = {"Seal": "BYD_Seal", "Dolphin": "BYD_Dolphin", "Seagull": "BYD_Seagull", "e2": "BYD_e2", "Atto 3": "BYD_Atto_3",
              "Qin": "BYD_Qin", "Han": "BYD_Han", "Song": "BYD_Song", "Song Plus": "BYD_Song_Plus", "Destroyer 05": "BYD_Destroyer_05"}
WIKI = {}
for i, (k, slug) in enumerate(wiki_pages.items()):
    sid = f"S{36+i}"
    WIKI[k] = sid
    S(sid, f"Wikipedia - {slug.replace('_',' ')}", f"https://en.wikipedia.org/wiki/{slug}", "secondary-encyclopedia",
      "PARTIAL (first ~40k chars verbatim, remainder via summary for Seal/Dolphin/Seagull)", "Production dates, body style, doors, market trims.", "secondary")
S("S46", "Autohome 车家号 - Dolphin five colour names post (2021)", "https://chejiahao.autohome.com.cn/info/9124221/", "creator post (not official Autohome)", "TITLE + search snippet only (body not retrievable)", "Snippet reports BYD-announced Dolphin names: 噗噗粉、冲浪蓝、蜜蜜橙、飒飒绿、闪闪蓝.", "weak-secondary")
S("S47", "Autohome news - Dolphin pure-colour versions (2022-06)", "https://www.autohome.com.cn/news/202206/1252424.html", "media article", "search snippet only", "Snippet: 噗噗粉 and 贝贝灰 pure-colour versions limited to Free and Fashion trims.", "weak-secondary")

# ------------------------------------------------------------------ extra models/generations (Han DM, Han DM-p)
def add_model(key, brand_id, series, zh, pt, src):
    mid = f"M{len(models)+1:03d}"
    m = dict(model_id=mid, brand_id=brand_id, series=series, model_key=key, name_zh=zh, alt_names=None, powertrain=pt, source_id=src)
    models.append(m); model_by_key[key] = m
    return m
def add_gen(model, name, intro, disc, body_raw, status, note, src):
    gid = f"G{len(gens)+1:03d}"
    g = dict(generation_id=gid, model_id=model["model_id"], source_row_name=name, generation_label=None, status=status,
             intro_year=intro, facelift_year="", discontinued_year=disc, body_type_id=gen_by_name["Han EV"]["body_type_id"],
             body_raw=body_raw, size_class="Full-size", doors="", exterior_design="", note=note, source_id=src)
    gens.append(g); gen_by_name[name] = g
    return g
m = add_model("Han DM", "B2", "Dynasty", None, "PHEV", WIKI["Han"])
add_gen(m, "Han DM", "2020", "2021", "Full-size sedan", "discontinued", "Added in batch 2 from Wikipedia 'Han DM (2020-2021)' section; not in batch-1 list page.", WIKI["Han"])
m = add_model("Han DM-p", "B2", "Dynasty", None, "PHEV", WIKI["Han"])
add_gen(m, "Han DM-p", "2022", "", "Full-size sedan", "current", "Added in batch 2: Autohome lists 汉DM-p 战神版 (2022-2024). Wikipedia: DM-p part of 2022 facelift.", WIKI["Han"])
model_id_by_key = {k: v["model_id"] for k, v in model_by_key.items()}

# ------------------------------------------------------------------ Wikipedia-derived generation facts (priority models)
FACTS = {  # gen source_row_name -> dict
 "Seal":       dict(doors=4, body="mid-size fastback sedan (4-door)", start="August 2022 (China)", end="2026 (China); export 2023-present", src=WIKI["Seal"], note="MY 2022-2025 (China); refresh Aug 2024 (new colours, LiDAR); Champion Ed. May 2023; Honor Ed. Mar 2024"),
 "Dolphin":    dict(doors=5, body="5-door hatchback; subcompact (China 2021-25), compact (global 2023-)", start="August 2021", end=None, src=WIKI["Dolphin"], note="2025 facelift Feb/Mar 2025 (page inconsistent); Champion Ed. Feb 2024; 500,000 Commemorative Sep 2023"),
 "Seagull (1st gen)": dict(doors=5, body="5-door hatchback (4-seat), city car", start="April 2023", end="2026 (China)", src=WIKI["Seagull"], note="Honor Ed. Mar 2024 added Ice Blue; update Feb 2025"),
 "Seagull (2nd gen)": dict(doors=None, body="hatchback, 5-seat (door count not separately stated)", start="October 2026", end=None, src=WIKI["Seagull"], note="MY2027; rear-motor RWD"),
 "e2":         dict(doors=5, body="5-door hatchback, compact (C-segment); e3 is the 4-door sedan", start="2019 (unveiled Shanghai Apr 2019)", end=None, src=WIKI["e2"], note="2021 LFP update; 2023 facelift"),
 "Yuan Plus (1st gen)": dict(doors=5, body="5-door compact crossover SUV (C-segment)", start="January 2022", end=None, src=WIKI["Atto 3"], note="Sold as Atto 3 abroad; Champion Ed. Sep 2023; 2025 China facelift"),
 "Yuan Plus (2nd gen)": dict(doors=None, body="compact crossover SUV", start="2026", end=None, src=WIKI["Atto 3"], note="Atto 3 page names successor 'Yuan Plus (second generation)'. Sina/Autohome call 2026 model '第三代元PLUS' (numbering conflict)."),
 "Han EV":     dict(doors=4, body="4-door full-size (E-segment) sedan", start="July 2020 (China sale)", end=None, src=WIKI["Han"], note="2022 facelift Apr 2022; 2025MY Sep 2024; 2nd gen 2026 'to commence'"),
 "Han DM-i":   dict(doors=4, body="4-door full-size (E-segment) sedan", start="April 2022 (DM-i with 2022 facelift)", end=None, src=WIKI["Han"], note="Wikipedia: DM-i versions introduced in 2022 facelift"),
 "Han DM":     dict(doors=4, body="4-door full-size sedan", start="July 2020", end="2021", src=WIKI["Han"], note="Han DM (2020-2021) 2.0T"),
 "Han DM-p":   dict(doors=4, body="4-door full-size sedan", start="April 2022", end=None, src=WIKI["Han"], note="Part of 2022 facelift"),
 "Qin Plus DM-i": dict(doors=4, body="4-door sedan (series infobox; Qin Plus not separately described)", start="March 2021 (renamed from Qin Pro)", end=None, src=WIKI["Qin"], note="2nd generation announced 2026"),
 "Qin Plus DM-i (2nd gen)": dict(doors=None, body="mid-size sedan (batch-1 list page)", start="2026", end=None, src=WIKI["Qin"], note="BYD official site calls this '第三代秦PLUS DM-i' (numbering conflict)"),
 "Qin Plus EV": dict(doors=4, body="4-door sedan (series infobox)", start="March 2021", end=None, src=WIKI["Qin"], note=None),
 "Song Plus DM-i": dict(doors=5, body="5-door compact crossover SUV", start="March 2021 (DM-i sales; model from Sep 2020)", end="2026 (China; removed from BYD site Jan 2026)", src=WIKI["Song Plus"], note="2023 facelift June 2023 (Champion Edition); export Seal U / Sealion 6"),
 "Song Plus EV": dict(doors=5, body="5-door compact crossover SUV", start="April 2021", end="2026 (China)", src=WIKI["Song Plus"], note="Export Seal U EV"),
 "Destroyer 05": dict(doors=4, body="4-door compact (C-segment) sedan", start="March 2022 (unveiled Nov 2021)", end="2025 (China); export 2023-", src=WIKI["Destroyer 05"], note="Successor Seal 05 DM-i; export Chazor/King/Seal 5 DM-i"),
}
for g in gens:
    for c in ("doors_source_id", "body_style_text", "production_start_text", "production_end_text", "generation_facts_note"):
        g.setdefault(c, None)
for name, f in FACTS.items():
    g = gen_by_name[name]
    if f["doors"] is not None and not g.get("doors"):
        g["doors"] = f["doors"]
    g["doors_source_id"] = f["src"] if f["doors"] is not None else None
    g["body_style_text"] = f["body"]; g["production_start_text"] = f["start"]; g["production_end_text"] = f["end"]
    g["generation_facts_note"] = f["note"]; g["facts_source_id"] = f["src"]

# ------------------------------------------------------------------ Autohome specs
RAW = json.load(open(os.path.join(HERE, "raw", "autohome_specs.json"), encoding="utf-8"))

def spec_kind(lab):
    if re.search(r"概念|Concept|ocean-X", lab, re.I): return "concept"
    if "试装车" in lab: return "pre_production_trial_fit"
    if "欧洲版" in lab: return "europe_export_spec"
    if "香港车展" in lab: return "hk_auto_show"
    if lab.endswith("基本型"): return "placeholder_few_photos"
    if re.search(r"联名|定制版|限量版|国漫版|战神版|特别版|纪念版", lab): return "special_edition"
    return "standard"

def resolve_model(series, lab):
    if series == "Seal": return "Seal 07 DM-i" if "DM-i" in lab else "Seal"
    if series in ("Dolphin", "Seagull", "Yuan Plus", "Destroyer 05", "e2"): return series
    if series == "Han":
        if "DM-p" in lab: return "Han DM-p"
        if "DM-i" in lab: return "Han DM-i"
        if re.match(r"DM\b", lab): return "Han DM"
        if lab.startswith("EV"): return "Han EV"
        return None
    if series in ("Qin Plus", "Song Plus"):
        if "DM-i" in lab: return f"{series} DM-i"
        if re.search(r"\bEV\b", lab): return f"{series} EV"
        return None

def resolve_gen(mkey, year):
    """returns (generation source_row_name, assignment)"""
    if mkey == "Seagull": return ("Seagull (2nd gen)", "inferred_from_year") if year >= 2027 else ("Seagull (1st gen)", "inferred_from_year")
    if mkey == "Yuan Plus": return ("Yuan Plus (2nd gen)", "inferred_from_year") if year >= 2026 else ("Yuan Plus (1st gen)", "inferred_from_year")
    if mkey == "Qin Plus DM-i": return ("Qin Plus DM-i (2nd gen)", "inferred_from_year") if year >= 2026 else ("Qin Plus DM-i", "inferred_from_year")
    if mkey in ("Han EV", "Han DM-i"): return (mkey, "unresolved_possible_2nd_gen" if year >= 2027 else "single_generation_documented")
    return (mkey, "single_generation_documented")

model_years = {}  # (gen_id, year) -> dict
def get_my(gid, mid, year, label_zh=None, assignment=None):
    k = (gid, year)
    if k not in model_years:
        model_years[k] = dict(model_year_id=f"Y{len(model_years)+1:04d}", model_id=mid, generation_id=gid, year=year,
                              label_zh=label_zh, generation_assignment=assignment, evidence=set(), source_ids=set())
    d = model_years[k]
    if label_zh and not d["label_zh"]: d["label_zh"] = label_zh
    if assignment and not d["generation_assignment"]: d["generation_assignment"] = assignment
    return d

# batch-1 documented anchor years (intro / facelift) -> sourced
estimates = []
for r in b1_my:
    g = next(x for x in gens if x["generation_id"] == r["generation_id"])
    if r["year_basis"].startswith("derived"):
        estimates.append(dict(generation_id=r["generation_id"], model_id=g["model_id"], source_row_name=g["source_row_name"], year=r["year"],
                              estimate_basis="every calendar year from intro to discontinued year of the Wikipedia list row; NOT documented year-by-year",
                              evidence_class="ESTIMATE", source_id="S01"))
    elif r["year_basis"] == "color_source_year":
        pass  # re-created below from colour evidence
    else:
        d = get_my(r["generation_id"], g["model_id"], int(r["year"]), None, "single_generation_documented")
        d["evidence"].add("list_page:" + r["year_basis"].replace("_documented", "")); d["source_ids"].add("S01")

trims, trim_rows_by_spec, excluded, unmapped = [], {}, [], []
colors_agg = {}       # (gid, year, name_zh) -> dict
color_by_trim = []
for series, blk in RAW.items():
    ssrc = SERIES_SRC[series]
    for sp in blk["specs"]:
        year = int(sp["year"][:4]); lab = sp["label"]; kind = spec_kind(lab)
        base = dict(series=series, year=year, spec_id=sp["spec_id"], label=lab, photos=sp["photos"], url=sp["url"], kind=kind)
        if kind == "concept":
            excluded.append(dict(base, reason="concept/show vehicle, not a production model-year")); continue
        mkey = resolve_model(series, lab)
        if not mkey:
            unmapped.append(dict(base, reason="cannot tell EV/DM-i variant (Europe export, special edition or trial-fit with no powertrain token)")); continue
        gname, assign = resolve_gen(mkey, year)
        g = gen_by_name[gname]; mid = g["model_id"]
        d = get_my(g["generation_id"], mid, year, sp["year"], assign)
        d["evidence"].add("autohome_gallery_spec_listing"); d["source_ids"].add(ssrc)
        tid = f"T{len(trims)+1:04d}"
        trims.append(dict(trim_id=tid, model_year_id=d["model_year_id"], model_id=mid, generation_id=g["generation_id"], market="China", year=year,
                          trim_name_zh=lab, trim_name_en=None, autohome_spec_id=sp["spec_id"], spec_kind=kind, gallery_photos=sp["photos"],
                          on_sale_status="discontinued (停售)" if sp.get("stopsale") else "on sale per Autohome", evidence_url=sp["url"], source_id=ssrc))
        for c in sp["colors"]:
            if kind in ("pre_production_trial_fit",):  # keep but flag via kind in by-trim file
                pass
            k = (g["generation_id"], year, c["name_zh"])
            a = colors_agg.setdefault(k, dict(gen=g, mid=mid, year=year, name_zh=c["name_zh"], hexes=[], photos=0, specs=[], urls=[], kinds=set(), ssrc=ssrc, series=series))
            a["hexes"].append(c["hex"]); a["photos"] += c["photos"]; a["specs"].append(sp["spec_id"]); a["urls"].append(sp["url"]); a["kinds"].add(kind)
            color_by_trim.append(dict(trim_id=tid, autohome_spec_id=sp["spec_id"], year=year, trim_name_zh=lab, color_name_zh=c["name_zh"], swatch_hex=c["hex"], photos=c["photos"], spec_kind=kind, evidence_url=sp["url"], source_id=ssrc))

# ------------------------------------------------------------------ colours
colors = []
def add_color(gen_name, year, market, name_zh, name_en, name_en_official, role, evidence_class, src, retrieval, note, url=None, extra=None):
    g = gen_by_name.get(gen_name) if gen_name else None
    my_id = None
    if g and year:
        d = get_my(g["generation_id"], g["model_id"], int(year), None, "single_generation_documented")
        d["evidence"].add("colour_source_year:" + src); d["source_ids"].add(src); my_id = d["model_year_id"]
    row = dict(color_id=f"C{len(colors)+1:04d}", model_id=g["model_id"] if g else None, generation_id=g["generation_id"] if g else None,
               model_year_id=my_id, year_text=None, market=market, color_name_zh=name_zh, color_name_en=name_en,
               name_en_is_official=name_en_official, color_role=role, swatch_hex=None, evidence_class=evidence_class,
               gallery_photo_count=None, gallery_spec_ids=None, spec_kinds=None, source_id=src, retrieval=retrieval, evidence_url=url, note=note)
    if extra: row.update(extra)
    colors.append(row)
    return row

# (a) Autohome per-trim observations aggregated per model-year-colour
for (gid, year, nm), a in sorted(colors_agg.items(), key=lambda kv: (kv[1]["gen"]["model_id"], kv[1]["year"], -kv[1]["photos"])):
    hx = collections.Counter(a["hexes"]).most_common(1)[0][0]
    r = add_color(a["gen"]["source_row_name"], a["year"], "China", nm, None, None, "body", "GALLERY_OBSERVED", a["ssrc"],
                  "FULL", "Observed in photos of %d trim(s) of this model year; absence of a colour here does NOT mean it was not offered." % len(set(a["specs"])),
                  a["urls"][0])
    r.update(swatch_hex=hx, gallery_photo_count=a["photos"], gallery_spec_ids=";".join(sorted(set(a["specs"]))), spec_kinds=";".join(sorted(a["kinds"])))

# (b) carried over from batch 1 (non-China market / OEM sources); drop superseded Qin PLUS snippet set
for r in b1_col:
    if r["source_id"] == "S04" and not r["generation_id"]: continue
    g = next((x for x in gens if x["generation_id"] == r["generation_id"]), None)
    yr = None
    if r["model_year_id"]:
        yr = next(y["year"] for y in b1_my if y["model_year_id"] == r["model_year_id"])
    ec = {"S02": "OEM_BROCHURE", "S09": "OEM_WEBSITE_SNIPPET", "S10": "OEM_BROCHURE_SNIPPET", "S11": "OEM_WEBSITE_SNIPPET"}.get(r["source_id"], "MEDIA_OR_RETAIL_SNIPPET")
    add_color(g["source_row_name"] if g else None, yr, r["market"], r["color_name_zh"] or None, r["color_name_en"], True if ec.startswith("OEM_") else None,
              r["color_role"], ec, r["source_id"], r["retrieval"], r["note"], SRC[r["source_id"]]["url"])

# (c) new article / OEM-site colours
for nm in ["萌芽绿", "极夜黑", "蜜桃粉", "暖阳白"]:
    add_color("Seagull (1st gen)", 2023, "China", nm, None, None, "body", "MEDIA_LAUNCH_ARTICLE", "S24", "FULL", "Article: BYD announced 4 creative colours at launch (2023-04-07).", SRC["S24"]["url"])
for nm in ["水晶白", "山脉灰", "法兰红", "苍穹蓝"]:
    add_color("e2", 2019, "China", nm, None, None, "body (single colour)", "MEDIA_LAUNCH_ARTICLE", "S25", "FULL", "2019 launch buying guide: 4 single-colour paints.", SRC["S25"]["url"])
for nm in ["律动黑红", "节奏黑白"]:
    add_color("e2", 2019, "China", nm, None, None, "two-tone", "MEDIA_LAUNCH_ARTICLE", "S25", "FULL", "2019 launch buying guide: 2 two-tone paints.", SRC["S25"]["url"])
for nm in ["噗噗粉", "冲浪蓝", "蜜蜜橙", "飒飒绿", "闪闪蓝"]:
    add_color("Dolphin", 2021, "China", nm, None, None, "body", "MEDIA_SNIPPET", "S46", "SNIPPET", "Reported as BYD-announced Dolphin colour names (search snippet; article body not retrievable). Possibly colour+interior theme names.", SRC["S46"]["url"])
for nm in ["幻梦粉双色", "潮玩蓝双色", "气场绿双色", "境遇青", "空境白", "线条灰"]:
    add_color("Yuan Plus (2nd gen)", 2026, "China", nm, None, None, "two-tone" if nm.endswith("双色") else "body", "MEDIA_ANNOUNCEMENT", "S35", "FULL", "Article attributes announcement to BYD Dynasty sales GM; no official BYD URL given. Matches Autohome 2026款 gallery names.", SRC["S35"]["url"])
for nm, role in [("千山翠/银双色", "two-tone"), ("赤帝红/银双色", "two-tone"), ("星汉银/黑双色", "two-tone"), ("云海米/黑双色", "two-tone"),
                 ("曜石黑", "body"), ("千山翠", "body"), ("赤帝红", "body"), ("星汉银", "body"), ("云海米", "body")]:
    add_color("Dahan EV", None, "China", nm, None, None, role, "OEM_WEBSITE_EXTRACT", "S27", "FULL (extracted)", "Official BYD China page; applicable 款型/年款 not stated on page.", SRC["S27"]["url"])

# English-name candidates are filled after candidates are built (supplier-published names only)

# ------------------------------------------------------------------ supplier code candidates (transcribed from fetched pages)
cands = []
def cand(src, market, model, year, code_raw, names_raw, level, url, note=None):
    cands.append(dict(candidate_id=f"P{len(cands)+1:03d}", source_id=src, market=market, model_as_listed=model, year_as_listed=year,
                      code_raw=code_raw, names_raw=names_raw, listing_level=level, evidence_url=url, note=note))
CT = SRC["S29"]["url"]
for code, nm in [("LAQ","Parkour Red"),("LAP","Surfing Blue"),("LAT","Mercury Blue"),("UV","Azure Blue"),("HB5","Vanishing Atlantis"),
                 ("HBG","Lisbon Beige"),("UA6","Exploration Green"),("UQ","Chinese Olive Green"),("00AN","Xuan Empty Black")]:
    cand("S29", "Australia", None, None, code, nm, "name-only", CT)
cand("S29", "Australia", None, None, "9010", "RAL 9010 White", "name-only", CT, "RAL reference colour, not a BYD code; excluded from paint_codes.")
CA = "https://www.cartouchuppaint.com.au/your-color-code?txtYear=%s&txtmake=BYD+AUTO&txtModel=%s"
for yr, rows in {"2022": [("LAP","SURF BLUE, LAGOON BLUE")],
                 "2023": [("UA6, LAG","EXPLORATION GREEN, EMERALD, FOREST GREEN"),("HAN, HA4","HARBOUR GREY, BOULDER GREY"),("RA5, LAQ","PARKOUR RED, BLUSH, SOLAR RED"),("WAC, W46C","SKI WHITE, DODO, FROST WHITE"),("LAP","SURF BLUE, LAGOON BLUE")],
                 "2024": [("AA1, AN, 00AN","COSMOS BLACK, TIDAL BLACK"),("UA6, LAG","EXPLORATION GREEN, EMERALD, FOREST GREEN"),("HAN, HA4","HARBOUR GREY, BOULDER GREY"),("RA5, LAQ","PARKOUR RED, BLUSH, SOLAR RED"),("WAC, W46C","SKI WHITE, DODO, FROST WHITE"),("LAP","SURF BLUE, LAGOON BLUE")],
                 "2025": [("HB5, HB6, H84C","ATLANTIS GREY, HARBOUR GREY"),("AA1, AN, 00AN","COSMOS BLACK, TIDAL BLACK"),("HAN, HA4","HARBOUR GREY, BOULDER GREY"),("H3, BMS","MARSEILLES GREY"),("RA5, LAQ","PARKOUR RED, BLUSH, SOLAR RED"),("WAC, W46C","SKI WHITE, DODO, FROST WHITE"),("LAP","SURF BLUE, LAGOON BLUE")]}.items():
    for code, nm in rows:
        cand("S30", "Australia", "ATTO 3", yr, code, nm, "model+year", CA % (yr, "ATTO+3"), "Only first rows retrieved ('Load More' not fetched).")
cand("S30", "Australia", "DOLPHIN", "2024", "HAN, HA4", "BOULDER GREY, TIME GREY", "model+year", CA % ("2024", "DOLPHIN"), "Only first rows retrieved.")
cand("S30", "Australia", "SEAL", "2024", None, None, "model+year", CA % ("2024", "SEAL"), "Page returned no code rows.")
cand("S30", "Australia", "SEAGULL", "2024", None, None, "model+year", CA % ("2024", "SEAGULL"), "Page returned no code rows.")
CR = SRC["S31"]["url"]
CARROSS = """HB6|ATLANTIS GREY-MET. ¤MAT|2022
AAP|OBSIDIAN BLACK-MET.|2023
HCJ|MILK ASH GREEN-MET.|2023-2024
EY|QUANTA SILVER-MET. ¤MAT|2023
BYU|PINAMU GREEN-MET.|2024
LAQ, RA5|BLUSH/PARKOUR RED-MET.|2021-2024
BB8|SNOW SILVER-MET.|2024
BBN|HIGHLIGHT BLACK|2024
BYH, XC|JADEITE YELLOW-MET.|2017-2019
BLG, ZB|TIME BROWN-MET.|2017-2018
W36C, WA2|SNOW WHITE-MET.|2017-2024
C9|GROOVE PURPLE-MET.|2023-2024
RAT|BOLD PINK-MET.|2024
BFL, R2|FLANGE RED|2009-2021
LAD, UY|GRASS GREEN-MET.|2022-2024
BYM, DN|MOUNTAINS GREY-MET.|2018-2023
BW|TIANSHAN WHITE|2007-2017
BMS, H16C, H3|MARSEILLES GREY-MET.|2009-2021
BSA|BRIGHT SILVER-MET.|2016
BYS, WW|CRYSTAL WHITE|2017-2023
BBM|FANTASY BLUE-MET.|2007
F2, L32C|FIRMAMENT BLUE-MET.|2015-2019
BGG, YU|CHAMPAGNE GOLD-MET.|2016-2019
BYT, W0, WG|WHITE|2015-2018
BBS, S1|ELEGANT SILVER-MET.|2007-2017
BBB|GERMANY BLUISH BLACK-MET.|2007-2017
SS|RHEA SILVER-MET.|2019
BFH|FLANGE YELLOW|2009
BCZ, Z2|CHOCOLATE BROWN-MET.|2015-2016
BCB, LU|EISMEER BLUE-MET.|2015-2018
LYA|CYBER GOLD-MET.|2024
BCP, XB|VITALITY ORANGE-MET.|2016-2018
BAQ|AEGAE BLUE-MET.|2015
BGD|SPLENDOROUS GOLD-MET.|2016
L25C|OCEAN BLUE-MET.|2007
LYE|ARGYLE PURPLE-MET.|2024
00AN, AA1, AN|DARK BLACK-MET.|2020-2024
BH06|OOZE GREEN-MET.|2024
BCR, RV|PURPLE RED-MET.|2016-2018
CA3|WINE RED-MET.|2023
LAR|TRISTA GREEN-MET.|2022-2023
BPB, LA|INNER MONGOLIA PURPLE BLUE-MET.|2016
UAM|HOLMES GREEN-MET.|2023
BCO, X4|MAGIC ORANGE-MET.|2015-2016
BBQ, LL|OCEAN BLUE-MET.|2007-2015
BR|FLYER RED|2007-2008
BYB, LT|FLICKER BLUE-MET.|2018
LYB|TUNDRA GREEN-MET.|2024
BGB|MINT GREEN-MET.|2016
U9|SINGAPORE GREEN-MET.|2023
G28C, GX|SOUL GREEN-MET.|2015
BHN, RH|HAOLA RED-MET.|2017
LYC|MATTE PURPLE-MET. ¤MAT|2024
BXK|SKY BLUE|2009
BBA|DONAU BLUE-MET.|2016
BRA|SEINE RED-MET.|2016
BBH|DEEP GOLD-MET.|2009
BBF|HONOURABLE GREEN-MET.|2007
BZL|NAMIBIA BEIGE-MET.|2023
J01|INKA GOLD-MET.|2005-2014
BYJ|INCA GOLD-MET.|2009
BG, G2|ENVIRONMENTAL GREEN|2007
BCM|SILVER BLACK-MET.|2016-2024
BCL|CASHMERE SILVER-MET.|2016
LYD|ATOM BLUE-MET.|2024
BSM|ROSE RED-MET.|2023
BYL|FIRFAMENT BLUE-MET.|2016-2017
CAC|KILN PURPLE-MET.|2023
BZN|PURPLE BLUE-MET.|2009"""
for line in CARROSS.splitlines():
    code, nm, yrs = line.split("|")
    cand("S31", "Europe", None, yrs, code, nm, "name-only", CR, "Main list; model not shown per row.")
cand("S31", "Europe", "Seal", "2022", "HB6", "ATLANTIS GREY-MET. ¤MAT", "model+year", "https://www.carross.eu/en/paint-byd-seal-m4147", "Model sub-page (2 colours).")
cand("S31", "Europe", "Seal", "2022-2024", "LAD, UY", "GRASS GREEN-MET.", "model+year", "https://www.carross.eu/en/paint-byd-seal-m4147", "Model sub-page.")
cand("S31", "Europe", "ATTO 3", "2021-2024", "LAQ, RA5", "BLUSH/PARKOUR RED-MET.", "model+year", "https://www.carross.eu/en/paint-byd-atto-3-m4151", "Model sub-page (2 colours).")
cand("S31", "Europe", "ATTO 3", "2023-2024", "C9", "GROOVE PURPLE-MET.", "model+year", "https://www.carross.eu/en/paint-byd-atto-3-m4151", "Model sub-page.")
for code, nm, yrs in [("BYH, XC","JADEITE YELLOW-MET.","2017-2019"),("BYM, DN","MOUNTAINS GREY-MET.","2018-2023"),("SS","RHEA SILVER-MET.","2019"),("BCB, LU","EISMEER BLUE-MET.","2015-2018"),("BCP, XB","VITALITY ORANGE-MET.","2016-2018")]:
    cand("S31", "Europe", "SONG (2015-2019 generation; NOT Song PLUS)", yrs, code, nm, "model+year", "https://www.carross.eu/en/paint-byd-song-m4143", "Model sub-page; legacy Song, listed for completeness only.")
TU = "https://touchuppaintfactory.com/brands/byd/%s/"
for model, rows in {
 "seal": [("BYHA-00002;HBG;YB9","APRICITY WHITE, LISBON SUNSHINE, LISBON WARM WHITE, TEA BEIGE, WARM WHITE"),("LAT","ARCTIC BLUE, AZUL GLACIER, GLACIER BLUE, ICE BLUE, MERCURY BLUE"),("HB6","ATLANTIS GREY MATT"),("HB5","ATLANTIS GREY, DEEP SEA BLUE"),("HAZ","BOUNDLESS CLOUD, HAZY GREY, SMOKE GREY"),("BYHB-00001;W36C;WA2;WA8","BRIGHT WHITE, GREAT WHITE, POLAR WHITE, SNOW WHITE, SNOWFIELD WHITE, SUMMIT WHITE, WHITE PEARL"),("HB4","CINZA DE ALECRIM, INDIGO GREY, ROSEMARY GREY, SHARK GREY"),("00AN;AA1","COSMOS BLACK, SPACE BLACK"),("UY","COURTYARD GREEN, SHADOW GREEN, VERDE ERVA"),("AAP","OBSIDIAN BLACK, TIDAL BLACK"),("CA3","WINE RED")],
 "dolphin": [("KW","AFTERGLOW PINK, CORAL PINK, POOPS PINK, PUPU PINK"),("UA5","ALAMO CYAN, SPROUT GREEN, LIME GREEN"),("CA2","AMETHYST PURPLE"),("BYHA-00002;HBG;YB9","APRICITY WHITE, LISBON SUNSHINE, LISBON WARM WHITE, TEA BEIGE, WARM WHITE"),("HB5","ATLANTIS GREY, DEEP SEA BLUE"),("LAP","AZUL SURFING, SURF BLUE, SURFING BLUE"),("HAN","BOULDER GREY, CINZA BEIBEI, CINZA BOULDER GRAY, CLIMBING GREY, DOLPHIN GREY, URBAN GREY"),("WAC","BRIGHT SILVER, DODO WHITE, DOODLE WHITE, SAND WHITE, SKI WHITE, SKIING WHITE"),("YB1","CHEESE YELLOW, CREAM WHITE"),("B1;B7822;DBU","DELAN BLACK, JET BLACK, POLAR NIGHT BLACK"),("YAK","HONEY ORANGE"),("SSL;UT","RUSTLE GREEN")],
 "atto-3": [("LAG;UA6","ADVENTURING GREEN, EXPLORATION GREEN, EXPLORING GREEN"),("LAP","AZUL SURFING, SURF BLUE, SURFING BLUE"),("LAQ;RA5","BLUSH RED, PARKOUR RED"),("HAN","BOULDER GREY, CINZA BEIBEI, CINZA BOULDER GRAY, CLIMBING GREY, DOLPHIN GREY, URBAN GREY"),("WAC","BRIGHT SILVER, DODO WHITE, DOODLE WHITE, SAND WHITE, SKI WHITE, SKIING WHITE"),("HA4","TIME GREY")]}.items():
    for code, nm in rows:
        cand("S32", "unspecified (multi-market names)", {"seal":"SEAL","dolphin":"DOLPHIN","atto-3":"ATTO 3"}[model], None, code, nm, "model", TU % model, "Years not shown per row; one code may carry names from several markets/languages.")
cand("S33", "unspecified", "multiple", "2020-2024", "BYD-001..BYD-010", "Crystal White, Obsidian Black, Glacier Blue, ... Rose Gold", "REJECTED", SRC["S33"]["url"], "Rejected, see sources.")
cand("S34", "China", None, None, None, None, "location-only", SRC["S34"]["url"], "Says nameplate under bonnet ('paintcolor' / 'H/S'); no code example given.")

def tokens(code_raw):
    if not code_raw: return []
    return [t.strip() for t in re.split(r"[;,]", code_raw) if t.strip()]

# ------------------------------------------------------------------ paint codes (distinct tokens) -> POSSIBLE only
tok_src = collections.defaultdict(lambda: dict(cands=[], srcs=set(), names=set()))
for c in cands:
    if c["listing_level"] in ("REJECTED", "location-only") or c["code_raw"] in ("9010", None): continue
    for t in tokens(c["code_raw"]):
        d = tok_src[t]; d["cands"].append(c["candidate_id"]); d["srcs"].add(c["source_id"]); d["names"].update(n.strip() for n in (c["names_raw"] or "").split(","))
paint_codes = []; pc_id = {}
for t in sorted(tok_src):
    pid = f"PC{len(paint_codes)+1:03d}"; pc_id[t] = pid
    d = tok_src[t]
    fmt = "long part-number style (BYHA-/BYHB-)" if t.startswith("BYH") and "-" in t else None
    paint_codes.append(dict(paint_code_id=pid, oem_code=t, code_status="POSSIBLE", alt_code_group=None,
                            supplier_sources=";".join(sorted(d["srcs"])), n_independent_suppliers=len(d["srcs"]),
                            candidate_ids=";".join(d["cands"]), names_published=" | ".join(sorted(x for x in d["names"] if x))[:600],
                            format_note=fmt, note="Supplier-catalog code; not confirmed on any exact vehicle label."))

# ------------------------------------------------------------------ colour -> code links (explicit name evidence only)
LINKS = [
 # (model_key(s), market, colour name (zh or en), code tokens, candidate selectors (source, model_as_listed, code_raw), basis, confidence, note)
 (["Seal"], "China", "玄空黑", ["00AN","AA1"], [("S32","SEAL","00AN;AA1"),("S29",None,"00AN"),("S31",None,"00AN, AA1, AN")], "supplier name equivalence: 'Cosmos Black'/'Xuan Empty Black' (literal of 玄空黑)", "medium", "Three independent suppliers; 'Xuan Empty Black' is a literal rendering of 玄空黑."),
 (["Seal"], "China", "亚特兰蒂斯灰", ["HB5","HB6"], [("S32","SEAL","HB5"),("S32","SEAL","HB6"),("S31","Seal","HB6")], "exact name 'Atlantis Grey'", "low", "CONFLICT: HB5 (gloss) vs HB6 (listed MATT / ¤MAT). Which applies to which year/finish is unknown."),
 (["Seal"], "China", "迷迭灰", ["HB4"], [("S32","SEAL","HB4")], "supplier name 'Rosemary Grey' (literal of 迷迭灰; 'Cinza de Alecrim' = rosemary)", "medium", "Same code also lists 'Shark Grey' (AU brochure name)."),
 (["Seal"], "China", "北冰蓝", ["LAT"], [("S32","SEAL","LAT")], "supplier name 'Arctic Blue' (literal of 北冰蓝)", "medium", None),
 (["Seal"], "China", "风卷草绿", ["UY","LAD"], [("S32","SEAL","UY"),("S31","Seal","LAD, UY")], "supplier names 'Grass Green'/'Verde Erva' (grass green)", "low", "Literal match is partial (风卷草 = windswept grass)."),
 (["Seal"], "Australia", "Atlantis Grey", ["HB5","HB6"], [("S32","SEAL","HB5"),("S32","SEAL","HB6"),("S31","Seal","HB6"),("S29",None,"HB5")], "exact name match", "low", "Same HB5/HB6 conflict as above."),
 (["Seal"], "Australia", "Cosmos Black", ["00AN","AA1"], [("S32","SEAL","00AN;AA1"),("S30","ATTO 3","AA1, AN, 00AN")], "exact name match", "medium", None),
 (["Seal"], "Australia", "Shark Grey", ["HB4"], [("S32","SEAL","HB4")], "exact name match", "medium", None),
 (["Dolphin"], "China", "噗噗粉", ["KW"], [("S32","DOLPHIN","KW")], "supplier names 'Pupu Pink'/'Poops Pink' (literal 噗噗粉)", "medium", None),
 (["Dolphin"], "China", "冲浪蓝", ["LAP"], [("S32","DOLPHIN","LAP"),("S29",None,"LAP")], "supplier names 'Surfing Blue' (literal 冲浪蓝)", "medium", None),
 (["Dolphin"], "China", "芝士黄", ["YB1"], [("S32","DOLPHIN","YB1")], "supplier name 'Cheese Yellow' (literal)", "medium", None),
 (["Dolphin"], "China", "亚特兰蒂斯灰", ["HB5"], [("S32","DOLPHIN","HB5")], "exact name 'Atlantis Grey'", "low", "HB6 (matte) variant may also exist."),
 (["Dolphin"], "China", "贝贝灰", ["HAN"], [("S32","DOLPHIN","HAN"),("S30","DOLPHIN","HAN, HA4")], "supplier name list contains 'Cinza Beibei' (贝贝灰)", "low", "Code HAN is shared in supplier lists with Urban/Boulder/Climbing/Time Grey (multi-name group); treat as unreliable until label seen."),
 (["Dolphin"], "United Kingdom", "Amethyst Purple", ["CA2"], [("S32","DOLPHIN","CA2")], "exact name match (other market)", "low", None),
 (["Dolphin"], "United Kingdom", "Coral Pink", ["KW"], [("S32","DOLPHIN","KW")], "exact name match (other market)", "low", None),
 (["Dolphin"], "United Kingdom", "Skiing White", ["WAC"], [("S32","DOLPHIN","WAC")], "exact name match (other market)", "low", None),
 (["Dolphin"], "United Kingdom", "Surfing Blue", ["LAP"], [("S32","DOLPHIN","LAP"),("S29",None,"LAP")], "exact name match", "low", None),
 (["Dolphin"], "United Kingdom", "Jet Black", ["B1","B7822","DBU"], [("S32","DOLPHIN","B1;B7822;DBU")], "exact name match (other market)", "low", None),
 (["Dolphin"], "United Kingdom", "Urban Grey", ["HAN"], [("S32","DOLPHIN","HAN")], "exact name match (other market)", "low", "Multi-name group (see 贝贝灰)."),
 (["Dolphin"], "United Kingdom", "Atlantis Grey", ["HB5"], [("S32","DOLPHIN","HB5")], "exact name match", "low", None),
 (["Yuan Plus (1st gen)"], "China", "探险绿", ["UA6","LAG"], [("S32","ATTO 3","LAG;UA6"),("S29",None,"UA6"),("S30","ATTO 3","UA6, LAG")], "supplier name 'Exploration Green' (literal of 探险绿)", "medium", "Three suppliers."),
 (["Yuan Plus (1st gen)"], "China", "冲浪蓝", ["LAP"], [("S32","ATTO 3","LAP"),("S30","ATTO 3","LAP")], "supplier name 'Surf(ing) Blue' (literal)", "medium", None),
 (["Yuan Plus (1st gen)"], "China", "跑酷红", ["LAQ","RA5"], [("S32","ATTO 3","LAQ;RA5"),("S30","ATTO 3","RA5, LAQ"),("S31","ATTO 3","LAQ, RA5"),("S29",None,"LAQ")], "supplier name 'Parkour Red' (literal)", "medium", "Four suppliers."),
 (["Yuan Plus (1st gen)"], "China", "攀岩灰", ["HAN","HA4"], [("S32","ATTO 3","HAN"),("S30","ATTO 3","HAN, HA4")], "supplier names 'Boulder/Climbing Grey' (literal 攀岩灰)", "low", "Multi-name group (also Time Grey, Harbour Grey, Urban Grey)."),
 (["Yuan Plus (1st gen)"], "China", "滑雪白", ["WAC","W46C"], [("S32","ATTO 3","WAC"),("S30","ATTO 3","WAC, W46C")], "supplier name 'Ski White' (literal)", "medium", None),
 (["Yuan Plus (1st gen)"], "Nepal", "Surf Blue", ["LAP"], [("S32","ATTO 3","LAP"),("S30","ATTO 3","LAP")], "exact name match", "medium", None),
 (["Yuan Plus (1st gen)"], "Nepal", "Ski White", ["WAC","W46C"], [("S32","ATTO 3","WAC"),("S30","ATTO 3","WAC, W46C")], "exact name match", "medium", None),
 (["Yuan Plus (1st gen)"], "Nepal", "Harbour Grey", ["HAN","HA4","HB5","HB6","H84C"], [("S30","ATTO 3","HAN, HA4"),("S30","ATTO 3","HB5, HB6, H84C")], "exact name match", "low", "Cartouch lists 'Harbour Grey' under two different code groups (HAN/HA4 and HB5/HB6/H84C): ambiguous."),
 (["Yuan Plus (1st gen)"], "Nepal", "Cosmos Black", ["AA1","AN","00AN"], [("S30","ATTO 3","AA1, AN, 00AN")], "exact name match", "medium", None),
 (["Yuan Plus (1st gen)"], "India (publisher-inferred)", "Atlantis Gray", ["HB5","HB6","H84C"], [("S30","ATTO 3","HB5, HB6, H84C")], "exact name match (Atlantis Grey, 2025 list)", "low", None),
 (["Yuan Plus (1st gen)"], "Australia", "Forest Green", ["UA6","LAG"], [("S30","ATTO 3","UA6, LAG")], "exact name 'Forest Green' inside the Exploration Green code group", "low", "AU supplier lists Forest Green as an alias of the Exploration Green code."),
 (["Seagull (1st gen)"], "China", "北冰蓝", ["LAT"], [("S32","SEAL","LAT")], "supplier name 'Arctic Blue' (literal)", "low", "Code listed under Seal page, not Seagull."),
 (["Seagull (1st gen)"], "China", "萌芽绿", ["UA5"], [("S32","DOLPHIN","UA5")], "supplier name 'Sprout Green' (literal of 萌芽绿)", "low", "Code listed under Dolphin page, not Seagull."),
 (["Seagull (1st gen)"], "Philippines", "Apricity White", ["BYHA-00002","HBG","YB9"], [("S32","SEAL","BYHA-00002;HBG;YB9")], "exact name match", "low", "Code group listed under Seal/Dolphin pages, not Seagull."),
 (["Seagull (1st gen)"], "Philippines", "Delan Black", ["B1","B7822","DBU"], [("S32","DOLPHIN","B1;B7822;DBU")], "exact name match", "low", "Listed under Dolphin page."),
 (["Seagull (1st gen)"], "Philippines", "Sprout Green", ["UA5"], [("S32","DOLPHIN","UA5")], "exact name match", "low", "Listed under Dolphin page."),
 (["Seagull (1st gen)"], None, "Arctic Blue", ["LAT"], [("S32","SEAL","LAT")], "exact name match", "low", "Listed under Seal page."),
]
cand_index = {(c["source_id"], c["model_as_listed"], c["code_raw"]): c["candidate_id"] for c in cands}
links, ver = [], []
def vr(subject_type, subject_id, status, evidence, srcs, urls):
    ver.append(dict(verification_id=f"V{len(ver)+1:04d}", subject_type=subject_type, subject_id=subject_id, status=status, evidence=evidence,
                    source_ids=";".join(sorted(set(srcs))), evidence_urls=" ".join(sorted(set(urls))), editor_approved="false", reviewed_on=None))
colors_by_key = collections.defaultdict(list)
for c in colors:
    g = next((x for x in gens if x["generation_id"] == c["generation_id"]), None)
    c["_gen"] = g["source_row_name"] if g else None
    colors_by_key[(c["_gen"], c["market"], c["color_name_zh"] or c["color_name_en"])].append(c)
linked_colors = set()
for mkeys, market, name, toks, sels, basis, conf, note in LINKS:
    for gname in mkeys:
        for col in colors_by_key.get((gname, market, name), []):
            cids = [cand_index[s] for s in sels if s in cand_index]
            missing = [s for s in sels if s not in cand_index]
            assert not missing, ("missing candidate selector", missing)
            for t in toks:
                lid = f"L{len(links)+1:04d}"
                links.append(dict(link_id=lid, color_id=col["color_id"], paint_code_id=pc_id[t], oem_code=t, link_basis=basis, confidence=conf,
                                  candidate_ids=";".join(cids), year_specificity="supplier listing is model-level or name-only; year not matched" if not any(cands[int(x[1:])-1]["listing_level"] == "model+year" for x in cids) else "partly year-listed (see candidates)",
                                  conflict_note=note, status="POSSIBLE"))
            linked_colors.add(col["color_id"])
            names_pub = sorted({n.strip() for s in sels for n in (next(c for c in cands if c["candidate_id"] == cand_index[s])["names_raw"] or "").split(",")})
            col["_pub_names"] = names_pub
            srcs = {next(c for c in cands if c["candidate_id"] == x)["source_id"] for x in cids}
            urls = {next(c for c in cands if c["candidate_id"] == x)["evidence_url"] for x in cids}
            vr("color_paint_code_link", col["color_id"], "POSSIBLE",
               f"Code(s) {'/'.join(toks)} listed by {len(srcs)} retailer catalog(s) for a name matching this colour ({basis}). Not confirmed on an exact-vehicle label; no editor approval.",
               srcs, urls)
for p in paint_codes:
    vr("paint_code", p["paint_code_id"], "POSSIBLE", f"Appears in {p['n_independent_suppliers']} retailer catalog(s): {p['supplier_sources']}. No OEM document or exact-vehicle label evidence.",
       p["supplier_sources"].split(";"), [c["evidence_url"] for c in cands if c["candidate_id"] in p["candidate_ids"].split(";")])
for col in colors:
    if col["color_id"] not in linked_colors:
        vr("factory_color", col["color_id"], "NOT FOUND", "No reliable paint code located for this colour on this model; supplier catalogs checked do not list this model/colour combination.", [col["source_id"]], [col["evidence_url"] or ""])
for c in cands:
    if c["listing_level"] == "REJECTED":
        vr("source", "S33", "NOT FOUND", "Rejected source; no codes recorded.", ["S33"], [c["evidence_url"]])
for col in colors:
    pn = col.pop("_pub_names", None)
    col["supplier_published_en_names"] = " | ".join(pn) if pn else None
    col.pop("_gen", None)

# ------------------------------------------------------------------ writers
my_rows = []
for k, d in sorted(model_years.items(), key=lambda kv: kv[1]["model_year_id"]):
    my_rows.append(dict(model_year_id=d["model_year_id"], model_id=d["model_id"], generation_id=d["generation_id"], year=d["year"],
                        label_zh=d["label_zh"], generation_assignment=d["generation_assignment"], evidence_class="SOURCED",
                        evidence=";".join(sorted(d["evidence"])), source_ids=";".join(sorted(d["source_ids"]))))
gen_cols = ["generation_id","model_id","source_row_name","generation_label","status","intro_year","facelift_year","discontinued_year","body_type_id","body_raw","size_class","doors","doors_source_id","body_style_text","production_start_text","production_end_text","generation_facts_note","facts_source_id","exterior_design","note","source_id"]
w("brands.csv", brands, ["brand_id","name","parent_brand_id"])
w("models.csv", models, ["model_id","brand_id","series","model_key","name_zh","alt_names","powertrain","source_id"])
w("generations.csv", gens, gen_cols)
w("model_years.csv", my_rows, ["model_year_id","model_id","generation_id","year","label_zh","generation_assignment","evidence_class","evidence","source_ids"])
w("estimates_model_years.csv", estimates, ["generation_id","model_id","source_row_name","year","estimate_basis","evidence_class","source_id"])
w("trims.csv", trims, ["trim_id","model_year_id","model_id","generation_id","market","year","trim_name_zh","trim_name_en","autohome_spec_id","spec_kind","gallery_photos","on_sale_status","evidence_url","source_id"])
w("body_types.csv", body_types, ["body_type_id","name"])
col_cols = ["color_id","model_id","generation_id","model_year_id","year_text","market","color_name_zh","color_name_en","name_en_is_official","supplier_published_en_names","color_role","swatch_hex","evidence_class","gallery_photo_count","gallery_spec_ids","spec_kinds","source_id","retrieval","evidence_url","note"]
w("factory_colors.csv", colors, col_cols)
w("color_by_trim.csv", color_by_trim, ["trim_id","autohome_spec_id","year","trim_name_zh","color_name_zh","swatch_hex","photos","spec_kind","evidence_url","source_id"])
w("paint_code_candidates.csv", cands, ["candidate_id","source_id","market","model_as_listed","year_as_listed","code_raw","names_raw","listing_level","evidence_url","note"])
w("paint_codes.csv", paint_codes, ["paint_code_id","oem_code","code_status","supplier_sources","n_independent_suppliers","candidate_ids","names_published","format_note","note"])
w("color_paint_code_links.csv", links, ["link_id","color_id","paint_code_id","oem_code","link_basis","confidence","candidate_ids","year_specificity","conflict_note","status"])
w("verification_records.csv", ver, ["verification_id","subject_type","subject_id","status","evidence","source_ids","evidence_urls","editor_approved","reviewed_on"])
w("sources.csv", [SRC[k] for k in sorted(SRC)], ["source_id","title","url","source_type","retrieval","reliability","notes"])
w("excluded_specs.csv", excluded, ["series","year","spec_id","label","photos","kind","url","reason"])
w("unmapped_specs.csv", unmapped, ["series","year","spec_id","label","photos","kind","url","reason"])

# ------------------------------------------------------------------ coverage / missing data
PRIORITY = {"Seal": ["Seal"], "Dolphin": ["Dolphin"], "Seagull": ["Seagull"], "Atto 3 / Yuan PLUS": ["Yuan Plus"], "Han": ["Han EV","Han DM-i","Han DM","Han DM-p"],
            "Qin PLUS": ["Qin Plus DM-i","Qin Plus EV"], "Song PLUS": ["Song Plus DM-i","Song Plus EV"], "Destroyer 05": ["Destroyer 05"], "e2": ["e2"]}
mk_of = {m["model_id"]: m["model_key"] for m in models}
gen_of = {g["generation_id"]: g for g in gens}
col_by_my = collections.defaultdict(list)
for c in colors:
    if c["model_year_id"]: col_by_my[c["model_year_id"]].append(c)
missing = []
cov = []
for label, keys in PRIORITY.items():
    mids = {model_by_key[k]["model_id"] for k in keys}
    mys = [d for d in my_rows if d["model_id"] in mids]
    yrs = sorted({int(d["year"]) for d in mys})
    n_my = len(mys); n_my_col = sum(1 for d in mys if col_by_my.get(d["model_year_id"]))
    n_trim = sum(1 for t in trims if t["model_id"] in mids)
    n_col = sum(1 for c in colors if c["model_id"] in mids)
    ids = {c["color_id"] for c in colors if c["model_id"] in mids}
    n_link = len({l["color_id"] for l in links if l["color_id"] in ids})
    for d in mys:
        if not col_by_my.get(d["model_year_id"]):
            missing.append(dict(scope=label, model=mk_of[d["model_id"]], year=d["year"], issue="model-year has no colour record", severity="gap"))
    if yrs:
        for y in range(yrs[0], yrs[-1] + 1):
            if y not in yrs:
                missing.append(dict(scope=label, model=",".join(keys), year=y, issue="no model-year record between first and last documented year (no 款 listed in Autohome gallery; may simply have no photos)", severity="gap"))
    for k in keys:
        for g in gens:
            if g["model_id"] == model_by_key[k]["model_id"] and not g.get("doors"):
                missing.append(dict(scope=label, model=g["source_row_name"], year=None, issue="door count not documented", severity="gap"))
    cov.append(dict(model=label, model_years=n_my, model_years_with_colours=n_my_col, trims=n_trim, colour_records=n_col, colours_with_possible_code=n_link,
                    years=f"{yrs[0]}-{yrs[-1]}" if yrs else None))
for c in colors:
    if c["color_id"] not in linked_colors and c["model_id"] in {model_by_key[k]["model_id"] for ks in PRIORITY.values() for k in ks}:
        pass
w("missing_data.csv", missing, ["scope","model","year","issue","severity"])
w("coverage_priority.csv", cov, ["model","years","model_years","model_years_with_colours","trims","colour_records","colours_with_possible_code"])

pri_mids = {model_by_key[k]["model_id"] for ks in PRIORITY.values() for k in ks}
pri_cols = [c for c in colors if c["model_id"] in pri_mids]
stats = dict(
    models=len(models), generations=len(gens), model_year_sourced=len(my_rows), model_year_estimates_separate=len(estimates),
    trims=len(trims), trims_priority=sum(1 for t in trims if t["model_id"] in pri_mids),
    color_records=len(colors), color_records_priority=len(pri_cols),
    distinct_zh_names_priority=len({c["color_name_zh"] for c in pri_cols if c["color_name_zh"]}),
    color_by_trim_rows=len(color_by_trim),
    colour_evidence_classes=dict(collections.Counter(c["evidence_class"] for c in colors)),
    paint_code_tokens=len(paint_codes), candidates=len(cands), links=len(links), colours_with_possible_code=len(linked_colors),
    colours_linked_priority=len({l["color_id"] for l in links} & {c["color_id"] for c in pri_cols}),
    verification=dict(collections.Counter(v["status"] for v in ver)),
    excluded_specs=len(excluded), unmapped_specs=len(unmapped), missing_rows=len(missing), coverage=cov,
)
json.dump(stats, open(os.path.join(HERE, "stats.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(stats, indent=1, ensure_ascii=False))

# ------------------------------------------------------------------ conflicts file
CONFLICTS = [
 ("Han DM-i", "start year", "Wikipedia list page: intro 2020", "Wikipedia Han article: DM-i introduced with April 2022 facelift; Autohome lists 2020款 as 'DM' (not DM-i)", "model_years row Han DM-i 2020 rests only on the list page; treat as doubtful"),
 ("Song Plus DM-i", "start year", "Wikipedia list page: intro 2020", "Song Plus article: model Sep 2020 (petrol); DM-i on sale Mar 2021; Autohome DM-i starts 2021款", "Song Plus DM-i 2020 rests only on the list page; treat as doubtful"),
 ("Yuan Plus 2026", "generation number", "Wikipedia list: 2nd generation (Atto 5)", "Sina/Autohome: 第三代元PLUS", "Numbering differs by source; batch 2 keeps Wikipedia numbering and records the conflict"),
 ("Qin Plus DM-i 2026+", "generation number", "Wikipedia list: 2nd gen (HA3H)", "BYD official site: 第三代秦PLUS DM-i", "Same as above; Autohome 2026款/2027款 assigned to 2nd gen by year (inferred)"),
 ("Seal", "production end", "Wikipedia infobox: production to 2026, model years 2022-2025", "Autohome lists 2025款 as last", "Both recorded as text; no model-year 2026 created"),
 ("Dolphin", "2025 facelift month", "Wikipedia overview: March 2025", "Wikipedia China section: February 2025", "Recorded as 'Feb/Mar 2025'"),
 ("Seal (all markets)", "paint code for Atlantis Grey", "TouchUp Paint Factory: HB5 = Atlantis Grey, HB6 = Atlantis Grey MATT", "Carross: HB6 = Atlantis Grey (listed with matt flag) for Seal 2022", "Links to both HB5 and HB6 at 'low' confidence"),
 ("Atto 3 (Harbour Grey)", "paint code", "Cartouch AU: Harbour Grey listed under HAN/HA4", "Cartouch AU 2025: Harbour Grey also listed under HB5/HB6/H84C", "Ambiguous; linked at 'low' confidence"),
 ("Grey group HAN", "multi-name code", "Suppliers list one code (HAN) for Boulder/Climbing/Urban/Dolphin/Beibei Grey; HA4 for Time Grey", "A vehicle label carries one code, so these names are probably different paints grouped by the retailer", "Links to HAN are 'low'; do not import as OEM codes without label evidence"),
 ("Seal India colours", "colour count", "BYD India page (snippet): 5 colours incl. Shark Grey", "Another India source: 4 colours without Shark Grey", "Both kept; snippet-level"),
 ("Alias collisions (batch 1)", "export names", "Qin L DM-i and Seal 06 DM-i both 'Seal 6 DM-i'; Destroyer 05 and Seal 05 DM-i both 'Seal 5 DM-i'/'King'; Dolphin and e2 both 'e2'", "n/a", "Editor decision needed before import"),
 ("Paint label location", "where to find code", "Colour Tubes: black label in driver door jamb (B-pillar), field 颜色/车身颜色 (Atto 3, Dolphin, Seal)", "Autohome Q&A (weak): nameplate under bonnet marked 'paintcolor' or 'H/S'", "Door-jamb location has retailer support only; neither is OEM documentation"),
]
w("source_conflicts.csv", [dict(subject=a, field=b, source_a=c, source_b=d, handling=e) for a, b, c, d, e in CONFLICTS], ["subject","field","source_a","source_b","handling"])

# ------------------------------------------------------------------ progress report
pm = {r["model"]: r for r in cov}
tot_my = sum(r["model_years"] for r in cov); tot_my_col = sum(r["model_years_with_colours"] for r in cov)
tot_tr = sum(r["trims"] for r in cov); tot_col = sum(r["colour_records"] for r in cov); tot_lk = sum(r["colours_with_possible_code"] for r in cov)
rows_md = "\n".join(f"| {r['model']} | {r['years']} | {r['model_years']} | {r['model_years_with_colours']} | {r['trims']} | {r['colour_records']} | {r['colours_with_possible_code']} |" for r in cov)
gal = sum(1 for c in pri_cols if c["evidence_class"] == "GALLERY_OBSERVED")
oem_c = sum(1 for c in pri_cols if c["evidence_class"].startswith("OEM_"))
rep = f"""# BYD research - Batch 2 progress report (priority models)

Status: research only. **No application files modified. Nothing imported.** Nothing is VERIFIED.
Rebuild all files with `python3 build_batch2.py` (reads `batch1/` and `raw/autohome_specs.json`).

## What changed since batch 1
* **Sourced facts and estimates are now separate.** `model_years.csv` holds only years with a source ({len(my_rows)} rows).
  The {len(estimates)} range-derived years from batch 1 moved to `estimates_model_years.csv` and are labelled ESTIMATE; they are not used anywhere else.
* New evidence base: Autohome picture-gallery pages decoded from GBK, read per exact trim (款型) and model year (年款), 9 series.
* Paint-code candidates from 4 supplier catalogs (one more rejected). All codes are POSSIBLE; none is VERIFIED.

## Priority-model coverage (China market, from sourced records)
| Model | Years with a 款 / source year | Model-year records | ...with >=1 colour | Trims (款型) | Colour records | ...with a POSSIBLE code |
|---|---|---|---|---|---|---|
{rows_md}
| **Total** | | **{tot_my}** | **{tot_my_col}** | **{tot_tr}** | **{tot_col}** | **{tot_lk}** |

* {len(pri_cols)} colour records for the priority models: {gal} are Autohome per-trim photo observations, {oem_c} come from OEM-class sources, the rest from media articles. {stats['distinct_zh_names_priority']} distinct Chinese colour names.
* Han includes EV, DM-i, DM and DM-p; Qin PLUS and Song PLUS include DM-i and EV. Seal's DM-i versions (海豹DM-i = Seal 07 DM-i) are recorded as a separate model.
* **How to read a colour record:** `GALLERY_OBSERVED` = a photo of that exact model year exists in that colour. Each trim shows only some colours (usually 1-5), so the list per model-year is a **lower bound**, not an official colour list.

## Paint codes
* Candidate rows from suppliers: {len(cands)}; distinct code tokens: {len(paint_codes)} (all POSSIBLE; 0 VERIFIED).
* Colour-to-code links: {len(links)} link rows covering {len(linked_colors)} colour records, all POSSIBLE, confidence medium/low only. Models with links: Seal, Dolphin, Yuan PLUS/Atto 3, Seagull.
* **Han, Qin PLUS, Song PLUS, Destroyer 05, e2: no supplier lists them, so no code at all (NOT FOUND).** I deliberately did not copy codes by colour name from other models (e.g. "Time Grey" -> HA4 appears for Atto 3/Dolphin only).
* Rejected: Paint Calculators (`BYD-001..010` sequential IDs with generic names, no source); NonPaints (no per-model codes).
* Nothing found from BYD itself: no OEM label photo, parts-catalog or paint-formula document. Official BYD model pages for the priority models returned no colour lists (see sources S27 note).
* Label location is supported only by retailers (driver door jamb, field 颜色/车身颜色). The one conflicting claim (under the bonnet) is a weak Q&A answer.

## Other fields requested
| Field | Status |
|---|---|
| Exact model name / generation | Done for priority models; generation numbering conflicts recorded in `source_conflicts.csv` |
| Production years | Month/year start and end text from Wikipedia for each priority generation (`production_start_text/end_text`); per-year records only where a source lists the 款 |
| Body style / doors | Doors documented for most priority generations (source per row); one-line body style text; **exterior design descriptions NOT collected** (no source text describes styling beyond body class; Seal 'fastback') |
| Trims | {tot_tr} Chinese 款型 names with Autohome spec IDs and photo counts. English trim names only in notes; `trim_name_en` is empty |
| Colours per model year | Chinese names exact; hex swatches from gallery (display colour, not a paint spec) |
| English colour names | **Not documented officially for China-market colours.** Only market names from OEM sites/brochures (Seal AU, Atto 3 Nepal, India/Europe snippets). Supplier-published English names are stored in `supplier_published_en_names` for the {len(linked_colors)} linked colours and are NOT official |

## Known gaps (full list in `missing_data.csv`, `unmapped_specs.csv`, `excluded_specs.csv`)
* {len(missing)} priority-scope gaps: years with no 款 in the gallery (Dolphin 2022, Qin PLUS 2022, Song PLUS 2022, e2 2022), model-years with no colour photo (Dolphin 2026, Seagull 2026, Han 2027, ...), missing door counts for next-generation rows.
* {len(unmapped)} specs could not be assigned to EV/DM-i (Europe-export and special editions); {len(excluded)} concept-car specs excluded.
* The Autohome gallery is a Chinese-market view only. Export colours (Australia, UK, India, Europe, Nepal, Philippines) exist only as batch-1 snippet-level records.
* No colour record has OEM-document evidence for China-market model years (BYD China site model pages did not expose colours).
* The two list-page years 'Han DM-i 2020' and 'Song Plus DM-i 2020' look wrong (see conflicts).

## Source reliability summary
OEM-class: BYD Australia Seal brochure (read in full, colour names only), BYD China Dahan EV page, BYD India/Nepal/Europe pages (snippets). Everything else is secondary (Autohome, Wikipedia, media) or retailer catalog. See `sources.csv` (reliability column).

## Suggested next steps (needs your decision)
1. Acquire real code evidence: label photos, BYD parts catalog / paint-formula access, or a licensed refinish database. Without it, codes stay POSSIBLE.
2. Fill export-market colours per year from BYD country sites and brochures (AU, UK, EU, Brazil, TH) for the priority models.
3. Continue to the remaining BYD-group models with the same pipeline (Seal 07/DM-i, Seal 05/06, Sealion, Tang, Song L/Pro, Frigate, Denza, Yangwang, Fangchengbao, Linghui).
4. Decide how to treat gallery-observed colours (lower bound) vs an official list when importing.
"""
open(os.path.join(HERE, "REPORT_batch2.md"), "w", encoding="utf-8").write(rep)
print("report written")
