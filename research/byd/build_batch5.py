#!/usr/bin/env python3
"""
Batch 5 - BYD Group OEM paint-code verification.  Reproducible build.

Reads ONLY the frozen Batch 1-4 union tables (research/byd/catalog_union/*.csv) and writes the Batch 5
deliverables to research/byd/batch5/.  It never modifies Batch 1-4 files and never touches the application.

Evidence policy (see REPORT_batch5.md):
  * A status other than POSSIBLE/CONFLICTED/UNVERIFIED is assigned ONLY when a row exists in
    batch5/manual_evidence_input (hand-entered, with page + quote) -- none exist after the Batch 5 search.
  * Retailer repetition is never corroboration (no retailer cites an OEM source).
  * Supplier codes are written to `supplier_candidate_code`; `oem_paint_code` stays NULL unless VERIFIED_*.

Usage: python3 build_batch5.py
"""
import csv, os, collections, datetime, re

HERE = os.path.dirname(os.path.abspath(__file__))
U = os.path.join(HERE, "catalog_union")
OUT = os.path.join(HERE, "batch5")
os.makedirs(OUT, exist_ok=True)
TODAY = "2026-11-24"          # access date of the Batch 5 research session


def code_tokens(raw):
    """Supplier code_raw can hold several codes ('00AN;AA1', '00AN, AA1, AN'); split into tokens."""
    return {t.strip().upper() for t in re.split(r"[;,/]+|\s+\|\s+", raw or "") if t.strip()}


