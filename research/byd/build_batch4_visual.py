#!/usr/bin/env python3
"""
BYD research dataset, batch 4: VISUAL CATALOG for the remaining BYD-group series (same architecture as batch 3).

Inputs  : raw_b4/ (autohome_specs_b4.json, autohome_images.jsonl.gz, retry_*.jsonl, expected_counts.json, empty_category_checks.jsonl,
          autohome_interior_colors.json, harvest_run.json, view_review_sample_b4.json)
          catalog_union/ (models_all, generations_all, model_years_all, trims_all, factory_colors_all)  built by build_batch4.py
          batch4/series_sources_b4.csv, batch3 visual tables (read only, for ID continuity and duplicate checks)
Outputs : batch4/images/*  (large tables gzipped), written to a STAGING folder, validated by validate_batch4.py, then published.
RULES (unchanged from batch 3): URLs/metadata only; nothing constructed; redirect-to-no-photos is never a success; view labels are
CANDIDATE unless I individually inspected the image; nothing is VERIFIED; no licence is cleared; earlier batches are never modified.
Run: python3 build_batch4_visual.py
"""
import csv, gzip, json, os, re, shutil, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__)); RAWD = os.path.join(HERE, "raw_b4"); UNION = os.path.join(HERE, "catalog_union")
OUTD = os.path.join(HERE, "batch4", "images"); STAGE = os.path.join(HERE, ".stage_batch4_visual")
if os.path.exists(STAGE): shutil.rmtree(STAGE)
os.makedirs(STAGE)

def rdp(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f: return list(csv.DictReader(f))
def w(name, rows, cols):
    path = os.path.join(STAGE, name)
    op = (lambda p: gzip.open(p, "wt", encoding="utf-8", newline="")) if name.endswith(".gz") else (lambda p: open(p, "w", encoding="utf-8", newline=""))
    with op(path) as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); wr.writeheader()
        for r in rows: wr.writerow(r)
