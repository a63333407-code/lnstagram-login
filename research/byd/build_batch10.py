#!/usr/bin/env python3
"""
Batch 10 - real-world evidence & source quality audit (BYD Group).  Reproducible build.

Research only.  Re-audits every source (Batches 1-9), builds a source-lineage graph (copies of one upstream count once),
audits the four priority colour groups, audits model-year consistency for ALL 1,223 colour records, and states the exact
evidence needed.  Nothing is promoted; no conflict is resolved; old records are preserved (reclassifications are explained).

Inputs (read-only): catalog_union/*, batch5/source_register.csv, batch6/{discovered_codes,sources,conflicts}.csv, batch6/raw/*.json,
                    batch7/{discovered_codes,sources,conflicts,source_lineage_analysis}.csv, batch7/raw/*.json,
                    batch8/{sources,discovered_codes,verification_results}.csv, batch9/{evidence_register,conflict_priority}.csv
Outputs: batch10/{source_audit,source_lineage_graph,colour_conflict_audit,model_year_consistency,evidence_requirements}.csv, stats_batch10.json
"""
import csv, os, re, json, collections
from pypinyin import lazy_pinyin

HERE = os.path.dirname(os.path.abspath(__file__)); U = f"{HERE}/catalog_union"
B5, B6, B7, B8, B9, B10 = (f"{HERE}/batch{i}" for i in (5, 6, 7, 8, 9, 10)); os.makedirs(B10, exist_ok=True)
TODAY = "2026-11-24"


def rd(p):
    with open(p, encoding="utf-8", newline="") as f: return list(csv.DictReader(f))


def wr(name, rows, fields):
    with open(f"{B10}/{name}", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in fields})


brands = {b["brand_id"]: b["name"] for b in rd(f"{U}/brands_all.csv")}
models = {m["model_id"]: m for m in rd(f"{U}/models_all.csv")}
gens = {g["generation_id"]: g for g in rd(f"{U}/generations_all.csv")}
years = {y["model_year_id"]: y for y in rd(f"{U}/model_years_all.csv")}
cols = {c["color_id"]: c for c in rd(f"{U}/factory_colors_all.csv")}
cands = rd(f"{U}/paint_code_candidates_all.csv")
REF_RE = re.compile(r"BYH[A-Z]-\d+|BYD\d{2,}[A-Z0-9]*")
def tokens(raw): return {t.strip().upper() for t in re.split(r"[;,/]+|\s+\|\s+", raw or "") if t.strip()}

# =============================================================================================== A. SOURCE AUDIT
rows_src = collections.OrderedDict()
def add_src(sid, title, url, stype, notes, batch, extra=""):
    if sid in rows_src: rows_src[sid]["also_listed_in"] += f",{batch}"; return
    rows_src[sid] = dict(source_key=sid, first_batch=batch, title=title, url_or_query=url, original_type=stype, original_notes=notes, extra=extra, also_listed_in="")
for s in rd(f"{U}/sources_all.csv"): add_src(s["source_id"], s["title"], s["url"], s["source_type"] + " / " + s["reliability"], s["notes"], "1-4")
for s in rd(f"{B5}/source_register.csv"): add_src(s["b5_source_id"], s["title"], s["url_or_query"], s["publisher_or_type"], s["notes"], "5")
for s in rd(f"{B6}/sources.csv"): add_src(s["source_id"], s["title"], s["url_or_query"], s["publisher_or_type"], s["notes"], "6")
for s in rd(f"{B7}/sources.csv"): add_src(s["source_id"], s["title"], s["url_or_query"], s["publisher_or_type"], s["notes"], "7")
for s in rd(f"{B8}/sources.csv"): add_src(s["source_id"], s["title"], s["url_or_query"], s["publisher_or_type"], s["notes"], "8")
for s in rd(f"{B9}/evidence_register.csv"): add_src(s["evidence_id"], s["description"][:160], s["source"], s["category"], s.get("notes", ""), "9")
ADDED10 = [("B10S01", "BYD Australia ATTO 3 2026 brochure (colour page re-read)", "https://bydautomotive.com.au/brochures/BYD-ATTO-3-2026.pdf", "OEM-importer brochure", "Lists exterior colours Ski White, Harbour Grey, Cosmos Black, Atlantis Grey ('Atlantis Grey only available on PREMIUM Model'); NO paint codes and NO finish statement (no 'matte' wording found by keyword search)."),
           ("B10S02", "Denza official service-support page", "https://www.tengshiauto.com/support/service-support.html", "Manufacturer-controlled website", "Fetched 2026-11-24 (HTTP 200): lists '24小时道路救援热线：950856' (so 950856 appears on two separate Denza page elements: footer customer-service line and this rescue line); warranty text; no paint information."),
           ("B10S03", "Search record - genuine label photographs / official evidence for 雪域白, 攀岩灰/Boulder Grey, 亚特兰蒂斯灰/Atlantis Grey, 苍穹蓝", "queries: BYD 雪域白 色号 W36C OR WA2 OR WA8 ... 铭牌 照片; BYD Atto 3 Boulder Grey paint code HA4 OR HAN owner photo sticker; BYD Seal Atlantis Grey paint code HB5 OR HB6 owner forum; 比亚迪 苍穹蓝 色号 BYL OR F2 OR LAN OR L32C OR L-27", "web search record", "No owner photograph of a BYD colour-code label and no official BYD statement of any of these codes was found. Only retailer pages, importer colour-name pages and generic guidance surfaced."),
           ("B10S04", "Search record - Linghui (领汇) official sources", "领汇 汽车 品牌 ...; 领汇汽车 官方网站 官网 用户手册 下载 ...", "web search record", "Media/portal pages describe Linghui as a BYD sub-brand launched in 2026 (e5, e7, e9, M9; models reported as derived from Dynasty/Ocean models). No official Linghui site, manual or service page found. Name or parentage similarity is not evidence of shared paint codes.")]
for sid, t, u, ty, n in ADDED10: add_src(sid, t, u, ty, n, "10")

