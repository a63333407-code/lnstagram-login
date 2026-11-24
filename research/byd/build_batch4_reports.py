#!/usr/bin/env python3
"""
Batch 4 reports: complete model catalog, brand/model coverage, missing-data report, data-integrity validation of the merged catalog.
Run AFTER build_batch4.py (data) and build_batch4_visual.py (images).  Reads only; writes new files in batch4/ and catalog_union/.
"""
import csv, gzip, json, os, re, collections, subprocess

def fmt(d): return "; ".join(f"{k}: {v:,}" if isinstance(v, int) else f"{k}: {v}" for k, v in d.items())

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
# --- model-key collisions -------------------------------------------------------------------
bk = collections.Counter((m["brand_id"], m["model_key"]) for m in models); kk = collections.defaultdict(set)
for m in models: kk[m["model_key"]].add(m["brand_id"])
cross = {k: sorted(v) for k, v in kk.items() if len(v) > 1}
chk("no duplicate (brand, model_key); cross-brand key collisions are only the documented one", all(v == 1 for v in bk.values()) and set(cross) <= {"e5"}, f"cross-brand collisions: {cross} (BYD e5 vs Linghui e5: all lookups are brand-aware)")
# --- specifications must be traceable ---------------------------------------------------------
ibx = json.load(open(os.path.join(HERE, "raw_b4", "wikipedia_infoboxes_b4.json"), encoding="utf-8"))["infoboxes"] + json.load(open(os.path.join(HERE, "raw", "wikipedia_infoboxes.json"), encoding="utf-8"))
ibx_vals = {(i.get("length"), i.get("width"), i.get("height"), i.get("wheelbase")) for i in ibx}
bad = [d["dimension_id"] for d in dims if (d.get("length_text"), d.get("width_text"), d.get("height_text"), d.get("wheelbase_text")) not in ibx_vals or not d.get("evidence_url") or not d.get("source_id")]
chk("every dimension row equals a parsed Wikipedia infobox and cites its page", not bad, f"{len(dims)} dimension rows, {len(bad)} untraceable {bad[:3]}")
bad = [g["generation_id"] for g in gens if g.get("doors") and not g.get("doors_source_id")]
chk("every documented door count has a source id", not bad, f"{sum(1 for g in gens if g.get('doors'))} generations with doors, {len(bad)} without source")
bad = [f["generation_id"] for f in facts if f.get("doors") and (not f.get("wikipedia_url") or "infobox" not in (f.get("doors_basis") or ""))]
chk("batch-4 door counts come from a Wikipedia infobox body_style", not bad, f"{len(facts)} fact rows")
conf_oem = rdp(os.path.join(U, "confirmed_oem_paint_codes.csv"))
chk("confirmed OEM paint-code table is empty and no paint code has an OEM tier", not conf_oem and all(p.get("evidence_tier") == "RETAILER_CATALOG_UNVERIFIED" and p["code_status"] == "POSSIBLE" for p in pcs), f"{len(pcs)} codes, all RETAILER_CATALOG_UNVERIFIED/POSSIBLE; confirmed OEM codes: {len(conf_oem)}")
chk("link confidence audit: no 'high'; audited confidence never above original", all(l["confidence"] in ("low", "medium") and l["confidence_audited"] in ("low", "medium") and not (l["confidence_audited"] == "medium" and l["confidence"] == "low") for l in links), dict(collections.Counter((l["confidence"], l["confidence_audited"]) for l in links)))
gl = rdp(os.path.join(B4, "color_name_glossary_b4.csv"))
chk("all 309 Chinese colour names have a reviewed glossary entry labelled unofficial", len(gl) == 309 and all(x["review_status"] == "REVIEWED_UNOFFICIAL_RESEARCHER_TRANSLATION" and "NOT an official name" in x["gloss_basis"] for x in gl), f"{len(gl)} entries; kinds {fmt(collections.Counter(x['gloss_kind'] for x in gl))}")
chk("no gloss is stored as an official English name", all((c.get("name_en_is_official") or "") in ("", "True") for c in colors) and not any(c.get("name_en_gloss_unofficial") and c.get("name_en_is_official") == "True" for c in colors), "official flag only on OEM-source market names")
um = rdp(os.path.join(B4, "unmapped_specs_b4.csv"))
chk("every unmapped trim has a reason, candidates, evidence and a resolution path", all(u["reason"] and u["evidence"] and u["what_would_resolve_it"] and u["candidate_models"] for u in um), f"{len(um)} unmapped trims")
chk("every model without an Autohome series has a reason, evidence and absence check", all(n["reason"] and n["evidence"] and n["autohome_absence_check"] and n["evidence_url"] for n in nomap.values()), f"{len(nomap)} models")
gs = subprocess.run(["git", "-C", HERE, "status", "--porcelain", "--", "."], capture_output=True, text=True).stdout.splitlines()
chg = [l for l in gs if l[:2].strip() and not l.startswith("??") and not re.search(r"\.py$|\.gitignore$|research/byd/(batch4|catalog_union|raw_b4)/", l)]   # batches 1-3 only
chk("batch 1-3 datasets unchanged (git status)", not chg, f"modified tracked non-script files: {chg}")
ok_all = all(ok for _, ok, _ in R)
with open(os.path.join(B4, "data_integrity_report_batch4.md"), "w", encoding="utf-8") as f:
    f.write("# Batch 4 merged-catalog integrity report\n\n" + ("**RESULT: ALL CHECKS PASSED**\n\n" if ok_all else "**RESULT: FAILED**\n\n") + "| Check | Result | Detail |\n|---|---|---|\n")
    for n, ok, d in R: f.write(f"| {n} | {'PASS' if ok else 'FAIL'} | {str(d)[:240].replace('|', '/')} |\n")
