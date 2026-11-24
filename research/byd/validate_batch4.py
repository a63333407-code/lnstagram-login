#!/usr/bin/env python3
"""Validation gate for the batch-4 visual tables (staging dir).  Nothing is published unless every hard check passes."""
import csv, gzip, json, os, re, subprocess, collections

STD = {"front_left_three_quarter", "front", "front_right_three_quarter", "left_side", "rear_left_three_quarter", "rear", "right_side", "rear_right_three_quarter"}
CATCODE = {"exterior": "1", "official_press": "53", "interior_cockpit": "10", "interior_seats": "3"}
ALLOWED_STATUS = {"COMPLETED", "NO_IMAGES_AVAILABLE", "FAILED_RETRY_REQUIRED", "PARTIAL"}
VIEW_STATUS = {"CANDIDATE", "MODEL_REVIEWED_NOT_EDITOR_VERIFIED", "REVIEWED_GALLERY_IRREGULAR_NO_LABEL", "UNKNOWN_NON_STANDARD_GALLERY_SIZE", "UNKNOWN_NO_SEQUENCE_CONTEXT"}

def rd(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f: return list(csv.DictReader(f))

def run(stage, here, stats):
    R = []
    def chk(name, ok, detail="", hard=True): R.append((name, bool(ok), detail, hard))
    U = os.path.join(here, "catalog_union")
    trims = {t["trim_id"]: t for t in rd(os.path.join(U, "trims_all.csv"))}; trim_by_spec = {t["autohome_spec_id"]: t for t in trims.values()}
    models = {m["model_id"]: m for m in rd(os.path.join(U, "models_all.csv"))}; gens = {g["generation_id"]: g for g in rd(os.path.join(U, "generations_all.csv"))}
    mys = {m["model_year_id"]: m for m in rd(os.path.join(U, "model_years_all.csv"))}; colors = {c["color_id"]: c for c in rd(os.path.join(U, "factory_colors_all.csv"))}
    RAW = json.load(open(os.path.join(here, "raw_b4", "autohome_specs_b4.json"), encoding="utf-8"))
    series_of_spec = {sp["spec_id"]: b["series_id"] for k, b in RAW.items() for sp in b["specs"]}
    img = rd(os.path.join(stage, "vehicle_images_b4.csv.gz")); ext = {r["image_id"]: r for r in rd(os.path.join(stage, "exterior_images_b4.csv.gz"))}
    cock = {r["image_id"] for r in rd(os.path.join(stage, "interior_images_b4.csv.gz"))}; seat = {r["image_id"] for r in rd(os.path.join(stage, "seat_images_b4.csv.gz"))}
    off = {r["image_id"] for r in rd(os.path.join(stage, "official_press_images_b4.csv.gz"))}
    vci = rd(os.path.join(stage, "vehicle_color_images_b4.csv.gz")); sw = rd(os.path.join(stage, "color_swatches_b4.csv")); st = rd(os.path.join(stage, "trim_harvest_status_b4.csv"))
    b3 = rd(os.path.join(here, "vehicle_images.csv")); b3_ids = {r["image_id"] for r in b3}; b3_pairs = {(r["autohome_spec_id"], r["autohome_photo_id"]) for r in b3}
    b3_sw = {r["swatch_id"] for r in rd(os.path.join(here, "color_swatches.csv"))}
    ids = {r["image_id"]: r for r in img}
    chk("image_id unique within batch 4 and disjoint from batch 3", len(ids) == len(img) and not (set(ids) & b3_ids), f"{len(img)} rows")
    pairs = collections.Counter((r["autohome_spec_id"], r["autohome_photo_id"]) for r in img)
    chk("(spec, photo id) unique and disjoint from batch 3", all(v == 1 for v in pairs.values()) and not (set(pairs) & b3_pairs), f"{len(pairs)} pairs")
    chk("swatch_id unique and disjoint from batch 3", len({s["swatch_id"] for s in sw}) == len(sw) and not ({s["swatch_id"] for s in sw} & b3_sw), f"{len(sw)} swatches")
    bad = []; unl = 0
    for r in img:
        t = trim_by_spec.get(r["autohome_spec_id"])
        if r["link_status"] == "LINKED_EXACT_TRIM":
            if not t: bad.append((r["image_id"], "linked but spec has no trim")); continue
            if (r["trim_id"], r["vehicle_id"], r["generation_id"], r["model_year_id"], r["model_year"]) != (t["trim_id"], t["model_id"], t["generation_id"], t["model_year_id"], t["year"]): bad.append((r["image_id"], "ids differ from trim"))
            my = mys.get(t["model_year_id"])
            if not my or my["generation_id"] != t["generation_id"] or str(my["year"]) != t["year"] or my["model_id"] != t["model_id"]: bad.append((r["image_id"], "model_year row inconsistent"))
            if t["generation_id"] not in gens or gens[t["generation_id"]]["model_id"] != t["model_id"] or t["model_id"] not in models: bad.append((r["image_id"], "generation/model inconsistent"))
        else:
            unl += 1
            if t: bad.append((r["image_id"], "unlinked although spec has a trim"))
            if r["trim_id"] or r["vehicle_id"]: bad.append((r["image_id"], "unlinked row carries ids"))
    chk("image -> trim/model/generation/year consistent (union catalog)", not bad, f"{len(bad)} problems, e.g. {bad[:3]}; unlinked(model unresolved)={unl}")
    pat_img = re.compile(r"^https://car\d*\.autoimg\.cn/(cardfs|upload|car/upload)/[^\s]+\.(jpg|jpeg|png|webp|gif)$")   # cardfs = current CDN path; upload / car/upload = older galleries
    pat_pg = re.compile(r"^https://www\.autohome\.com\.cn/cars/imgs-(\d+)-(\d+)-(\d+)(?:-([^/]+))?/(\d+)\.html$")
    bu = []
    for r in img:
        if not r["image_url"] or not pat_img.match(r["image_url"]): bu.append((r["image_id"], "image_url", r["image_url"])); continue
        m = pat_pg.match(r["source_page_url"] or "")
        if not m: bu.append((r["image_id"], "source_page_url", r["source_page_url"])); continue
        if m.group(2) != r["autohome_spec_id"] or m.group(5) != r["autohome_photo_id"] or int(m.group(1)) != series_of_spec.get(r["autohome_spec_id"]): bu.append((r["image_id"], "ids in URL differ", r["source_page_url"]))
        if m.group(3) != CATCODE[r["image_category"]] and not (r["color_facet_id"] and m.group(3) == "1"): bu.append((r["image_id"], "category code in URL", r["source_page_url"]))
        if m.group(4) not in (None, "x") and m.group(4) != r["color_facet_id"]: bu.append((r["image_id"], "URL carries a colour the row does not", r["source_page_url"]))
        if r["color_facet_id"]:
            m2 = pat_pg.match(r["color_gallery_photo_page_url"] or "")
            if not m2 or (m2.group(2), m2.group(4), m2.group(5)) != (r["autohome_spec_id"], r["color_facet_id"], r["autohome_photo_id"]): bu.append((r["image_id"], "colour gallery photo URL disagrees", r["color_gallery_photo_page_url"]))
            if f"spec-{r['autohome_spec_id']}-{r['color_facet_id']}-1-" not in (r["color_gallery_list_url"] or ""): bu.append((r["image_id"], "colour gallery list URL disagrees", r["color_gallery_list_url"]))
    chk("image URLs well-formed; spec/series/photo/category/colour ids in the source URL agree with the row", not bu, f"{len(bu)} problems, e.g. {bu[:3]}")
    chk("required per-image fields present", all(r["image_url"] and r["source_page_url"] and r["image_category"] and r["attribution"] and r["license_status"] and r["collected_at"] and r["autohome_photo_id"] for r in img), "url, source page, category, attribution, licence, collected_at")
    cats = {"exterior": set(ext), "interior_cockpit": cock, "interior_seats": seat, "official_press": off}
    chk("each image appears in exactly its category's gallery dataset", all({r["image_id"] for r in img if r["image_category"] == c} == s for c, s in cats.items()), {c: len(s) for c, s in cats.items()})
    vb = []
    for r in img:
        if r["image_category"] != "exterior" and (r["view_label"] or r["view_verification_status"]): vb.append((r["image_id"], "view on non-exterior"))
        if r["image_category"] == "exterior":
            e = ext[r["image_id"]]
            if (e["view_label"] or "") != (r["view_label"] or "") or e["view_verification_status"] != r["view_verification_status"]: vb.append((r["image_id"], "master vs exterior_images"))
            if r["view_verification_status"] not in VIEW_STATUS: vb.append((r["image_id"], "status", r["view_verification_status"]))
            if r["view_label"] and r["view_label"] not in STD: vb.append((r["image_id"], "label", r["view_label"]))
            if r["view_verification_status"] == "CANDIDATE" and e["colour_gallery_size"] not in ("7", "8"): vb.append((r["image_id"], "CANDIDATE outside 7/8 gallery"))
            if not r["view_label"] and r["view_verification_status"] in ("CANDIDATE", "MODEL_REVIEWED_NOT_EDITOR_VERIFIED"): vb.append((r["image_id"], "status without label"))
    chk("view labels: exterior only; CANDIDATE or individually inspected; never VERIFIED", not vb and not any((r["view_verification_status"] or "") == "VERIFIED" for r in img), f"{len(vb)} problems {vb[:3]}")
    cb = []; byimg = {r["image_id"]: r for r in img}
    for x in vci:
        r = byimg.get(x["image_id"])
        if not r or r["image_category"] != "exterior" or r["trim_id"] != x["trim_id"] or r["color_facet_id"] != x["autohome_facet_id"]: cb.append((x["image_id"], "link vs image")); continue
        if x["color_id"]:
            c = colors.get(x["color_id"]); t = trims[x["trim_id"]]
            if not c or c["generation_id"] != t["generation_id"] or c["model_year_id"] != t["model_year_id"] or c["color_name_zh"] != x["color_name_zh"]: cb.append((x["image_id"], "factory colour record differs from trim", x["color_id"]))
    chk("colour associations consistent with trim, facet and factory_colors", not cb, f"{len(cb)} problems {cb[:3]}; {len(vci)} associations; {sum(1 for x in vci if not x['color_id'])} without a factory_colors record")
    sb = [s["swatch_id"] for s in sw if s["trim_id"] not in trims or (s["color_id"] and s["color_id"] not in colors) or not re.fullmatch(r"#[0-9A-Fa-f]{3,6}", s["hex"] or "")]
    chk("swatches: trim/colour FKs and hex format", not sb, f"{len(sw)} swatches, {len(sb)} problems")
    allspec = {sp["spec_id"] for k, b in RAW.items() for sp in b["specs"] if not re.search(r"概念|Concept|ocean-X", sp["label"], re.I)}
    chk("every trim/spec has a final status", {r["autohome_spec_id"] for r in st} == allspec and all(r["status"] in ALLOWED_STATUS for r in st), f"{len(st)} specs; {dict(collections.Counter(r['status'] for r in st))}")
    cnt = collections.Counter((r["autohome_spec_id"], r["image_category"]) for r in img); mism = []
    for r in st:
        for cat, col in (("official_press", "harvested_official"), ("interior_cockpit", "harvested_cockpit"), ("interior_seats", "harvested_seats")):
            if int(r[col]) != cnt.get((r["autohome_spec_id"], cat), 0): mism.append((r["autohome_spec_id"], cat))
    chk("status counts equal image rows (non-exterior categories)", not mism, f"{len(mism)} mismatches {mism[:3]}")
    failed = [r["autohome_spec_id"] for r in st if r["status"] == "FAILED_RETRY_REQUIRED"]
    chk("no trim left in FAILED_RETRY_REQUIRED (publish gate)", not failed, f"{len(failed)} trims: {failed[:10]}")
    retry_urls = [json.loads(l)["url"] for fn in sorted(os.listdir(os.path.join(here, "raw_b4"))) if re.fullmatch(r"retry_log_\d+\.jsonl", fn) for l in open(os.path.join(here, "raw_b4", fn), encoding="utf-8") if l.strip()]
    unretried = [r["autohome_spec_id"] for r in st if r["status"] == "PARTIAL" and not any(re.search(r"(?:series-s|spec-)%s\b" % r["autohome_spec_id"], u) for u in retry_urls)]
    fr = rd(os.path.join(stage, "failed_requests_report_b4.csv"))
    chk("no unexplained or unresolved failed request remains", not any(r["classification"] in ("UNEXPLAINED_FAILURE", "GENUINE_FAILURE_UNRESOLVED") for r in fr), dict(collections.Counter(r["classification"] for r in fr)))
    chk("every PARTIAL trim was re-fetched at least once", not unretried, f"{sum(1 for r in st if r['status']=='PARTIAL')} PARTIAL trims; not retried: {unretried[:10]}")
    # image URLs must come from harvested records (no constructed URLs)
    raw_dir = os.path.join(here, "raw_b4"); harvested_thumbs = set(); harvested_pages = set(); harvested_lists = set()
    def _jl(path):
        op = gzip.open if path.endswith(".gz") else open
        with op(path, "rt", encoding="utf-8") as f:
            for line in f:
                if line.strip(): yield json.loads(line)
    for fn in sorted(os.listdir(raw_dir)):
        if fn == "autohome_images.jsonl.gz" or re.fullmatch(r"retry_records_\d+\.jsonl", fn):
            for r_ in _jl(os.path.join(raw_dir, fn)):
                if "error" in r_ or r_.get("_supersede"): continue
                harvested_thumbs.add(r_.get("thumb_url")); harvested_pages.add(r_.get("photo_page_url")); harvested_lists.add(r_.get("list_url"))
    inv_urls = [r["image_url"] for r in img if r["image_url"] not in harvested_thumbs]
    inv_pg = [r["source_page_url"] for r in img if r["source_page_url"] not in harvested_pages]
    inv_gl = [r["gallery_list_url"] for r in img if r["gallery_list_url"] not in harvested_lists]
    chk("no invented image URLs: every image URL, photo-page URL and gallery URL appears in a harvested record", not inv_urls and not inv_pg and not inv_gl, f"{len(img)} images; not harvested: {len(inv_urls)} image urls, {len(inv_pg)} page urls, {len(inv_gl)} list urls")
    # earlier batches untouched (datasets, not scripts)
    gs = subprocess.run(["git", "-C", here, "status", "--porcelain", "--", "."], capture_output=True, text=True).stdout.splitlines()
    changed = [l for l in gs if l[:2].strip() and not l.startswith("??") and not re.search(r"\.py$|\.gitignore$|research/byd/(batch4|catalog_union|raw_b4)/", l)]   # batches 1-3 only
    chk("previously committed datasets (batches 1-3) unchanged (git status)", not changed, f"modified tracked non-script files: {changed}")
    chk("no test/partial outputs in staging", not any(n.startswith(".") or "test" in n.lower() or "sample" in n.lower() for n in os.listdir(stage)), "")
    ok_all = all(ok for _, ok, _, hard in R if hard)
    with open(os.path.join(stage, "validation_report_batch4_visual.md"), "w", encoding="utf-8") as f:
        f.write("# Batch 4 visual validation report\n\n" + ("**RESULT: ALL HARD CHECKS PASSED**\n\n" if ok_all else "**RESULT: FAILED - nothing published**\n\n"))
        f.write("| Check | Result | Detail |\n|---|---|---|\n")
        for name, ok, detail, hard in R: f.write(f"| {name} | {'PASS' if ok else 'FAIL'} | {str(detail)[:300].replace('|', '/')} |\n")
    return ok_all