PAINT_SRC = {"S29": ("RETAILER_TOUCHUP_PAINT", "L-PC-COLOURTUBES"), "S30": ("RETAILER_TOUCHUP_PAINT", "L-PC-TUPF-CARTOUCH"), "S31": ("RETAILER_TOUCHUP_PAINT", "L-PC-CARROSS"), "S227": ("RETAILER_TOUCHUP_PAINT", "L-PC-CARROSS"),
             "S32": ("RETAILER_TOUCHUP_PAINT", "L-PC-TUPF-CARTOUCH"), "S226": ("RETAILER_TOUCHUP_PAINT", "L-PC-TUPF-CARTOUCH"), "B6S02": ("RETAILER_TOUCHUP_PAINT", "L-PC-OEMATCH-LUNA"), "B7S02": ("RETAILER_TOUCHUP_PAINT", "L-PC-OEMATCH-LUNA"),
             "B6S03": ("RETAILER_TOUCHUP_PAINT", "L-PC-CROP"), "S03": ("RETAILER_TOUCHUP_PAINT", "L-PC-CROP"), "S13": ("RETAILER_TOUCHUP_PAINT", "L-PC-CHIPEX"), "S33": ("MARKETPLACE_OR_COPIED_LISTING", "L-PC-PAINTCALCULATORS-REJECTED")}
def classify(sid, title, url, ty, notes):
    t = f"{title} {url} {ty} {notes}".lower(); u = (url or "").lower()
    if sid in PAINT_SRC: return PAINT_SRC[sid][0], PAINT_SRC[sid][1], "RETAILER_NAME_MATCH", "YES" if sid not in ("S03", "S13", "S33") else "NO"
    if sid.startswith("EP"): return "PENDING_PLACEHOLDER", "L-PENDING-PLACEHOLDER", "PENDING_FIELD_EVIDENCE", "NO"
    if sid == "EV08": return "SEARCH_RECORD", "L-SEARCH-RECORD", "SEARCH_NEGATIVE_OR_LEAD", "NO"
    if "i-car" in t or "rts.i-car" in u: return "INDUSTRY_BODY_INDEX", "L-ICAR", "INDEX_OF_REPAIR_INFO_AVAILABILITY", "NO"
    if "apps.apple.com" in u: return "MANUFACTURER_CONTROLLED", "L-OEM-BYD", "OEM_APP_LISTING_SNIPPET_ONLY", "NO"
    if "carmudi" in t or "dailymotion" in t: return "MEDIA_ARTICLE", "L-MEDIA", "BACKGROUND", "NO"
    if "search record" in t or "web search record" in t or sid in ("B10S03", "B10S04", "B8S08", "B7S17", "B7S18", "B6S07", "B6S08", "B6S09", "B5S11", "B5S12", "B5S13", "B5S14"): return "SEARCH_RECORD", "L-SEARCH-RECORD", "SEARCH_NEGATIVE_OR_LEAD", "NO"
    if "github.com/bydcar" in u or "byd.ev-manual.com" in u: return "MARKETPLACE_OR_COPIED_LISTING", "L-UNVERIFIED-MIRROR", "ACCESS_ATTEMPT_ONLY", "NO"
    if sid in ("S34", "B6S04") or "q&a" in t or "autohome.com.cn/ask" in u: return "FORUM_QA", "L-AUTOHOME-QA", "WEAK_CLAIM", "NO"
    if sid in ("B6S05",) or "jd.com" in u: return "MARKETPLACE_OR_COPIED_LISTING", "L-MARKETPLACE-JD", "COLOUR_NAME_LISTING", "NO"
    if "gb/t" in t or "chinesestandard" in u: return "REGULATORY_STANDARD", "L-GB-STANDARDS", "REGULATORY_TEXT", "NO"
    if "17vin" in t or "vin decoder" in t or "vindecoder" in u or "vincario" in u: return "DATA_PLATFORM_THIRD_PARTY", "L-17VIN" if "17vin" in t else "L-VIN-DECODERS", "VIN_DATA_PLATFORM", "NO"
    if any(k in t for k in ("baslac", "formula finder")): return "LICENSED_PAINT_SYSTEM", "L-PAINTSYSTEM-BASF", "PAINT_SYSTEM_BEHAVIOUR", "NO"
    if any(k in t for k in ("glasurit", "basf")): return "LICENSED_PAINT_SYSTEM", "L-PAINTSYSTEM-BASF", "PAINT_SYSTEM_BEHAVIOUR", "NO"
    if "akzonobel" in t: return "LICENSED_PAINT_SYSTEM", "L-PAINTSYSTEM-AKZONOBEL", "PAINT_SYSTEM_BEHAVIOUR", "NO"
    if "axalta" in t and "cartouch" not in t: return "LICENSED_PAINT_SYSTEM", "L-PAINTSYSTEM-AXALTA", "PAINT_SYSTEM_BEHAVIOUR", "NO"
    if "onwings" in t or "donglai" in t or "maigoo" in u or "cnpp" in u: return "LICENSED_PAINT_SYSTEM", "L-PAINTSYSTEM-DONGLAI", "PAINT_SYSTEM_BEHAVIOUR", "NO"
    if any(k in u for k in ("fangchengbao.com",)): return "MANUFACTURER_CONTROLLED", "L-OEM-FANGCHENGBAO", "OEM_SITE", "NO"
    if "tengshiauto.com" in u: return "MANUFACTURER_CONTROLLED", "L-OEM-DENZA", "OEM_SITE", "NO"
    if "yangwangauto.com" in u: return "MANUFACTURER_CONTROLLED", "L-OEM-YANGWANG", "OEM_SITE", "NO"
    if "bydautomotive.com.au" in u or "carplus.se" in u or "importer" in t: return "MANUFACTURER_CONTROLLED", "L-OEM-BYD-IMPORTERS", "OEM_IMPORTER_DOCUMENT", "NO"
    if "byd.com" in u or "bydauto.com" in u or sid.startswith("B5S0") or sid in ("B7S12", "B7S13", "B7S14", "B7S15", "B8S03", "B8S04", "B8S09", "B6S01", "EV01", "EV02", "EV06", "EV07", "B8S05"): return "MANUFACTURER_CONTROLLED", "L-OEM-BYD", "OEM_SITE_OR_MANUAL", "NO"
    if "autohome" in t or "autoimg" in t: return "MEDIA_PORTAL_CATALOG", "L-AUTOHOME", "COLOUR_NAME_YEAR_TRIM", "NO"
    if "wikipedia" in t or "secondary-encyclopedia" in t: return "ENCYCLOPEDIA", "L-WIKIPEDIA", "MODEL_YEAR_BACKGROUND", "NO"
    if any(k in t for k in ("media", "news", "sina", "sohu", "pconline", "xchuxing")): return "MEDIA_ARTICLE", "L-MEDIA", "BACKGROUND", "NO"
    if "paintscratch" in t or "vinaudit" in t or "dipyourcar.com/blogs" in u or "chipex" in t: return "RETAILER_TOUCHUP_PAINT", "L-GENERIC-PAINT-GUIDES", "GENERIC_GUIDANCE", "NO"
    return "OTHER", "L-OTHER", "UNCLASSIFIED", "NO"

