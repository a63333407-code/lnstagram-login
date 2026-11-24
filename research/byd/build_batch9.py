#!/usr/bin/env python3
"""
Batch 9 - field verification & official dealer evidence (BYD Group).  Reproducible build.

NO calls were made, NO dealer was visited, NO label was photographed, NO VIN was used.  This builder therefore produces:
  * dealer_contact_results.csv     - the call workflow with every answer UNANSWERED / NOT_CALLED
  * field_verification_cases.csv   - T01 and T02 workflows, all steps PENDING
  * evidence_register.csv          - what is verified (access facts), what is pending, what cannot be stored
  * conflict_priority.csv          - transparent prioritisation of the 107 conflicted colour records / 39 conflict rows
No status is upgraded; no conflict is resolved.

Inputs (read-only): catalog_union/*, batch7/{conflicts,verification_sample_plan}.csv, batch8/{verification_results,conflicts}.csv
"""
import csv, os, re, json, math, collections

HERE = os.path.dirname(os.path.abspath(__file__)); U = f"{HERE}/catalog_union"; B7 = f"{HERE}/batch7"; B8 = f"{HERE}/batch8"; B9 = f"{HERE}/batch9"
os.makedirs(B9, exist_ok=True)
TODAY = "2026-11-24"


def rd(p):
    with open(p, encoding="utf-8", newline="") as f: return list(csv.DictReader(f))


