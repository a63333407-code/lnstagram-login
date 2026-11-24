#!/usr/bin/env python3
"""
Batch 8 - real OEM verification & Chinese data access (BYD Group).  Reproducible build.

No verification could be performed in this environment (needs a service-centre visit / physical label / a user-accepted
licence), so this batch (1) classifies identifiers with the 7-status scheme, (2) prepares and prioritises the field verification
(20 targets), (3) records which Chinese systems were reachable and what they do/do not provide.  Nothing is promoted.

Inputs (read-only): batch6/discovered_codes.csv, batch7/{discovered_codes,conflicts,sources,verification_sample_plan}.csv, catalog_union/*
Outputs: batch8/{discovered_codes.csv, sources.csv, conflicts.csv, verification_results.csv, stats_batch8.json}
(dealer_inquiry_zh.md, dealer_inquiry_en.md, baslac_manual_test_plan.md, REPORT_batch8.md, validation_report.md are written separately)
"""
import csv, os, re, json, collections

HERE = os.path.dirname(os.path.abspath(__file__)); U = f"{HERE}/catalog_union"; B6 = f"{HERE}/batch6"; B7 = f"{HERE}/batch7"; B8 = f"{HERE}/batch8"
TODAY = "2026-11-24"
os.makedirs(B8, exist_ok=True)


def rd(p):
    with open(p, encoding="utf-8", newline="") as f: return list(csv.DictReader(f))


def wr(name, rows, fields):
    with open(f"{B8}/{name}", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in fields})


STATUSES = ["VERIFIED_OEM", "VERIFIED_LABEL", "CORROBORATED", "PAINT_SYSTEM_REFERENCE", "POSSIBLE", "CONFLICTED", "UNVERIFIED"]
REF_RE = re.compile(r"BYH[A-Z]-\d+|BYD\d{2,}[A-Z0-9]*")

b6 = rd(f"{B6}/discovered_codes.csv"); b7 = rd(f"{B7}/discovered_codes.csv"); b7c = rd(f"{B7}/conflicts.csv"); b7s = rd(f"{B7}/sources.csv"); plan = rd(f"{B7}/verification_sample_plan.csv")

# ---------------------------------------------------------------------------------------------- current state = Batch 6 rows overlaid with Batch 7 changes
state = {}
for r in b6:
    if r["link_scope"] == "COLOUR_RECORD": k = ("C", r["color_id"], r["paint_code"])
    elif r["link_scope"] == "MODEL_LEVEL_LISTING": k = ("M", r["source_record_ids"], r["paint_code"])
    else: k = ("O", r["source_ids"], r["paint_code"], re.sub(r"[^a-z0-9]", "", r["english_color_name"].lower()))
    state[k] = dict(link_scope=r["link_scope"], brand=r["brand"], chinese_model_name=r["chinese_model_name"], international_model_name=r["international_model_name"], model_id=r["model_id"], production_year=r["production_year"],
                    color_id=r["color_id"], original_chinese_color_name=r["original_chinese_color_name"], english_color_name=r["english_color_name"], paint_code=r["paint_code"], source_ids=r["source_ids"], source_url=r["source_url"],
                    evidence_description=r["evidence_description"], status=r["confidence_status"], batch="6")
for r in b7:
    if r["link_scope"] == "COLOUR_RECORD": k = ("C", r["color_id"], r["paint_code"])
    else: k = ("O", r["source_ids"], r["paint_code"], re.sub(r"[^a-z0-9]", "", r["english_color_name"].lower()))
    state[k] = dict(link_scope=r["link_scope"], brand=r["brand"], chinese_model_name=r["chinese_model_name"], international_model_name=r["international_model_name"], model_id=r["model_id"], production_year=r["production_year"],
                    color_id=r["color_id"], original_chinese_color_name=r["original_chinese_color_name"], english_color_name=r["english_color_name"], paint_code=r["paint_code"], source_ids=r["source_ids"], source_url=r["source_url"],
                    evidence_description=r["evidence_description"], status=r["confidence_status"], batch="7")

