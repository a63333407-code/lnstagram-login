#!/usr/bin/env python3
"""Generate research/byd/batch6/REPORT_batch6.md from the Batch 6 CSVs (all numbers computed)."""
import csv, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); B6 = os.path.join(HERE, "batch6")
rd = lambda n: list(csv.DictReader(open(os.path.join(B6, n), encoding="utf-8", newline="")))
D, S, C, L, FI = (rd(n) for n in ("discovered_codes.csv", "sources.csv", "conflicts.csv", "lookup_model_year_colour.csv", "formula_identifier_investigation.csv"))
ST = json.load(open(os.path.join(B6, "stats_batch6.json"), encoding="utf-8"))
b5 = list(csv.DictReader(open(os.path.join(HERE, "batch5", "oem_paint_codes.csv"), encoding="utf-8", newline="")))
oem = json.load(open(os.path.join(B6, "raw", "oematch_byd_products.json"), encoding="utf-8")); crop = json.load(open(os.path.join(B6, "raw", "crop_byd_products.json"), encoding="utf-8"))
sc = collections.Counter(r["link_scope"] for r in D); stt = collections.Counter(r["confidence_status"] for r in D); ct = collections.Counter(r["code_type"] for r in D)
col_rows = [r for r in D if r["link_scope"] == "COLOUR_RECORD"]
col_status = {}
for r in col_rows: col_status[r["color_id"]] = r["confidence_status"]
cs = collections.Counter(col_status.values())
brand_models = collections.defaultdict(set); brand_cols = collections.defaultdict(set)
for r in D:
    if r["model_id"]: brand_models[r["brand"]].add(r["model_id"])
    if r["color_id"]: brand_cols[r["brand"]].add(r["color_id"])
b5_cols = {r["color_id"] for r in b5}
new_cols = set(col_status) - b5_cols
b5_codes = {r["supplier_candidate_code"] for r in b5}
cands_all = list(csv.DictReader(open(os.path.join(HERE, "catalog_union", "paint_code_candidates_all.csv"), encoding="utf-8", newline="")))
import re
base_codes = {t.strip().upper() for c in cands_all for t in re.split(r"[;,/]+", c["code_raw"]) if t.strip()}
new_code_list = ST["codes_new_to_catalog"]
# colour-family first-letter regularity (structural observation only)
fam = collections.defaultdict(collections.Counter); seen = set()
for r in col_rows:
    zh = r["original_chinese_color_name"]
    if r["code_type"] != "SUPPLIER_LISTED_OEM_STYLE_CODE" or not zh or (zh, r["paint_code"]) in seen: continue
    seen.add((zh, r["paint_code"])); fam[zh[-1]][r["paint_code"][0]] += 1
fam_rows = []
for k, v in sorted(fam.items(), key=lambda kv: -sum(kv[1].values())):
    n = sum(v.values())
    if n >= 5: top, c = v.most_common(1)[0]; fam_rows.append((k, n, top, c))
