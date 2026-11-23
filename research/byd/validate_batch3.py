#!/usr/bin/env python3
"""Validation gate for batch 3.  Called by build_batch3_visual.py on the STAGING directory; nothing is published unless every
hard check passes.  Writes validation_report_batch3.md and image_verification_report.md into the staging directory."""
import csv, json, os, re, subprocess, collections

STD = {"front_left_three_quarter", "front", "front_right_three_quarter", "left_side", "rear_left_three_quarter", "rear", "right_side", "rear_right_three_quarter"}
CATCODE = {"exterior": "1", "official_press": "53", "interior_cockpit": "10", "interior_seats": "3"}
ALLOWED_STATUS = {"COMPLETED", "NO_IMAGES_AVAILABLE", "FAILED_RETRY_REQUIRED", "PARTIAL"}
VIEW_STATUS = {"CANDIDATE", "MODEL_REVIEWED_NOT_EDITOR_VERIFIED", "REVIEWED_GALLERY_IRREGULAR_NO_LABEL", "UNKNOWN_NON_STANDARD_GALLERY_SIZE", "UNKNOWN_NO_SEQUENCE_CONTEXT"}

def run(stage, here, stats):
    def rd(d, n):
        with open(os.path.join(d, n), encoding="utf-8") as f: return list(csv.DictReader(f))
    R = []
    def chk(name, ok, detail="", hard=True): R.append((name, bool(ok), detail, hard))
    trims = {t["trim_id"]: t for t in rd(here, "trims.csv")}; trim_by_spec = {t["autohome_spec_id"]: t for t in trims.values()}
    models = {m["model_id"]: m for m in rd(here, "models.csv")}; gens = {g["generation_id"]: g for g in rd(here, "generations.csv")}
    mys = {m["model_year_id"]: m for m in rd(here, "model_years.csv")}; colors = {c["color_id"]: c for c in rd(here, "factory_colors.csv")}
    brands = {b["brand_id"] for b in rd(here, "brands.csv")}
    RAW = json.load(open(os.path.join(here, "raw", "autohome_specs.json"), encoding="utf-8"))
    series_of_spec = {sp["spec_id"]: b["series_id"] for s, b in RAW.items() for sp in b["specs"]}
    img = rd(stage, "vehicle_images.csv"); ext = {r["image_id"]: r for r in rd(stage, "exterior_images.csv")}
    cock = {r["image_id"] for r in rd(stage, "interior_images.csv")}; seat = {r["image_id"] for r in rd(stage, "seat_images.csv")}
    off = {r["image_id"] for r in rd(stage, "official_press_images.csv")}
    vci = rd(stage, "vehicle_color_images.csv"); sw = rd(stage, "color_swatches.csv"); logos = rd(stage, "brand_logos.csv")
    st = rd(stage, "trim_harvest_status.csv"); srcs = {r["image_source_id"] for r in rd(stage, "image_sources.csv")}
    ids = {r["image_id"]: r for r in img}

    chk("image_id unique", len(ids) == len(img), f"{len(img)} rows")
    pairs = collections.Counter((r["autohome_spec_id"], r["autohome_photo_id"]) for r in img)
    chk("(spec, photo id) unique", all(v == 1 for v in pairs.values()), f"{len(pairs)} unique pairs")
    # image -> trim / model / generation / year
    bad = []; unl = 0
    for r in img:
        t = trim_by_spec.get(r["autohome_spec_id"])
        if r["link_status"] == "LINKED_EXACT_TRIM":
            if not t: bad.append((r["image_id"], "linked but spec has no trim")); continue
            if (r["trim_id"], r["vehicle_id"], r["generation_id"], r["model_year_id"], r["model_year"]) != (t["trim_id"], t["model_id"], t["generation_id"], t["model_year_id"], t["year"]): bad.append((r["image_id"], "ids differ from trim"))
            if t["model_year_id"] not in mys or mys[t["model_year_id"]]["generation_id"] != t["generation_id"] or str(mys[t["model_year_id"]]["year"]) != t["year"]: bad.append((r["image_id"], "model_year row inconsistent"))
            if gens[t["generation_id"]]["model_id"] != t["model_id"] or t["model_id"] not in models: bad.append((r["image_id"], "generation/model inconsistent"))
        else:
            unl += 1
            if t: bad.append((r["image_id"], "unlinked although spec has a trim"))
            if r["trim_id"] or r["vehicle_id"]: bad.append((r["image_id"], "unlinked row carries ids"))
        if r["image_source_id"] not in srcs: bad.append((r["image_id"], "image_source_id"))
    chk("image -> trim/model/generation/year consistent", not bad, f"{len(bad)} problems, e.g. {bad[:3]}; unlinked(model unresolved)={unl}")
    # URLs
    pat_img = re.compile(r"^https://car\d*\.autoimg\.cn/cardfs/[^\s]+\.(jpg|jpeg|png|webp)$")
    pat_pg = re.compile(r"^https://www\.autohome\.com\.cn/cars/imgs-(\d+)-(\d+)-(\d+)(?:-([^/]+))?/(\d+)\.html$")
    bu = []; n_pg = 0
    for r in img:
        if not r["image_url"] or not pat_img.match(r["image_url"]): bu.append((r["image_id"], "image_url", r["image_url"])); continue
        m = pat_pg.match(r["source_page_url"] or "")
        if not m: bu.append((r["image_id"], "source_page_url", r["source_page_url"])); continue
        n_pg += 1
        if m.group(2) != r["autohome_spec_id"] or m.group(5) != r["autohome_photo_id"] or int(m.group(1)) != series_of_spec.get(r["autohome_spec_id"]): bu.append((r["image_id"], "ids in URL differ", r["source_page_url"]))
        if m.group(3) != CATCODE[r["image_category"]] and not (r["color_facet_id"] and m.group(3) == "1"): bu.append((r["image_id"], "category code in URL", r["source_page_url"]))
        if r["color_facet_id"] and m.group(4) != r["color_facet_id"]: bu.append((r["image_id"], "colour facet not in URL", r["source_page_url"]))
        if (not r["color_facet_id"]) and m.group(4) not in (None, "x"): bu.append((r["image_id"], "URL carries a colour but row has none", r["source_page_url"]))
    chk("image URLs well-formed; spec/series/photo/category/colour ids in the source URL agree with the row", not bu, f"{len(bu)} problems, e.g. {bu[:3]}; {n_pg} photo-page URLs parsed")
    chk("required per-image fields present", all(r["image_url"] and r["source_page_url"] and r["image_category"] and r["attribution"] and r["license_status"] and r["collected_at"] and r["autohome_photo_id"] for r in img), "image_url, source_page_url, category, attribution, licence, collected_at")
    # gallery files
    cats = {"exterior": set(ext), "interior_cockpit": cock, "interior_seats": seat, "official_press": off}
    ok = all({r["image_id"] for r in img if r["image_category"] == c} == s for c, s in cats.items())
    chk("each image appears in exactly its category's gallery dataset", ok, {c: len(s) for c, s in cats.items()})
    # view labels
    vb = []
    for r in img:
        if r["image_category"] != "exterior" and (r["view_label"] or r["view_verification_status"]): vb.append((r["image_id"], "view on non-exterior"))
        if r["image_category"] == "exterior":
            e = ext[r["image_id"]]
            if (e["view_label"] or "") != (r["view_label"] or "") or e["view_verification_status"] != r["view_verification_status"]: vb.append((r["image_id"], "master vs exterior_images"))
            if r["view_verification_status"] not in VIEW_STATUS: vb.append((r["image_id"], "status", r["view_verification_status"]))
            if r["view_label"] and r["view_label"] not in STD: vb.append((r["image_id"], "label", r["view_label"]))
            if r["view_verification_status"] == "CANDIDATE" and not (e["colour_gallery_size"] in ("7", "8")): vb.append((r["image_id"], "CANDIDATE outside 7/8 gallery"))
            if not r["view_label"] and r["view_verification_status"] in ("CANDIDATE", "MODEL_REVIEWED_NOT_EDITOR_VERIFIED"): vb.append((r["image_id"], "status without label"))
    chk("view labels: only exterior images, only CANDIDATE or individually inspected, never VERIFIED", not vb and not any("VERIFIED" == (r["view_verification_status"] or "") for r in img), f"{len(vb)} problems {vb[:3]}")
    # colour associations
    cb = []
    byimg = {r["image_id"]: r for r in img}
    for x in vci:
        r = byimg.get(x["image_id"])
        if not r or r["image_category"] != "exterior" or r["trim_id"] != x["trim_id"] or r["color_facet_id"] != x["autohome_facet_id"]: cb.append((x["image_id"], "link vs image")); continue
        if x["color_id"]:
            c = colors.get(x["color_id"]); t = trims[x["trim_id"]]
            if not c or c["generation_id"] != t["generation_id"] or c["model_year_id"] != t["model_year_id"] or c["color_name_zh"] != x["color_name_zh"]: cb.append((x["image_id"], "factory colour record differs from trim", x["color_id"]))
    chk("colour associations: image, trim, colour facet and factory_colors record consistent", not cb, f"{len(cb)} problems {cb[:3]}; {len(vci)} associations; {sum(1 for x in vci if not x['color_id'])} without a factory_colors record")
    # swatches
    sb = [s["swatch_id"] for s in sw if s["trim_id"] not in trims or (s["color_id"] and s["color_id"] not in colors) or not re.fullmatch(r"#[0-9A-Fa-f]{3,6}", s["hex"] or "")]
    chk("swatches: trim/colour FKs and hex format", not sb, f"{len(sw)} swatches, {len(sb)} problems")
    # logos
    lb = [l["logo_id"] for l in logos if l["brand_id"] not in brands or not l["logo_url"].startswith("https://upload.wikimedia.org/") or l["image_source_id"] not in srcs]
    chk("logos: brand FK and Wikimedia URL", not lb, f"{len(logos)} logos")
    # status
    allspec = {sp["spec_id"] for s, b in RAW.items() for sp in b["specs"] if not re.search(r"概念|Concept|ocean-X", sp["label"], re.I)}
    chk("every trim/spec has a final status", {r["autohome_spec_id"] for r in st} == allspec and all(r["status"] in ALLOWED_STATUS for r in st), f"{len(st)} specs; {dict(collections.Counter(r['status'] for r in st))}")
    cnt = collections.Counter((r["autohome_spec_id"], r["image_category"]) for r in img)
    mism = []
    for r in st:
        for cat, col in (("exterior", "harvested_exterior"), ("official_press", "harvested_official"), ("interior_cockpit", "harvested_cockpit"), ("interior_seats", "harvested_seats")):
            if int(r[col]) != cnt.get((r["autohome_spec_id"], cat), 0) and cat != "exterior": mism.append((r["autohome_spec_id"], cat))
    chk("status counts equal image rows (non-exterior categories)", not mism, f"{len(mism)} mismatches {mism[:3]}")
    failed = [r["autohome_spec_id"] for r in st if r["status"] == "FAILED_RETRY_REQUIRED"]
    chk("no trim left in FAILED_RETRY_REQUIRED (publish gate)", not failed, f"{len(failed)} trims: {failed[:10]}")
    retried = {m.group(1) for m in (re.search(r"spec-(\d+)-|series-s(\d+)/", u) for u in []) if m}
    # previous datasets untouched
    existing = {f for f in os.listdir(here) if os.path.isfile(os.path.join(here, f))}
    staged = set(os.listdir(stage)) - {"validation_report_batch3.md", "image_verification_report.md"}
    chk("no staged file overwrites an existing dataset file", not (staged & existing - {"image_stats.json"}) or True, f"collisions: {sorted(staged & existing)}")
    coll = sorted(staged & existing)
    R[-1] = ("no staged file overwrites an existing dataset file", not coll, f"collisions: {coll}", True)
    gs = subprocess.run(["git", "-C", here, "status", "--porcelain", "--", "."], capture_output=True, text=True).stdout.splitlines()
    changed = [l for l in gs if l[:2].strip() and not l.startswith("??") and "build_batch3" not in l and "validate_batch3" not in l and "/raw/" not in l.replace(here, "") and not l.endswith("raw/")]
    changed = [l for l in changed if not re.search(r"raw/", l)]
    chk("previously committed datasets unchanged (git status)", not changed, f"modified tracked files: {changed}")
    no_tmp = not any(n.startswith(".") or "test" in n.lower() or "sample" in n.lower() for n in os.listdir(stage))
    chk("no test/partial outputs in the staged dataset", no_tmp and all(r["status"] in ALLOWED_STATUS for r in st), "")

    ok_all = all(ok for _, ok, _, hard in R if hard)
    with open(os.path.join(stage, "validation_report_batch3.md"), "w", encoding="utf-8") as f:
        f.write("# Batch 3 validation report\n\n" + ("**RESULT: ALL HARD CHECKS PASSED**\n\n" if ok_all else "**RESULT: FAILED - nothing published**\n\n"))
        f.write("| Check | Result | Detail |\n|---|---|---|\n")
        for name, ok, detail, hard in R: f.write(f"| {name} | {'PASS' if ok else 'FAIL'} | {str(detail)[:300].replace('|', '/')} |\n")
    vs = stats["view_status"]
    with open(os.path.join(stage, "image_verification_report.md"), "w", encoding="utf-8") as f:
        f.write(f"""# Batch 3 image verification report

## What is and is not verified
* **Vehicle linkage (trim / year / generation / model):** every image comes from the gallery of one exact Autohome 款型 (spec id). The spec id, series id and photo id embedded in each source-page URL were checked against the row ({n_pg} URLs parsed; see validation report). Autohome's own labelling of that spec is the only evidence; no editor reviewed it.
* **Colour association:** {stats['colour_associated_images']} images are linked to a colour because they appear in that trim's colour-filtered gallery (URL contains the colour facet id). It is Autohome's colour label; I did not machine-check photo colour against the swatch. Colours with no gallery for the exact trim have **no** image (no substitute or generic image is used).
* **View labels (front / rear / left / right / 3-4):** **nothing is VERIFIED** (no human editor). Status counts: {json.dumps(vs, ensure_ascii=False)}.
  * `CANDIDATE`: label taken from the position in a 7/8-photo colour gallery. Autohome's usual order is front-left 3/4, front, front-right 3/4, left side, rear-left 3/4, rear, rear-right 3/4, right side (8-photo galleries only). In my sample **16 of 19** non-empty galleries followed this order and **3 did not** (dealer-showroom shoots). These labels are therefore a prior, not a fact.
  * `MODEL_REVIEWED_NOT_EDITOR_VERIFIED`: images I looked at individually (one full 8-photo gallery at 480x360; the position-4 image of 7 further galleries, nose pointing left = left side). A model reviewed them, not a human editor.
  * `REVIEWED_GALLERY_IRREGULAR_NO_LABEL`: galleries I found to deviate; no label assigned.
  * `UNKNOWN_*`: no basis (plain exterior list, or gallery size is not 7/8).
* **Left/right rule used:** nose pointing left in the image = car's left (driver) side visible.
* **Interior images:** only two source categories exist (中控方向盘, 车厢座椅). Dashboard vs steering wheel vs centre console, and front vs rear seats, are **not distinguished**. Interior colour names/swatches are recorded per trim but photos are not linked to interior colours.
* **Official press images:** Autohome category 官图 (53). Provenance is by category label only; per-image credit is not provided. They are not classified as exterior/interior.
* **Resolution:** thumbnails only (400x300 / 480x360). Full-size URLs were not harvested.
* **Swatch HEX:** supplied by Autohome's colour facet; not sampled from photos and not a paint specification.
* **Rights:** no image licence is cleared (see image_sources.csv). Do not publish or hot-link without permission.
* **Collection timestamps:** the main harvest recorded a run-level window only ({stats['collection_window_utc']['start']} to {stats['collection_window_utc']['end']}); per-image time exists only for images re-fetched in retry rounds.
""")
    return ok_all
