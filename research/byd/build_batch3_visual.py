#!/usr/bin/env python3
"""
BYD research dataset, batch 3: VISUAL CATALOG (priority models).

Inputs : batch-2 CSVs in this folder (models, generations, model_years, trims, factory_colors, ...)
         raw/autohome_specs.json            exact trims + exterior colour facets (batch 2)
         raw/autohome_images.jsonl          image METADATA harvested by raw/harvest_images.py (URLs only)
         raw/autohome_interior_colors.json  interior colour facets per trim
         raw/wikipedia_infoboxes.json       dimensions
         raw/brand_logos_wikipedia.json     logo file URLs + licence metadata
         raw/view_review_sample.json        my visual review of 20 colour galleries
Outputs: image_sources, vehicle_images, exterior_images, interior_images, color_swatches,
         vehicle_color_images, brand_logos, vehicle_dimensions, vehicle_identification,
         image_gaps, image_coverage_by_model  (all .csv) + REPORT_batch3_visual.md + image_stats.json

RULES
  * Only URLs that were extracted from a fetched page are stored. No URL is constructed or guessed.
  * No image files are stored in the repository.  Rights are NOT cleared (see image_sources.csv).
  * An image is linked to a trim only through that trim's own (spec-specific) Autohome gallery.
  * An image is linked to a colour only through the colour-filtered gallery of that exact trim.
  * A view label (front/rear/side...) is a CANDIDATE unless status says MODEL_REVIEWED.
Run:  python3 build_batch3_visual.py [path/to/autohome_images.jsonl]
"""
import csv, json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
RAWD = os.path.join(HERE, "raw")

def rd(n):
    with open(os.path.join(HERE, n), encoding="utf-8") as f:
        return list(csv.DictReader(f))