# ---------------------------------------------------------------------------------------------- reference-driven conflicts (analysis only: statuses are NOT changed)
ref_driven_cids = set(); real_cids = set(); ref_driven_rows = []
for r in b7c:
    if not r["conflict_type"].startswith("SOURCES_DISAGREE"): continue
    sets = {s_: set(v) for s_, v in json.loads(r["values_in_conflict"]).items()}
    stripped = {s_: {c for c in v if not REF_RE.fullmatch(c)} for s_, v in sets.items()}
    same_after = len({frozenset(v) for v in stripped.values()}) == 1
    cids = [c for c in r["color_id"].split(";") if c]
    (ref_driven_cids if same_after else real_cids).update(cids)
    if same_after: ref_driven_rows.append((r, sets))

# ---------------------------------------------------------------------------------------------- discovered_codes.csv : PAINT_SYSTEM_REFERENCE reclassification
out = []
for k, s in sorted(state.items(), key=lambda kv: (kv[1]["brand"], kv[1]["model_id"], kv[1]["production_year"], kv[1]["original_chinese_color_name"], kv[1]["paint_code"])):
    if not REF_RE.fullmatch(s["paint_code"].upper()): continue
    out.append(dict(link_scope=s["link_scope"], brand=s["brand"], chinese_model_name=s["chinese_model_name"], international_model_name=s["international_model_name"], model_id=s["model_id"], production_year=s["production_year"],
                    color_id=s["color_id"], original_chinese_color_name=s["original_chinese_color_name"], english_color_name=s["english_color_name"], paint_code=s["paint_code"],
                    code_type="PAINT_SYSTEM_REFERENCE_IDENTIFIER", code_role="FORMULA_SYSTEM_REFERENCE (not a vehicle paint code)", paint_manufacturer_system="not stated by supplier (supplier/paint-system style 'BYH?-nnnnn' format)",
                    source_ids=s["source_ids"], source_url=s["source_url"], evidence_description=s["evidence_description"] + " Identifier format ('BYH?-digits') differs from OEM-style short codes; treated as a paint-system/supplier reference, never as an OEM code.",
                    confidence_status="PAINT_SYSTEM_REFERENCE", batch7_status=s["status"], reference_driven_conflict=("YES" if s["color_id"] in ref_driven_cids else ("NO" if s["color_id"] else "n/a")),
                    notes="Reclassified in Batch 8 (identifier class). The colour record's own status is unchanged. Not verified by any OEM source."))
for i, r in enumerate(out, 1): r["record_id"] = f"B8D{i:05d}"
FD = ["record_id", "link_scope", "brand", "chinese_model_name", "international_model_name", "model_id", "production_year", "color_id", "original_chinese_color_name", "english_color_name", "paint_code", "code_type", "code_role",
      "paint_manufacturer_system", "source_ids", "source_url", "evidence_description", "confidence_status", "batch7_status", "reference_driven_conflict", "notes"]
wr("discovered_codes.csv", out, FD)

# ---------------------------------------------------------------------------------------------- verification targets (20) from the Batch 7 plan
def find(model_name, colour, years_contains=None):
    for r in plan:
        if r["international_model_name"] == model_name and r["original_chinese_color_name"] == colour: return r
    raise KeyError((model_name, colour))