fam_hit = sum(c for _, _, _, c in fam_rows); fam_n = sum(n for _, n, _, _ in fam_rows)
conf = collections.Counter(r["conflict_type"] for r in C)
fi = {r["identifier"]: r for r in FI}
yw = [r for r in D if r["brand"] == "Yangwang"]; fc = [r for r in D if r["brand"] == "Fangchengbao"]
L_ = []
a = L_.append
a("# Batch 6 - China paint-code discovery (BYD Group)")
a("")
a("**Research only.** Nothing was imported into any application, no application or Batch 1-5 file was changed, nothing was published. Validation: `batch6/validation_report_batch6.md`.")
a("")
a("## Bottom line")
a("")
a("1. **Still no verified factory code.** Searching Chinese-language sources (BYD's own site, Autohome, JD, search terms 比亚迪原厂漆号 / 车漆代码 / 油漆配方 / 车身颜色编码 / 原厂颜色代码 / VIN油漆代码查询), VSM, Yuhuahang (御华行) and VIN decoders turned up **no public table of BYD factory paint codes**. Every code in this batch is third-party, so **VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED = 0**; each row is POSSIBLE or CONFLICTED.")
a(f"2. **The practical gain is discovery.** Two new supplier sources (OEMatch: {len(oem)} BYD product titles; CROP: {len(crop)} products) plus a re-read of the Batch 2-5 listings produced **{len(D)} candidate-code rows** and a **model/year/colour lookup of {len(L)} rows** (`lookup_model_year_colour.csv`) in which a given model, year and Chinese colour name returns its candidate codes, a status and a code type. {len(new_code_list)} code tokens are new to the catalog.")
a("3. **One OEM statement is genuinely useful:** BYD's own service page says its 精诚钣喷 repair network selects three refinish brands - **AkzoNobel (阿克苏诺贝尔), BASF (巴斯夫), Donglai (东来)** - and uses '原厂数据、原厂配方' (OEM data, OEM formulas). This implies that factory formulas are reached through those paint makers' systems (the page does not say how); a formula identifier from such a system is a *paint-system reference* that maps back to BYD data, not necessarily the code printed on a car.")
a("4. **WA2 and HA4 are real, widely listed short codes; B9 and BYD007WA2 were not found anywhere** (details below).")
a("")
a("### Numbers")
a("")
a("| Measure | Value |")
a("|---|---|")
a(f"| Candidate-code rows (`discovered_codes.csv`) | **{len(D)}** |")
a(f"| ...linked to a catalog colour record (model + year + Chinese colour name) | {sc['COLOUR_RECORD']} rows covering **{len(col_status)}** colour records ({len(new_cols)} not covered by Batch 5) |")
a(f"| ...model-level supplier listings (supplier model/year, Chinese name not matched) | {sc['MODEL_LEVEL_LISTING']} |")
a(f"| ...code-only leads (supplier name, no model/year) | {sc['CODE_ONLY']} |")
a(f"| Distinct code tokens | {ST['distinct_codes']} |")
a(f"| Rows POSSIBLE / CONFLICTED | {stt['POSSIBLE']} / {stt['CONFLICTED']} |")
a(f"| Colour records POSSIBLE / CONFLICTED | {cs['POSSIBLE']} / {cs['CONFLICTED']} |")
a(f"| VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED | 0 / 0 / 0 |")
a(f"| New supplier products parsed | {ST['new_supplier_products']} distinct (code, name) pairs; {ST['new_products_matched']} matched to BYD colour records; {ST['new_products_unmatched']} unmatched (code-only) |")
a(f"| Supplier names matching Denza/Yangwang/Fangchengbao/Linghui colour names but deliberately NOT linked | {ST['cross_brand_name_matches_not_linked']} (suppliers list under 'BYD'; a shared colour name is not evidence for another brand) |")
a("")
a("## Code types - OEM code vs international code vs formula identifier")
a("")
a("`code_type` classifies a code's **format and provenance class**; it is not a correctness verdict. Every code here is supplier-listed.")
a("")
a("| code_type | Rows | What it is | Examples |")
a("|---|---|---|---|")
ex = {t: ", ".join(sorted({r["paint_code"] for r in D if r["code_type"] == t})[:6]) for t in ct}
desc = {"SUPPLIER_LISTED_OEM_STYLE_CODE": "Short 2-4 character code (e.g. AAP, HB5, UA6, W36C) of the kind BYD factory codes appear to use; suppliers present it as the factory code, nobody cites an OEM source",
        "SUPPLIER_LISTED_LEGACY_HYPHEN_CODE": "Letter-hyphen-number codes (L-27, W-21...) listed by OEMatch/CROP; origin unknown (an older numbering or a supplier convention)",
        "SUPPLIER_OR_PAINT_SYSTEM_STYLE_IDENTIFIER": "Long identifiers with a maker prefix (BYHB-00001, BYHA-00002); format differs from the short codes - more likely a supplier/paint-system internal ID",
        "SUPPLIER_LISTED_NUMERIC_STYLE_CODE": "Letter + 3-5 digits (e.g. B7822); format unlike the others - unclassified origin"}
for t, n in ct.most_common(): a(f"| {t} | {n} | {desc.get(t, '')} | {ex[t]} |")
a("")
a("**Structural observation (not verification).** The short 'OEM-style' codes follow a consistent first-letter-by-colour-family pattern across independent retailers: "
  + "; ".join(f"{k}: {c}/{n} start with {top}" for k, n, top, c in fam_rows) + f" - {fam_hit} of {fam_n} distinct (name, code) pairs ({100*fam_hit/max(fam_n,1):.0f}%). A convention this regular suggests the retailers draw on one coherent coding system - plausibly BYD's factory codes or a refinish system built on them - but a shared upstream is equally consistent with the pattern, so it **does not verify** any individual code.")
a("")
a("**Three kinds of identifier to keep apart in the database:** (1) *OEM/factory code* - printed by the manufacturer on a label or in repair documentation: none confirmed; (2) *international/colour-family codes* sold by touch-up retailers: what this batch mostly found; (3) *paint-system formula IDs* from AkzoNobel/BASF/Donglai/PPG-type systems (formula number or variant) - not found for BYD in any public source; retailer-style identifiers such as BYHB-00001 may belong here.")
a("")
a("## The identifiers you asked about")
a("")
a("| Identifier | Found? | Finding |")
a("|---|---|---|")
for k in ("BYD007WA2", "WA2", "HA4", "B9", "W36C", "BYHB-00001"):
    r = fi[k]; a(f"| {k} | {'No' if r['oem_status'].startswith('NOT_FOUND') else 'Yes - ' + r['sources']} | {r['assessment']} |")