SA = []
for sid, r in rows_src.items():
    cls, lin, role, codes = classify(sid, r["title"], r["url_or_query"], r["original_type"], r["original_notes"])
    mc = "YES" if cls == "MANUFACTURER_CONTROLLED" else "NO"
    gate = "login/licence/paid" if cls in ("LICENSED_PAINT_SYSTEM", "DATA_PLATFORM_THIRD_PARTY") else ("owner/dealer account for some documents" if cls == "MANUFACTURER_CONTROLLED" and "app" in r["original_notes"].lower() else "public")
    effect = {"MANUFACTURER_CONTROLLED": "Authoritative for what the manufacturer states; no paint code obtained from any such source yet",
              "RETAILER_TOUCHUP_PAINT": "Candidate codes only (POSSIBLE/CONFLICTED); can never reach VERIFIED_OEM alone; copies of one upstream count once",
              "LICENSED_PAINT_SYSTEM": "Describes how formula systems work; any identifier from them is PAINT_SYSTEM_REFERENCE, not an OEM code; terms restrict storage",
              "MEDIA_PORTAL_CATALOG": "Colour names, years and trims (gallery evidence); contains no paint codes", "ENCYCLOPEDIA": "Background for models/years; not paint evidence",
              "FORUM_QA": "Weak, unsourced claims; never evidence for a code", "MARKETPLACE_OR_COPIED_LISTING": "Not usable as evidence (copied/unverified provenance)", "REGULATORY_STANDARD": "Regulatory facts (e.g. certificate colour classes)",
              "DATA_PLATFORM_THIRD_PARTY": "Schema/availability facts only; no paint field documented", "SEARCH_RECORD": "Negative or lead record; not a source document", "PENDING_PLACEHOLDER": "Placeholder for field evidence NOT obtained; not a source", "INDUSTRY_BODY_INDEX": "Index of whether OEM repair information exists; no paint codes", "MEDIA_ARTICLE": "Background only", "OTHER": "Unclassified - background only"}[cls]
    SA.append(dict(source_key=sid, first_batch=r["first_batch"], also_listed_in=r["also_listed_in"].strip(","), title=r["title"][:200], url_or_query=r["url_or_query"][:300], original_type=r["original_type"][:120], source_class=cls, manufacturer_controlled=mc,
                   access_gate=gate, evidence_role=role, contains_vehicle_paint_codes=codes, lineage_id=lin, status_effect=effect,
                   audit_note="Reclassified by Batch 10 rules; original label kept in original_type" if cls in ("MARKETPLACE_OR_COPIED_LISTING", "FORUM_QA") else ""))
SAF = ["source_key", "first_batch", "also_listed_in", "title", "url_or_query", "original_type", "source_class", "manufacturer_controlled", "access_gate", "evidence_role", "contains_vehicle_paint_codes", "lineage_id", "status_effect", "audit_note"]
wr("source_audit.csv", SA, SAF)
cls_count = collections.Counter(r["source_class"] for r in SA)

# =============================================================================================== A2. LINEAGE GRAPH
lat = {(r["source_a"], r["source_b"]): r for r in rd(f"{B7}/source_lineage_analysis.csv")}
LG = []
def lg(**k): LG.append(k)
lin_members = collections.defaultdict(list)
for r in SA: lin_members[r["lineage_id"]].append(r["source_key"])
LINNOTE = {"L-PC-OEMATCH-LUNA": ("SAME_UPSTREAM_EVIDENCED", "OEMatch (B6S02) and DipYourCar (B7S02): 57 of 60 shared codes carry identical normalised romanised names and the same abbreviations (95%)"),
           "L-PC-TUPF-CARTOUCH": ("LIKELY_SHARED_UPSTREAM", "Touch Up Paint Factory (S32, S226) and Cartouch (S30): 12 of 12 shared codes carry identical normalised colour names (100%); Cartouch states its paints come from Axalta. Merged for counting (heuristic: >=10 shared codes and >=90% identical names); not proven"),
           "L-PC-CARROSS": ("SAME_SITE", "Carross: S31 (colour list) and S227 (model pages) are one retailer"), "L-PC-COLOURTUBES": ("SINGLE_SOURCE", "Colour Tubes (AU)"), "L-PC-CROP": ("SAME_SITE", "CROP products sold via NonPaints (B6S03) and its guidance page (S03)")}