def rd(name):
    with open(os.path.join(U, name), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def wr(name, rows, fields):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


brands = {b["brand_id"]: b["name"] for b in rd("brands_all.csv")}
models = {m["model_id"]: m for m in rd("models_all.csv")}
gens = {g["generation_id"]: g for g in rd("generations_all.csv")}
years = {y["model_year_id"]: y for y in rd("model_years_all.csv")}
cols = {c["color_id"]: c for c in rd("factory_colors_all.csv")}
links = rd("color_paint_code_links_all.csv")
cands = {c["candidate_id"]: c for c in rd("paint_code_candidates_all.csv")}
srcs = {s["source_id"]: s for s in rd("sources_all.csv")}
pcs = {p["paint_code_id"]: p for p in rd("paint_codes_all.csv")}

# ----------------------------------------------------------------------------------------------
# Priority series (user's research order).  model_ids resolved from the Batch 4 catalog.
PRIORITY = [
    (1, "Seal", ["M020"]), (2, "Dolphin", ["M026"]), (3, "Seagull", ["M028"]),
    (4, "Atto 3 / Yuan PLUS", ["M016"]), (5, "Han", ["M002", "M036", "M128", "M129"]),
    (6, "Qin PLUS", ["M007", "M039"]), (7, "Song PLUS", ["M034", "M049", "M133"]),
    (8, "Destroyer 05", ["M019"]), (9, "e2", ["M027"]),
]
prio = {}
for rank, name, ids in PRIORITY:
    for mid in ids:
        assert mid in models, mid
        prio[mid] = (rank, name)

# ----------------------------------------------------------------------------------------------
# Manual evidence input.  Intentionally EMPTY: no OEM document or label with a paint code for an exact
# vehicle was found.  Any future entry must carry model_year_id/color_id, code, source, page and quote.
MANUAL_EVIDENCE = []   # list of dicts: color_id, code, status(VERIFIED_OEM|VERIFIED_LABEL|CORROBORATED), source_id, page, quote

# ----------------------------------------------------------------------------------------------
# Status per colour record
bycol = collections.defaultdict(list)
for l in links:
    bycol[l["color_id"]].append(l)

col_info = {}
for cid, c in cols.items():
    ls = bycol.get(cid, [])
    codes = sorted({l["oem_code"] for l in ls})
    persrc = collections.defaultdict(set); allsrc = collections.defaultdict(set)
    for l in ls:
        for pid in l["candidate_ids"].split(";"):
            cd = cands.get(pid)
            if cd and l["oem_code"].upper() in code_tokens(cd["code_raw"]):
                persrc[cd["source_id"]].add(l["oem_code"])
                allsrc[cd["source_id"]] |= code_tokens(cd["code_raw"])
    sets = {frozenset(v) for v in allsrc.values()}
    if not ls:
        status, ambiguity = "UNVERIFIED", "NO_CANDIDATE_CODE"
    elif len(sets) > 1:
        status, ambiguity = "CONFLICTED", "SOURCES_DISAGREE"
    elif len(codes) > 1:
        status, ambiguity = "POSSIBLE", "MULTI_CODE_ALIAS_GROUP"
    else:
        status, ambiguity = "POSSIBLE", "SINGLE_CODE"
    col_info[cid] = dict(status=status, ambiguity=ambiguity, codes=codes, persrc={k: sorted(v) for k, v in allsrc.items()})

for ev in MANUAL_EVIDENCE:   # none; kept so the rule is explicit and testable
    col_info[ev["color_id"]]["status"] = ev["status"]

# ----------------------------------------------------------------------------------------------
# oem_paint_codes.csv  (one row per colour-record x candidate code; supplier code kept separate from OEM code)
FIELDS_CODES = ["record_id", "brand", "model_id", "model", "model_name_zh", "generation_id", "generation", "model_year_id",
                "model_year_or_range", "market_colour_record", "supplier_markets", "color_id", "color_name_zh_original",
                "color_name_en_unofficial", "supplier_published_names", "oem_paint_code", "supplier_candidate_code",
                "evidence_status", "code_ambiguity", "source_ids", "source_titles", "source_urls", "document_page_section",
                "evidence_description", "date_accessed", "confidence_and_limitations", "link_id", "priority_rank"]
rows = []
for i, l in enumerate(sorted(links, key=lambda x: x["link_id"]), 1):
    c = cols[l["color_id"]]; m = models[c["model_id"]]; ci = col_info[l["color_id"]]
    cl = [cands[p] for p in l["candidate_ids"].split(";") if p in cands and l["oem_code"].upper() in code_tokens(cands[p]["code_raw"])]
    sids = sorted({x["source_id"] for x in cl})
    y = years.get(c["model_year_id"], {}); g = gens.get(c["generation_id"], {})
    yr = y.get("year", "")
    dates = sorted({x["fetched_utc"][:10] for x in cl if x["fetched_utc"]})
    levels = sorted({f'{x["source_id"]}:{x["listing_level"]}' for x in cl})
    names = sorted({x["names_raw"] for x in cl if x["names_raw"]})
    mk = sorted({x["market"] for x in cl if x["market"]})
    desc = (f"Retailer/supplier catalog lists code {l['oem_code']} for a name matched to this colour ({l['link_basis']}). "
            f"Listing level(s): {', '.join(levels)}. Not an OEM document; not a vehicle label.")
    lim = (f"Status {ci['status']}. Matching is by colour NAME, not by VIN/vehicle; listing is model-level or name-only so model-year "
           f"applicability is not confirmed. Retailers cite no OEM source, so agreement between them is not corroboration. "
           f"Audited link confidence: {l['confidence_audited']}.")
    if not c["model_year_id"]:
        lim += " No model year is assigned to this colour record in the Batch 4 baseline (model-level observation)."
    if ci["ambiguity"] == "SOURCES_DISAGREE":
        lim += f" Suppliers disagree on the code set for this colour: {ci['persrc']}."
    elif ci["ambiguity"] == "MULTI_CODE_ALIAS_GROUP":
        lim += f" Suppliers list several codes ({', '.join(ci['codes'])}) for one alias group of names; which applies to this exact vehicle is unknown."
    rows.append(dict(
        record_id=f"B5P{i:04d}", brand=brands.get(m["brand_id"], ""), model_id=m["model_id"], model=m["model_key"], model_name_zh=m["name_zh"],
        generation_id=c["generation_id"], generation=g.get("generation_label", "") or g.get("source_row_name", ""), model_year_id=c["model_year_id"],
        model_year_or_range=yr, market_colour_record=c["market"], supplier_markets=" | ".join(mk), color_id=c["color_id"],
        color_name_zh_original=c["color_name_zh"], color_name_en_unofficial=c["name_en_gloss_unofficial"],
        supplier_published_names=" | ".join(names), oem_paint_code="", supplier_candidate_code=l["oem_code"],
        evidence_status=ci["status"], code_ambiguity=ci["ambiguity"], source_ids=";".join(sids),
        source_titles=" | ".join(srcs[s]["title"] for s in sids if s in srcs), source_urls=" ".join(sorted({x["evidence_url"] for x in cl})),
        document_page_section="; ".join(levels) + " (web catalog page; no document page number)", evidence_description=desc,
        date_accessed=" | ".join(dates), confidence_and_limitations=lim, link_id=l["link_id"],
        priority_rank=prio.get(c["model_id"], ("", ""))[0]))
rows.sort(key=lambda r: (int(r["priority_rank"]) if r["priority_rank"] != "" else 99, r["model_id"], r["color_id"], r["supplier_candidate_code"]))
wr("oem_paint_codes.csv", rows, FIELDS_CODES)
n_link_status = collections.Counter(r["evidence_status"] for r in rows)

# ----------------------------------------------------------------------------------------------
# source_register.csv
SR = []
def sr(**k): SR.append(k)
F_SR = ["b5_source_id", "title", "url_or_query", "publisher_or_type", "evidence_tier", "accessed", "retrieval_method", "access_result",
        "contains_exact_vehicle_paint_code", "usable_as_verification", "baseline_source_id", "notes"]
MAN = [  # (id, title, url, pdf_pages, nameplate pdf page, printed page, creation, text)
    ("B5S01", "BYD ATTO 3 2024 Owner's Manual - Left-hand Drive - EN (Owner Manual for SC2ES European)", "https://www.byd.com/material/byd-site/eu/support/service/manual/20250812/BYD%20ATTO%203%202024%20Owner's%20Manual-Left-hand%20Drive-EN.pdf", 215, 205, "204"),
    ("B5S02", "Owner Manual for SC2EGZ Middle East BYD ATTO 3 EN", "https://www.byd.com/material/byd-site/mea-public/after-sales/manual/middle-east/atto-3/Owner%20Manual%20for%20SC2EGZ%20Middle%20East%20BYD%20ATTO%203%20EN.pdf", 202, 193, "192"),
    ("B5S03", "BYD DOLPHIN SURF Owner's Manual - RHD", "https://www.byd.com/material/__EU/byd-site/byd-uk/manuals/owner/01-BYD%20DOLPHIN%20SURF%20Owner%27s%20Manual-RHD.pdf", 196, 187, "186"),
    ("B5S04", "ATTO 3 EVO Owner's Manual - Left-hand Drive - 20260327 - EN (Owner Manual for SC2E European LHD)", "https://www.byd.com/material/seal-2026/ATTO%203%20EVO%20Owner's%20Manual-Left-hand%20Drive-20260327-EN.pdf", 250, 238, ""),
    ("B5S05", "ATTO 2 LONG RANGE Owner's Manual - Right-hand Drive - 20251114 - EN", "https://www.byd.com/material/byd-atto-2-ev-long-range/ATTO%202%20LONG%20RANGE%20Owner%27s%20Manual-Right-hand+Drive-20251114-EN.pdf", 224, 208, ""),
    ("B5S06", "BYD ETP3 Owner's Manual - Left-hand Drive - EN", "https://www.byd.com/material/byd-site/eu/support/service/manual/20241107/etp-3/BYD%20ETP3%20Owner's%20Manual-Left-hand%20Drive-EN.pdf", 180, 169, ""),
    ("B5S07", "BYD ATTO3 2022 Owner's Manual (20251004 EN)", "https://www.byd.com/material/BYD%20ATTO3%202022%20Owner's%20Manual-20251004-EN.pdf", 199, 191, "190"),
]
for sid, t, u, npg, npp, prt in MAN:
    sr(b5_source_id=sid, title=t, url_or_query=u, publisher_or_type="BYD official website - owner's manual PDF (OEM document)", evidence_tier="PRIORITY_1_OEM_DOCUMENTATION (owner's manual, not a repair manual)",
       accessed=TODAY, retrieval_method="curl download + pdftotext full text; nameplate page rendered", access_result="HTTP 200; full document read",
       contains_exact_vehicle_paint_code="NO", usable_as_verification="NO - documents label location/contents only; no colour-code table",
       baseline_source_id="", notes=f"{npg} PDF pages; 'Vehicle Nameplate' on PDF page {npp}" + (f" (printed page {prt})" if prt else "") + ". Text search for 'paint code', 'colour code', 'body colour', 'paint colour' found no colour-code field or table.")
sr(b5_source_id="B5S08", title="byd.ev-manual.com (third-party BYD repair-manual/DTC portal)", url_or_query="https://byd.ev-manual.com/", publisher_or_type="Third-party commercial portal (provenance of content unverified)",
   evidence_tier="NOT_USABLE_AS_OEM (provenance unverified, paid)", accessed=TODAY, retrieval_method="curl landing page only", access_result="HTTP 200; landing page lists models/DTC lookup; no paint-code content visible without payment",
   contains_exact_vehicle_paint_code="UNKNOWN", usable_as_verification="NO", baseline_source_id="", notes="Claims 'official-level' content; claim not verifiable. Paywalled content was not accessed or circumvented.")
sr(b5_source_id="B5S09", title="GitHub BYDcar/BYDRepairManual and BYDcar/BYDPackagesByChip1 (third-party mirrors, reported to hold dealer repair-manual PDFs)", url_or_query="https://github.com/BYDcar/BYDRepairManual ; https://github.com/BYDcar/BYDPackagesByChip1",
   publisher_or_type="Third-party GitHub repositories (unknown provenance)", evidence_tier="NOT_USABLE_AS_OEM", accessed=TODAY, retrieval_method="curl",
   access_result="HTTP 403 - GitHub access to these repositories is not enabled for this session", contains_exact_vehicle_paint_code="UNKNOWN", usable_as_verification="NO",
   baseline_source_id="", notes="Not accessed. Not pursued further: mirrored dealer-restricted manuals would be of unverifiable provenance and probably unauthorised copies; they could at best be a secondary lead, never VERIFIED_OEM without attributable origin.")
sr(b5_source_id="B5S10", title="I-CAR OEM Technical Information Matrix (US collision-repair information availability)", url_or_query="https://rts.i-car.com/oem-information/oem-technical-information-matrix.html",
   publisher_or_type="Industry body index (USA-only)", evidence_tier="PRIORITY_1 pointer only", accessed=TODAY, retrieval_method="web search snippet; BYD row not inspected",
   access_result="Search returned the matrix and its legend but no BYD-specific entry", contains_exact_vehicle_paint_code="NO", usable_as_verification="NO", baseline_source_id="",
   notes="Matrix indexes whether OEM repair information exists; it contains no paint codes. BYD is not sold in the US passenger-car market.")
for sid, t, q, note in [
    ("B5S11", "Search: Axalta Cromax / Standox / Spies Hecker / PPG / Glasurit / BASF BYD colour library", "web search 'Axalta Cromax BYD library', 'PPG BYD library', 'Glasurit OR Standox OR Spies Hecker BYD colour code formula'", "No public BYD colour-library page located; paint-manufacturer colour databases are login-gated and not indexed."),
    ("B5S12", "Search: BYD genuine touch-up paint / official accessories part numbers", "web search 'BYD genuine touch up paint pen part number official accessories colour code'", "No BYD-issued touch-up part list found. Retailer pens (CROP, Greendrive) are aftermarket; a retailer reference such as 3701388181349 is a retailer product number, not an OEM code."),
    ("B5S13", "Search: Chinese-language OEM paint-code sources (比亚迪 车漆/色号/铭牌/车身修复手册)", "web search 比亚迪 车身修复手册 颜色代码 / 车漆代码 / 铭牌 车身颜色 代码", "Only Autohome gallery pages and a dealer re-paint colour-mismatch article returned; no code table."),
    ("B5S14", "Search: owner forums / Reddit / Whirlpool photos of BYD paint-code labels", "web search 'BYD Atto 3 paint code label photo door jamb forum', 'BYD Seal OR Dolphin paint code sticker where is it'", "No forum post with a photographed label tied to an exact vehicle found.")]:
    sr(b5_source_id=sid, title=t, url_or_query=q, publisher_or_type="Search record (no source document)", evidence_tier="n/a", accessed=TODAY, retrieval_method="web search",
       access_result="NOT_FOUND", contains_exact_vehicle_paint_code="NO", usable_as_verification="NO", baseline_source_id="", notes=note)
sr(b5_source_id="B5S15", title="CROP / NonPaints and Chipex guidance on where the colour code sticker is (search snippets)", url_or_query="https://www.nonpaints.com/en/color-code/byd ; https://chipex.co.uk/brands/byd/m9/..",
   publisher_or_type="Retailer guidance (generic across brands)", evidence_tier="PRIORITY_3_RETAILER", accessed=TODAY, retrieval_method="web search snippet (page not read in full)",
   access_result="Snippet only", contains_exact_vehicle_paint_code="NO", usable_as_verification="NO", baseline_source_id="S03;S13",
   notes="CROP: sticker under bonnet, on driver's door / B-pillar / door frame, or service booklet. Chipex: driver's door jamb or engine compartment. Generic; not BYD model-specific.")
for sid in ("S29", "S30", "S31", "S32", "S226", "S227", "S34", "S33"):
    s = srcs[sid]
    sr(b5_source_id=sid, title=s["title"], url_or_query=s["url"], publisher_or_type=s["source_type"], evidence_tier="PRIORITY_3_RETAILER" if sid not in ("S34", "S33") else ("WEAK_FORUM" if sid == "S34" else "REJECTED"),
       accessed="Batches 2-4 (2026-11-24 for rows with fetched_utc)", retrieval_method="carried over unchanged from Batch 2-4", access_result="see baseline",
       contains_exact_vehicle_paint_code="CANDIDATE CODES ONLY (supplier code, not OEM-confirmed)" if sid in ("S29", "S30", "S31", "S32", "S226", "S227") else "NO",
       usable_as_verification="NO - POSSIBLE at most" if sid in ("S29", "S30", "S31", "S32", "S226", "S227") else "NO", baseline_source_id=sid, notes=s["notes"])
wr("source_register.csv", SR, F_SR)

# ----------------------------------------------------------------------------------------------
# vehicle_label_evidence.csv
F_LE = ["evidence_id", "brand", "model_scope", "catalog_model_id", "model_year_or_range", "market", "document_or_source_title", "source_url", "page", "evidence_type",
        "label_location_stated", "label_contents_stated", "paint_or_colour_field_listed", "paint_code_value_observed", "vehicle_identity_linked_to_label", "visually_inspected_page",
        "evidence_status", "date_accessed", "limitations"]
LE = []
def le(**k): LE.append(k)
le(evidence_id="B5L01", brand="BYD", model_scope="ATTO 3 (EU, LHD, 2024 manual)", catalog_model_id="M016", model_year_or_range="2024 manual edition (document dated 2025-05)", market="Europe",
   document_or_source_title="BYD ATTO 3 2024 Owner's Manual - Left-hand Drive - EN", source_url=MAN[0][2], page="PDF p.205 (printed 204), 'Vehicle Nameplate'", evidence_type="OEM owner's manual",
   label_location_stated="Vehicle nameplate is located under the right B-pillar.", label_contents_stated="Not listed in this edition.", paint_or_colour_field_listed="NOT STATED", paint_code_value_observed="",
   vehicle_identity_linked_to_label="n/a (no code)", visually_inspected_page="YES (figure shows nameplate position only, no sample plate)", evidence_status="UNVERIFIED", date_accessed=TODAY,
   limitations="Documents location only; no colour code or sample label content.")
le(evidence_id="B5L02", brand="BYD", model_scope="ATTO 3 (Middle East manual)", catalog_model_id="M016", model_year_or_range="not stated in extracted text", market="Middle East",
   document_or_source_title="Owner Manual for SC2EGZ Middle East BYD ATTO 3 EN", source_url=MAN[1][2], page="PDF p.193 (printed 192)", evidence_type="OEM owner's manual",
   label_location_stated="Vehicle nameplate is located under the B-pillar.", label_contents_stated="Not listed.", paint_or_colour_field_listed="NOT STATED", paint_code_value_observed="",
   vehicle_identity_linked_to_label="n/a (no code)", visually_inspected_page="NO (text extraction only)", evidence_status="UNVERIFIED", date_accessed=TODAY, limitations="Location only.")
le(evidence_id="B5L03", brand="BYD", model_scope="DOLPHIN SURF (catalog Seagull; export name per Batch 4 alias table)", catalog_model_id="M028", model_year_or_range="not stated", market="UK (RHD)",
   document_or_source_title="BYD DOLPHIN SURF Owner's Manual - RHD", source_url=MAN[2][2], page="PDF p.187 (printed 186)", evidence_type="OEM owner's manual",
   label_location_stated="Vehicle nameplate is attached to the metal sheet surface on the lower part of the right B-pillar.", label_contents_stated="Not listed.", paint_or_colour_field_listed="NOT STATED",
   paint_code_value_observed="", vehicle_identity_linked_to_label="n/a (no code)", visually_inspected_page="YES (figure shows location only)", evidence_status="UNVERIFIED", date_accessed=TODAY,
   limitations="Location only. Mapping of 'Dolphin Surf' to catalog model M028 follows the Batch 4 alias table, not this document.")
le(evidence_id="B5L04", brand="BYD", model_scope="ATTO 3 EVO (EU, LHD)", catalog_model_id="M016", model_year_or_range="manual dated 2026-03-27", market="Europe",
   document_or_source_title="ATTO 3 EVO Owner's Manual - Left-hand Drive - 20260327 - EN", source_url=MAN[3][2], page="PDF p.238, 'Vehicle Nameplate'", evidence_type="OEM owner's manual",
   label_location_stated="Vehicle nameplate is located on the lower part of the right B-pillar.", label_contents_stated="Not listed.", paint_or_colour_field_listed="NOT STATED", paint_code_value_observed="",
   vehicle_identity_linked_to_label="n/a (no code)", visually_inspected_page="NO (text extraction only)", evidence_status="UNVERIFIED", date_accessed=TODAY,
   limitations="Location only. EVO is a facelift; catalog generation mapping not verified from this document.")
le(evidence_id="B5L05", brand="BYD", model_scope="ATTO 2 LONG RANGE (RHD)", catalog_model_id="M053", model_year_or_range="manual dated 2025-11-14", market="RHD export",
   document_or_source_title="ATTO 2 LONG RANGE Owner's Manual - Right-hand Drive - 20251114 - EN", source_url=MAN[4][2], page="PDF p.208, 'Vehicle Nameplate'", evidence_type="OEM owner's manual",
   label_location_stated="Vehicle nameplate is located under the right B-pillar.", label_contents_stated="Not listed.", paint_or_colour_field_listed="NOT STATED", paint_code_value_observed="",
   vehicle_identity_linked_to_label="n/a (no code)", visually_inspected_page="NO (text extraction only)", evidence_status="UNVERIFIED", date_accessed=TODAY,
   limitations="Location only. Mapping Atto 2 -> Yuan UP (BEV) per Batch 4 alt_names; the catalog alias is shared with the DM-i model, so treat as approximate.")
le(evidence_id="B5L06", brand="BYD", model_scope="ETP3 (LHD)", catalog_model_id="", model_year_or_range="manual 2023/2024", market="Europe",
   document_or_source_title="BYD ETP3 Owner's Manual - Left-hand Drive - EN", source_url=MAN[5][2], page="PDF p.169, 'Vehicle nameplate'", evidence_type="OEM owner's manual",
   label_location_stated="Vehicle nameplate is located 15 cm below the lock ring on the front right door.", label_contents_stated="Not listed.", paint_or_colour_field_listed="NOT STATED", paint_code_value_observed="",
   vehicle_identity_linked_to_label="n/a (no code)", visually_inspected_page="NO (text extraction only)", evidence_status="UNVERIFIED", date_accessed=TODAY,
   limitations="Location only. ETP3 is not mapped to a catalog model_id (mapping not established).")
le(evidence_id="B5L07", brand="BYD", model_scope="ATTO 3 (2022 manual)", catalog_model_id="M016", model_year_or_range="2022 manual (PDF created 2023-09)", market="global/export",
   document_or_source_title="BYD ATTO3 2022 Owner's Manual (20251004 EN)", source_url=MAN[6][2], page="PDF p.191 (printed 190), 'Vehicle Nameplate'", evidence_type="OEM owner's manual",
   label_location_stated="Nameplate attached to the metal sheet surface below the right B-pillar.",
   label_contents_stated="Company name, brand, country of manufacture, vehicle model, seating capacity, year and month of manufacture, drive motor model, peak power of drive motor, rated voltage and rated capacity of the high-voltage battery system, VIN, maximum allowable total mass.",
   paint_or_colour_field_listed="NO - the OEM list of nameplate contents contains no paint/colour item", paint_code_value_observed="", vehicle_identity_linked_to_label="n/a (no code)",
   visually_inspected_page="NO (text extraction; page image rendered but not reviewed)", evidence_status="UNVERIFIED", date_accessed=TODAY,
   limitations="Strongest label finding of Batch 5: for the ATTO 3 the OEM-described B-pillar nameplate does NOT carry a paint code, contradicting generic retailer statements that the code is on the B-pillar plate. Where (if anywhere) a BYD colour code is printed is not documented.")
le(evidence_id="B5L08", brand="BYD", model_scope="generic (retailer guidance, all BYD)", catalog_model_id="", model_year_or_range="", market="AU/EU/UK",
   document_or_source_title="CROP / NonPaints and Chipex generic location guidance (search snippets)", source_url="https://www.nonpaints.com/en/color-code/byd ; https://chipex.co.uk/brands/byd/m9/..", page="n/a (snippet)",
   evidence_type="RETAILER CLAIM (not label evidence)", label_location_stated="Under bonnet; driver's door / B-pillar / door frame; door jamb; engine compartment; or service booklet.", label_contents_stated="'3- or 4-digit' or letter-number code (examples R1A, B23, LZ5).",
   paint_or_colour_field_listed="Claimed", paint_code_value_observed="", vehicle_identity_linked_to_label="NO", visually_inspected_page="NO", evidence_status="UNVERIFIED", date_accessed=TODAY,
   limitations="Generic; not tied to any BYD model; examples are not BYD codes tied to a vehicle. Location claims conflict with each other and with the OEM manuals.")
le(evidence_id="B5L09", brand="BYD", model_scope="unspecified (Autohome Q&A, baseline S34)", catalog_model_id="", model_year_or_range="2025-08-28 post", market="China",
   document_or_source_title="Autohome Q&A - 比亚迪车漆标编号在哪里", source_url=srcs["S34"]["url"], page="forum answer", evidence_type="WEAK FORUM CLAIM",
   label_location_stated="Nameplate under the bonnet marked 'paintcolor' or 'H/S'.", label_contents_stated="", paint_or_colour_field_listed="Claimed", paint_code_value_observed="", vehicle_identity_linked_to_label="NO",
   visually_inspected_page="NO", evidence_status="UNVERIFIED", date_accessed="Batch 4", limitations="AI-disclaimed Q&A, author type not shown; unverified; kept as a lead (an under-bonnet plate with a colour field would be consistent with Chinese-market practice but is not documented).")
wr("vehicle_label_evidence.csv", LE, F_LE)

# ----------------------------------------------------------------------------------------------
# paint_code_conflicts.csv  (nothing is merged silently)
F_CF = ["conflict_id", "conflict_type", "subject", "brand", "model", "color_id_or_code", "color_name_zh", "values_in_conflict", "sources_involved", "status_effect", "resolution_status", "note"]
CF = []
def cf(**k): CF.append(k)
for cid, ci in sorted(col_info.items()):
    if ci["ambiguity"] not in ("SOURCES_DISAGREE", "MULTI_CODE_ALIAS_GROUP"): continue
    c = cols[cid]; m = models[c["model_id"]]
    if ci["ambiguity"] == "SOURCES_DISAGREE":
        sets_ = [set(v) for v in ci["persrc"].values()]
        nested = all(a <= b or b <= a for a in sets_ for b in sets_)
        cf(conflict_type="SOURCES_DISAGREE", status_effect="colour record set to CONFLICTED", values_in_conflict=str(ci["persrc"]), resolution_status="OPEN",
           note="Different suppliers list different code sets for the same colour name. Not merged. " +
                ("Sets are NESTED (one supplier lists a subset of another's codes): possibly incomplete listings rather than contradiction, but not resolvable without OEM evidence."
                 if nested else "Sets are NOT nested: each supplier lists a code the other omits."))
    else:
        cf(conflict_type="ALIAS_GROUP_AMBIGUITY", status_effect="none (stays POSSIBLE; ambiguity flag)", values_in_conflict=" / ".join(ci["codes"]), resolution_status="OPEN",
           note="All suppliers list the same several codes for one alias group of colour names; which code belongs to this exact vehicle/year is unknown.")
    CF[-1].update(subject="colour record", brand=brands[m["brand_id"]], model=m["model_key"], color_id_or_code=cid, color_name_zh=c["color_name_zh"],
                  sources_involved=";".join(sorted(ci["persrc"])))
byc = collections.defaultdict(set)
for l in links:
    byc[l["oem_code"]].add(cols[l["color_id"]]["color_name_zh"])
for code, names in sorted(byc.items()):
    if len(names) > 1:
        cf(conflict_type="CODE_MULTI_COLOUR_NAME", subject="supplier code", brand="BYD Group", model="various", color_id_or_code=code, color_name_zh=" | ".join(sorted(names)),
           values_in_conflict=f"{len(names)} distinct Chinese colour names matched to one supplier code", sources_involved=pcs.get(next((p for p in pcs if pcs[p]["oem_code"] == code), ""), {}).get("supplier_sources", ""),
           status_effect="none (informational)", resolution_status="OPEN", note="Supplier names are shared/translated aliases; the same code may cover several Chinese names or the match may be wrong.")
cf(conflict_type="LABEL_LOCATION", subject="where the colour code is printed", brand="BYD", model="all", color_id_or_code="n/a", color_name_zh="",
   values_in_conflict="CROP: under bonnet / driver's door-B-pillar / service booklet | Chipex: driver's door jamb or engine compartment | Autohome Q&A S34: plate under bonnet 'paintcolor'/'H/S' | BYD manuals: nameplate under right B-pillar (ATTO 3 2022 manual lists contents WITHOUT a paint item)",
   sources_involved="B5S01-B5S07;B5S15;S34", status_effect="none", resolution_status="OPEN", note="Not resolvable from documents obtained; needs photographs of identified vehicles or OEM repair documentation.")
cf(conflict_type="OEM_VS_RETAILER_NAMEPLATE", subject="nameplate content", brand="BYD", model="ATTO 3 (M016)", color_id_or_code="n/a", color_name_zh="",
   values_in_conflict="OEM manual (B5S07): nameplate carries company, brand, country, model, seats, build date, motor and battery data, VIN, mass - no colour | retailers: colour code on B-pillar plate",
   sources_involved="B5S07;B5S15", status_effect="none", resolution_status="OPEN (OEM document favoured for what the nameplate contains)", note="Retailer claim is generic across brands.")
for i, r in enumerate(CF, 1): r["conflict_id"] = f"B5C{i:04d}"
wr("paint_code_conflicts.csv", CF, F_CF)
n_conf = collections.Counter(r["conflict_type"] for r in CF)

# ----------------------------------------------------------------------------------------------
# unresolved_paint_codes.csv  (every colour record that is not VERIFIED_* - i.e. all)
F_UN = ["color_id", "brand", "model_id", "model", "model_year", "market", "color_name_zh", "color_name_en_unofficial", "evidence_status", "candidate_codes_supplier", "reason_unresolved", "evidence_needed", "priority_rank"]
UN = []
for cid, c in cols.items():
    ci = col_info[cid]
    if ci["status"].startswith("VERIFIED") or ci["status"] == "CORROBORATED": continue
    m = models[c["model_id"]]
    reason = {"NO_CANDIDATE_CODE": "No supplier lists a code for this colour name and no OEM/label evidence found.",
              "SOURCES_DISAGREE": "Suppliers disagree on the code (e.g. HB5 vs HB6).",
              "MULTI_CODE_ALIAS_GROUP": "Several supplier codes for one alias group; no exact-vehicle evidence to choose.",
              "SINGLE_CODE": "Single supplier code only; no OEM document or label confirms it for this model-year/market."}[ci["ambiguity"]]
    UN.append(dict(color_id=cid, brand=brands[m["brand_id"]], model_id=m["model_id"], model=m["model_key"], model_year=years.get(c["model_year_id"], {}).get("year", ""), market=c["market"],
                   color_name_zh=c["color_name_zh"], color_name_en_unofficial=c["name_en_gloss_unofficial"], evidence_status=ci["status"], candidate_codes_supplier="; ".join(ci["codes"]),
                   reason_unresolved=reason, evidence_needed="BYD body/paint repair documentation for the exact model-year, or a photographed original vehicle label (with VIN/model/year), or an OEM parts/paint-system listing.",
                   priority_rank=prio.get(c["model_id"], ("", ""))[0]))
UN.sort(key=lambda r: (int(r["priority_rank"]) if r["priority_rank"] != "" else 99, r["model_id"], r["color_id"]))
wr("unresolved_paint_codes.csv", UN, F_UN)

# ----------------------------------------------------------------------------------------------
# model_coverage.csv
MODEL_DOC = {"M016": "B5S01;B5S02;B5S04;B5S07", "M028": "B5S03", "M053": "B5S05"}
F_MC = ["model_id", "brand", "model", "model_name_zh", "priority_rank", "priority_group", "colour_records", "colours_with_supplier_candidate_code", "distinct_supplier_codes", "n_possible", "n_conflicted",
        "n_unverified", "n_verified_oem", "n_verified_label", "n_corroborated", "owner_manual_label_location_docs", "oem_paint_code_evidence", "reliable_paint_code_evidence"]
MC = []
bymodel = collections.defaultdict(list)
for cid, c in cols.items(): bymodel[c["model_id"]].append(cid)
for mid, m in models.items():
    cl = bymodel.get(mid, []); st = collections.Counter(col_info[c]["status"] for c in cl)
    codes = {x for c in cl for x in col_info[c]["codes"]}
    rk, pg = prio.get(mid, ("", ""))
    MC.append(dict(model_id=mid, brand=brands[m["brand_id"]], model=m["model_key"], model_name_zh=m["name_zh"], priority_rank=rk, priority_group=pg, colour_records=len(cl),
                   colours_with_supplier_candidate_code=sum(1 for c in cl if col_info[c]["codes"]), distinct_supplier_codes=len(codes), n_possible=st["POSSIBLE"], n_conflicted=st["CONFLICTED"],
                   n_unverified=st["UNVERIFIED"], n_verified_oem=st["VERIFIED_OEM"], n_verified_label=st["VERIFIED_LABEL"], n_corroborated=st["CORROBORATED"],
                   owner_manual_label_location_docs=MODEL_DOC.get(mid, ""), oem_paint_code_evidence="NONE FOUND",
                   reliable_paint_code_evidence="NO"))
MC.sort(key=lambda r: (int(r["priority_rank"]) if r["priority_rank"] != "" else 99, r["model_id"]))
wr("model_coverage.csv", MC, F_MC)

# ----------------------------------------------------------------------------------------------
# summary numbers for the report/validator
col_status = collections.Counter(ci["status"] for ci in col_info.values())
STATS = dict(models=len(models), by_brand=collections.Counter(brands[m["brand_id"]] for m in models.values()), colours=len(cols), colour_status=col_status,
             link_rows=len(rows), link_status=n_link_status, distinct_codes=len(byc), conflicts=n_conf,
             models_with_any_candidate=sum(1 for r in MC if r["colours_with_supplier_candidate_code"]),
             models_no_candidate=[r for r in MC if not r["colours_with_supplier_candidate_code"]],
             models_zero_colour=[r for r in MC if r["colour_records"] == 0],
             priority_models=[r for r in MC if r["priority_rank"] != ""], label_rows=len(LE), sources=len(SR))
import json
with open(os.path.join(OUT, "stats_batch5.json"), "w", encoding="utf-8") as f:
    json.dump({k: (dict(v) if isinstance(v, collections.Counter) else (len(v) if isinstance(v, list) and k.startswith("models_") else v)) for k, v in STATS.items() if k != "priority_models"},
              f, ensure_ascii=False, indent=1, default=str)
print(json.dumps({k: (dict(v) if isinstance(v, collections.Counter) else (len(v) if isinstance(v, list) else v)) for k, v in STATS.items()}, ensure_ascii=False, default=str, indent=1))