def wr(name, rows, fields):
    with open(f"{B9}/{name}", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader()
        for r in rows: w.writerow({k: r.get(k, "") for k in fields})


brands = {b["brand_id"]: b["name"] for b in rd(f"{U}/brands_all.csv")}
models = {m["model_id"]: m for m in rd(f"{U}/models_all.csv")}
years = {y["model_year_id"]: y for y in rd(f"{U}/model_years_all.csv")}
cols = {c["color_id"]: c for c in rd(f"{U}/factory_colors_all.csv")}
trims = rd(f"{U}/trims_all.csv")
b7c = rd(f"{B7}/conflicts.csv"); b8c = rd(f"{B8}/conflicts.csv"); b8v = rd(f"{B8}/verification_results.csv")
on_sale_models = {t["model_id"] for t in trims if t["on_sale_status"].startswith("on sale")}

# ------------------------------------------------------------------------------------------------ 1. dealer_contact_results.csv
QS = [(1, "授权服务店能否凭车架号（VIN）查询这辆车的原厂车漆色号？", "Can an authorised service centre retrieve the original factory paint code from a vehicle's VIN?"),
      (2, "这个信息是否记录在车辆的出厂/生产档案（build record）里？", "Is this information held in the vehicle's factory / build record?"),
      (3, "服务店能否以书面形式提供准确的原厂车漆色号？", "Can the dealer provide the exact OEM paint code in writing?"),
      (4, "车主能否拿到官方记录、系统截图或打印的确认件？", "Can the owner receive an official record, screenshot or printed confirmation?"),
      (5, "这个流程是否因车型、生产年份或品牌（王朝/海洋/腾势/仰望/方程豹）而不同？", "Does the process differ by model, production year or brand?")]
CH = [("K01", "BYD official customer-service hotline", "950858", "REQUIRED", "BYD after-sales page https://www.byd.com/cn/after-sales-service (re-read 2026-11-24): '通过比亚迪公司官方服务热线950858联系：全年365天，全天24小时提供服务'", "EV01"),
      ("K02", "BYD customer-service phone printed in owner's manuals", "400-830-3666", "REQUIRED", "'比亚迪官方客服电话：400-830-3666' in the front matter of the Han L EV and Han DM-i owner's manuals (Batch 7 copies, line re-checked 2026-11-24)", "EV02"),
      ("K03", "Fangchengbao official hotline", "950859", "REQUIRED", "Fangchengbao site configuration 'offcialTelephone: 950859 官方热线' (https://www.fangchengbao.com/ and /store.html, re-fetched 2026-11-24)", "EV03"),
      ("K04", "Denza footer customer-service number", "950856", "OPTIONAL", "Denza site footer '客服电话：950856' beside '©腾势汽车销售服务有限公司' (https://www.tengshiauto.com/, fetched 2026-11-24); config also contains template residue from the Fangchengbao site, so treat as unconfirmed until a call or second page confirms it", "EV04"),
      ("K05", "Yangwang footer contact number", "950855", "OPTIONAL", "Yangwang site footer '联系我们：950855' (https://www.yangwangauto.com/, fetched 2026-11-24); a booking-failure message in another config instead names 400-039-6666 - which is current is unconfirmed", "EV05")]
DC = []
for cid, name, num, req, src, ev in CH:
    for qn, zh, en in QS:
        DC.append(dict(contact_id=cid, channel_name=name, phone_number=num, channel_requirement=req, number_provenance=src, evidence_ref=ev, question_no=qn, question_zh=zh, question_en=en,
                       call_status="NOT_CALLED", call_datetime="", caller_role="", operator_name_or_id="", answer_category="UNANSWERED", answer_verbatim="", written_follow_up_offered="", reference_number="", answer_reliability="n/a",
                       status_effect="none - a verbal statement verifies no paint code; unanswered questions stay unanswered", notes="No call was made by the researcher. Fill only from a call actually completed by the user or an authorised researcher."))
DF = ["contact_id", "channel_name", "phone_number", "channel_requirement", "number_provenance", "evidence_ref", "question_no", "question_zh", "question_en", "call_status", "call_datetime", "caller_role", "operator_name_or_id",
      "answer_category", "answer_verbatim", "written_follow_up_offered", "reference_number", "answer_reliability", "status_effect", "notes"]
wr("dealer_contact_results.csv", DC, DF)

# ------------------------------------------------------------------------------------------------ 2. field_verification_cases.csv
OUTCOMES = "DOC_CODE_PROVIDED | DOC_NAME_ONLY | DOC_FORMULA_NUMBER_ONLY | VERBAL_ONLY | REFUSED_POLICY | SYSTEM_HAS_NO_FIELD | REQUIRES_OWNER_PRESENCE | REQUIRES_OTHER_DEPARTMENT | NOT_ATTEMPTED"
EFFECT = ("DOC_CODE_PROVIDED -> VERIFIED_OEM if the document shows VIN + code + colour name from a BYD service system/OEM document; DOC_NAME_ONLY -> no code evidence (record 'system has no code field'); "
          "DOC_FORMULA_NUMBER_ONLY -> PAINT_SYSTEM_REFERENCE; VERBAL_ONLY -> no upgrade; REFUSED_POLICY / SYSTEM_HAS_NO_FIELD / REQUIRES_* -> record exact reason and wording, no upgrade")
STEPS = [(1, "Obtain the vehicle owner's written consent to use their own vehicle and VIN for this check; if the researcher is not the owner, the owner must attend or authorise in writing."),
         (2, "Record vehicle identity WITHOUT the VIN: model, model year, contract colour name, 合格证 body-colour class, gloss or matte, respray history (ask the owner)."),
         (3, "Compute the SHA-256 of the VIN locally and keep only the hash and the first 9 characters (WMI+VDS) in research files; keep the full VIN, photos and screenshots in a private store (Batch 7 privacy method, vin_evidence_template.csv)."),
         (4, "Make the VIN-free policy call(s) in dealer_contact_results.csv (K01/K02) and record answers verbatim; unanswered stays UNANSWERED."),
         (5, "At the service centre (or by phone with the owner present) ask questions A-F of dealer_inquiry_zh.md / dealer_inquiry_en.md: build record, paint-code field, written confirmation, paint system, repair history."),
         (6, "Ask for written confirmation of the factory paint code: system screenshot, printout or stamped statement with VIN, colour name and code visible together."),
         (7, "If a document is provided: store privately, transcribe the code exactly (letters, digits, hyphens), note gloss/matte and any variant, note whether the number is a factory colour code or a refinish formula number."),
         (8, "If the centre cannot provide it: record the exact reason (policy / no field / needs another department / needs owner presence), the wording used, staff role, date, and any reference number."),
         (9, "Optionally inspect the car for a printed colour label (location undocumented by BYD) and photograph it with the VIN plate in the same frame."),
         (10, "Classify with the seven-status rules; log the result in this file; do NOT change any catalogue conflict until the record has been reviewed.")]
CASES = []
for tid, case in (("T01", "C-T01"), ("T02", "C-T02")):
    v = next(r for r in b8v if r["target_id"] == tid)
    base = dict(case_id=case, target_id=tid, brand=v["brand"], model=v["international_model_name"], chinese_model_name=v["chinese_model_name"], colour_zh=v["original_chinese_color_name"], catalog_model_years=v["model_years_in_catalog"],
                candidate_codes=v["candidate_codes"], catalog_status=v["current_status"], conflict_ids=v["conflict_ids"], hypothesis=v["hypothesis_to_test"])
    CASES.append(dict(base, row_type="CASE", step_no="", step_description="", case_status="PENDING", owner_consent="NOT_OBTAINED", requires_owner_participation="YES - a real vehicle, its owner's consent and VIN",
                      vin_sha256_hex="", vin_wmi_vds_first_9="", vehicle_model_year="", gloss_or_matte="", contract_colour_name="", certificate_colour_class="", respray_history="", centre_name_city="", responder_role="", observation_date="",
                      allowed_outcomes=OUTCOMES, outcome_code="", outcome_wording="", reason_if_not_provided="", evidence_type="", evidence_file_ref_private="", status_if_document=EFFECT, resulting_status="(unchanged) " + v["current_status"],
                      notes="PENDING: no consent, VIN, call, visit or document exists. Nothing in this row is a test result."))
    for n, d in STEPS:
        CASES.append(dict(base, row_type="STEP", step_no=n, step_description=d, case_status="PENDING", step_status="NOT_PERFORMED", notes="Step not performed; requires owner/user participation." if n in (1, 2, 3, 5, 6, 7, 8, 9) else "Step not performed."))
CF = ["row_type", "case_id", "target_id", "brand", "model", "chinese_model_name", "colour_zh", "catalog_model_years", "candidate_codes", "catalog_status", "conflict_ids", "hypothesis", "step_no", "step_description", "step_status", "case_status", "owner_consent",
      "requires_owner_participation", "vin_sha256_hex", "vin_wmi_vds_first_9", "vehicle_model_year", "gloss_or_matte", "contract_colour_name", "certificate_colour_class", "respray_history", "centre_name_city", "responder_role", "observation_date",
      "allowed_outcomes", "outcome_code", "outcome_wording", "reason_if_not_provided", "evidence_type", "evidence_file_ref_private", "status_if_document", "resulting_status", "notes"]
wr("field_verification_cases.csv", CASES, CF)

# ------------------------------------------------------------------------------------------------ 3. evidence_register.csv
ER = []
def er(**k): ER.append(k)
er(evidence_id="EV01", category="ACCESS_FACT (verified)", description="BYD official after-sales page lists hotline 950858 (24 h, 365 days), 2,300+ Dynasty/Ocean outlets, store finders, BYD App, 精诚管家", source="https://www.byd.com/cn/after-sales-service", date=TODAY, obtained_by="researcher (fetched and read)", verification_level="FETCHED_AND_READ", supports_status_upgrade="NO", classification_effect="none - contact/process information, no paint code")
er(evidence_id="EV02", category="ACCESS_FACT (verified)", description="Owner's manuals (Han L EV, Han DM-i) print 'BYD official customer-service phone 400-830-3666' and https://www.bydauto.com.cn", source="https://www.byd.com/material/domestic-official/user-manual/dynasty/汉L EV用户手册1104.pdf ; .../汉DM-i智驾版-长续航版 用户手册20260410.pdf", date="read Batch 7; line re-checked in the local copy 2026-11-24", obtained_by="researcher", verification_level="READ_IN_LOCAL_COPY", supports_status_upgrade="NO", classification_effect="none")
er(evidence_id="EV03", category="ACCESS_FACT (verified)", description="Fangchengbao site configuration: 官方热线 950859; after-sales page /sell.html; store finder /store.html; '下载用户手册' link; manual page is a JavaScript app with no static PDF list", source="https://www.fangchengbao.com/ ; https://www.fangchengbao.com/store.html ; https://www.fangchengbao.com/user-manual", date=TODAY, obtained_by="researcher", verification_level="FETCHED_AND_READ (/sell.html connection-reset in Batch 8, not re-read)", supports_status_upgrade="NO", classification_effect="none")
er(evidence_id="EV04", category="ACCESS_FACT (partly verified)", description="Denza site footer shows 客服电话 950856 and '©腾势汽车销售服务有限公司'; store finder claims 400+ service outlets in 180+ cities; no manual-download link found on the home configuration; /support/service-support.html not reachable (connection reset)", source="https://www.tengshiauto.com/ ; https://www.tengshiauto.com/store.html", date=TODAY, obtained_by="researcher", verification_level="FETCHED_AND_READ (home, store); service-support NOT ACCESSED", supports_status_upgrade="NO", classification_effect="none", notes="Footer config also carries Fangchengbao template residue; number needs confirmation.")
er(evidence_id="EV05", category="ACCESS_FACT (partly verified)", description="Yangwang site: footer '联系我们 950855'; booking-failure text elsewhere names 400-039-6666 (two configurations); '下载用户手册' page exists ('仰望车型手册下载') but is a JavaScript app with no static PDF list", source="https://www.yangwangauto.com/ ; https://www.yangwangauto.com/user-manual", date=TODAY, obtained_by="researcher", verification_level="FETCHED_AND_READ", supports_status_upgrade="NO", classification_effect="none")
er(evidence_id="EV06", category="ACCESS_FACT (verified, Batch 8)", description="BYD domestic manual index offers Dynasty, Ocean and 'other models'; some manuals only in the Dynasty/Ocean App after owner authentication", source="https://www.byd.com/cn/user-manual", date="2026-11-24 (Batch 8)", obtained_by="researcher", verification_level="FETCHED_AND_READ", supports_status_upgrade="NO", classification_effect="none")
er(evidence_id="EV07", category="OEM_STATEMENT (verified, Batch 6)", description="BYD says 精诚钣喷 uses AkzoNobel, BASF and Donglai refinish paints with '原厂数据、原厂配方'; not stated whether VIN lookup returns a paint code", source="https://www.byd.com/cn/after-sales-service/maintenance-protection", date="2026-11-24 (Batch 6)", obtained_by="researcher", verification_level="FETCHED_AND_READ", supports_status_upgrade="NO", classification_effect="none - supports plausibility of the dealer route only")
er(evidence_id="EV08", category="ABSENCE_FINDING", description="No public BYD, Denza, Yangwang or Fangchengbao document stating that a service centre can retrieve factory paint information by VIN; no owner-manual PDF located for Denza, Yangwang, Fangchengbao; no Linghui (领汇) official source found", source="Batch 8/9 searches and page reads (see unresolved_questions.md)", date=TODAY, obtained_by="researcher", verification_level="SEARCH_AND_PAGE_READ (negative)", supports_status_upgrade="NO", classification_effect="none", notes="Absence of a public statement is not evidence that the lookup does not exist.")
er(evidence_id="EV09", category="LICENSING_RESTRICTION", description="Baslac Formula Finder agreement (read, not accepted): formulas are BASF property/secret, only for use with BASF products, not to be passed on or saved without a separate written licence, no integration into third-party software", source="https://formula-finder.baslac.com/disclaimer/text/B_en.jpg", date="2026-11-24 (Batch 8)", obtained_by="researcher (public image viewed)", verification_level="READ_NOT_ACCEPTED", supports_status_upgrade="NO", classification_effect="Formula data CANNOT be stored in this project; only user-supplied factual answers may be recorded")
er(evidence_id="EP01", category="PENDING_FIELD_EVIDENCE", description="Hotline calls K01-K05: NOT MADE. All 25 question rows UNANSWERED.", source="dealer_contact_results.csv", date="", obtained_by="(none)", verification_level="NOT_OBTAINED", supports_status_upgrade="NO", classification_effect="none", notes="Requires the user or an authorised researcher to make the calls.")
er(evidence_id="EP02", category="PENDING_FIELD_EVIDENCE", description="T01 (Seal 亚特兰蒂斯灰) dealer document / label photo: NOT OBTAINED. No owner consent, VIN or visit exists.", source="field_verification_cases.csv C-T01", date="", obtained_by="(none)", verification_level="NOT_OBTAINED", supports_status_upgrade="NO", classification_effect="stays CONFLICTED (HB5 | HB6)", notes="Requires a Seal owner's participation.")
er(evidence_id="EP03", category="PENDING_FIELD_EVIDENCE", description="T02 (Han EV 雪域白) dealer document / label photo: NOT OBTAINED. No owner consent, VIN or visit exists.", source="field_verification_cases.csv C-T02", date="", obtained_by="(none)", verification_level="NOT_OBTAINED", supports_status_upgrade="NO", classification_effect="stays CONFLICTED (BYHB-00001 | W36C | WA2 | WA8)", notes="Requires a Han EV owner's participation.")
er(evidence_id="EP04", category="PENDING_FIELD_EVIDENCE", description="Baslac Formula Finder factual test (8 questions): NOT PERFORMED by the user. If performed, record only the factual answers and the permission restrictions - no formula content.", source="batch8/baslac_manual_test_plan.md", date="", obtained_by="(none)", verification_level="NOT_OBTAINED", supports_status_upgrade="NO", classification_effect="none", notes="Terms acceptance is the user's decision; the researcher will not accept terms or create accounts.")
ERF = ["evidence_id", "category", "description", "source", "date", "obtained_by", "verification_level", "supports_status_upgrade", "classification_effect", "notes"]
wr("evidence_register.csv", ER, ERF)

# ------------------------------------------------------------------------------------------------ 4. conflict_priority.csv
CORE = {"M020", "M026", "M028", "M016", "M002", "M036", "M128", "M129", "M007", "M039", "M034", "M049", "M133", "M019", "M027"}   # user's priority series (proxy for popularity; the repo has no sales data)
gm = next((r for r in b7c if r["conflict_type"] == "GLOSS_VS_MATTE_CODE_PAIR"), None)
matte_codes = set()
if gm:
    for part in gm["values_in_conflict"].split("|"):
        m_ = re.search(r"gloss ([A-Z0-9/\-]+) vs matt ([A-Z0-9/\-]+)", part)
        if m_: matte_codes |= set(m_.group(1).split("/")) | set(m_.group(2).split("/"))
REF_RE = re.compile(r"BYH[A-Z]-\d+|BYD\d{2,}[A-Z0-9]*")
rows_g = []; rec_rows = []
def score_group(r):
    cids = [c for c in r["color_id"].split(";") if c]
    sets = json.loads(r["values_in_conflict"]) if r["conflict_type"].startswith("SOURCES_DISAGREE") else None
    codes = set()
    if sets:
        for v in sets.values(): codes |= set(v)
    else: codes = set(x.strip() for x in r["values_in_conflict"].split("/") if x.strip())
    veh = {c for c in codes if not REF_RE.fullmatch(c)}
    mids = {cols[c]["model_id"] for c in cids}; bids = {models[m]["brand_id"] for m in mids}
    P = 3 if mids & CORE else 1
    comp = len(veh); C = 0 if comp < 2 else (1 if comp == 2 else (2 if comp == 3 else 3))
    M = 2 if (veh & matte_codes or any(cols[c]["color_name_zh"].startswith("哑光") for c in cids)) else 0
    cur = any(m in on_sale_models for m in mids)
    R = 3 if ("B2" in bids and cur) else (2 if "B2" in bids else 1)
    G = 2 if r["conflict_type"] == "SOURCES_DISAGREE_NOT_NESTED" else (1 if r["conflict_type"] == "SOURCES_DISAGREE_NESTED" else 0)
    S = min(3, math.ceil(len(cids) / 10)) if cids else 0
    tot = 2 * P + C + M + R + G + S
    return dict(cids=cids, codes=sorted(codes), veh=sorted(veh), mids=sorted(mids), P=P, C=C, M=M, R=R, G=G, S=S, tot=tot, cur=cur)
scored = {}
for r in b7c:
    if r["conflict_type"].startswith("SOURCES_DISAGREE") or r["conflict_type"] == "MULTI_CODE_ALIAS_GROUP":
        scored[r["conflict_id"]] = score_group(r)
tots = sorted(s["tot"] for s in scored.values() if True)
TIER_A = 14; TIER_B = 11
def tier(t): return "A" if t >= TIER_A else ("B" if t >= TIER_B else "C")
for r in b7c:
    cid = r["conflict_id"]; s = scored.get(cid)
    if s:
        route = ("BYD service centre build-record read via VIN (Dynasty/Ocean network; on-sale model)" if s["R"] == 3 else ("BYD service centre read (older model years; owner of such a car needed)" if s["R"] == 2 else "Separate brand network (Denza/Yangwang/Fangchengbao): hotline known, process untested"))
        rows_g.append(dict(row_type="GROUP", priority_id="", conflict_id=cid, conflict_type=r["conflict_type"], colour_zh=r["original_chinese_color_name"], models="; ".join(models[m]["model_key"] for m in s["mids"])[:160], n_colour_records=len(s["cids"]),
                           candidate_codes=" | ".join(s["codes"]), distinct_vehicle_codes=len(s["veh"]), popularity_proxy=s["P"], competition=s["C"], matte_gloss=s["M"], route_plausibility=s["R"], genuine_disagreement=s["G"], size=s["S"], score=s["tot"],
                           tier=tier(s["tot"]), colour_status="CONFLICTED" if r["conflict_type"].startswith("SOURCES_DISAGREE") else "POSSIBLE (alias group; competing candidates)", evidence_route=route,
                           rationale=f"2xpopularity({s['P']}) + competition({s['C']}) + matte/gloss({s['M']}) + route({s['R']}) + genuine({s['G']}) + size({s['S']}) = {s['tot']}", status_effect="none - not resolved; no majority vote; shared-upstream sites not counted as extra evidence"))
    else:
        cross = {"RETAILER_LINEAGE": "Cross-cutting: rule that shared-upstream retailers count once (already enforced)", "COLOUR_CLASS_VS_CODE": "Cross-cutting limit (certificate colour class cannot pick a code)", "LABEL_LOCATION": "Cross-cutting: needs label photographs on real cars", "FINISH_TYPE": "Needs a car or an OEM spec; low priority",
                 "NAME_MATCH_REVIEW": "Human review of romanisation differences; low priority", "GLOSS_VS_MATTE_CODE_PAIR": "Hypothesis informing T01 (HB5/HB6) and matte pairs HA4/HC2, UAM/UAN, LAT/LAV", "CODE_VS_CODE_SAME_NAME": "Named conflict; covered by its component GROUP rows"}.get(r["conflict_type"], "")
        rows_g.append(dict(row_type="CROSS_CUTTING", conflict_id=cid, conflict_type=r["conflict_type"], colour_zh=r["original_chinese_color_name"], models=r["model"][:80], n_colour_records="", candidate_codes=r["values_in_conflict"][:200], tier="n/a", colour_status="n/a",
                           evidence_route=cross, rationale="not scored: not a single colour/code disagreement", status_effect="none - carried open"))
# assign priority ids by score among GROUP rows
gl = sorted([r for r in rows_g if r["row_type"] == "GROUP"], key=lambda r: (-r["score"], -r["n_colour_records"], r["conflict_id"]))
for i, r in enumerate(gl, 1): r["priority_id"] = f"P{i:02d}"
tier_by_conf = {r["conflict_id"]: (r["tier"], r["priority_id"]) for r in gl}
for r in b7c:
    if not r["conflict_type"].startswith("SOURCES_DISAGREE"): continue
    for cid in [c for c in r["color_id"].split(";") if c]:
        c = cols[cid]; m = models[c["model_id"]]
        rec_rows.append(dict(row_type="COLOUR_RECORD", priority_id=tier_by_conf[r["conflict_id"]][1], conflict_id=r["conflict_id"], conflict_type=r["conflict_type"], colour_zh=c["color_name_zh"], models=m["model_key"], color_id=cid,
                             model_year=years.get(c["model_year_id"], {}).get("year", ""), brand=brands[m["brand_id"]], tier=tier_by_conf[r["conflict_id"]][0], colour_status="CONFLICTED", candidate_codes=" | ".join(scored[r["conflict_id"]]["codes"]),
                             status_effect="none - unchanged"))
PF = ["row_type", "priority_id", "conflict_id", "conflict_type", "colour_zh", "models", "n_colour_records", "color_id", "model_year", "brand", "candidate_codes", "distinct_vehicle_codes", "popularity_proxy", "competition", "matte_gloss", "route_plausibility",
      "genuine_disagreement", "size", "score", "tier", "colour_status", "evidence_route", "rationale", "status_effect"]
out = sorted(gl, key=lambda r: r["priority_id"]) + [r for r in rows_g if r["row_type"] == "CROSS_CUTTING"] + rec_rows
wr("conflict_priority.csv", out, PF)

STATS = dict(contact_rows=len(DC), channels=len(CH), calls_made=0, cases=2, case_rows=len(CASES), evidence_rows=len(ER), conflict_groups_scored=len(gl), tier_counts=dict(collections.Counter(r["tier"] for r in gl)), cross_cutting=sum(1 for r in rows_g if r["row_type"] == "CROSS_CUTTING"),
             colour_records_mapped=len(rec_rows), colour_records_by_tier=dict(collections.Counter(r["tier"] for r in rec_rows)), top=[(r["priority_id"], r["conflict_id"], r["colour_zh"], r["models"][:40], r["score"], r["tier"]) for r in sorted(gl, key=lambda r: r["priority_id"])[:10]],
             matte_codes=sorted(matte_codes), verified_total=0)
json.dump(STATS, open(f"{B9}/stats_batch9.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(STATS, ensure_ascii=False, indent=1))