paint_lineages = [l for l in LINNOTE]
for lid, mem in sorted(lin_members.items()):
    cls = collections.Counter(next(r["source_class"] for r in SA if r["source_key"] == m) for m in mem).most_common(1)[0][0]
    codes = any(r["contains_vehicle_paint_codes"] == "YES" for r in SA if r["lineage_id"] == lid)
    rel = LINNOTE.get(lid, ("", ""))
    lg(row_type="NODE", id=lid, source_class=cls, members=";".join(mem)[:300], n_sources=len(mem), contains_vehicle_paint_codes="YES" if codes else "NO", counts_as_independent_paint_code_lineage="YES (but independence from unknown shared paint-database upstream is UNPROVEN)" if lid in paint_lineages and codes else "NO (does not carry vehicle paint codes)",
       relation=rel[0] or ("SINGLE_PUBLISHER_OR_CLASS_GROUP" if len(mem) > 1 else "SINGLE_SOURCE"), evidence=rel[1] or f"{len(mem)} source(s) grouped by publisher/site/source class; no copying between members is claimed or tested", oem_grade="NO")
for (a, b), r in sorted(lat.items()):
    if a not in PAINT_SRC or b not in PAINT_SRC: continue
    la, lb = PAINT_SRC[a][1], PAINT_SRC[b][1]
    sc, sn = int(r["shared_codes"]), int(r["shared_codes_with_identical_normalised_name"])
    if la == lb: rel = "SAME_LINEAGE"
    elif sc >= 10 and sn / max(sc, 1) >= 0.9: rel = "LIKELY_SHARED_UPSTREAM"
    elif sc >= 3 and sn / max(sc, 1) >= 0.6: rel = "HIGH_NAME_OVERLAP_UNPROVEN"
    else: rel = "INDEPENDENCE_UNPROVEN"
    lg(row_type="EDGE", id=f"{a}~{b}", source_class="retailer pair", members=f"{a};{b}", n_sources=2, contains_vehicle_paint_codes="YES", counts_as_independent_paint_code_lineage="", relation=rel, evidence=f"shared codes {sc}; identical normalised names {sn} ({r['identical_name_share']}); lineage {la} vs {lb}", oem_grade="NO")
lg(row_type="EDGE", id="Cartouch~Axalta (claim)", source_class="claimed origin", members="S30;B7S07", n_sources=2, contains_vehicle_paint_codes="YES", relation="CLAIMED_ORIGIN", evidence="Cartouch's baseline entry (S30) says its touch-up paints are Axalta-sourced; Axalta's public colour-tools page (B7S07) does not list BYD codes", oem_grade="NO")
LGF = ["row_type", "id", "source_class", "members", "n_sources", "contains_vehicle_paint_codes", "counts_as_independent_paint_code_lineage", "relation", "evidence", "oem_grade"]
wr("source_lineage_graph.csv", LG, LGF)
n_lineages_all = len({r["lineage_id"] for r in SA if r["source_class"] not in ("SEARCH_RECORD", "PENDING_PLACEHOLDER")})
n_code_lineages = len(paint_lineages) - 1 + 0   # L-PC-CROP counts; CHIPEX/PAINTCALCULATORS carry no usable codes
n_code_lineages = len([l for l in paint_lineages])
edge_rel = collections.Counter(r["relation"] for r in LG if r["row_type"] == "EDGE")

# =============================================================================================== B. STATE (current code records)
b6 = rd(f"{B6}/discovered_codes.csv"); b7 = rd(f"{B7}/discovered_codes.csv")
state = {}
for r in b6 + b7:
    if r["link_scope"] != "COLOUR_RECORD": continue
    state[(r["color_id"], r["paint_code"])] = dict(sources=set(r["source_ids"].split(";")), status=r["confidence_status"])
by_col = collections.defaultdict(dict)
for (cid, code), v in state.items(): by_col[cid][code] = v
col_status = {}
for cid in cols:
    cs = by_col.get(cid)
    if not cs: col_status[cid] = "UNVERIFIED"; continue
    veh = [c for c in cs if not REF_RE.fullmatch(c.upper())]
    stt = {v["status"] for v in cs.values()}
    col_status[cid] = "PAINT_SYSTEM_REFERENCE" if not veh else ("CONFLICTED" if "CONFLICTED" in stt else "POSSIBLE")

# finish tags per code from raw supplier strings
def finish_tags(text):
    t = text or ""; tags = set()
    if re.search(r"\bmatt?e?\b|¤MAT|哑光", t, re.I): tags.add("MATTE")
    if re.search(r"\bmet\b|met\.|metallic", t, re.I): tags.add("METALLIC")
    if re.search(r"\bpearl\b|\bp\.m\.?\b|\bpm\b|\bp\.x\b", t, re.I): tags.add("PEARL")
    if re.search(r"\bsolid\b", t, re.I): tags.add("SOLID")
    return tags
RAWP = []
for p in json.load(open(f"{B6}/raw/oematch_byd_products.json", encoding="utf-8")): RAWP.append(("B6S02", p["title"], p["url"]))
for p in json.load(open(f"{B7}/raw/dipyourcar_byd_products.json", encoding="utf-8")): RAWP.append(("B7S02", p["title"], p["url"]))
for p in json.load(open(f"{B6}/raw/crop_byd_products.json", encoding="utf-8")): RAWP.append(("B6S03", p["slug"].replace("-", " "), p["url"]))
def code_in_title(code, title):
    t = re.sub(r"\s*\|\s*(OEMatch|Luna OEM Basecoat).*$", "", title).upper()
    return bool(re.search(r"(^|\s)" + re.escape(code.upper().replace("-", " ") if "CROP" in title else code.upper()) + r"(\s|$)", t.replace(" - ", " ")))
code_finish = collections.defaultdict(set); code_support = collections.defaultdict(list)    # code -> tags; code -> support rows
for c in cands:
    if c["source_id"] in ("S33", "S34") or c["listing_level"] == "REJECTED": continue
    for tk in tokens(c["code_raw"]):
        code_finish[tk] |= finish_tags(c["names_raw"])
        code_support[tk].append(dict(source=c["source_id"], market=c["market"], level=c["listing_level"], model=c["model_as_listed"], year=c["year_as_listed"], names=c["names_raw"], tags=sorted(finish_tags(c["names_raw"]))))