TARGETS = [  # (model, colour, hypothesis, backup)
    ("Seal", "亚特兰蒂斯灰", "HB5 vs HB6: is HB6 the MATTE variant (OEMatch/DipYourCar label HB6 'Matt'), or are both used on gloss cars? Record gloss/matte and year on the car.", "paint-chip match; label photo"),
    ("Han EV", "雪域白", "W36C vs WA2 vs WA8; is BYHB-00001 a paint-system reference? Record model year (2020-2023 in catalog).", "BASF/AkzoNobel chip back (code printed on chip)"),
    ("Qin Plus EV", "雪域白", "W36C vs WA2 vs WA8 for 2021-2025 Qin PLUS EV.", "chip match"),
    ("Qin Plus DM-i", "雪域白", "Same disagreement on the DM-i body; also check whether code differs between 2021 and 2023+.", "chip match"),
    ("Song Plus EV", "雪域白", "W36C vs WA2 vs WA8 for Song PLUS EV (2023-2025).", "chip match"),
    ("Song Plus DM-i", "雪域白", "W36C vs WA2 vs WA8 for Song PLUS DM-i (2021-2025).", "chip match"),
    ("Yuan Plus", "滑雪白", "Atto 3 / Yuan PLUS white: W46C vs WAC (Ski White).", "label photo; chip match"),
    ("Yuan Plus", "攀岩灰", "Atto 3 grey: HAN vs HA4/HAN (alias group 'Boulder Grey').", "chip match"),
    ("Yuan Plus", "探险绿", "Atto 3 green: LAG vs UA6.", "chip match"),
    ("Yuan Plus", "跑酷红", "Atto 3 red: LAQ vs RA5.", "chip match"),
    ("Seal", "玄空黑", "00AN vs AA1 (Cosmos Black): one code or two (years/markets)?", "label photo"),
    ("Seal", "风卷草绿", "LAD vs UY.", "chip match"),
    ("Qin Plus DM-i", "时光灰", "HA4 (only one lineage family lists it) vs matte HC2 - confirm gloss code and year range 2021-2026.", "chip match"),
    ("Song Plus EV", "德兰黑", "B1 vs B7822 vs DBU - numeric-style and short codes; which is the factory colour code?", "label photo"),
    ("Song Plus DM-i", "苍烟色", "HAZ appears only in the OEMatch/DipYourCar lineage - test whether it is real.", "chip match"),
    ("Han EV", "玄空黑", "00AN vs AA1 across 2020-2026.", "label photo"),
    ("Dolphin", "贝贝灰", "HAN listed alone yet flagged CONFLICTED (HA4/HAN alias group).", "chip match"),
    ("e2", "苍穹蓝", "BYL vs F2 vs LAN (2019-2021).", "label photo"),
    ("Destroyer 05", "雪域白", "W36C vs WA2 vs WA8 for Destroyer 05 (2022-2025).", "chip match"),
    ("U9", "阿盖尔紫", "Yangwang U9 brand-coverage probe: CA7 vs LYE (separate Yangwang service channel).", "label photo"),
]
conf_by_name = collections.defaultdict(list)
for r in b7c: conf_by_name[r["original_chinese_color_name"]].append(r["conflict_id"])
VR = []
for i, (model, colour, hyp, backup) in enumerate(TARGETS, 1):
    p = find(model, colour)
    VR.append(dict(target_id=f"T{i:02d}", priority=i, priority_group=p["priority_group"], brand=p["brand"], model_id=p["model_id"], international_model_name=p["international_model_name"], chinese_model_name=p["chinese_model_name"],
                   original_chinese_color_name=colour, model_years_in_catalog=p["model_years_in_catalog"], candidate_codes=p["candidate_codes"], current_status=p["current_status"], independent_lineages=p["independent_lineages"],
                   conflict_ids=";".join(conf_by_name.get(colour, [])), hypothesis_to_test=hyp,
                   preferred_route="BYD service centre reads the factory colour from the VIN build record (dealer_inquiry_zh.md / dealer_inquiry_en.md)" if p["brand"] != "Yangwang" else "Yangwang service centre (separate network; contact not verified)",
                   backup_route=backup, evidence_required="documentary: screen/printout/photo showing VIN + code + colour name (dealer system) OR label photo with VIN plate in frame",
                   verification_status="PENDING_FIELD_EVIDENCE", status_after_field_evidence="", verified_code="", evidence_type="", evidence_file_ref_private="", observer_role="", observation_date="", respray_history="",
                   resolves_conflict="NO - nothing performed in Batch 8", notes="Targets are checked ONLY with a VIN the researcher owns or has the owner's written permission to use."))
