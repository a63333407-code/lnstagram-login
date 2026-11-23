#!/usr/bin/env python3
"""
BYD research dataset, batch 3: VISUAL CATALOG (priority models).  Reproducible from files committed in raw/.

Inputs (raw/): autohome_specs.json, autohome_images.jsonl[.gz] (+ retry_records_N.jsonl, retry_log_N.jsonl),
               expected_counts.json, autohome_interior_colors.json, harvest_run.json, view_review_sample.json,
               wikipedia_infoboxes.json, brand_logos_wikipedia.json  + batch-1/2 CSVs (read only, never modified).
Output: written to a STAGING directory first, validated (validate_batch3.py), and only then moved next to the batch-2 CSVs.
        If validation fails nothing is published.

RULES
  * Only URLs extracted from fetched pages are stored; nothing is constructed or guessed.
  * No image files are stored.  Rights are NOT cleared.
  * A redirect to a trim landing page (no photos) is never counted as a harvested list.
  * View labels are CANDIDATE unless I individually inspected that very image (MODEL_REVIEWED_NOT_EDITOR_VERIFIED);
    nothing is VERIFIED (no human editor has approved any label).
Run:  python3 build_batch3_visual.py
"""
import csv, gzip, json, os, re, shutil, subprocess, sys, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RAWD = os.path.join(HERE, "raw")
STAGE = os.path.join(HERE, ".stage_batch3")
if os.path.exists(STAGE): shutil.rmtree(STAGE)
os.makedirs(STAGE)

def rd(n):
    with open(os.path.join(HERE, n), encoding="utf-8") as f:
        return list(csv.DictReader(f))
def w(name, rows, cols):
    with open(os.path.join(STAGE, name), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); wr.writeheader()
        for r in rows: wr.writerow(r)