for src, title, url in RAWP:
    t = re.sub(r"\s*\|\s*(OEMatch|Luna OEM Basecoat).*$", "", title).strip(); t = re.sub(r"\s+(Basecoat Paint|Complete Car Paint Kit|Touch Up Spray Paint)$", "", t, flags=re.I); t = re.sub(r"^(BYD|Byd)\s+", "", t)
    toks = t.split()
    if not toks: continue
    cd = toks[-1].upper() if re.fullmatch(r"[A-Za-z0-9]{1,5}(-[A-Za-z0-9]{1,3})?", toks[-1]) else (toks[0].upper() if re.fullmatch(r"[A-Za-z]\d{1,3}[cC]?", toks[0]) else "")
    if src == "B6S03": cd = (toks[0] + "-" + toks[1]).upper() if len(toks) > 1 and re.fullmatch(r"[a-zA-Z]", toks[0]) and re.fullmatch(r"\d{2}", toks[1]) else toks[0].upper()
    if not cd: continue
    name = " ".join(toks[:-1]) if cd == toks[-1].upper() else " ".join(toks[1:])
    code_finish[cd] |= finish_tags(name); code_support[cd].append(dict(source=src, market="US/EU retailer (no market stated)", level="name-only", model="", year="", names=name, tags=sorted(finish_tags(name))))

# =============================================================================================== C. PRIORITY COLOUR AUDIT
GROUPS = [("雪域白", "1", "Chinese name appears in OEMatch/DYC/CROP as 'Xue Yu Bai Pearl'; Carross/TUPF use English 'Snow White' (translation assumed)"),
          ("攀岩灰", "2", "Atto 3 / Yuan PLUS 'Boulder Grey'; Dolphin's 贝贝灰 shares the code HAN in several lists"),
          ("亚特兰蒂斯灰", "3", "Seal (and others) 'Atlantis Grey'; finish labels differ between codes"),
          ("苍穹蓝", "4", "e2 / Yuan EV 'Firmament Blue'; supplier code families differ by era")]
def codes_for(zh):
    cs = collections.Counter()
    for (cid, code), v in state.items():
        if cols[cid]["color_name_zh"] == zh: cs[code] += 1
    return cs
CA = []
conf7 = rd(f"{B7}/conflicts.csv")
for zh, rank, note in GROUPS:
    cc = codes_for(zh); recs = [c for c in cols.values() if c["color_name_zh"] == zh]
    modelsx = sorted({models[c["model_id"]]["model_key"] for c in recs}); yrs = sorted({years[c["model_year_id"]]["year"] for c in recs if c["model_year_id"]})
    cids = [x["conflict_id"] for x in conf7 if x["original_chinese_color_name"] == zh]
    alltags = collections.defaultdict(set)
    CA.append(dict(row_type="GROUP", priority=rank, colour_zh=zh, code="", competing_codes=" | ".join(sorted(cc)), catalog_records=len(recs), catalog_models=" | ".join(modelsx)[:200], catalog_model_years=" | ".join(yrs), conflict_ids=";".join(cids),
                   resolution_status="OPEN", note=note))
    for code in sorted(cc):
        sup = code_support.get(code, [])
        srcs_ = sorted({s["source"] for s in sup} | {x for (cid, cd), v in state.items() if cd == code and cols[cid]["color_name_zh"] == zh for x in v["sources"]})
        lins = sorted({PAINT_SRC[s][1] for s in srcs_ if s in PAINT_SRC})
        tags = sorted(code_finish.get(code, set())); markets = sorted({s["market"] for s in sup if s["market"]}); lv = collections.Counter(s["level"] for s in sup)
        yl = sorted({s["year"] for s in sup if s["year"]}); ml = sorted({s["model"] for s in sup if s["model"]})[:10]; nm = sorted({s["names"] for s in sup if s["names"]})[:6]
        cls_ = "PAINT_SYSTEM_REFERENCE" if REF_RE.fullmatch(code.upper()) else "VEHICLE_PAINT_CODE_CANDIDATE"
        # explanation tests
        expl = []
        if "MATTE" in tags: expl.append("FINISH: at least one supplier labels this code MATT" + (" (and others label it plain/metallic)" if len(tags) > 1 else ""))
        if yl and len(set(yl)) >= 1: expl.append("YEAR: supplier-listed ranges " + "; ".join(yl[:5]))
        if len(markets) > 1: expl.append("MARKET: lists span " + "; ".join(markets))
        if not expl: expl.append("none visible in the listings (no model/year/finish given)")
        CA.append(dict(row_type="CODE", priority=rank, colour_zh=zh, code=code, code_class=cls_, competing_codes=" | ".join(sorted(cc)), catalog_records=cc[code], supporting_sources=";".join(srcs_), supporting_lineages=" | ".join(lins) or "(reference only)",
                       n_lineages=len(lins), lineage_independence="NOT INDEPENDENT" if len(lins) <= 1 else "lineages differ but independence from a common paint-database upstream is UNPROVEN",
                       finish_tags_in_supplier_text="/".join(tags) or "unspecified", listing_levels="; ".join(f"{k}:{v}" for k, v in lv.items()), listing_markets=" | ".join(markets)[:120], listed_years=" | ".join(yl)[:80], listed_models=" | ".join(ml)[:120],
                       supplier_names=" | ".join(nm)[:200], explanation_tests=" || ".join(expl), official_or_label_evidence="NONE FOUND (Batch 10 search B10S03; Batches 5-9)", status="PAINT_SYSTEM_REFERENCE" if cls_.startswith("PAINT") else ("CONFLICTED" if any(col_status[cid] == "CONFLICTED" for (cid, cd) in state if cd == code and cols[cid]["color_name_zh"] == zh) else "POSSIBLE"),
                       resolution_status="OPEN"))