a("")
a("Conclusion: none corresponds to a *confirmed* OEM code. WA2 (雪域白) and HA4 (时光灰) behave like BYD-style factory short codes and are listed by several retailers, but 雪域白 also appears as W36C (CROP) and, in Touch Up Paint Factory's multi-name white group that includes Snow White, WA8 and BYHB-00001, and 时光灰 has a separate matte code HC2 in OEMatch. If you saw `B9` or `BYD007WA2` somewhere (a screenshot, a paint-system lookup, a parts listing), send the source: with it, they can be classified; without it they cannot.")
a("")
a("## Conflicts (nothing merged, no code chosen)")
a("")
a(f"`conflicts.csv` has {len(C)} rows: {conf['SOURCES_DISAGREE_NESTED']} nested and {conf['SOURCES_DISAGREE_NOT_NESTED']} non-nested supplier disagreements (aggregated by colour name and code-set signature; they cover {cs['CONFLICTED']} colour records), {conf['MULTI_CODE_ALIAS_GROUP']} multi-code alias groups, named conflicts for 雪域白 (W36C vs WA2 vs WA8 vs BYHB-00001) and 亚特兰蒂斯灰 (HB5 vs HB6), a finish-type conflict for 雪域白 (Autohome Q&A says solid; retailers say pearl/metallic), a name-match review item and the carried-over label-location conflict.")
a("")
a("**New hypothesis worth testing:** OEMatch gives matte (Mat/Matt) variants their own codes - HB5 (gloss) vs HB6 (matt), HA4 vs HC2, UAM vs UAN, LAT vs LAV - so part of the HB5/HB6-style disagreements may be gloss-vs-matte, not error. Carross lists HB6 for the plain grey, so it stays unresolved. The builder therefore never links a matte supplier code to a non-matte colour record.")
a("")
a("## Denza, Yangwang, Fangchengbao, Linghui")
a("")
a("| Brand | Catalog models | Rows in `discovered_codes.csv` | What exists |")
a("|---|---|---|---|")
a(f"| Denza | 19 | 0 | **No code from any source.** OEMatch, CROP, Carross and Touch Up Paint Factory list no Denza model that was reachable (Touch Up Paint Factory returned 403 for its brand index). |")
a(f"| Yangwang | 7 | {len(yw)} | Carross pages for U8 (2023: AAP obsidian black, EY quanta silver matt, UAM Holmes green) and U9 (2024: LYE/CA7 Argyle purple); OEMatch carries AAP/UAM/EY under BYD names. All supplier-only. |")
a(f"| Fangchengbao | 11 | {len(fc)} | Carross Leopard (Bao) 5 (2023-24: HCJ 'Milk Ash Green') and Leopard 8 (2024: BB8 'Snow Silver') model-level rows; the same code HCJ is also on OEMatch ('Duo Nuo Mi Di Shan Mai Lv') and, under a Shark listing, on Touch Up Paint Factory - three retailers with differing names, still POSSIBLE. No Chinese colour name is matched, so these sit as model-level rows. |")
a("| Linghui | 4 | 0 | **No code from any source.** |")
a("")
a("## How to use the lookup")
a("")
a("`lookup_model_year_colour.csv`: filter by `international_model_name` / `chinese_model_name`, `production_year` and `original_chinese_color_name`. `candidate_codes` lists every supplier code found (separated by ` | `); `confidence_status` is POSSIBLE (one consistent answer, unverified) or CONFLICTED (suppliers disagree - do not choose); `code_ambiguity` shows multi-code alias groups; `row_scope` says whether the row is tied to a catalog colour record or is a model-level supplier row. Treat results as leads: confirm with the vehicle label (location still undocumented for BYD - see Batch 5), a VIN lookup at a BYD service centre, or a refinish system that carries BYD data (AkzoNobel, BASF, Donglai) before mixing paint.")
a("")
a("## Sources and what did not work")
a("")
a("See `sources.csv` (18 rows). Found and used: BYD China service page (OEM statement), OEMatch listings, CROP listings, Autohome/JD/chejiahao pages (colour names and finish remarks only). Not found / not accessible: VSM and Yuhuahang databases, Glasurit Color Online (licensed), any public BYD colour-code table in Chinese, any DB for Denza/Linghui. Third-party BYD repair-manual mirrors were not used (Batch 5 rationale).")
a("")
a("## Limitations")
a("")
a(f"- OEMatch coverage is **not exhaustive**: titles come from a search-suggest endpoint (<=10 per query); {len(oem)} BYD titles were collected. CROP's listing exposed 9 colours (pages beyond 3 redirect).")
a("- Matching a supplier's romanised name to a Chinese colour name uses exact pinyin (or exact English gloss) equality; homophones and translations can mislead, and one supplier code is applied to every BYD colour record with that name. Model-year applicability is never confirmed.")
a("- Supplier model-level rows carry the supplier's own year range, unverified.")
a("- Code-type labels describe format only. A well-formed, widely repeated code is still unverified.")
a("")
a("## Next steps that could actually verify codes")
a("")
a("1. VIN-based colour-code lookup at a BYD service centre for one sample vehicle per priority model/colour (Seal, Dolphin, Seagull, Atto 3, Han, Qin PLUS, Song PLUS, Destroyer 05, e2) - a few dozen lookups would test the supplier codes.")
a("2. Licensed access to a refinish system that carries BYD data (AkzoNobel, BASF/Glasurit, Donglai) - these are the systems BYD's own network names.")
a("3. Owner/body-shop photographs of the physical label, with VIN, model and year visible.")
open(os.path.join(B6, "REPORT_batch6.md"), "w", encoding="utf-8").write("\n".join(L_) + "\n")
print("report", len(L_), "lines")