VF = ["target_id", "priority", "priority_group", "brand", "model_id", "international_model_name", "chinese_model_name", "original_chinese_color_name", "model_years_in_catalog", "candidate_codes", "current_status", "independent_lineages",
      "conflict_ids", "hypothesis_to_test", "preferred_route", "backup_route", "evidence_required", "verification_status", "status_after_field_evidence", "verified_code", "evidence_type", "evidence_file_ref_private", "observer_role",
      "observation_date", "respray_history", "resolves_conflict", "notes"]
wr("verification_results.csv", VR, VF)

# ---------------------------------------------------------------------------------------------- conflicts.csv : carry Batch 7 (all OPEN) + new analysis rows
CF = []
for r in b7c:
    x = dict(r); x["carried_from"] = r["conflict_id"]; x["batch8_status"] = "OPEN - unchanged; no genuine evidence obtained"; CF.append(x)
agg = collections.OrderedDict()
for r, sets in ref_driven_rows:
    k = (r["original_chinese_color_name"], json.dumps({s_: sorted(v) for s_, v in sorted(sets.items())}, ensure_ascii=False))
    a = agg.setdefault(k, dict(cids=[], conf_ids=[], brands=set(), models=set())); a["cids"] += [c for c in r["color_id"].split(";") if c]; a["conf_ids"].append(r["conflict_id"]); a["brands"].add(r["brand"]); a["models"].add(r["model"])
n = 0
for (nm, sig), a in agg.items():
    n += 1
    CF.append(dict(conflict_id=f"B8C{n:04d}", conflict_type="REFERENCE_DRIVEN_CONFLICT_CANDIDATE", subject_scope=f"{len(a['cids'])} colour record(s) whose disagreement exists only because a paint-system reference (BYH?-nnnnn) is listed beside vehicle codes",
                   brand="; ".join(sorted(a["brands"])), model="; ".join(sorted(a["models"]))[:200], color_id=";".join(a["cids"]), original_chinese_color_name=nm, values_in_conflict=sig, sources_involved="S31;S32;S226;S227;B6S02;B7S02;B6S03",
                   status_effect="NONE - statuses preserved (user rule: conflicts stay until genuine evidence resolves them)", resolution="OPEN - candidate for reclassification once a verified OEM code exists for this colour", note=f"After removing BYH?-nnnnn tokens the supplier code sets agree. Parent Batch 7 conflict ids: {';'.join(a['conf_ids'])}.",
                   carried_from="", batch8_status="OPEN - flagged only"))
CFF = ["conflict_id", "conflict_type", "subject_scope", "brand", "model", "color_id", "original_chinese_color_name", "values_in_conflict", "sources_involved", "status_effect", "resolution", "note", "carried_from", "batch8_status"]
wr("conflicts.csv", CF, CFF)

# ---------------------------------------------------------------------------------------------- sources.csv
SF = ["source_id", "title", "url_or_query", "publisher_or_type", "evidence_tier", "accessed", "retrieval_method", "access_result", "contains_paint_codes", "usable_as_oem_verification", "notes"]
NS = []
def ns(sid, title, url, pub, tier, how, res, codes, oemv, notes): NS.append(dict(source_id=sid, title=title, url_or_query=url, publisher_or_type=pub, evidence_tier=tier, accessed=TODAY, retrieval_method=how, access_result=res, contains_paint_codes=codes, usable_as_oem_verification=oemv, notes=notes))
ns("B8S01", "Baslac Formula Finder Online - licensing and non-disclosure agreement (disclaimer image; NOT accepted)", "https://formula-finder.baslac.com/ ; https://formula-finder.baslac.com/disclaimer/text/B_en.jpg ; https://formula-finder.baslac.com.au/",
   "Paint manufacturer online tool (BASF Coatings GmbH trademark) behind a click-through", "PRIORITY_3 (licensed paint database)", "curl of landing page (HTTP 200) and of the public disclaimer image; image viewed; no form submitted", "Landing = disclaimer form with 'I agree'/'I disagree'; tool itself NOT accessed",
   "NO", "NO", "Terms read (not accepted): 'baslac' is a registered trademark of BASF Coatings GmbH; BASF colour mixing formulas remain BASF property and are a company secret, provided only for non-exclusive, non-transferable use WITH BASF coating products; may not be sold, leased or passed to third parties; downloading/saving requires a separate written licence; integration into third-party software is not permitted. Consequence: formulas shown there must not be copied into this research database; any manual test is the user's decision and should record only whether BYD exists and which inputs the tool accepts.")