ASSESS = {"雪域白": "Competing codes W36C, WA2, WA8 and BYHB-00001. W36C is named for 'Xue Yu Bai Pearl' by CROP and for 'SNOW WHITE-MET.' by Carross (which lists W36C and WA2 together for Qin/Tang 2017-2024); WA2 is named for 'Xue Yu Bai Pearl' by OEMatch/DipYourCar (one lineage). TUPF lists all four for a SEVEN-name white group (Bright/Great/Polar/Snow/Snowfield/Summit/White Pearl), so it does not isolate 雪域白. BYHB-00001 is a reference-style identifier. No listing assigns W36C vs WA2 to different years, models or markets; Carross lists both for the same rows. Finish, year, market or trim therefore do NOT demonstrably explain the difference; two codes may also belong to one colour. OPEN.",
          "攀岩灰": "Competing HAN and HA4(+HAN). HA4 is tied to 时光灰/'TIME GREY' by two lineages (OEMatch/DipYourCar pinyin 'Shi Guang Hui'; TUPF 'TIME GREY'); Cartouch lists 'HAN, HA4' together on rows naming Harbour/Boulder/Time Grey, i.e. a name-lumped row. HAN is tied to 'Bei Bei Hui' (贝贝灰, OEMatch/DYC) AND to 'Boulder Grey / Climbing Grey' (TUPF), so one code spans two Chinese names. Plausible reading: 攀岩灰 = HAN and HA4 belongs to 时光灰 - but name-lumping, not a label, is all that supports it. OPEN.",
          "亚特兰蒂斯灰": "HB5 vs HB6. Every supplier text that carries a finish tag labels HB6 as MATT (Carross '¤MAT', TUPF 'ATLANTIS GREY MATT', OEMatch/DipYourCar 'Matt Metallic') and HB5 as plain metallic (CROP, OEMatch, TUPF). Finish therefore probably explains the difference, but the catalogue's Chinese 亚特兰蒂斯灰 records carry no finish evidence, and BYD's importer brochures give no finish wording. Whether a given Seal is HB5 or HB6 depends on its finish: UNKNOWN. Cartouch lists HB5, HB6 and H84C together for ATTO 3 2025 (name-lumped). OPEN.",
          "苍穹蓝": "Codes by era in Carross: BYL 2016-2017, F2/L32C 2015-2019 (Yuan EV 'FIRMAMENT BLUE-MET.'); TUPF e2: BYL;F2 for 'SKY BLUE, FIRMAMENT BLUE'; LAN (TUPF: 'AZUL SKY, CERULEAN BLUE, DOME BLUE, SKY BLUE' - 'Dome Blue' suggests 穹顶蓝, a different colour; OEMatch/DipYourCar pinyin 'Cang Qiong Lan' LAN); L-27 (OEMatch/DYC 'Cangqiong Blue Metallic' - an English name that was not linked to a catalogue colour record, so it is not counted among the competing codes above). Model year/generation may explain F2/L32C/BYL (2015-2019) versus LAN/L-27, but no supplier ties a code to a catalogue year inside 2019-2021 (e2). OPEN."}
for r in CA:
    if r["row_type"] == "GROUP": r["assessment"] = ASSESS[r["colour_zh"]]
CAF = ["row_type", "priority", "colour_zh", "code", "code_class", "competing_codes", "catalog_records", "catalog_models", "catalog_model_years", "conflict_ids", "supporting_sources", "supporting_lineages", "n_lineages", "lineage_independence",
       "finish_tags_in_supplier_text", "listing_levels", "listing_markets", "listed_years", "listed_models", "supplier_names", "explanation_tests", "official_or_label_evidence", "status", "resolution_status", "assessment", "note"]
wr("colour_conflict_audit.csv", CA, CAF)

# =============================================================================================== D. MODEL-YEAR CONSISTENCY (all colour records)
def nk(s): return re.sub(r"[^a-z0-9]", "", (s or "").lower())
model_keys = {}
for mid, m in models.items():
    ks = {nk(m["model_key"])} | {nk(a) for a in m["alt_names"].split(";") if a.strip()}
    model_keys[mid] = {k for k in ks if k}
def listed_matches(listed, mid):
    l = nk(re.sub(r"^BYD\s+", "", listed or "", flags=re.I))
    if not l or l in ("allmodels",): return False
    return any(k == l or (k.startswith(l) and len(l) >= 3 and k[len(l):] in ("dmi", "ev", "dm", "dmp", "dmiev", "plus", "pro")) for k in model_keys[mid])
def parse_range(y):
    m = re.findall(r"(20\d\d)", y or "")
    return (int(m[0]), int(m[-1])) if m else None