def jl(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip(): yield json.loads(line)

models = {r["model_id"]: r for r in rd("models.csv")}
gens = {r["generation_id"]: r for r in rd("generations.csv")}
gen_by_name = {r["source_row_name"]: r for r in gens.values()}
mys = {r["model_year_id"]: r for r in rd("model_years.csv")}
trims = rd("trims.csv"); trim_by_spec = {t["autohome_spec_id"]: t for t in trims}
colors = rd("factory_colors.csv"); brands = {r["brand_id"]: r for r in rd("brands.csv")}
body_types = {r["body_type_id"]: r["name"] for r in rd("body_types.csv")}
RAW = json.load(open(os.path.join(RAWD, "autohome_specs.json"), encoding="utf-8"))
spec_info = {sp["spec_id"]: (series, sp, b["series_id"]) for series, b in RAW.items() for sp in b["specs"] if not re.search(r"概念|Concept|ocean-X", sp["label"], re.I)}
EXP = json.load(open(os.path.join(RAWD, "expected_counts.json"), encoding="utf-8"))
inner_colors = json.load(open(os.path.join(RAWD, "autohome_interior_colors.json"), encoding="utf-8"))
infoboxes = json.load(open(os.path.join(RAWD, "wikipedia_infoboxes.json"), encoding="utf-8"))
logos = json.load(open(os.path.join(RAWD, "brand_logos_wikipedia.json"), encoding="utf-8"))
review = json.load(open(os.path.join(RAWD, "view_review_sample.json"), encoding="utf-8"))
RUN = json.load(open(os.path.join(RAWD, "harvest_run.json"), encoding="utf-8"))

# ------------------------------------------------------------------ load harvest records (+ retry supersession)
main_path = os.path.join(RAWD, "autohome_images.jsonl.gz")
if not os.path.exists(main_path): main_path = os.path.join(RAWD, "autohome_images.jsonl")
main_recs, main_errors = [], []
for r in jl(main_path): (main_errors if "error" in r else main_recs).append(r)
retry_files = sorted(f for f in os.listdir(RAWD) if re.fullmatch(r"retry_records_\d+\.jsonl", f))
retry_log_files = sorted(f for f in os.listdir(RAWD) if re.fullmatch(r"retry_log_\d+\.jsonl", f))
superseded = {}     # (spec,kind,key) -> result of the LAST retry round
retry_recs = collections.defaultdict(list)
for f in retry_files:
    cur = None
    for r in jl(os.path.join(RAWD, f)):
        if r.get("_supersede"):
            cur = (r["spec_id"], r["kind"], r["key"]); superseded[cur] = r["retry_result"]; retry_recs[cur] = []
        else: retry_recs[cur].append(r)
recs = [r for r in main_recs if (r["spec_id"], r["kind"], r["key"]) not in superseded]
for lst in retry_recs.values(): recs.extend(lst)
retry_log = [r for f in retry_log_files for r in jl(os.path.join(RAWD, f))]

# ------------------------------------------------------------------ image sources / rights
IMG_SRC = [
 dict(image_source_id="IS01", name="Autohome (汽车之家) picture gallery - exact-trim photo lists", site="car.autohome.com.cn / www.autohome.com.cn",
      rights_holder="Autohome and/or its photographers (sampled images show 汽车之家 plates/watermarks)", license_status="NOT CLEARED - all rights presumed reserved",
      redistribution_allowed="NO / UNKNOWN", attribution="Photo: Autohome (汽车之家)",
      notes="Thumbnail URLs (400x300 / 480x360) extracted from gallery list pages. Full-size URLs exist on each photo page but were not harvested. No files stored. Hot-linking terms unknown."),
 dict(image_source_id="IS02", name="Autohome 官图 (official press images) category", site="car.autohome.com.cn",
      rights_holder="Manufacturer (BYD) press material distributed via Autohome", license_status="NOT CLEARED - press use terms unknown",
      redistribution_allowed="NO / UNKNOWN", attribution="Image: BYD via Autohome 官图",
      notes="Category 53 on each trim. The closest thing to official manufacturer photographs found; manufacturer attribution is by category label only (no per-image credit field)."),
 dict(image_source_id="IS03", name="Wikimedia Commons / Wikipedia file pages - brand logos", site="upload.wikimedia.org",
      rights_holder="BYD / respective brand (trademarks)", license_status="per file: see brand_logos.csv", redistribution_allowed="Per file; trademark rights remain with the brand",
      attribution="Wikimedia file description page", notes="Denza logo is 'Fair use' on English Wikipedia only."),
]
w("image_sources.csv", IMG_SRC, ["image_source_id","name","site","rights_holder","license_status","redistribution_allowed","attribution","notes"])
SRC_ATTR = {r["image_source_id"]: r for r in IMG_SRC}

# ------------------------------------------------------------------ images (unique per spec + photo id)
KIND_ORDER = {"official": 0, "exterior": 1, "cockpit": 2, "seats": 3}
CAT = {"official": "official_press", "exterior": "exterior", "cockpit": "interior_cockpit", "seats": "interior_seats"}
by_key = {}; members = collections.defaultdict(list)
for r in recs:
    k = r["kind"]
    if k in KIND_ORDER:
        key = (r["spec_id"], r["photo_id"])
        if key not in by_key or KIND_ORDER[k] < KIND_ORDER[by_key[key]["kind"]]:
            prev = by_key.get(key); by_key[key] = dict(r, also=(set(prev["also"]) | {prev["kind"]}) if prev else set())
        else: by_key[key]["also"].add(k)
    elif k == "exterior_color": members[(r["spec_id"], r["key"])].append((r["position"], r["photo_id"], r))
for (spec, cid), lst in members.items():
    for pos, pid, r in lst:
        if (spec, pid) not in by_key: by_key[(spec, pid)] = dict(r, kind="exterior", also=set(), position=pos)
gal_of = {}
for (spec, cid), lst in members.items():
    for pos, pid, _ in lst: gal_of[(spec, pid)] = (cid, pos, len(lst))
colour_name = {}
for spec, (series, sp, sid) in spec_info.items():
    for c in sp["colors"]: colour_name[(spec, c["color_id"])] = c["name_zh"]
col_idx = {(c["generation_id"], int(mys[c["model_year_id"]]["year"]), c["color_name_zh"]): c["color_id"] for c in colors if c["evidence_class"] == "GALLERY_OBSERVED"}

# view labels --------------------------------------------------------------
STD = {1: "front_left_three_quarter", 2: "front", 3: "front_right_three_quarter", 4: "left_side", 5: "rear_left_three_quarter", 6: "rear", 7: "rear_right_three_quarter", 8: "right_side"}
rev = {(g["spec_id"], g["autohome_color_id"]): g["result"] for g in review["galleries"]}
INSPECTED = {}   # (spec, colour facet, position) -> label : images I examined individually at >=400x300
for pos in range(1, 9): INSPECTED[("66988", "9685", pos)] = STD[pos]
for spec, cid in [("67380", "10515"), ("69005", "10387"), ("52453", "7686"), ("41399", "4936"), ("61095", "10387"), ("49506", "7686"), ("55772", "7686")]:
    INSPECTED[(spec, cid, 4)] = "left_side"
COLLECT = RUN["collection_window_utc"]
ordered = sorted(by_key.values(), key=lambda r: (int(r["spec_id"]), KIND_ORDER[r["kind"]], r["position"]))
img_id = {}; vimg = []; ext = []; n_view = collections.Counter()
sizes = re.compile(r"/(\d+x\d+)_")
for r in ordered:
    iid = f"IMG{len(vimg)+1:06d}"; img_id[(r["spec_id"], r["photo_id"])] = iid
    t = trim_by_spec.get(r["spec_id"]); series, sp, sid = spec_info[r["spec_id"]]
    cat = CAT[r["kind"]]
    g = gal_of.get((r["spec_id"], r["photo_id"]))
    cid_f = col_idx.get((t["generation_id"], int(t["year"]), colour_name.get((r["spec_id"], g[0])))) if (t and g) else None
    label = status = None
    if cat == "exterior":
        if g:
            cid, pos, n = g; res = rev.get((r["spec_id"], cid))
            if (r["spec_id"], cid, pos) in INSPECTED:
                label, status = INSPECTED[(r["spec_id"], cid, pos)], "MODEL_REVIEWED_NOT_EDITOR_VERIFIED"
            elif res == "irregular": status = "REVIEWED_GALLERY_IRREGULAR_NO_LABEL"
            elif n in (7, 8) and pos <= n: label, status = STD[pos], "CANDIDATE"
            else: status = "UNKNOWN_NON_STANDARD_GALLERY_SIZE"
        else: status = "UNKNOWN_NO_SEQUENCE_CONTEXT"
        n_view[status] += 1
        ext.append(dict(image_id=iid, view_label=label, view_verification_status=status,
                        view_basis=("individually inspected image" if status.startswith("MODEL_REVIEWED") else
                                    "position in a 7/8-photo colour-filtered gallery that follows Autohome's usual order; 16 of 19 sampled galleries matched, 3 showroom galleries did not; THIS image not individually inspected" if status == "CANDIDATE" else
                                    "gallery sampled and found to deviate from the usual order" if status.startswith("REVIEWED") else "no basis for a view label"),
                        colour_gallery_facet_id=g[0] if g else None, colour_gallery_position=g[1] if g else None, colour_gallery_size=g[2] if g else None))
    vimg.append(dict(
        image_id=iid, image_url=r["thumb_url"], image_url_kind="thumbnail (%s)" % ((sizes.search(r["thumb_url"] or "") or [None, "size unknown"])[1]),
        source_page_url=r["photo_page_url"], gallery_list_url=r.get("list_url"), autohome_photo_id=r["photo_id"], autohome_spec_id=r["spec_id"],
        vehicle_id=t["model_id"] if t else None, generation_id=t["generation_id"] if t else None, model_year=t["year"] if t else sp["year"][:4],
        model_year_id=t["model_year_id"] if t else None, trim_id=t["trim_id"] if t else None, image_category=cat,
        also_listed_as=";".join(sorted(CAT[x] for x in r["also"] if x in CAT)) or None, gallery_position=r["position"], caption_zh=r.get("alt"),
        view_label=label, view_verification_status=status,
        color_id=cid_f, color_name_zh=colour_name.get((r["spec_id"], g[0])) if g else None, color_facet_id=g[0] if g else None,
        color_association_basis="photo is in the colour-filtered exterior gallery of this exact trim (Autohome's own colour label)" if g else None,
        image_source_id="IS02" if cat == "official_press" else "IS01", attribution=SRC_ATTR["IS02" if cat == "official_press" else "IS01"]["attribution"],
        license_status="NOT CLEARED", link_status="LINKED_EXACT_TRIM" if t else "UNLINKED_MODEL_UNRESOLVED",
        year_match_basis=f"listed in the gallery of Autohome spec {r['spec_id']} ({sp['year']} {sp['label']}); gallery is specific to that exact 款型",
        collected_at=r.get("collected_utc") or f"{COLLECT['start']}/{COLLECT['end']} (run-level window; per-image time not recorded)"))
VCOLS = ["image_id","image_url","image_url_kind","source_page_url","gallery_list_url","autohome_photo_id","autohome_spec_id","vehicle_id","generation_id","model_year","model_year_id","trim_id","image_category","also_listed_as","gallery_position","caption_zh","view_label","view_verification_status","color_id","color_name_zh","color_facet_id","color_association_basis","image_source_id","attribution","license_status","link_status","year_match_basis","collected_at"]
w("vehicle_images.csv", vimg, VCOLS)
w("exterior_images.csv", ext, ["image_id","view_label","view_verification_status","view_basis","colour_gallery_facet_id","colour_gallery_position","colour_gallery_size"])
AREA = {"interior_cockpit": "dashboard / steering wheel / centre console area (Autohome category 中控方向盘; not subdivided by the source)",
        "interior_seats": "seats / cabin (Autohome category 车厢座椅; not subdivided: front vs rear seats unknown)"}
w("interior_images.csv", [dict(image_id=v["image_id"], interior_area=AREA["interior_cockpit"], source_category="10 中控方向盘", subview_status="NOT_SUBDIVIDED_BY_SOURCE") for v in vimg if v["image_category"] == "interior_cockpit"],
  ["image_id","interior_area","source_category","subview_status"])
w("seat_images.csv", [dict(image_id=v["image_id"], interior_area=AREA["interior_seats"], source_category="3 车厢座椅", subview_status="NOT_SUBDIVIDED_BY_SOURCE") for v in vimg if v["image_category"] == "interior_seats"],
  ["image_id","interior_area","source_category","subview_status"])
w("official_press_images.csv", [dict(image_id=v["image_id"], source_category="53 官图", provenance="manufacturer press material distributed via Autohome", content_type_status="NOT_CLASSIFIED (exterior/interior mixed)") for v in vimg if v["image_category"] == "official_press"],
  ["image_id","source_category","provenance","content_type_status"])

# ------------------------------------------------------------------ swatches + colour images
ssrc = {"Seal": "S15", "Dolphin": "S16", "Seagull": "S17", "Yuan Plus": "S18", "Han": "S19", "Qin Plus": "S20", "Song Plus": "S21", "Destroyer 05": "S22", "e2": "S23"}
swatches = []; vci = []
for spec, (series, sp, sid) in spec_info.items():
    t = trim_by_spec.get(spec)
    if not t: continue
    for c in sp["colors"]:
        cid_f = col_idx.get((t["generation_id"], int(t["year"]), c["name_zh"]))
        swatches.append(dict(swatch_id=f"SW{len(swatches)+1:05d}", swatch_kind="exterior", color_id=cid_f, trim_id=t["trim_id"], model_year_id=t["model_year_id"], model_id=t["model_id"], generation_id=t["generation_id"],
                             name_zh=c["name_zh"], name_en=None, autohome_facet_id=c["color_id"], hex=c["hex"],
                             hex_basis="swatch colour supplied by Autohome's colour facet; NOT sampled from a photo and NOT a paint specification",
                             gallery_photos=c["photos"], evidence_url=sp["url"], source_id=ssrc[series], verification_status="SOURCE_SUPPLIED_NOT_VERIFIED"))
for v in vimg:
    if v["color_facet_id"] and v["trim_id"]:
        vci.append(dict(image_id=v["image_id"], color_id=v["color_id"], trim_id=v["trim_id"], model_year_id=v["model_year_id"], autohome_facet_id=v["color_facet_id"],
                        color_name_zh=v["color_name_zh"], gallery_position=v["gallery_position"], link_basis=v["color_association_basis"],
                        colour_status="GALLERY_CLASSIFIED (Autohome's own colour label; swatch-vs-photo agreement not machine-checked)"))
seen_sw = set()
for spec, d in inner_colors.items():
    t = trim_by_spec.get(spec)
    if not t or spec not in spec_info: continue
    series, sp, sid = spec_info[spec]
    for area, lst in d.items():
        for f in lst:
            if (spec, f["facet_id"]) in seen_sw: continue
            seen_sw.add((spec, f["facet_id"]))
            swatches.append(dict(swatch_id=f"SW{len(swatches)+1:05d}", swatch_kind="interior", color_id=None, trim_id=t["trim_id"], model_year_id=t["model_year_id"], model_id=t["model_id"], generation_id=t["generation_id"],
                                 name_zh=f["name_zh"], name_en=None, autohome_facet_id=f["facet_id"], hex=f["hex"], hex_basis="swatch colour supplied by Autohome's interior-colour facet; not a material specification",
                                 gallery_photos=f["photos"], evidence_url=f"https://car.autohome.com.cn/pic/series-s{spec}/{sid}-{10 if area == 'cockpit' else 3}.html", source_id=ssrc[series], verification_status="SOURCE_SUPPLIED_NOT_VERIFIED"))
w("color_swatches.csv", swatches, ["swatch_id","swatch_kind","color_id","trim_id","model_year_id","model_id","generation_id","name_zh","name_en","autohome_facet_id","hex","hex_basis","gallery_photos","evidence_url","source_id","verification_status"])
w("vehicle_color_images.csv", vci, ["image_id","color_id","trim_id","model_year_id","autohome_facet_id","color_name_zh","gallery_position","link_basis","colour_status"])

# ------------------------------------------------------------------ logos / dimensions / identification
LOGO_FOR = {"BYD Company, Ltd. - Logo.svg": ("B1", "BYD Group (parent)"), "BYD Auto 2022 logo.svg": ("B2", "BYD"), "Denza Logo.svg": ("B3", "Denza"),
            "Yangwang logo.png": ("B4", "Yangwang"), "Fangchengbao logo.png": ("B5", "Fangchengbao"), "Linghui logo.svg": ("B6", "Linghui")}
logo_rows = []
for L in logos:
    b = LOGO_FOR.get(L["file"].replace("File:", ""))
    if not b: continue
    logo_rows.append(dict(logo_id=f"LG{len(logo_rows)+1:02d}", brand_id=b[0], brand_name=b[1], file_name=L["file"].replace("File:", ""), logo_url=L["url"], source_page_url=L["desc_url"],
                          width_px=L["width"], height_px=L["height"], license_text=L["license"], restrictions=L["restrictions"], creator=L["artist"] or None,
                          image_source_id="IS03", collected_at=RUN["logo_collection_utc"],
                          usage_note="Logo is a trademark of the brand regardless of file licence." + (" Fair-use on English Wikipedia only: do not reuse without permission." if (L["license"] or "").lower().startswith("fair") else "")))
w("brand_logos.csv", logo_rows, ["logo_id","brand_id","brand_name","file_name","logo_url","source_page_url","width_px","height_px","license_text","restrictions","creator","image_source_id","collected_at","usage_note"])
logo_by_brand = {r["brand_id"]: r["logo_id"] for r in logo_rows}
DIM_MAP = {("BYD_Seal", 0): ["Seal"], ("BYD_Dolphin", 0): ["Dolphin"], ("BYD_Seagull", 1): ["Seagull (1st gen)"], ("BYD_Seagull", 2): ["Seagull (2nd gen)"], ("BYD_e2", 0): ["e2"],
           ("BYD_Atto_3", 0): ["Yuan Plus (1st gen)"], ("BYD_Qin", 2): ["Qin Plus DM-i", "Qin Plus EV"], ("BYD_Han", 1): ["Han EV", "Han DM-i", "Han DM", "Han DM-p"],
           ("BYD_Song_Plus", 0): ["Song Plus DM-i", "Song Plus EV"], ("BYD_Destroyer_05", 0): ["Destroyer 05"]}
WIKI_SRC = {"BYD_Seal": "S36", "BYD_Dolphin": "S37", "BYD_Seagull": "S38", "BYD_e2": "S39", "BYD_Atto_3": "S40", "BYD_Qin": "S41", "BYD_Han": "S42", "BYD_Song_Plus": "S44", "BYD_Destroyer_05": "S45"}
dims = []; dim_of_gen = {}
num = lambda v: int(re.fullmatch(r"\s*(\d{3,5})\s*mm\s*", v or "").group(1)) if re.fullmatch(r"\s*(\d{3,5})\s*mm\s*", v or "") else None
for ib in infoboxes:
    key = (ib["page"], ib["infobox_index"])
    if not ib["length"]: continue
    targets = DIM_MAP.get(key); note = "Wikipedia infobox text; ranges/variants/markets are as stated there and are not split by model year."
    if key == ("BYD_Qin", 2): note += " Infobox is for 'Qin Pro / Qin Plus' combined."
    if key == ("BYD_Han", 2): targets = [None]; note += " Second-generation Han (2026): not mapped to any catalog generation yet."
    if key == ("BYD_Dolphin", 0): note += " Length differs by version."
    if key == ("BYD_Seagull", 1): note += " Length/height differ by export market."
    if targets is None: continue
    for gname in targets:
        g = gen_by_name.get(gname) if gname else None; did = f"DM{len(dims)+1:03d}"
        if g: dim_of_gen[g["generation_id"]] = did
        dims.append(dict(dimension_id=did, generation_id=g["generation_id"] if g else None, generation_name=gname, infobox_name=ib["name"], length_text=ib["length"], width_text=ib["width"], height_text=ib["height"],
                         wheelbase_text=ib["wheelbase"], weight_text=ib["weight"], length_mm=num(ib["length"]), width_mm=num(ib["width"]), height_mm=num(ib["height"]), wheelbase_mm=num(ib["wheelbase"]),
                         source_id=WIKI_SRC[ib["page"]], evidence_url=ib["page_url"], note=note))
w("vehicle_dimensions.csv", dims, ["dimension_id","generation_id","generation_name","infobox_name","length_text","width_text","height_text","wheelbase_text","weight_text","length_mm","width_mm","height_mm","wheelbase_mm","source_id","evidence_url","note"])
ident = []
for t in trims:
    g = gens[t["generation_id"]]; m = models[t["model_id"]]
    ident.append(dict(trim_id=t["trim_id"], brand_name=brands[m["brand_id"]]["name"], brand_logo_id=logo_by_brand.get(m["brand_id"]), model_key=m["model_key"], model_name_zh=m["name_zh"], generation=g["source_row_name"],
                      year=t["year"], trim_name_zh=t["trim_name_zh"], autohome_spec_id=t["autohome_spec_id"], spec_kind=t["spec_kind"], body_type=body_types.get(g["body_type_id"]), body_style_text=g.get("body_style_text"),
                      doors=g.get("doors") or None, doors_source_id=g.get("doors_source_id") or None, dimension_id=dim_of_gen.get(t["generation_id"]),
                      production_start_text=g.get("production_start_text"), production_end_text=g.get("production_end_text")))
w("vehicle_identification.csv", ident, ["trim_id","brand_name","brand_logo_id","model_key","model_name_zh","generation","year","trim_name_zh","autohome_spec_id","spec_kind","body_type","body_style_text","doors","doors_source_id","dimension_id","production_start_text","production_end_text"])

# ------------------------------------------------------------------ per-trim final status
have = collections.defaultdict(set)
for r in recs:
    if "error" not in r: have[(r["spec_id"], r["kind"], r["key"])].add(r["photo_id"])
CATKEY = {"exterior": "1", "official": "53", "cockpit": "10", "seats": "3"}
last_outcome = {}
for r in retry_log: last_outcome[r["url"]] = r
status_rows = []; missing = []
STAT = collections.Counter()
for spec, (series, sp, sid) in sorted(spec_info.items(), key=lambda kv: int(kv[0])):
    t = trim_by_spec.get(spec); e = EXP.get(spec, {})
    issues = []; exp_tot = got_tot = 0; per = {}
    if "error" in e or not e: issues.append("landing page (expected counts) not retrieved")
    for kind, key in CATKEY.items():
        exp = e.get(kind); got = len(have.get((spec, kind, key), ()))
        per[kind] = (exp, got); got_tot += got
        if exp is None: issues.append(f"{kind}: expected count not parsed")
        else:
            exp_tot += exp
            if exp != got:
                red = superseded.get((spec, kind, key))
                issues.append(f"{kind}: expected {exp}, harvested {got}" + (f" (last retry: {red})" if red else ""))
                missing.append(dict(scope="trim_category", subject=f"spec {spec} {sp['year']} {sp['label']}", category=kind, expected=exp, harvested=got, reason=(f"retry result: {superseded.get((spec, kind, key))}" if (spec, kind, key) in superseded else "count mismatch, not retried"), trim_id=t["trim_id"] if t else None))
            elif exp == 0:
                missing.append(dict(scope="trim_category", subject=f"spec {spec} {sp['year']} {sp['label']}", category=kind, expected=0, harvested=0, reason="Autohome states 0 photos in this category (empty confirmed by stated count)", trim_id=t["trim_id"] if t else None))
    cg_exp = cg_got = 0
    for c in sp["colors"]:
        got = len(have.get((spec, "exterior_color", c["color_id"]), ())); cg_exp += c["photos"]; cg_got += got
        if got != c["photos"]:
            issues.append(f"colour gallery {c['name_zh']}: facet says {c['photos']}, harvested {got}")
            missing.append(dict(scope="trim_colour_gallery", subject=f"spec {spec} {sp['year']} {sp['label']}", category=f"colour {c['name_zh']} ({c['color_id']})", expected=c["photos"], harvested=got, reason=f"retry result: {superseded.get((spec, 'exterior_color', c['color_id']), 'not retried')}", trim_id=t["trim_id"] if t else None))
    if "error" in e or not e: st = "FAILED_RETRY_REQUIRED"
    elif not issues and exp_tot == 0 and got_tot == 0: st = "NO_IMAGES_AVAILABLE"
    elif not issues: st = "COMPLETED"
    elif got_tot == 0: st = "FAILED_RETRY_REQUIRED"
    else: st = "PARTIAL"
    STAT[st] += 1
    status_rows.append(dict(autohome_spec_id=spec, trim_id=t["trim_id"] if t else None, series=series, model_year=sp["year"][:4], trim_name_zh=sp["label"], status=st,
                            expected_exterior=per["exterior"][0], harvested_exterior=per["exterior"][1], expected_official=per["official"][0], harvested_official=per["official"][1],
                            expected_cockpit=per["cockpit"][0], harvested_cockpit=per["cockpit"][1], expected_seats=per["seats"][0], harvested_seats=per["seats"][1],
                            colour_galleries=len(sp["colors"]), colour_gallery_photos_expected=cg_exp, colour_gallery_photos_harvested=cg_got,
                            issues=" | ".join(issues) or None, model_link=("LINKED" if t else "UNLINKED_MODEL_UNRESOLVED"),
                            interior_colour_galleries="not harvested (facets only)"))
w("trim_harvest_status.csv", status_rows, ["autohome_spec_id","trim_id","series","model_year","trim_name_zh","status","expected_exterior","harvested_exterior","expected_official","harvested_official","expected_cockpit","harvested_cockpit","expected_seats","harvested_seats","colour_galleries","colour_gallery_photos_expected","colour_gallery_photos_harvested","issues","model_link","interior_colour_galleries"])
# standing gaps
for c in colors:
    if c["evidence_class"] != "GALLERY_OBSERVED" and c["model_id"]:
        missing.append(dict(scope="colour_record", subject=f"{models[c['model_id']]['model_key']} {c['market']} {c['color_name_zh'] or c['color_name_en']}", category="colour image", expected=None, harvested=0, reason="colour known from a text source only; no exact-trim image linked (no generic substitute used)", trim_id=None))
for lbl, why in [("exterior view labels", "front/rear/left/right/3-4 labels are CANDIDATE only except individually inspected images"),
                 ("interior sub-views", "source does not separate dashboard / steering wheel / centre console / front vs rear seats"),
                 ("interior colour galleries", "interior colour names + swatches recorded per trim; photos not linked to interior colours"),
                 ("full-size images", "only thumbnails harvested; larger versions exist on each photo page"),
                 ("licensing", "no image has a cleared licence")]:
    missing.append(dict(scope="global", subject="all images", category=lbl, expected=None, harvested=None, reason=why, trim_id=None))
w("missing_images_report.csv", missing, ["scope","subject","category","expected","harvested","reason","trim_id"])

# failed requests report
fails = []
for e in main_errors:
    fin = superseded.get((e["spec_id"], e["kind"], e["key"]))
    fails.append(dict(source="main harvest", utc=None, spec_id=e["spec_id"], list_kind=e["kind"], url=e["url"], http=None, outcome="fetch_failed (page <3000 bytes or curl error; HTTP code not recorded in main run)",
                      final_disposition=(f"re-fetched in retry pass: {fin}" if fin else "list not re-fetched (counts matched the source's own totals, so nothing was missing)")))
for r in retry_log:
    if r["outcome"] != "ok":
        fails.append(dict(source="retry pass", utc=r["utc"], spec_id=None, list_kind=None, url=r["url"], http=r["http"], outcome=r["outcome"], final_disposition=f"attempt {r['attempt']} of 3"))
w("failed_requests_report.csv", fails, ["source","utc","spec_id","list_kind","url","http","outcome","final_disposition"])

# ------------------------------------------------------------------ coverage
by_model = collections.defaultdict(collections.Counter)
for v in vimg:
    if v["vehicle_id"]: by_model[v["vehicle_id"]][v["image_category"]] += 1
cov = []
for mid, m in models.items():
    c = by_model.get(mid, collections.Counter())
    cov.append(dict(model_id=mid, model_key=m["model_key"], brand_id=m["brand_id"], images_total=sum(c.values()), exterior=c.get("exterior", 0), official_press=c.get("official_press", 0),
                    interior_cockpit=c.get("interior_cockpit", 0), interior_seats=c.get("interior_seats", 0), status="HARVESTED" if c else "NOT_YET_RESEARCHED"))
w("image_coverage_by_model.csv", cov, ["model_id","model_key","brand_id","images_total","exterior","official_press","interior_cockpit","interior_seats","status"])
tot = collections.Counter(v["image_category"] for v in vimg)
stats = dict(trim_status=dict(STAT), specs=len(spec_info), images=len(vimg), by_category=dict(tot), linked_exact_trim=sum(1 for v in vimg if v["link_status"] == "LINKED_EXACT_TRIM"),
             unlinked=sum(1 for v in vimg if v["link_status"] != "LINKED_EXACT_TRIM"), colour_associated_images=len(vci), exterior_swatches=sum(1 for s in swatches if s["swatch_kind"] == "exterior"),
             interior_swatches=sum(1 for s in swatches if s["swatch_kind"] == "interior"), view_status=dict(n_view), logos=len(logo_rows), dimension_rows=len(dims),
             main_run_errors=len(main_errors), retry_requests=len(retry_log), retry_failed_requests=sum(1 for r in retry_log if r["outcome"] == "failed"), missing_rows=len(missing),
             models_harvested=sum(1 for c in cov if c["status"] == "HARVESTED"), models_total=len(cov), collection_window_utc=COLLECT)
json.dump(stats, open(os.path.join(STAGE, "image_stats.json"), "w"), indent=1)

# ------------------------------------------------------------------ validate, then publish
sys.path.insert(0, HERE)
import validate_batch3
ok = validate_batch3.run(STAGE, HERE, stats)
if not ok:
    print("VALIDATION FAILED - nothing published. See", os.path.join(STAGE, "validation_report_batch3.md")); sys.exit(1)
NEW = [f for f in os.listdir(STAGE)]
for f in NEW: shutil.move(os.path.join(STAGE, f), os.path.join(HERE, f))
os.rmdir(STAGE)
print(json.dumps(stats, indent=1))
