#!/usr/bin/env python3
"""
Batch 4 reports: complete model catalog, brand/model coverage, missing-data report, data-integrity validation of the merged catalog.
Run AFTER build_batch4.py (data) and build_batch4_visual.py (images).  Reads only; writes new files in batch4/ and catalog_union/.
"""
import csv, gzip, json, os, re, collections, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); U = os.path.join(HERE, "catalog_union"); B4 = os.path.join(HERE, "batch4")
def rdp(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f: return list(csv.DictReader(f))
def w(path, rows, cols):
    with open(path, "w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); wr.writeheader(); wr.writerows(rows)

models = rdp(os.path.join(U, "models_all.csv")); gens = rdp(os.path.join(U, "generations_all.csv")); mys = rdp(os.path.join(U, "model_years_all.csv"))
trims = rdp(os.path.join(U, "trims_all.csv")); colors = rdp(os.path.join(U, "factory_colors_all.csv")); links = rdp(os.path.join(U, "color_paint_code_links_all.csv"))
cands = rdp(os.path.join(U, "paint_code_candidates_all.csv")); pcs = rdp(os.path.join(U, "paint_codes_all.csv")); ver = rdp(os.path.join(U, "verification_records_all.csv"))
srcs = rdp(os.path.join(U, "sources_all.csv")); brands = {b["brand_id"]: b["name"] for b in rdp(os.path.join(U, "brands_all.csv"))}
img3 = rdp(os.path.join(HERE, "vehicle_images.csv"))
p4 = os.path.join(B4, "images", "vehicle_images_b4.csv.gz"); img4 = rdp(p4) if os.path.exists(p4) else []
dims = rdp(os.path.join(HERE, "vehicle_dimensions.csv")) + rdp(os.path.join(B4, "vehicle_dimensions_b4.csv"))
facts = rdp(os.path.join(B4, "generation_facts_b4.csv")); inv = rdp(os.path.join(B4, "series_inventory_b4.csv")); nomap = {r["model_id"]: r for r in rdp(os.path.join(B4, "models_without_autohome_mapping_b4.csv"))}
trim_status = rdp(os.path.join(B4, "images", "trim_harvest_status_b4.csv")) if os.path.exists(os.path.join(B4, "images", "trim_harvest_status_b4.csv")) else []
gen_by_model = collections.defaultdict(list)
for g in gens: gen_by_model[g["model_id"]].append(g)
gen_model = {g["generation_id"]: g["model_id"] for g in gens}
img_by_model = collections.defaultdict(collections.Counter)
for r in img3 + img4:
    if r["vehicle_id"]: img_by_model[r["vehicle_id"]][r["image_category"]] += 1
col_by_model = collections.defaultdict(list)
for c in colors:
    if c["model_id"]: col_by_model[c["model_id"]].append(c)
link_cols = {l["color_id"] for l in links}
trims_by_model = collections.defaultdict(list)
for t in trims: trims_by_model[t["model_id"]].append(t)
my_by_model = collections.defaultdict(list)
for m in mys: my_by_model[m["model_id"]].append(m)
dim_models = {d["model_id"] for d in dims if d.get("model_id")} | {gen_model[d["generation_id"]] for d in dims if d.get("generation_id") in gen_model}
series_of_model = collections.defaultdict(set)   # keyed by model_id (model_key is not unique across brands)
for r in inv:
    for k in (r["mapped_model_ids"] or "").split(";"):
        if k: series_of_model[k].add(f"{r['series_name']}({r['series_id']})")
batch23_series = {"海豹(6394)": ["Seal", "Seal 07 DM-i"], "海豚(6139)": ["Dolphin"], "海鸥(6762)": ["Seagull"], "元PLUS(6298)": ["Yuan Plus"], "汉(5499)": ["Han EV", "Han DM-i", "Han DM", "Han DM-p"], "秦PLUS(5964)": ["Qin Plus DM-i", "Qin Plus EV"],
                  "宋PLUS新能源(5761)": ["Song Plus DM-i", "Song Plus EV"], "驱逐舰05(6337)": ["Destroyer 05"], "比亚迪e2(5238)": ["e2"]}
_b2key = {(m["brand_id"], m["model_key"]): m["model_id"] for m in models}
for s_, ks in batch23_series.items():
    for k in ks: series_of_model[_b2key[("B2", k)]].add(s_)
notes_by_model = {}
for g in gens:
    if g.get("note") and g["model_id"] not in notes_by_model: notes_by_model[g["model_id"]] = g["note"]

cat_rows = []; missing = []; cov = []
BATCH_OF = {}
b2_models = {m["model_id"] for m in rdp(os.path.join(HERE, "models.csv"))}
for m in models:
    mid = m["model_id"]; mk = m["model_key"]; gl = gen_by_model[mid]; ty = trims_by_model[mid]; cl = col_by_model[mid]; im = img_by_model.get(mid, collections.Counter()); my = my_by_model[mid]
    yrs = sorted({int(x["year"]) for x in my})
    doors = any(g.get("doors") for g in gl); bodystyle = any(g.get("body_style_text") or g.get("body_raw") for g in gl)
    n_img = sum(im.values()); has_series = bool(series_of_model.get(mid))
    status = ("COMPLETE_FOR_AVAILABLE_SOURCES" if ty and cl and n_img else "PARTIAL" if (ty or cl or n_img) else "NO_SOURCE_DATA_FOUND")
    miss = []
    if not has_series: miss.append("no Autohome series/trims (" + (notes_by_model.get(mid) or "not listed on Autohome") + ")")
    if not yrs: miss.append("sourced model-years")
    if not doors: miss.append("doors")
    if mid not in dim_models: miss.append("dimensions")
    if cl and not any(c["color_id"] in link_cols for c in cl): miss.append("paint code (no retailer candidate linked; none verified anyway)")
    if not cl and has_series: miss.append("exterior colours (no colour photos on any trim)")
    if not n_img and has_series: miss.append("images")
    for x in miss: missing.append(dict(brand=brands[m["brand_id"]], model_key=mk, missing_item=x.split(" (")[0], detail=x, severity="NO_SOURCE" if "no Autohome" in x else "GAP"))
    missing.append(dict(brand=brands[m["brand_id"]], model_key=mk, missing_item="OEM-verified paint code", detail="no OEM or exact-vehicle evidence for any model; supplier-catalog codes are POSSIBLE at best", severity="GLOBAL"))
    missing.append(dict(brand=brands[m["brand_id"]], model_key=mk, missing_item="official English colour names", detail="only unofficial literal glosses exist for China-market colours", severity="GLOBAL"))
    missing.append(dict(brand=brands[m["brand_id"]], model_key=mk, missing_item="exterior design description", detail="no source text describes styling beyond body class", severity="GLOBAL"))
    cat_rows.append(dict(model_id=mid, brand=brands[m["brand_id"]], series=m["series"], model_key=mk, name_zh=m["name_zh"], alt_names=m["alt_names"], powertrain=m["powertrain"], generations=len(gl), generation_names=" | ".join(g["source_row_name"] for g in gl)[:200],
                         status_values=";".join(sorted({g["status"] for g in gl})), documented_intro_years=";".join(sorted({g["intro_year"] for g in gl if g["intro_year"]})) or None, sourced_model_years=len(yrs), sourced_year_range=(f"{yrs[0]}-{yrs[-1]}" if yrs else None),
                         trims=len(ty), colour_records=len(cl), distinct_zh_colours=len({c["color_name_zh"] for c in cl if c["color_name_zh"]}), colours_with_possible_code=sum(1 for c in cl if c["color_id"] in link_cols), doors_documented=doors, body_style_documented=bodystyle,
                         dimensions_documented=mid in dim_models, images_exterior=im.get("exterior", 0), images_interior_cockpit=im.get("interior_cockpit", 0), images_seats=im.get("interior_seats", 0), images_official_press=im.get("official_press", 0),
                         autohome_series=";".join(sorted(series_of_model.get(mid, []))) or None, research_status=status, missing=" ; ".join(x.split(" (")[0] for x in miss) or None, origin=("batch2/3" if any(mid == _b2key[("B2", k)] for ks in batch23_series.values() for k in ks) else "batch4" if mid not in b2_models or has_series else "batch1 list only")))
cols = list(cat_rows[0].keys())
w(os.path.join(U, "catalog_complete_models.csv"), cat_rows, cols)
w(os.path.join(B4, "missing_data_b4.csv"), missing, ["brand", "model_key", "missing_item", "detail", "severity"])
# coverage by brand
bc = collections.defaultdict(collections.Counter)
for r in cat_rows:
    bc[r["brand"]]["models"] += 1; bc[r["brand"]][r["research_status"]] += 1
    bc[r["brand"]]["trims"] += r["trims"]; bc[r["brand"]]["colour_records"] += r["colour_records"]; bc[r["brand"]]["images"] += r["images_exterior"] + r["images_interior_cockpit"] + r["images_seats"] + r["images_official_press"]
w(os.path.join(B4, "brand_coverage_b4.csv"), [dict(brand=b, models=c["models"], complete_for_available_sources=c["COMPLETE_FOR_AVAILABLE_SOURCES"], partial=c["PARTIAL"], no_source_data_found=c["NO_SOURCE_DATA_FOUND"], trims=c["trims"], colour_records=c["colour_records"], images=c["images"]) for b, c in sorted(bc.items())],
  ["brand", "models", "complete_for_available_sources", "partial", "no_source_data_found", "trims", "colour_records", "images"])

# ---------------------------------------------------------------- integrity of the merged catalog
R = []
def chk(n, ok, d=""): R.append((n, bool(ok), d))
mid_set = {m["model_id"] for m in models}; gid = {g["generation_id"]: g for g in gens}; myd = {m["model_year_id"]: m for m in mys}; tid = {t["trim_id"] for t in trims}; cid = {c["color_id"]: c for c in colors}
def uniq(rows, k): return len({r[k] for r in rows}) == len(rows)
chk("primary keys unique in every merged table", all([uniq(models, "model_id"), uniq(gens, "generation_id"), uniq(mys, "model_year_id"), uniq(trims, "trim_id"), uniq(colors, "color_id"), uniq(pcs, "paint_code_id"), uniq(links, "link_id"), uniq(cands, "candidate_id"), uniq(ver, "verification_id"), uniq(srcs, "source_id")]), f"{len(models)} models, {len(gens)} generations, {len(mys)} model-years, {len(trims)} trims, {len(colors)} colours")
chk("generation -> model FK", all(g["model_id"] in mid_set for g in gens), "")
chk("model-year -> generation/model FK and (generation, year) unique", all(m["generation_id"] in gid and gid[m["generation_id"]]["model_id"] == m["model_id"] for m in mys) and len({(m["generation_id"], m["year"]) for m in mys}) == len(mys), "")
chk("trim -> model-year/generation/model consistent", all(t["model_year_id"] in myd and myd[t["model_year_id"]]["generation_id"] == t["generation_id"] and str(myd[t["model_year_id"]]["year"]) == str(t["year"]) and t["model_id"] in mid_set for t in trims), f"{len(trims)} trims")
chk("one trim per Autohome spec id", len({t["autohome_spec_id"] for t in trims}) == len(trims), "")
bad = [c["color_id"] for c in colors if c["model_id"] and (c["model_id"] not in mid_set or (c["generation_id"] and gid.get(c["generation_id"], {}).get("model_id") != c["model_id"]) or (c["model_year_id"] and myd.get(c["model_year_id"], {}).get("generation_id") != c["generation_id"]))]
chk("colour -> model/generation/model-year consistent", not bad, f"{len(colors)} colours, {len(bad)} problems {bad[:3]}")
chk("every colour has a source id that exists", all(c["source_id"] in {s["source_id"] for s in srcs} for c in colors), "")
chk("link -> colour/code FKs", all(l["color_id"] in cid and l["paint_code_id"] in {p["paint_code_id"] for p in pcs} for l in links), f"{len(links)} links")
chk("no VERIFIED anywhere (codes, links, verification records)", not any(p.get("code_status") == "VERIFIED" for p in pcs) and not any(l["status"] == "VERIFIED" for l in links) and not any(v["status"] == "VERIFIED" for v in ver), f"verification statuses: {dict(collections.Counter(v['status'] for v in ver))}")
chk("all model-year rows are SOURCED (no estimates in the merged table)", all(m["evidence_class"] == "SOURCED" for m in mys), "estimates stay in batch-2 estimates_model_years.csv only")
chk("every model has a catalog row", len(cat_rows) == len(models), f"{len(cat_rows)} rows")
chk("every model with an Autohome mapping has images or documented gap", all(r["images_exterior"] + r["images_interior_cockpit"] + r["images_seats"] + r["images_official_press"] > 0 or not r["autohome_series"] or r["research_status"] != "COMPLETE_FOR_AVAILABLE_SOURCES" for r in cat_rows), "")
chk("every model without trims is explained in missing_data_b4.csv", all(any(x["model_key"] == r["model_key"] and x["brand"] == r["brand"] and x["severity"] == "NO_SOURCE" for x in missing) for r in cat_rows if r["research_status"] == "NO_SOURCE_DATA_FOUND"), "")
if trim_status: chk("every harvested trim has a final status", all(r["status"] in ("COMPLETED", "NO_IMAGES_AVAILABLE", "FAILED_RETRY_REQUIRED", "PARTIAL") for r in trim_status), dict(collections.Counter(r["status"] for r in trim_status)))
gs = subprocess.run(["git", "-C", HERE, "status", "--porcelain", "--", "."], capture_output=True, text=True).stdout.splitlines()
chg = [l for l in gs if l[:2].strip() and not l.startswith("??") and not re.search(r"\.py$|\.gitignore$", l)]
chk("batch 1-3 datasets unchanged (git status)", not chg, f"modified tracked non-script files: {chg}")
ok_all = all(ok for _, ok, _ in R)
with open(os.path.join(B4, "data_integrity_report_batch4.md"), "w", encoding="utf-8") as f:
    f.write("# Batch 4 merged-catalog integrity report\n\n" + ("**RESULT: ALL CHECKS PASSED**\n\n" if ok_all else "**RESULT: FAILED**\n\n") + "| Check | Result | Detail |\n|---|---|---|\n")
    for n, ok, d in R: f.write(f"| {n} | {'PASS' if ok else 'FAIL'} | {str(d)[:240].replace('|', '/')} |\n")
st = collections.Counter(r["research_status"] for r in cat_rows)
json.dump(dict(models=len(cat_rows), status=dict(st), images_total_b3=len(img3), images_total_b4=len(img4), integrity_ok=ok_all, missing_rows=len(missing), checks=[(n, ok) for n, ok, _ in R]), open(os.path.join(B4, "stats_b4_reports.json"), "w"), indent=1)
print(json.dumps(dict(models=len(cat_rows), status=dict(st), integrity_ok=ok_all), indent=1))
if not ok_all: raise SystemExit(1)