MY = []
unres = collections.Counter(); scope_c = collections.Counter(); status_c = collections.Counter(); gen_flags = collections.Counter()
for cid, c in cols.items():
    m = models[c["model_id"]]; y = years.get(c["model_year_id"], {}); g = gens.get(c["generation_id"], {})
    cs = by_col.get(cid, {}); veh = sorted(x for x in cs if not REF_RE.fullmatch(x.upper())); refs = sorted(x for x in cs if REF_RE.fullmatch(x.upper()))
    my = int(y["year"]) if y.get("year", "").isdigit() else None
    scopes = []; yr_flags = []; ranges = []
    for code in veh + refs:
        rows_ = [s for s in code_support.get(code, []) if s["level"] in ("model", "model+year") and listed_matches(s["model"], c["model_id"])]
        if rows_:
            scopes.append(f"{code}:MODEL_LISTED_APPROX"); scope_c["MODEL_LISTED_APPROX"] += 1
            rng = [parse_range(s["year"]) for s in rows_ if parse_range(s["year"])]
            if rng and my:
                inside = any(a <= my <= b for a, b in rng)
                yr_flags.append(f"{code}:{'YEAR_LISTED_MATCH' if inside else 'YEAR_OUTSIDE_LISTED_RANGE'}"); ranges.append(f"{code}:" + "/".join(sorted({s['year'] for s in rows_ if s['year']})))
            else: yr_flags.append(f"{code}:YEAR_UNKNOWN")
        else:
            scopes.append(f"{code}:NAME_PROPAGATED" ); scope_c["NAME_PROPAGATED"] += 1; yr_flags.append(f"{code}:YEAR_UNKNOWN")
    tags = sorted({t for code in cs for t in code_finish.get(code, set())})
    finish = "MATTE" if c["color_name_zh"].startswith("哑光") else "UNKNOWN"
    reasons = []
    if any("YEAR_OUTSIDE_LISTED_RANGE" in f for f in yr_flags): reasons.append("supplier year range excludes this model year")
    if len(veh) >= 2 and any(":MODEL_LISTED_APPROX" in s for s in scopes) and len({r_.split(":")[1] for r_ in ranges}) >= 2: reasons.append("codes carry different supplier year ranges")
    if "MATTE" in tags and len(veh) >= 2 and finish == "UNKNOWN": reasons.append("matte/gloss codes present but record finish unknown")
    if cs and not y.get("year"): reasons.append("no model year assigned to this colour record")
    genflag = "MULTI_GENERATION_MODEL_GENERATION_LABEL_EMPTY" if (g and g.get("generation_label", "") == "" and len([1 for gg in gens.values() if gg["model_id"] == c["model_id"]]) > 1) else ""
    gen_flags[genflag or "none"] += 1
    flag = "YES" if reasons else "NO"
    if cs and reasons: unres["records_with_candidates_flagged"] += 1
    for rr in reasons: unres[rr] += 1
    st_ = col_status[cid]; status_c[st_] += 1
    qs = []
    if st_ in ("POSSIBLE", "CONFLICTED"): qs.append("Which code (if any) is on a real vehicle of this model-year/market?")
    if st_ == "CONFLICTED": qs.append("Why do suppliers differ (finish, year, market, trim, or error)?")
    if st_ == "PAINT_SYSTEM_REFERENCE": qs.append("Which OEM code corresponds to this paint-system reference?")
    if st_ == "UNVERIFIED": qs.append("No code evidence of any kind: needs OEM/dealer record or label photo.")
    if flag == "YES": qs.append("Model-year applicability of the code is UNKNOWN/disputed.")
    ev = "NONE" if not cs else ("RETAILER_NAME_MATCH (" + ", ".join(sorted({s for v in cs.values() for s in v['sources']})) + ")")
    lin = sorted({PAINT_SRC[s][1] for v in cs.values() for s in v["sources"] if s in PAINT_SRC})
    MY.append(dict(color_id=cid, manufacturer="BYD Group", brand=brands[m["brand_id"]], model_id=m["model_id"], model=m["model_key"], chinese_model_name=m["name_zh"], generation_id=c["generation_id"], generation_label=g.get("generation_label", "") or g.get("source_row_name", ""),
                   generation_intro_year=g.get("intro_year", ""), generation_discontinued_year=g.get("discontinued_year", ""), model_year_id=c["model_year_id"], model_year=y.get("year", "") or "UNKNOWN", model_year_basis=(y.get("generation_assignment", "") + " / " + y.get("evidence_class", "")).strip(" /"),
                   market=c["market"] or "UNKNOWN", colour_name_zh=c["color_name_zh"], english_name_unofficial=c["name_en_gloss_unofficial"], pinyin_translit=" ".join(lazy_pinyin(re.sub(r"[^一-鿿]", "", c["color_name_zh"]))),
                   candidate_vehicle_codes=" | ".join(veh), paint_system_references=" | ".join(refs), finish_from_catalogue=finish, finish_labels_in_supplier_text="/".join(tags) or "none", code_support_scope="; ".join(scopes), code_year_applicability="; ".join(yr_flags) or "no candidate code",
                   supplier_year_ranges="; ".join(ranges), evidence_type=ev, source_lineages=" | ".join(lin), n_code_lineages=len(lin), status=st_, generation_flag=genflag, unresolved_year_difference=flag, unresolved_year_reasons="; ".join(reasons), unresolved_questions=" ".join(qs)))
MYF = ["color_id", "manufacturer", "brand", "model_id", "model", "chinese_model_name", "generation_id", "generation_label", "generation_intro_year", "generation_discontinued_year", "model_year_id", "model_year", "model_year_basis", "market", "colour_name_zh",
       "english_name_unofficial", "pinyin_translit", "candidate_vehicle_codes", "paint_system_references", "finish_from_catalogue", "finish_labels_in_supplier_text", "code_support_scope", "code_year_applicability", "supplier_year_ranges", "evidence_type",
       "source_lineages", "n_code_lineages", "status", "generation_flag", "unresolved_year_difference", "unresolved_year_reasons", "unresolved_questions"]
wr("model_year_consistency.csv", MY, MYF)
flagged = [r for r in MY if r["unresolved_year_difference"] == "YES"]; flagged_c = [r for r in flagged if r["status"] != "UNVERIFIED"]

# =============================================================================================== E. EVIDENCE REQUIREMENTS
conf9 = rd(f"{B9}/conflict_priority.csv"); grp9 = [r for r in conf9 if r["row_type"] == "GROUP"]
cnt_by_zh = collections.defaultdict(lambda: dict(rec=0, confl=0, core=0, score=0, codes=set(), tier="C"))
CORE = {"M020", "M026", "M028", "M016", "M002", "M036", "M128", "M129", "M007", "M039", "M034", "M049", "M133", "M019", "M027"}
for r in MY:
    if r["status"] in ("POSSIBLE", "CONFLICTED", "PAINT_SYSTEM_REFERENCE") and r["colour_name_zh"]:
        d = cnt_by_zh[r["colour_name_zh"]]; d["rec"] += 1; d["confl"] += (r["status"] == "CONFLICTED"); d["core"] += (r["model_id"] in CORE); d["codes"] |= {x for x in r["candidate_vehicle_codes"].split(" | ") if x}
for r in grp9:
    if r["colour_zh"] in cnt_by_zh:
        d = cnt_by_zh[r["colour_zh"]]; d["score"] = max(d["score"], int(r["score"])); d["tier"] = min(d["tier"], r["tier"])