ns("B8S02", "Baslac (百事利) colour-solution pages: Formula Finder, e-finder star, chip system", "https://www.baslac.com/zh-apac/colors ; https://www.baslac.com/zh-apac/baslac-e-finder-star ; https://www.baslac.com/zh-apac/baslac-effective-color-finder", "Paint manufacturer website (Chinese, APAC)", "PRIORITY_3",
   "curl + text", "HTTP 200; read", "NO", "NO", "Quotes: Formula Finder is an online database of all vehicle manufacturers' mixing formulas, '超过14万种配方' (colours page) / '125000多种' (e-finder page), continuously updated 'with the latest colours and variants'; chip set contains 'the basic original paint chips of all vehicle manufacturers' sorted by colour. Does not state BYD is included or which input fields exist. Page footer reads '© Surventis 2026' (operator relationship to BASF not established from these pages; the disclaimer states baslac is a BASF Coatings GmbH trademark).")
ns("B8S03", "BYD China after-sales service page (售后服务)", "https://www.byd.com/cn/after-sales-service", "BYD official website", "PRIORITY_1 (OEM statement)", "curl + text", "HTTP 200; read", "NO", "NO",
   "States: 王朝网与海洋网共2300+售后服务网点 (dynasty + ocean networks, 2300+ after-sales outlets); official service hotline 950858 ('全年365天，全天24小时'); footer: 客户服务热线 950858; store finders /cn/dynasty-home/find-store and /cn/ocean-home/find-store; BYD App; 精诚管家 online service. No statement about retrieving paint information by VIN.")
ns("B8S04", "BYD China user-manual download index", "https://www.byd.com/cn/user-manual", "BYD official website", "PRIORITY_1", "curl + parse embedded config", "HTTP 200; manual list is loaded dynamically (not enumerated)", "NO", "NO",
   "Brand groups offered: 王朝 (Dynasty), 海洋 (Ocean), 其他车型. Note on page: '部分车型暂不支持用户手册下载，请前往王朝APP或海洋APP认证车主后查看' - some manuals only inside the app after owner authentication. No Denza/Yangwang/Fangchengbao group on this index; footer links to tengshiauto.com, yangwangauto.com, fangchengbao.com.")
ns("B8S05", "Fangchengbao (方程豹) official site and manual page", "https://www.fangchengbao.com/ ; https://www.fangchengbao.com/user-manual", "Brand official website", "PRIORITY_1 (OEM site)", "curl", "Home HTTP 200 read; /user-manual HTTP 200 but JavaScript app (no static list); /sell.html connection reset",
   "NO", "NO", "Site config lists '官方热线 950859', after-sales page /sell.html, store finder /store.html and '下载用户手册' (user-manual). No manual PDF located; paint information not found.")
ns("B8S06", "Denza (腾势) and Yangwang (仰望) official sites", "https://www.tengshiauto.com/ ; https://www.yangwangauto.com/ (URLs as linked from byd.com footer)", "Brand official websites", "PRIORITY_1 (OEM site)", "curl", "Connection reset by the agent proxy (ws_closed_mid_exchange) - NOT ACCESSED", "UNKNOWN", "NO",
   "Existence of the sites is taken from BYD's own footer links, not from a successful fetch. Their manual, hotline and paint-service information is unverified.")