def jl(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip(): yield json.loads(line)

models = {r["model_id"]: r for r in rdp(os.path.join(UNION, "models_all.csv"))}
gens = {r["generation_id"]: r for r in rdp(os.path.join(UNION, "generations_all.csv"))}
mys = {r["model_year_id"]: r for r in rdp(os.path.join(UNION, "model_years_all.csv"))}
trims = rdp(os.path.join(UNION, "trims_all.csv")); trim_by_spec = {t["autohome_spec_id"]: t for t in trims}
colors = rdp(os.path.join(UNION, "factory_colors_all.csv"))
series_src = {r["series_id"]: r["source_id"] for r in rdp(os.path.join(HERE, "batch4", "series_sources_b4.csv"))}
RAW = json.load(open(os.path.join(RAWD, "autohome_specs_b4.json"), encoding="utf-8"))
spec_info = {sp["spec_id"]: (key, sp, b["series_id"], b["brand"]) for key, b in RAW.items() for sp in b["specs"] if not re.search(r"概念|Concept|ocean-X", sp["label"], re.I)}
EXP = json.load(open(os.path.join(RAWD, "expected_counts.json"), encoding="utf-8"))
inner_colors = json.load(open(os.path.join(RAWD, "autohome_interior_colors.json"), encoding="utf-8"))
review = json.load(open(os.path.join(RAWD, "view_review_sample_b4.json"), encoding="utf-8"))
RUN = json.load(open(os.path.join(RAWD, "harvest_run.json"), encoding="utf-8"))
EMPTY = {(r["spec_id"], r["kind"]): r for r in jl(os.path.join(RAWD, "empty_category_checks.jsonl"))}
b3_img = rdp(os.path.join(HERE, "vehicle_images.csv")); b3_pairs = {(r["autohome_spec_id"], r["autohome_photo_id"]) for r in b3_img}
next_img = max(int(r["image_id"][3:]) for r in b3_img) + 1
next_sw = max(int(r["swatch_id"][2:]) for r in rdp(os.path.join(HERE, "color_swatches.csv"))) + 1

main_path = os.path.join(RAWD, "autohome_images.jsonl.gz")
main_recs, main_errors = [], []
for r in jl(main_path): (main_errors if "error" in r else main_recs).append(r)
retry_files = sorted(f for f in os.listdir(RAWD) if re.fullmatch(r"retry_records_\d+\.jsonl", f))
retry_log_files = sorted(f for f in os.listdir(RAWD) if re.fullmatch(r"retry_log_\d+\.jsonl", f))
superseded = {}; retry_recs = collections.defaultdict(list)
for f in retry_files:
    cur = None
    for r in jl(os.path.join(RAWD, f)):
        if r.get("_supersede"): cur = (r["spec_id"], r["kind"], r["key"]); superseded[cur] = r["retry_result"]; retry_recs[cur] = []
        else: retry_recs[cur].append(r)
recs = [r for r in main_recs if (r["spec_id"], r["kind"], r["key"]) not in superseded]
for lst in retry_recs.values(): recs.extend(lst)
retry_log = [r for f in retry_log_files for r in jl(os.path.join(RAWD, f))]

IMG_SRC = [
 dict(image_source_id="IS01", name="Autohome (汽车之家) picture gallery - exact-trim photo lists", site="car.autohome.com.cn / www.autohome.com.cn", rights_holder="Autohome and/or its photographers", license_status="NOT CLEARED - all rights presumed reserved", redistribution_allowed="NO / UNKNOWN", attribution="Photo: Autohome (汽车之家)", notes="Same source record as batch 3."),
 dict(image_source_id="IS02", name="Autohome 官图 (official press images) category", site="car.autohome.com.cn", rights_holder="Manufacturer press material distributed via Autohome", license_status="NOT CLEARED - press use terms unknown", redistribution_allowed="NO / UNKNOWN", attribution="Image: manufacturer via Autohome 官图", notes="Same source record as batch 3."),
]
SRC_ATTR = {r["image_source_id"]: r for r in IMG_SRC}

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
    for pos, pid, rr in lst: gal_of[(spec, pid)] = (cid, pos, len(lst), rr["list_url"], rr["photo_page_url"])
colour_name = {(spec, c["color_id"]): c["name_zh"] for spec, (key, sp, sid, br) in spec_info.items() for c in sp["colors"]}
col_idx = {(c["generation_id"], int(mys[c["model_year_id"]]["year"]), c["color_name_zh"]): c["color_id"] for c in colors if c["evidence_class"] == "GALLERY_OBSERVED" and c["model_year_id"]}

STD = {1: "front_left_three_quarter", 2: "front", 3: "front_right_three_quarter", 4: "left_side", 5: "rear_left_three_quarter", 6: "rear", 7: "rear_right_three_quarter", 8: "right_side"}
rev = {(g["spec_id"], g["autohome_color_id"]): g["result"] for g in review["galleries"]}
INSPECTED = {(i["spec_id"], i["autohome_color_id"], int(i["position"])): i["label"] for i in review.get("individually_inspected", [])}
COLLECT = RUN["collection_window_utc"]
ordered = sorted(by_key.values(), key=lambda r: (int(r["spec_id"]), KIND_ORDER[r["kind"]], r["position"]))
img_id = {}; vimg = []; ext = []; n_view = collections.Counter(); dup_with_b3 = 0
sizes = re.compile(r"/(\d+x\d+)_")
for r in ordered:
    if (r["spec_id"], r["photo_id"]) in b3_pairs: dup_with_b3 += 1
    iid = f"IMG{next_img + len(vimg):06d}"; img_id[(r["spec_id"], r["photo_id"])] = iid
    t = trim_by_spec.get(r["spec_id"]); key, sp, sid, brand = spec_info[r["spec_id"]]
    cat = CAT[r["kind"]]; g = gal_of.get((r["spec_id"], r["photo_id"]))
    cid_f = col_idx.get((t["generation_id"], int(t["year"]), colour_name.get((r["spec_id"], g[0])))) if (t and g) else None
    label = status = None
    if cat == "exterior":
        if g:
            cid, pos, n = g[0], g[1], g[2]; res = rev.get((r["spec_id"], cid))
            if (r["spec_id"], cid, pos) in INSPECTED: label, status = INSPECTED[(r["spec_id"], cid, pos)], "MODEL_REVIEWED_NOT_EDITOR_VERIFIED"
            elif res == "irregular": status = "REVIEWED_GALLERY_IRREGULAR_NO_LABEL"
            elif n in (7, 8) and pos <= n: label, status = STD[pos], "CANDIDATE"
            else: status = "UNKNOWN_NON_STANDARD_GALLERY_SIZE"
        else: status = "UNKNOWN_NO_SEQUENCE_CONTEXT"
        n_view[status] += 1
        ext.append(dict(image_id=iid, view_label=label, view_verification_status=status, colour_gallery_facet_id=g[0] if g else None, colour_gallery_position=g[1] if g else None, colour_gallery_size=g[2] if g else None))
    src = "IS02" if cat == "official_press" else "IS01"
    vimg.append(dict(
        image_id=iid, image_url=r["thumb_url"], image_url_kind="thumbnail (%s)" % ((sizes.search(r["thumb_url"] or "") or [None, "size unknown"])[1]),
        source_page_url=r["photo_page_url"], gallery_list_url=r.get("list_url"), autohome_photo_id=r["photo_id"], autohome_spec_id=r["spec_id"],
        vehicle_id=t["model_id"] if t else None, generation_id=t["generation_id"] if t else None, model_year=t["year"] if t else sp["year"][:4], model_year_id=t["model_year_id"] if t else None,
        trim_id=t["trim_id"] if t else None, image_category=cat, also_listed_as=";".join(sorted(CAT[x] for x in r["also"] if x in CAT)) or None, gallery_position=r["position"], caption_zh=r.get("alt"),
        view_label=label, view_verification_status=status, color_id=cid_f, color_name_zh=colour_name.get((r["spec_id"], g[0])) if g else None, color_facet_id=g[0] if g else None,
        color_association_basis="COLOUR_FILTERED_GALLERY_OF_EXACT_TRIM" if g else None, color_gallery_list_url=g[3] if g else None, color_gallery_photo_page_url=g[4] if g else None,
        image_source_id=src, attribution=SRC_ATTR[src]["attribution"], license_status="NOT CLEARED", link_status="LINKED_EXACT_TRIM" if t else "UNLINKED_MODEL_UNRESOLVED",
        year_match_basis="EXACT_TRIM_GALLERY", collected_at=r.get("collected_utc") or f"{COLLECT['start']}/{COLLECT['end']}",
        collected_at_precision="per-request UTC" if r.get("collected_utc") else "run-level window (per-image time not recorded)"))
VCOLS = ["image_id","image_url","image_url_kind","source_page_url","gallery_list_url","autohome_photo_id","autohome_spec_id","vehicle_id","generation_id","model_year","model_year_id","trim_id","image_category","also_listed_as","gallery_position","caption_zh","view_label","view_verification_status","color_id","color_name_zh","color_facet_id","color_association_basis","color_gallery_list_url","color_gallery_photo_page_url","image_source_id","attribution","license_status","link_status","year_match_basis","collected_at","collected_at_precision"]
w("vehicle_images_b4.csv.gz", vimg, VCOLS)
w("exterior_images_b4.csv.gz", ext, ["image_id","view_label","view_verification_status","colour_gallery_facet_id","colour_gallery_position","colour_gallery_size"])
w("interior_images_b4.csv.gz", [dict(image_id=v["image_id"], interior_area="COCKPIT_DASH_WHEEL_CONSOLE_UNSPLIT", source_category="10 中控方向盘") for v in vimg if v["image_category"] == "interior_cockpit"], ["image_id","interior_area","source_category"])
w("seat_images_b4.csv.gz", [dict(image_id=v["image_id"], interior_area="SEATS_CABIN_FRONT_REAR_UNSPLIT", source_category="3 车厢座椅") for v in vimg if v["image_category"] == "interior_seats"], ["image_id","interior_area","source_category"])
w("official_press_images_b4.csv.gz", [dict(image_id=v["image_id"], source_category="53 官图", content_type_status="NOT_CLASSIFIED") for v in vimg if v["image_category"] == "official_press"], ["image_id","source_category","content_type_status"])

swatches = []; vci = []
for spec, (key, sp, sid, brand) in spec_info.items():
    t = trim_by_spec.get(spec)
    if not t: continue
    for c in sp["colors"]:
        cid_f = col_idx.get((t["generation_id"], int(t["year"]), c["name_zh"]))
        swatches.append(dict(swatch_id=f"SW{next_sw + len(swatches):05d}", swatch_kind="exterior", color_id=cid_f, trim_id=t["trim_id"], model_year_id=t["model_year_id"], model_id=t["model_id"], generation_id=t["generation_id"],
                             name_zh=c["name_zh"], name_en=None, autohome_facet_id=c["color_id"], hex=c["hex"], hex_basis="AUTOHOME_FACET_SUPPLIED_NOT_SAMPLED_NOT_PAINT_SPEC", gallery_photos=c["photos"], evidence_url=sp["url"], source_id=series_src[str(sid)], verification_status="SOURCE_SUPPLIED_NOT_VERIFIED"))
for v in vimg:
    if v["color_facet_id"] and v["trim_id"]:
        vci.append(dict(image_id=v["image_id"], color_id=v["color_id"], trim_id=v["trim_id"], model_year_id=v["model_year_id"], autohome_facet_id=v["color_facet_id"], color_name_zh=v["color_name_zh"], gallery_position=v["gallery_position"],
                        evidence_url=v["color_gallery_list_url"], colour_status="GALLERY_CLASSIFIED"))
seen_sw = set()
for spec, d in inner_colors.items():
    t = trim_by_spec.get(spec)
    if not t or spec not in spec_info: continue
    key, sp, sid, brand = spec_info[spec]
    for area, lst in d.items():
        for f in lst:
            if (spec, f["facet_id"]) in seen_sw: continue
            seen_sw.add((spec, f["facet_id"]))
            swatches.append(dict(swatch_id=f"SW{next_sw + len(swatches):05d}", swatch_kind="interior", color_id=None, trim_id=t["trim_id"], model_year_id=t["model_year_id"], model_id=t["model_id"], generation_id=t["generation_id"],
                                 name_zh=f["name_zh"], name_en=None, autohome_facet_id=f["facet_id"], hex=f["hex"], hex_basis="AUTOHOME_FACET_SUPPLIED_NOT_SAMPLED_NOT_PAINT_SPEC", gallery_photos=f["photos"],
                                 evidence_url=f"https://car.autohome.com.cn/pic/series-s{spec}/{sid}-{10 if area == 'cockpit' else 3}.html", source_id=series_src[str(sid)], verification_status="SOURCE_SUPPLIED_NOT_VERIFIED"))
w("color_swatches_b4.csv", swatches, ["swatch_id","swatch_kind","color_id","trim_id","model_year_id","model_id","generation_id","name_zh","name_en","autohome_facet_id","hex","hex_basis","gallery_photos","evidence_url","source_id","verification_status"])
w("vehicle_color_images_b4.csv.gz", vci, ["image_id","color_id","trim_id","model_year_id","autohome_facet_id","color_name_zh","gallery_position","evidence_url","colour_status"])

# per-trim final status ---------------------------------------------------------
have = collections.defaultdict(set)
for r in recs:
    if "error" not in r: have[(r["spec_id"], r["kind"], r["key"])].add(r["photo_id"])
CATKEY = {"exterior": "1", "official": "53", "cockpit": "10", "seats": "3"}
status_rows = []; missing = []; STAT = collections.Counter()
for spec, (key, sp, sid, brand) in sorted(spec_info.items(), key=lambda kv: int(kv[0])):
    t = trim_by_spec.get(spec); e = EXP.get(spec, {}); issues = []; exp_tot = got_tot = 0; per = {}
    if "error" in e or not e: issues.append("landing page (expected counts) not retrieved")
    for kind, ck in CATKEY.items():
        exp = e.get(kind); got = len(have.get((spec, kind, ck), ())); chk = EMPTY.get((spec, kind)); confirmed_empty = False
        if exp is None and chk and chk["outcome"] == "confirmed_empty_redirect" and got == 0: exp = 0; confirmed_empty = True
        per[kind] = (exp, got); got_tot += got
        if exp is None and chk and chk["outcome"] == "MISMATCH_photos_served":
            issues.append(f"{kind}: the landing page states no total for this category, but the list serves photos ({chk['photo_links_in_body']} on page 1; {got} harvested by paginating to exhaustion); completeness cannot be verified independently")
        elif exp is None: issues.append(f"{kind}: tab absent on landing page and not confirmed empty")
        elif confirmed_empty:
            missing.append(dict(scope="trim_category", subject=f"spec {spec} {sp['year']} {sp['label']}", category=kind, expected=0, harvested=0, reason=f"confirmed empty: HTTP {chk['http']} redirect ({chk['utc']}); a redirect is NOT counted as a harvest", trim_id=t["trim_id"] if t else None))
        else:
            exp_tot += exp
            if exp != got:
                issues.append(f"{kind}: expected {exp}, harvested {got}" + (f" (last retry: {superseded.get((spec, kind, ck))})" if (spec, kind, ck) in superseded else ""))
                missing.append(dict(scope="trim_category", subject=f"spec {spec} {sp['year']} {sp['label']}", category=kind, expected=exp, harvested=got, reason=(f"retry result: {superseded[(spec, kind, ck)]}" if (spec, kind, ck) in superseded else "count mismatch, not retried"), trim_id=t["trim_id"] if t else None))
            elif exp == 0:
                missing.append(dict(scope="trim_category", subject=f"spec {spec} {sp['year']} {sp['label']}", category=kind, expected=0, harvested=0, reason="Autohome states 0 photos in this category", trim_id=t["trim_id"] if t else None))
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
    status_rows.append(dict(autohome_spec_id=spec, trim_id=t["trim_id"] if t else None, series=key, model_year=sp["year"][:4], trim_name_zh=sp["label"], status=st,
                            expected_exterior=per["exterior"][0], harvested_exterior=per["exterior"][1], expected_official=per["official"][0], harvested_official=per["official"][1], expected_cockpit=per["cockpit"][0], harvested_cockpit=per["cockpit"][1],
                            expected_seats=per["seats"][0], harvested_seats=per["seats"][1], colour_galleries=len(sp["colors"]), colour_gallery_photos_expected=cg_exp, colour_gallery_photos_harvested=cg_got,
                            issues=" | ".join(issues) or None, model_link="LINKED" if t else "UNLINKED_MODEL_UNRESOLVED"))
w("trim_harvest_status_b4.csv", status_rows, ["autohome_spec_id","trim_id","series","model_year","trim_name_zh","status","expected_exterior","harvested_exterior","expected_official","harvested_official","expected_cockpit","harvested_cockpit","expected_seats","harvested_seats","colour_galleries","colour_gallery_photos_expected","colour_gallery_photos_harvested","issues","model_link"])
for lbl, why in [("exterior view labels", "front/rear/left/right/3-4 labels are CANDIDATE only except individually inspected images"), ("interior sub-views", "source does not separate dashboard / steering wheel / centre console / front vs rear seats"),
                 ("interior colour galleries", "interior colour names + swatches recorded per trim; photos not linked to interior colours"), ("full-size images", "only thumbnails harvested (batch 4 scope: no full-size downloads)"), ("licensing", "no image has a cleared licence")]:
    missing.append(dict(scope="global", subject="all images", category=lbl, expected=None, harvested=None, reason=why, trim_id=None))
w("missing_images_report_b4.csv", missing, ["scope","subject","category","expected","harvested","reason","trim_id"])

fails = []; unexplained = 0
for e in main_errors:
    chk = EMPTY.get((e["spec_id"], e["kind"])); fin = superseded.get((e["spec_id"], e["kind"], e["key"]))
    if chk and chk["outcome"] == "confirmed_empty_redirect":
        fails.append(dict(source="main harvest", utc=chk["utc"], spec_id=e["spec_id"], list_kind=e["kind"], url=e["url"], http=chk["http"], outcome="redirect_no_photos", classification="NOT_A_FAILURE_CATEGORY_EMPTY", final_disposition="redirect to trim landing page = no photos; confirmed by empty_category_checks.jsonl; NOT counted as a harvest"))
    elif fin == "ok":
        fails.append(dict(source="main harvest", utc=None, spec_id=e["spec_id"], list_kind=e["kind"], url=e["url"], http=None, outcome="fetch_failed (HTTP code not recorded in the main run)", classification="GENUINE_MAIN_RUN_FAILURE_RECOVERED_BY_RETRY", final_disposition="the whole list was re-fetched in the retry pass and returned photos"))
    else:
        unexplained += 1
        fails.append(dict(source="main harvest", utc=None, spec_id=e["spec_id"], list_kind=e["kind"], url=e["url"], http=None, outcome="fetch_failed", classification="UNEXPLAINED_FAILURE", final_disposition=(f"re-fetched in retry pass: {fin}" if fin else "NOT RE-FETCHED")))
ok_urls = {r["url"] for r in retry_log if r["outcome"] == "ok"}
for r in retry_log:
    if r["outcome"] != "ok":
        rec = r["url"] in ok_urls
        fails.append(dict(source="retry pass", utc=r["utc"], spec_id=None, list_kind=None, url=r["url"], http=r["http"], outcome=r["outcome"], classification="GENUINE_NETWORK_FAILURE_RECOVERED" if rec else "GENUINE_FAILURE_UNRESOLVED",
                          final_disposition=(f"curl rc={r['curl_rc']}; a later attempt on the same URL succeeded" if rec else "no later attempt succeeded")))
w("failed_requests_report_b4.csv", fails, ["source","utc","spec_id","list_kind","url","http","outcome","classification","final_disposition"])

by_model = collections.defaultdict(collections.Counter)
for v in vimg:
    if v["vehicle_id"]: by_model[v["vehicle_id"]][v["image_category"]] += 1
cov = [dict(model_id=mid, model_key=m["model_key"], brand_id=m["brand_id"], images_total_b4=sum(by_model[mid].values()), exterior=by_model[mid].get("exterior", 0), official_press=by_model[mid].get("official_press", 0),
            interior_cockpit=by_model[mid].get("interior_cockpit", 0), interior_seats=by_model[mid].get("interior_seats", 0)) for mid, m in models.items() if mid in by_model]
w("image_coverage_by_model_b4.csv", cov, ["model_id","model_key","brand_id","images_total_b4","exterior","official_press","interior_cockpit","interior_seats"])
tot = collections.Counter(v["image_category"] for v in vimg)
stats = dict(trim_status=dict(STAT), specs=len(spec_info), images=len(vimg), by_category=dict(tot), linked_exact_trim=sum(1 for v in vimg if v["link_status"] == "LINKED_EXACT_TRIM"), unlinked=sum(1 for v in vimg if v["link_status"] != "LINKED_EXACT_TRIM"),
             colour_associated_images=len(vci), exterior_swatches=sum(1 for s in swatches if s["swatch_kind"] == "exterior"), interior_swatches=sum(1 for s in swatches if s["swatch_kind"] == "interior"), view_status=dict(n_view),
             main_run_errors=len(main_errors), main_run_errors_unexplained=unexplained, retry_requests=len(retry_log), retry_failed_requests=sum(1 for r in retry_log if r["outcome"] == "failed"), missing_rows=len(missing),
             models_with_images=len(cov), photos_also_in_batch3=dup_with_b3, collection_window_utc=COLLECT)
json.dump(stats, open(os.path.join(STAGE, "image_stats_b4.json"), "w"), indent=1)
json.dump(dict(next_image_id=next_img, images=len(vimg)), open(os.path.join(STAGE, "id_ranges_b4.json"), "w"))

vs = stats["view_status"]; rs = review["summary"]
open(os.path.join(STAGE, "image_verification_report_b4.md"), "w", encoding="utf-8").write(f"""# Batch 4 image verification report

## What is and is not verified
* **Vehicle linkage (trim / year / generation / model):** every image comes from the gallery of one exact Autohome trim (spec id). The spec id, series id and photo id inside each source-page URL were checked against the row for all {stats['images']:,} images (validation report). Autohome's labelling is the only evidence; no editor reviewed it. Trims whose EV/DM-i variant could not be resolved keep their images as `UNLINKED_MODEL_UNRESOLVED` ({stats['unlinked']:,} images).
* **No invented URLs:** every image URL, photo-page URL and gallery URL in the tables appears in a harvested record (checked against raw_b4/autohome_images.jsonl.gz and the retry records).
* **Colour association:** {stats['colour_associated_images']:,} images are linked to a colour because they appear in that trim's colour-filtered gallery (the URL carries the colour facet id). It is Autohome's colour label; photo colour vs swatch was not machine-checked. A colour with no gallery for the exact trim has no image (no substitute is used).
* **View labels:** **nothing is VERIFIED** (no human editor). Status counts: {json.dumps(vs, ensure_ascii=False)}.
  * `CANDIDATE`: label from the position in a 7/8-photo colour gallery. In my visual review of {rs['galleries_reviewed']} galleries from {rs['galleries_reviewed']} different series, **{rs['standard']} followed the standard order and {rs['irregular']} did not** (all dealer-showroom shoots). With batch 3 (16 of 19) that is 44 of 51 galleries (86%), so a candidate label can be wrong about one time in seven.
  * `MODEL_REVIEWED_NOT_EDITOR_VERIFIED`: the {rs['individually_inspected_images']} images I looked at individually at 400x300 (position 4 = left side, position 8 = right side in 8 galleries; nose direction checked in each). A model reviewed them, not a human editor.
  * `REVIEWED_GALLERY_IRREGULAR_NO_LABEL`: galleries I found to deviate; no label assigned.  `UNKNOWN_*`: no basis (plain exterior list, or a gallery size other than 7/8).
* **Left/right rule:** nose pointing left in the image = car's left (driver) side visible.
* **Interior images:** only two source categories exist (中控方向盘, 车厢座椅); dashboard vs steering wheel vs centre console and front vs rear seats are not distinguished. Interior colours are recorded as names/swatches per trim; photos are not linked to interior colours.
* **Official press images:** Autohome category 官图 (53); provenance by category label only, not classified as exterior/interior.
* **Resolution:** thumbnails only (400x300 / 480x360). No full-size image was downloaded or its URL harvested (batch 4 scope).
* **Swatch HEX:** supplied by Autohome's colour facet; not sampled from photos and not a paint specification.
* **Rights:** no image licence is cleared (same terms as batch 3). Do not publish or hot-link without permission.
* **Collection timestamps:** run-level window ({stats['collection_window_utc']['start']} to {stats['collection_window_utc']['end']}); per-image time only for images re-fetched in retry rounds.
""")
sys.path.insert(0, HERE)
import validate_batch4
ok = validate_batch4.run(STAGE, HERE, stats)
if not ok:
    print("VALIDATION FAILED - nothing published. See", os.path.join(STAGE, "validation_report_batch4_visual.md")); sys.exit(1)
os.makedirs(OUTD, exist_ok=True)
for f in os.listdir(STAGE): shutil.move(os.path.join(STAGE, f), os.path.join(OUTD, f))
os.rmdir(STAGE); print(json.dumps(stats, indent=1))