def w(name, rows, cols):
    with open(os.path.join(HERE, name), "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        wr.writeheader()
        for r in rows:
            wr.writerow(r)

models = {r["model_id"]: r for r in rd("models.csv")}
gens = {r["generation_id"]: r for r in rd("generations.csv")}
gen_by_name = {r["source_row_name"]: r for r in gens.values()}
mys = {r["model_year_id"]: r for r in rd("model_years.csv")}
trims = rd("trims.csv")
trim_by_spec = {t["autohome_spec_id"]: t for t in trims}
colors = rd("factory_colors.csv")
brands = {r["brand_id"]: r for r in rd("brands.csv")}
body_types = {r["body_type_id"]: r["name"] for r in rd("body_types.csv")}
RAW = json.load(open(os.path.join(RAWD, "autohome_specs.json"), encoding="utf-8"))
spec_info = {sp["spec_id"]: (series, sp) for series, b in RAW.items() for sp in b["specs"]}
jl_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAWD, "autohome_images.jsonl")
recs = []
errors = []
with open(jl_path, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        (errors if "error" in r else recs).append(r)
inner_colors = json.load(open(os.path.join(RAWD, "autohome_interior_colors.json"), encoding="utf-8"))
infoboxes = json.load(open(os.path.join(RAWD, "wikipedia_infoboxes.json"), encoding="utf-8"))
logos = json.load(open(os.path.join(RAWD, "brand_logos_wikipedia.json"), encoding="utf-8"))
review = json.load(open(os.path.join(RAWD, "view_review_sample.json"), encoding="utf-8"))

# ------------------------------------------------------------------ image sources / rights
IMG_SRC = [
 dict(image_source_id="IS01", name="Autohome (汽车之家) picture gallery - exact-trim photo lists", site="car.autohome.com.cn / www.autohome.com.cn",
      rights_holder="Autohome and/or its photographers (sampled images show 汽车之家 plates/watermarks)", license_status="NOT CLEARED - all rights presumed reserved",
      redistribution_allowed="NO / UNKNOWN", attribution="Photo: Autohome (汽车之家), page URL stored per image",
      notes="Thumbnail URLs (400x300 / 480x360) extracted from gallery list pages. Full-size URLs exist on each photo page but were not harvested. No files stored. Hot-linking terms unknown."),
 dict(image_source_id="IS02", name="Autohome 官图 (official press images) category", site="car.autohome.com.cn",
      rights_holder="Manufacturer (BYD) press material distributed via Autohome", license_status="NOT CLEARED - press use terms unknown",
      redistribution_allowed="NO / UNKNOWN", attribution="Image: BYD via Autohome 官图, page URL stored per image",
      notes="Category 53 on every trim. Treated as the closest thing to official manufacturer photographs found; manufacturer attribution is by category label only (no per-image credit field was populated)."),
 dict(image_source_id="IS03", name="Wikimedia Commons / Wikipedia file pages - brand logos", site="upload.wikimedia.org",
      rights_holder="BYD / respective brand (trademarks)", license_status="per file: see brand_logos.csv (Public domain-textlogo, PD, Fair use)",
      redistribution_allowed="Per file; trademark rights remain with the brand", attribution="Wikimedia file description page URL stored per logo",
      notes="Denza logo is 'Fair use' on English Wikipedia only: not reusable elsewhere without permission."),
]
w("image_sources.csv", IMG_SRC, ["image_source_id","name","site","rights_holder","license_status","redistribution_allowed","attribution","notes"])

# ------------------------------------------------------------------ images
KIND_ORDER = {"official": 0, "exterior": 1, "cockpit": 2, "seats": 3}
CAT = {"official": "official_press", "exterior": "exterior", "cockpit": "interior_cockpit", "seats": "interior_seats"}
by_key = {}
members = collections.defaultdict(list)    # (spec, colourId) -> [(position, photo_id)]
for r in recs:
    k = r["kind"]
    if k in KIND_ORDER:
        key = (r["spec_id"], r["photo_id"])
        if key not in by_key or KIND_ORDER[k] < KIND_ORDER[by_key[key]["kind"]]:
            prev = by_key.get(key)
            by_key[key] = dict(r, also=set(prev["also"]) | {prev["kind"]} if prev else set())
        else:
            by_key[key]["also"].add(k)
    elif k == "exterior_color":
        members[(r["spec_id"], r["key"])].append((r["position"], r["photo_id"], r))
# colour-gallery photos not present in the plain exterior list -> still an exterior image of that trim
for (spec, cid), lst in members.items():
    for pos, pid, r in lst:
        if (spec, pid) not in by_key:
            by_key[(spec, pid)] = dict(r, kind="exterior", also=set(), position=pos)

ordered = sorted(by_key.values(), key=lambda r: (int(r["spec_id"]), KIND_ORDER[r["kind"]], r["position"]))
img_id = {}
vimg = []
sizes = re.compile(r"/(\d+x\d+)_")
for r in ordered:
    iid = f"IMG{len(vimg)+1:06d}"; img_id[(r["spec_id"], r["photo_id"])] = iid
    t = trim_by_spec.get(r["spec_id"])
    series, sp = spec_info[r["spec_id"]]
    gal_total = None
    cat = CAT[r["kind"]]
    vimg.append(dict(
        image_id=iid, autohome_photo_id=r["photo_id"], autohome_spec_id=r["spec_id"],
        trim_id=t["trim_id"] if t else None, model_id=t["model_id"] if t else None, generation_id=t["generation_id"] if t else None,
        model_year_id=t["model_year_id"] if t else None, year=t["year"] if t else sp["year"][:4],
        image_category=cat, also_listed_as=";".join(sorted(CAT[x] for x in r["also"] if x in CAT)) or None,
        gallery_position=r["position"], thumbnail_url=r["thumb_url"], thumbnail_size=(sizes.search(r["thumb_url"] or "") or [None, None])[1],
        photo_page_url=r["photo_page_url"], caption_zh=r.get("alt"),
        image_source_id="IS02" if cat == "official_press" else "IS01",
        provenance="autohome_official_press_category" if cat == "official_press" else "autohome_gallery_photographer_unspecified",
        year_match_basis=f"listed in the gallery of Autohome spec {r['spec_id']} ({sp['year']} {sp['label']}); the gallery is specific to that exact 款型",
        link_status="LINKED_EXACT_TRIM" if t else "UNLINKED_MODEL_UNRESOLVED",
        license_status="NOT CLEARED"))
w("vehicle_images.csv", vimg, ["image_id","autohome_photo_id","autohome_spec_id","trim_id","model_id","generation_id","model_year_id","year","image_category","also_listed_as","gallery_position","thumbnail_url","thumbnail_size","photo_page_url","caption_zh","image_source_id","provenance","year_match_basis","link_status","license_status"])

# ------------------------------------------------------------------ exterior view labels
STD = {1: "front_left_three_quarter", 2: "front", 3: "front_right_three_quarter", 4: "left_side",
       5: "rear_left_three_quarter", 6: "rear", 7: "rear_right_three_quarter", 8: "right_side"}
rev = {(g["spec_id"], g["autohome_color_id"]): g["result"] for g in review["galleries"]}
gal_of = {}   # (spec, photo) -> (colourId, pos, n)
for (spec, cid), lst in members.items():
    n = len(lst)
    for pos, pid, _ in lst:
        gal_of[(spec, pid)] = (cid, pos, n)
ext = []
n_status = collections.Counter()
for v in vimg:
    if v["image_category"] != "exterior": continue
    g = gal_of.get((v["autohome_spec_id"], v["autohome_photo_id"]))
    label = status = basis = None; cid = pos = n = None
    if g:
        cid, pos, n = g
        res = rev.get((v["autohome_spec_id"], cid))
        if res == "standard" and pos <= 8:
            label, status, basis = STD[pos], "MODEL_REVIEWED", "I viewed this gallery; it follows the standard 7/8-photo sequence (see raw/view_review_sample.json)"
        elif res == "irregular":
            status, basis = "REVIEWED_IRREGULAR_SEQUENCE", "gallery reviewed; order differs from the standard sequence, no view label assigned"
        elif n in (7, 8) and pos <= n:
            label, status, basis = STD[pos], "SEQUENCE_CANDIDATE", "position in a 7/8-photo colour gallery; 16 of 19 reviewed galleries matched the standard order, 3 did not (showroom shoots). Not checked for this image"
        else:
            status, basis = "UNKNOWN", f"colour gallery has {n} photos (not the standard 7/8); order not established"
    else:
        status, basis = "UNKNOWN", "photo is only in the plain exterior list (no colour/sequence context)"
    n_status[status] += 1
    ext.append(dict(image_id=v["image_id"], view_label=label, view_status=status, view_basis=basis,
                    colour_gallery_facet_id=cid, colour_gallery_position=pos, colour_gallery_size=n))
w("exterior_images.csv", ext, ["image_id","view_label","view_status","view_basis","colour_gallery_facet_id","colour_gallery_position","colour_gallery_size"])

# ------------------------------------------------------------------ interior images
AREA = {"interior_cockpit": "dashboard / steering wheel / centre console area (Autohome category 中控方向盘; not subdivided by the source)",
        "interior_seats": "seats / cabin (Autohome category 车厢座椅; not subdivided by the source: front vs rear seats unknown)"}
intr = [dict(image_id=v["image_id"], interior_area=AREA[v["image_category"]], source_category=("10 中控方向盘" if v["image_category"] == "interior_cockpit" else "3 车厢座椅"),
             subview_status="NOT_SUBDIVIDED_BY_SOURCE", interior_colour_name_zh=None, interior_colour_status="NOT_LINKED (interior-colour galleries not harvested in this batch)")
        for v in vimg if v["image_category"] in AREA]
w("interior_images.csv", intr, ["image_id","interior_area","source_category","subview_status","interior_colour_name_zh","interior_colour_status"])

# ------------------------------------------------------------------ swatches + colour images
col_idx = {}
for c in colors:
    if c["evidence_class"] == "GALLERY_OBSERVED":
        col_idx[(c["generation_id"], int(c["model_year_id"] and mys[c["model_year_id"]]["year"]), c["color_name_zh"])] = c["color_id"]
swatches = []; vci = []
ssrc = {"Seal": "S15", "Dolphin": "S16", "Seagull": "S17", "Yuan Plus": "S18", "Han": "S19", "Qin Plus": "S20", "Song Plus": "S21", "Destroyer 05": "S22", "e2": "S23"}
for spec, (series, sp) in spec_info.items():
    t = trim_by_spec.get(spec)
    if not t: continue
    for c in sp["colors"]:
        cid_f = col_idx.get((t["generation_id"], int(t["year"]), c["name_zh"]))
        swatches.append(dict(swatch_id=f"SW{len(swatches)+1:05d}", swatch_kind="exterior", color_id=cid_f, trim_id=t["trim_id"], model_year_id=t["model_year_id"],
                             model_id=t["model_id"], generation_id=t["generation_id"], name_zh=c["name_zh"], name_en=None, autohome_facet_id=c["color_id"],
                             hex=c["hex"], hex_basis="swatch colour supplied by Autohome's colour facet; NOT sampled from a photo and NOT a paint specification",
                             gallery_photos=c["photos"], evidence_url=sp["url"], source_id=ssrc[series], verification_status="SOURCE_SUPPLIED_NOT_VERIFIED"))
        for pos, pid, _ in sorted(members.get((spec, c["color_id"]), [])):
            iid = img_id.get((spec, pid))
            if iid:
                vci.append(dict(image_id=iid, color_id=cid_f, trim_id=t["trim_id"], model_year_id=t["model_year_id"], autohome_facet_id=c["color_id"],
                                color_name_zh=c["name_zh"], gallery_position=pos,
                                link_basis="photo is in the colour-filtered exterior gallery of this exact trim (spec %s)" % spec,
                                colour_status="GALLERY_CLASSIFIED (Autohome's own colour label; swatch-vs-photo agreement not machine-checked)"))
seen_sw = set()
for spec, d in inner_colors.items():
    t = trim_by_spec.get(spec)
    if not t: continue
    for area, lst in d.items():
        for f in lst:
            k = (spec, f["facet_id"])
            if k in seen_sw: continue
            seen_sw.add(k)
            series, sp = spec_info[spec]
            swatches.append(dict(swatch_id=f"SW{len(swatches)+1:05d}", swatch_kind="interior", color_id=None, trim_id=t["trim_id"], model_year_id=t["model_year_id"],
                                 model_id=t["model_id"], generation_id=t["generation_id"], name_zh=f["name_zh"], name_en=None, autohome_facet_id=f["facet_id"],
                                 hex=f["hex"], hex_basis="swatch colour supplied by Autohome's interior-colour facet; not a material specification",
                                 gallery_photos=f["photos"], evidence_url=f"https://car.autohome.com.cn/pic/series-s{spec}/{RAW[series]['series_id']}-{10 if area=='cockpit' else 3}.html",
                                 source_id=ssrc[series], verification_status="SOURCE_SUPPLIED_NOT_VERIFIED"))
w("color_swatches.csv", swatches, ["swatch_id","swatch_kind","color_id","trim_id","model_year_id","model_id","generation_id","name_zh","name_en","autohome_facet_id","hex","hex_basis","gallery_photos","evidence_url","source_id","verification_status"])
w("vehicle_color_images.csv", vci, ["image_id","color_id","trim_id","model_year_id","autohome_facet_id","color_name_zh","gallery_position","link_basis","colour_status"])

# ------------------------------------------------------------------ logos
LOGO_FOR = {"BYD Company, Ltd. - Logo.svg": ("B1", "BYD Group (parent)"), "BYD Auto 2022 logo.svg": ("B2", "BYD"), "Denza Logo.svg": ("B3", "Denza"),
            "Yangwang logo.png": ("B4", "Yangwang"), "Fangchengbao logo.png": ("B5", "Fangchengbao"), "Linghui logo.svg": ("B6", "Linghui")}
logo_rows = []
for L in logos:
    fn = L["file"].replace("File:", "")
    b = LOGO_FOR.get(fn)
    if not b: continue
    logo_rows.append(dict(logo_id=f"LG{len(logo_rows)+1:02d}", brand_id=b[0], brand_name=b[1], file_name=fn, logo_url=L["url"], width_px=L["width"], height_px=L["height"],
                          license_text=L["license"], restrictions=L["restrictions"], creator=L["artist"] or None, description_page_url=L["desc_url"], image_source_id="IS03",
                          usage_note="Logo is a trademark of the brand regardless of file licence." + (" Fair-use on English Wikipedia only: do not reuse without permission." if (L["license"] or "").lower().startswith("fair") else "")))
w("brand_logos.csv", logo_rows, ["logo_id","brand_id","brand_name","file_name","logo_url","width_px","height_px","license_text","restrictions","creator","description_page_url","image_source_id","usage_note"])
logo_by_brand = {r["brand_id"]: r["logo_id"] for r in logo_rows}

# ------------------------------------------------------------------ dimensions
DIM_MAP = {("BYD_Seal", 0): ["Seal"], ("BYD_Dolphin", 0): ["Dolphin"], ("BYD_Seagull", 1): ["Seagull (1st gen)"], ("BYD_Seagull", 2): ["Seagull (2nd gen)"],
           ("BYD_e2", 0): ["e2"], ("BYD_Atto_3", 0): ["Yuan Plus (1st gen)"], ("BYD_Qin", 2): ["Qin Plus DM-i", "Qin Plus EV"],
           ("BYD_Han", 1): ["Han EV", "Han DM-i", "Han DM", "Han DM-p"], ("BYD_Song_Plus", 0): ["Song Plus DM-i", "Song Plus EV"], ("BYD_Destroyer_05", 0): ["Destroyer 05"]}
WIKI_SRC = {"BYD_Seal": "S36", "BYD_Dolphin": "S37", "BYD_Seagull": "S38", "BYD_e2": "S39", "BYD_Atto_3": "S40", "BYD_Qin": "S41", "BYD_Han": "S42", "BYD_Song_Plus": "S44", "BYD_Destroyer_05": "S45"}
dims = []; dim_of_gen = {}
def num(v):
    m = re.fullmatch(r"\s*(\d{3,5})\s*mm\s*", v or "")
    return int(m.group(1)) if m else None
for ib in infoboxes:
    key = (ib["page"], ib["infobox_index"])
    if not ib["length"]: continue
    targets = DIM_MAP.get(key)
    note = "Wikipedia infobox text; ranges/variants/markets are as stated there and are not split by model year."
    if key == ("BYD_Qin", 2): note += " Infobox is for 'Qin Pro / Qin Plus' combined."
    if key == ("BYD_Han", 2): targets = None; note += " Second-generation Han (2026): not mapped to any catalog generation yet."
    if key == ("BYD_Dolphin", 0): note += " Length differs by version (China 2021-25 vs 2025+ vs global)."
    if key == ("BYD_Seagull", 1): note += " Length/height differ by export market."
    if targets is None and key != ("BYD_Han", 2): continue
    for gname in (targets or [None]):
        g = gen_by_name.get(gname) if gname else None
        did = f"DM{len(dims)+1:03d}"
        if g: dim_of_gen[g["generation_id"]] = did
        dims.append(dict(dimension_id=did, generation_id=g["generation_id"] if g else None, generation_name=gname, infobox_name=ib["name"],
                         length_text=ib["length"], width_text=ib["width"], height_text=ib["height"], wheelbase_text=ib["wheelbase"], weight_text=ib["weight"],
                         length_mm=num(ib["length"]), width_mm=num(ib["width"]), height_mm=num(ib["height"]), wheelbase_mm=num(ib["wheelbase"]),
                         source_id=WIKI_SRC[ib["page"]], evidence_url=ib["page_url"], note=note))
w("vehicle_dimensions.csv", dims, ["dimension_id","generation_id","generation_name","infobox_name","length_text","width_text","height_text","wheelbase_text","weight_text","length_mm","width_mm","height_mm","wheelbase_mm","source_id","evidence_url","note"])

# ------------------------------------------------------------------ identification view (one row per trim)
ident = []
for t in trims:
    g = gens[t["generation_id"]]; m = models[t["model_id"]]
    ident.append(dict(trim_id=t["trim_id"], brand_name=brands[m["brand_id"]]["name"], brand_logo_id=logo_by_brand.get(m["brand_id"]),
                      model_key=m["model_key"], model_name_zh=m["name_zh"], generation=g["source_row_name"], year=t["year"], trim_name_zh=t["trim_name_zh"],
                      autohome_spec_id=t["autohome_spec_id"], spec_kind=t["spec_kind"], body_type=body_types.get(g["body_type_id"]), body_style_text=g.get("body_style_text"),
                      doors=g.get("doors") or None, doors_source_id=g.get("doors_source_id") or None, dimension_id=dim_of_gen.get(t["generation_id"]),
                      production_start_text=g.get("production_start_text"), production_end_text=g.get("production_end_text")))
w("vehicle_identification.csv", ident, ["trim_id","brand_name","brand_logo_id","model_key","model_name_zh","generation","year","trim_name_zh","autohome_spec_id","spec_kind","body_type","body_style_text","doors","doors_source_id","dimension_id","production_start_text","production_end_text"])

# ------------------------------------------------------------------ gaps + coverage
imgs_by_trim = collections.defaultdict(collections.Counter)
for v in vimg:
    if v["trim_id"]: imgs_by_trim[v["trim_id"]][v["image_category"]] += 1
col_img_by_trim = collections.defaultdict(set)
for x in vci: col_img_by_trim[x["trim_id"]].add(x["autohome_facet_id"])
gaps = []
def gap(scope, subject, issue, detail=None):
    gaps.append(dict(scope=scope, subject=subject, issue=issue, detail=detail))
for t in trims:
    c = imgs_by_trim.get(t["trim_id"], collections.Counter())
    sub = f"{models[t['model_id']]['model_key']} {t['year']} {t['trim_name_zh']} (trim {t['trim_id']}, spec {t['autohome_spec_id']})"
    if not c.get("exterior"): gap("trim", sub, "no exterior photographs found")
    if not c.get("official_press"): gap("trim", sub, "no official-press (官图) images")
    if not c.get("interior_cockpit"): gap("trim", sub, "no dashboard/cockpit photographs")
    if not c.get("interior_seats"): gap("trim", sub, "no seat/cabin photographs")
    spec = t["autohome_spec_id"]; sp = spec_info[spec][1]
    for col in sp["colors"]:
        if col["color_id"] not in col_img_by_trim.get(t["trim_id"], set()):
            gap("trim_colour", sub, f"colour {col['name_zh']} listed but no colour-filtered gallery photos harvested")
for g in gens.values():
    pr = g["source_row_name"]
    if any(pr == x for k in DIM_MAP.values() for x in k) and g["generation_id"] not in dim_of_gen:
        gap("generation", pr, "no dimensions")
viewable = sum(1 for e in ext if e["view_label"])
for c in colors:
    if c["evidence_class"] != "GALLERY_OBSERVED" and c["model_id"]:
        gap("colour_record", f"{models[c['model_id']]['model_key']} {c['market']} {c['color_name_zh'] or c['color_name_en']}", "colour known from text source only; no exact-trim image linked", c["source_id"])
gap("global", "all exterior images", "left/right/3-4 views are labelled only as candidates except in reviewed galleries", f"MODEL_REVIEWED={n_status['MODEL_REVIEWED']}, SEQUENCE_CANDIDATE={n_status['SEQUENCE_CANDIDATE']}, UNKNOWN={n_status['UNKNOWN']}, IRREGULAR={n_status['REVIEWED_IRREGULAR_SEQUENCE']}")
gap("global", "interior images", "dashboard / steering wheel / centre console / front vs rear seats are not separated by the source", "only two source categories: 中控方向盘 and 车厢座椅")
gap("global", "interior colour options", "interior colour names + swatches recorded per trim, but photos are not linked to interior colours", "interior-colour-filtered galleries not harvested this batch")
gap("global", "full-size images", "only thumbnails (400x300/480x360) harvested", "each photo page exposes a larger version; not harvested")
gap("global", "rights", "no image has a cleared licence", "see image_sources.csv")
w("image_gaps.csv", gaps, ["scope","subject","issue","detail"])

cov = []
by_model = collections.defaultdict(collections.Counter)
for v in vimg:
    if v["model_id"]: by_model[v["model_id"]][v["image_category"]] += 1
for mid, m in models.items():
    c = by_model.get(mid, collections.Counter())
    cov.append(dict(model_id=mid, model_key=m["model_key"], brand_id=m["brand_id"], images_total=sum(c.values()), exterior=c.get("exterior", 0), official_press=c.get("official_press", 0),
                    interior_cockpit=c.get("interior_cockpit", 0), interior_seats=c.get("interior_seats", 0),
                    status="HARVESTED" if c else "NOT_YET_RESEARCHED"))
w("image_coverage_by_model.csv", cov, ["model_id","model_key","brand_id","images_total","exterior","official_press","interior_cockpit","interior_seats","status"])

pri = [r for r in cov if r["status"] == "HARVESTED"]
tot = collections.Counter(v["image_category"] for v in vimg)
stats = dict(images=len(vimg), by_category=dict(tot), linked_exact_trim=sum(1 for v in vimg if v["link_status"] == "LINKED_EXACT_TRIM"),
             unlinked=sum(1 for v in vimg if v["link_status"] != "LINKED_EXACT_TRIM"), trims_with_images=len({v["trim_id"] for v in vimg if v["trim_id"]}), trims=len(trims),
             colour_linked_images=len({x["image_id"] for x in vci}), colour_image_links=len(vci), exterior_swatches=sum(1 for s in swatches if s["swatch_kind"] == "exterior"),
             interior_swatches=sum(1 for s in swatches if s["swatch_kind"] == "interior"), view_status=dict(n_status), views_labelled=viewable,
             logos=len(logo_rows), dimension_rows=len(dims), gaps=len(gaps), harvest_errors=len(errors), models_harvested=len(pri), models_total=len(cov),
             official_press_images=tot.get("official_press", 0))
json.dump(stats, open(os.path.join(HERE, "image_stats.json"), "w"), indent=1)
print(json.dumps(stats, indent=1))