ns("B8S07", "17vin open API documentation - VIN query and parts list (docs 3001, 3002, 3003, 5105)", "https://www.17vin.com/doc/3001.html ; /doc/3002.html ; /doc/3003.html ; /doc/5105.html", "Chinese parts-data API vendor documentation", "PRIORITY_B (Chinese data ecosystem)", "curl + text + key extraction", "HTTP 200; read",
   "NO", "NO", "Documented JSON fields for VIN lookup: brand, build_date, epc, epc_cn, epc_id, gonggao_no, model_year_from_vin, model_list, model_original_epc_list, my_model_std_id ... Parts list adds is_fit_for_this_vin. No colour/paint field appears in any of the four documents. Conclusion limited to the PUBLISHED schema; real responses were not tested.")
ns("B8S08", "Search record - Chinese repair-data platforms, OEM parts catalogues (EPC), licensed paint systems (PPG/艾仕得/新劲/立邦/雅图/东来), Linghui (领汇), Denza/Yangwang manuals",
   "比亚迪 EPC 电子配件目录 授权 查询; 汽修 维修资料平台 比亚迪 维修手册 车身修复 涂装; PPG OR 艾仕得 OR 新劲 OR 立邦 OR 雅图 汽车修补漆 中国 配方查询; 领汇 比亚迪 官网 用户手册; 腾势/仰望 官网 用户手册 下载", "web search record", "n/a", "web search (standard)",
   "NOT_FOUND - no public BYD EPC entry point, no authorised BYD repair-data portal, no Chinese paint-system BYD lookup page, no Linghui (领汇) source, no Denza/Yangwang manual PDFs", "NO", "NO",
   "BYD's page offers only an anti-counterfeit code check for genuine parts (not a catalogue). A GitHub repository 'BYDcar' claims BYD repair manuals bought from resale channels; provenance and legality unverified - NOT used. Chinese repair platforms did not surface.")
ns("B8S09", "BYD owner's-manual front matter - official customer-service number", "https://www.byd.com/material/domestic-official/user-manual/dynasty/汉L EV用户手册1104.pdf ; .../汉DM-i智驾版-长续航版 用户手册20260410.pdf", "BYD official manuals (PDF, read in Batch 7)", "PRIORITY_1", "pdftotext (Batch 7 copies)", "read",
   "NO", "NO", "Both manuals print '比亚迪官方客服电话：400-830-3666' and the website https://www.bydauto.com.cn (Han L EV manual line 48-49; Han DM-i line 44-45).")
# carry Batch 7 sources (all)
for r in b7s:
    x = dict(r); x["notes"] = "[carried from Batch 7] " + r["notes"]; NS.append(x)
wr("sources.csv", NS, SF)

# ---------------------------------------------------------------------------------------------- stats
cs = collections.Counter(s["status"] for s in state.values() if s["link_scope"] == "COLOUR_RECORD")
STATS = dict(statuses_defined=STATUSES, state_rows=len(state), reference_rows=len(out), reference_rows_by_scope=dict(collections.Counter(r["link_scope"] for r in out)), reference_codes=sorted({r["paint_code"] for r in out}),
             reference_driven_colour_records=len(ref_driven_cids), real_conflict_colour_records=len(real_cids), reference_driven_conflict_groups=n, conflicts_carried=len(b7c), conflict_rows=len(CF),
             targets=len(VR), target_groups=dict(collections.Counter(r["priority_group"] for r in VR)), targets_conflicted=sum(1 for r in VR if r["current_status"] == "CONFLICTED"), verified_total=0, sources=len(NS),
             colour_status_state_by_row=dict(cs))
json.dump(STATS, open(f"{B8}/stats_batch8.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(STATS, ensure_ascii=False, indent=1))