FORCED = ["雪域白", "攀岩灰", "亚特兰蒂斯灰", "苍穹蓝"]
rank = sorted(cnt_by_zh.items(), key=lambda kv: (FORCED.index(kv[0]) if kv[0] in FORCED else 99, -kv[1]["score"], -kv[1]["confl"], -kv[1]["core"], kv[0]))
TOP = [k for k, _ in rank][:20]
REQ = []
STATUS_RULES = [("VERIFIED_OEM", "A document from a BYD (or other brand) service/OEM system or an official OEM document that shows VIN + colour name + colour code for one vehicle (screenshot, printout, stamped statement), obtained with the owner's consent", "Verbal answers; unofficial chats; retailer listings; formula numbers; colour-name matches"),
                ("VERIFIED_LABEL", "A photograph of a factory label attached to a vehicle, with the vehicle identity established (model, year, colour, and the VIN plate in the same frame or the owner's own hash), the label's authenticity plausible (in-situ context shots) and the code's meaning established (field name next to the code says colour/paint)", "Generic label examples; photos with no vehicle association; codes whose field meaning is unknown"),
                ("CORROBORATED", "At least two GENUINELY independent evidence lineages of OEM-grade or paint-maker-controlled origin agree on the code for the same model/year/market/finish (copies of one upstream count once)", "Several retailers (one upstream); sources agreeing on a name only"),
                ("PAINT_SYSTEM_REFERENCE", "An identifier that belongs to a paint system, formula or variant (e.g. BYHB-00001, formula numbers) - recorded and kept separate; may be linked to an OEM code only when a verified OEM code exists", "Treating it as the OEM code"),
                ("POSSIBLE", "A supplier-listed vehicle-code candidate with no contradicting candidate", "-"), ("CONFLICTED", "Sources (counted per lineage) list different code sets for the same colour", "Resolving by majority"), ("UNVERIFIED", "No code evidence", "-")]
for s, need, no in STATUS_RULES:
    REQ.append(dict(row_type="STATUS_RULE", rank="", colour_zh="", target=s, current_state="Batch 10: 0 records meet this" if s in ("VERIFIED_OEM", "VERIFIED_LABEL", "CORROBORATED") else "", minimum_evidence=need, does_not_count=no, evidence_route="", who_can_provide="", status_if_obtained=s))
SPEC = {"雪域白": ("(a) VIN-linked dealer record or label photo for Han EV, Qin PLUS (EV and DM-i), Song PLUS, Destroyer 05 - at minimum one 2020-2021 and one 2023-2025 vehicle of one model, to test whether W36C/WA2 split by year; (b) whether WA8 exists on any BYD vehicle; (c) paint-maker documentation stating what BYHB-00001 is", "A single vehicle record resolves only its own model-year; a split by year/model needs at least two vehicles per band"),
        "攀岩灰": ("A dealer record or label photo from one Atto 3 / Yuan PLUS in 攀岩灰 (HAN vs HA4) and one Dolphin in 贝贝灰 (HAN?), plus one 时光灰 car (HA4?) to settle the name-lumping", "Cartouch's lumped rows cannot be used"),
        "亚特兰蒂斯灰": ("Dealer record or label photo from one Seal in 亚特兰蒂斯灰, WITH the car's finish noted (gloss vs matte) and the year; ideally two cars (one each finish, if both exist) - an owner or BYD document stating whether a matte Atlantis Grey exists in China", "Retailer finish tags are labels, not evidence of what BYD produced"),
        "苍穹蓝": ("Dealer record or label photo from an e2 (2019-2021) in 苍穹蓝; plus any BYD document naming the colour's code era; separately clarify 穹顶蓝 vs 苍穹蓝 for the LAN listings", "Era inference from Carross year ranges is not enough")}
for i, zh in enumerate(TOP, 1):
    d = cnt_by_zh[zh]; sp = SPEC.get(zh)
    need = sp[0] if sp else f"One dealer record or label photo for a core-model car in {zh} (codes in dispute: {' | '.join(sorted(d['codes']))}); if models differ in year, one more car from a different year band"
    REQ.append(dict(row_type="COLOUR_REQUIREMENT", rank=i, colour_zh=zh, target=f"resolve {' vs '.join(sorted(d['codes']))}" if len(d["codes"]) > 1 else f"confirm {' '.join(sorted(d['codes']))}", current_state=f"{d['confl']} conflicted / {d['rec']} candidate colour records; Batch 9 score {d['score']} tier {d['tier']}",
                    minimum_evidence=need, does_not_count=(sp[1] if sp else "Retailer repetition; colour-name matches; verbal dealer statements"), evidence_route="BYD service-centre read-out with the owner's own VIN (dealer_request_*.md) or owner label photo (owner_request_*.md)",
                    who_can_provide="owner of a matching vehicle; BYD service centre", status_if_obtained="VERIFIED_OEM (dealer record) or VERIFIED_LABEL (label photo) for that vehicle only; conflict reviewed, not auto-closed"))
RQF = ["row_type", "rank", "colour_zh", "target", "current_state", "minimum_evidence", "does_not_count", "evidence_route", "who_can_provide", "status_if_obtained"]
wr("evidence_requirements.csv", REQ, RQF)

# =============================================================================================== STATS
STATS = dict(sources_audited=len(SA), source_classes=dict(cls_count), lineages_all=n_lineages_all, paint_code_lineages=n_code_lineages, paint_code_lineage_ids=paint_lineages, edge_relations=dict(edge_rel),
             colour_records=len(MY), status=dict(status_c), verified_oem=0, verified_label=0, corroborated=0, year_flag_rows=len(flagged), year_flag_rows_with_candidates=len(flagged_c), year_flag_reasons=dict(unres), generation_flags=dict(gen_flags), code_support_scope=dict(scope_c),
             top20=TOP, priority_groups=[g[0] for g in GROUPS], audit_rows=len(CA), requirement_rows=len(REQ), manufacturer_controlled_sources=sum(1 for r in SA if r["manufacturer_controlled"] == "YES"))
json.dump(STATS, open(f"{B10}/stats_batch10.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(STATS, ensure_ascii=False, indent=1))