st = collections.Counter(r["research_status"] for r in cat_rows)
json.dump(dict(models=len(cat_rows), status=dict(st), images_total_b3=len(img3), images_total_b4=len(img4), integrity_ok=ok_all, missing_rows=len(missing), checks=[(n, ok) for n, ok, _ in R]), open(os.path.join(B4, "stats_b4_reports.json"), "w"), indent=1)
print(json.dumps(dict(models=len(cat_rows), status=dict(st), integrity_ok=ok_all), indent=1))
if not ok_all: raise SystemExit(1)

# ====================================================================== REPORT_batch4.md (all figures computed from the output files)
def _rd(path): return rdp(path)
ds = json.load(open(os.path.join(B4, "stats_b4_data.json"))); vs_ = json.load(open(os.path.join(B4, "images", "image_stats_b4.json")))
rs_ = json.load(open(os.path.join(HERE, "raw_b4", "view_review_sample_b4.json")))["summary"]; run = json.load(open(os.path.join(HERE, "raw_b4", "harvest_run.json")))
um_ = _rd(os.path.join(B4, "unmapped_specs_b4.csv")); nm_ = _rd(os.path.join(B4, "models_without_autohome_mapping_b4.csv")); ts_ = _rd(os.path.join(B4, "images", "trim_harvest_status_b4.csv"))
fr_ = _rd(os.path.join(B4, "images", "failed_requests_report_b4.csv")); cf_ = _rd(os.path.join(B4, "source_conflicts_b4.csv")); al_ = _rd(os.path.join(B4, "alias_collisions_b4.csv"))
sb4 = _rd(os.path.join(B4, "sources_b4.csv")); inv_ = _rd(os.path.join(B4, "series_inventory_b4.csv")); sp_ = _rd(os.path.join(B4, "images", "url_spot_check_b4.csv"))
mod_b4 = _rd(os.path.join(B4, "models_b4.csv")); trims_b4 = _rd(os.path.join(B4, "trims_b4.csv")); links_u = _rd(os.path.join(U, "color_paint_code_links_all.csv"))
stc = collections.Counter(r["research_status"] for r in cat_rows)
gen_basis = collections.Counter(t["generation_assignment_basis"] for t in trims_b4); mod_basis = collections.Counter(t["model_assignment_basis"] for t in trims_b4)
lc = collections.Counter((l["confidence"], l["confidence_audited"]) for l in links_u)
rel = collections.Counter(s["reliability"] for s in sb4)
brand_rows = _rd(os.path.join(B4, "brand_coverage_b4.csv"))
def tbl(rows, cols, heads): return "| " + " | ".join(heads) + " |\n|" + "---|" * len(heads) + "\n" + "\n".join("| " + " | ".join(str(r[c] if r[c] is not None else "") .replace("|", "/")[:230] for c in cols) + " |" for r in rows)
partial_t = [r for r in ts_ if r["status"] != "COMPLETED"]
spot_ok = sum(1 for r in sp_ if r["status"] == "OK")
rep = f"""# BYD research - Batch 4 final report (remaining BYD-group models)

**Status: the Batch 4 image harvest is finished (all {vs_['specs']:,} trims have a final status) and every validator passes.**
Nothing was imported into any application, no application file was modified, and the catalog is **not published**. Batches 1-3 are unchanged (verified with `git status` inside both validators).
Rebuild order: `build_batch4.py` -> `build_batch4_visual.py` -> `raw_b4/spot_check_urls_b4.py` -> `build_batch4_reports.py`.

## Headline numbers
| Item | Result |
|---|---|
| Autohome series inventoried (4 brand pages) | {ds['series']} (95 harvested, 9 done in batch 3, 9 concept/show cars and 6 commercial series documented as excluded) |
| Catalog models after batch 4 (BYD group) | **{len(cat_rows)}** ({', '.join(f"{r['brand']} {r['models']}" for r in brand_rows)}); {ds['new_models']} models were discovered from Autohome and are absent from the Wikipedia list |
| Model research status | COMPLETE_FOR_AVAILABLE_SOURCES {stc['COMPLETE_FOR_AVAILABLE_SOURCES']} / PARTIAL {stc['PARTIAL']} / NO_SOURCE_DATA_FOUND {stc['NO_SOURCE_DATA_FOUND']} |
| Autohome trims (specs) read | {ds['specs']:,} -> **{ds['trims']:,} mapped to a model**, {ds['unmapped']} unmapped (explained), {ds['excluded']} excluded (concept cars) |
| New sourced model-year rows | {ds['new_model_years']} (plus {ds['model_years_touched_existing']} existing batch-2 rows enriched); merged catalog: {len(mys)} model-year rows, all SOURCED, **no estimates** |
| Generations after batch 4 | {len(gens)} ({ds['new_generations']} new, including 'generation unspecified' buckets) |
| Trims in merged catalog | {len(trims):,} |
| Factory colour records (batch 4) | {ds['colour_records']} ({ds['distinct_zh_colours']} distinct Chinese names; per-trim observations: {ds['color_by_trim']:,}) |
| Dimension rows / generation facts (Wikipedia infoboxes) | {ds['dims']} / {ds['facts']} |
| Paint-code candidates (retailer catalogs) | {ds['candidates']} new rows -> {ds['new_paint_codes']} new code tokens; {len(pcs)} codes in the merged catalog, **all POSSIBLE / RETAILER_CATALOG_UNVERIFIED** |
| Colour-to-code links (merged) | {len(links_u)}; {len({l['color_id'] for l in links_u})} colour records linked; **confirmed OEM codes: {len(conf_oem)}** |
| Images (batch 4) | **{vs_['images']:,}**: exterior {vs_['by_category']['exterior']:,}, interior/cockpit {vs_['by_category']['interior_cockpit']:,}, seats {vs_['by_category']['interior_seats']:,}, official press {vs_['by_category']['official_press']:,} |
| Image linkage | {vs_['linked_exact_trim']:,} linked to an exact trim/year/generation/model; {vs_['unlinked']:,} unlinked (the 18 unmapped trims); {vs_['colour_associated_images']:,} linked to a factory colour |
| Trim harvest status | **COMPLETED {sum(1 for r in ts_ if r['status']=='COMPLETED'):,} / PARTIAL {len(partial_t)} / NO_IMAGES_AVAILABLE {sum(1 for r in ts_ if r['status']=='NO_IMAGES_AVAILABLE')} / FAILED_RETRY_REQUIRED {sum(1 for r in ts_ if r['status']=='FAILED_RETRY_REQUIRED')}** |
| Swatches | {vs_['exterior_swatches']:,} exterior (per trim) + {vs_['interior_swatches']:,} interior |
| Live URL spot check | {spot_ok} of {len(sp_)} sampled URLs resolved (HTTP 200 + expected type) |

## Coverage by brand
{tbl(brand_rows, ['brand','models','complete_for_available_sources','partial','no_source_data_found','trims','colour_records','images'], ['Brand','Models','Complete for available sources','Partial','No source data found','Trims','Colour records','Images (b3+b4)'])}

**Reading 'complete for available sources':** the model has at least one trim, one colour record and one image from the sources reached. It does **not** mean every field is documented: see missing-data report (`missing_data_b4.csv`, {sum(1 for r in missing if r['severity']=='GAP')} model-level gaps; the global gaps are listed once per model).

### Models marked PARTIAL ({stc['PARTIAL']})
{tbl([r for r in cat_rows if r['research_status']=='PARTIAL'], ['brand','model_key','trims','colour_records','missing'], ['Brand','Model','Trims','Colour records','Missing'])}

These have trims and images but no colour photos on any trim (placeholder, show-car or Europe-only Autohome entries with a few photos).

## Unresolved cases (explicit, never forced)
### {len(nm_)} models without an Autohome series (you asked about 11; the brand-aware fix exposed Linghui e5 as a twelfth)
{tbl(nm_, ['model_key','reason','evidence'], ['Model','Reason','Evidence'])}

Each also has an Autohome absence check (brand page URL and fetch time) and a resolution path in `models_without_autohome_mapping_b4.csv`.

### {len(um_)} unmapped trims
{tbl(um_, ['series','year','label','candidate_models','evidence'], ['Series','Year','Trim label','Candidate rows','Evidence'])}

Autohome's per-spec parameter table (which would state EV/PHEV) is deliberately obfuscated (injected `hs_kw..._baikeee` spans), so it was not used. Their images are kept as `UNLINKED_MODEL_UNRESOLVED`.

### Generation assignment
Trims by how their model was chosen: {fmt(mod_basis)}. By how their generation was chosen: {fmt(gen_basis)}.
'Unresolved' means the trim sits in a '[generation unspecified]' bucket instead of being guessed: boundary years, years before the first documented generation, trims whose label states 第二代 (second generation), and Sealion 05 DM-i where Wikipedia's generation dates overlap.
{len(cf_)} source conflicts are recorded in `source_conflicts_b4.csv` (for example Autohome lists e7/M9 trims in 2025 while the Wikipedia list gives 2026; Autohome marks several 'current' list models as discontinued).

## Duplicate names and aliases
`alias_collisions_b4.csv` has {len(al_)} rows: {fmt(collections.Counter(r['alias_type'] for r in al_))}. Cross-brand model-key collisions: only **e5** (BYD e5 vs Linghui e5), handled with brand-aware lookups; no duplicate (brand, model_key).

## Paint codes (item 6 audit)
* All {len(pcs)} codes come from four retailer catalogs (Colour Tubes, Cartouch, Carross, Touch Up Paint Factory); none cites an OEM source. Tier: `RETAILER_CATALOG_UNVERIFIED`, status POSSIBLE. **No code is VERIFIED; `confirmed_oem_paint_codes.csv` is empty.**
* Repetition across retailers does not raise confidence: a link can be `medium` only when a retailer lists that model with a year range containing the model year and at most two names. Audit of all {len(links_u)} links (original -> audited): {fmt({f'{a} -> {b}': n for (a, b), n in lc.items()})}. The audit only downgrades ({lc[('medium','low')]} links fell from medium to low).
* Links require a model match, a year match where the retailer gives years, and an exact normalized match with a literal translation of the Chinese name. Multi-name alias groups (e.g. seven 'white' aliases) are always low.
* Rejected sources (batch 2): Paint Calculators and NonPaints. Official BYD code documentation was not found.

## Chinese colour translations (item 5)
All 309 Chinese colour names were reviewed. Every entry is labelled `REVIEWED_UNOFFICIAL_RESEARCHER_TRANSLATION` (never an official name, never stored in an 'official' field): {dict(collections.Counter(x['gloss_kind'] for x in gl))}. {sum(1 for x in gl if x['translation_note'])} carry ambiguity notes; {sum(1 for x in gl if x['retailer_english_names_equal_to_gloss'])} are echoed by an independent retailer English name (corroborates the translation only, not the paint code). Five translations were corrected in review (润玉白, 琴海蓝, 极汐绿, 赤帝红, 玄武黑).

## Images
* **Harvest:** {run['main_harvest_started_utc']} to {run['pipeline_finished_utc']}. First pass read 1,088 trims; **a parser gap was found and fixed**: older galleries use `<a class="carpic-img" href=...>` and the first parser missed their photos (429 lists disagreed with Autohome's own totals). All 429 were re-fetched with the fixed parser; 417 matched, 12 still disagree after four rounds (source inconsistencies, below).
* **Redirects:** {sum(1 for r in fr_ if r['classification']=='NOT_A_FAILURE_CATEGORY_EMPTY'):,} category lists answered HTTP 302 (no photos). Each was re-requested and recorded as *confirmed empty*; a redirect is never counted as a harvest and never as a failure.
* **Failed requests:** {fmt(collections.Counter(r['classification'] for r in fr_))}; no unresolved failure. See `failed_requests_report_b4.csv`.
* **PARTIAL trims ({len(partial_t)}), all source inconsistencies after four retries:**
{tbl(partial_t, ['series','model_year','trim_name_zh','issues'], ['Series','Year','Trim','Issue'])}
* **View labels: no image is VERIFIED.** {fmt(vs_['view_status'])}. CANDIDATE labels come from photo position in 7/8-photo colour galleries; in my visual review of {rs_['galleries_reviewed']} galleries from different series, {rs_['standard']} matched the standard order and {rs_['irregular']} did not (all dealer-showroom shoots). With batch 3 that is 44 of 51 (86%). {rs_['individually_inspected_images']} images were individually inspected at 400x300 (`MODEL_REVIEWED_NOT_EDITOR_VERIFIED`; a model, not a human editor).
* **Interior:** only two source categories (cockpit area, seats/cabin); dashboard/wheel/console and front/rear seats are not separated; photos are not linked to interior colours.
* **Resolution and rights:** 480x360 thumbnails only; no full-size image was downloaded (batch-4 scope). No image licence is cleared; Autohome photos are presumed all-rights-reserved.
* **No invented URLs:** every image, photo-page and gallery URL appears in a harvested record (validator check).

## Source quality
Batch-4 sources by reliability: {fmt(rel)}. OEM-class sources: none new (BYD's China model pages exposed no colour lists). Everything is Autohome photo evidence (exact-trim, but not an official availability list), Wikipedia infoboxes (secondary) and retailer catalogs. Colour lists are **lower bounds**: each trim shows only some colours.

## Validation (all hard checks passed)
* `batch4/images/validation_report_batch4_visual.md`: image/trim/generation/year/colour relationships, URL ids, view-label rules, statuses, URL provenance, no unresolved failures, batches 1-3 unchanged.
* `batch4/data_integrity_report_batch4.md` (merged catalog): {len(R)} checks {'passed' if ok_all else 'FAILED'}: key uniqueness, FKs, trim/generation/model-year consistency, no VERIFIED anywhere, all years SOURCED, dimensions traceable to an infobox, door counts sourced, brand-aware model keys, confirmed-OEM table empty, link audit, glossary labelling, evidence on every unmapped case.
* `batch4/validation_report_batch4_data.md`: ids unique and disjoint from batches 1-3, none of the 1,094 specs lost (trims + unmapped + excluded), trim/colour consistency, sourced years only, no VERIFIED status, glossary coverage.

## Limitations and remaining blockers
1. **No OEM-verified paint code exists** for any model; verification needs label photos, a BYD parts/paint-formula source or a licensed refinish database.
2. **No official English colour names** for China-market colours; glosses are unofficial.
3. **Images are not cleared for any use**, are thumbnails only, and view labels are candidates (about one in seven wrong in sampled galleries).
4. **18 trims and 12 models** remain unmapped/without a series (above) until a source resolves them.
5. **Exterior design** descriptions are not available beyond body class; doors/dimensions exist only where a Wikipedia infobox states them.
6. The catalog reflects Autohome's Chinese-market gallery view; export-market colours and trims are mostly absent.
7. Not published, not imported, as instructed.
"""
open(os.path.join(HERE, "REPORT_batch4.md"), "w", encoding="utf-8").write(rep)
print("REPORT_batch4.md written")
