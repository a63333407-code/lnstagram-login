# Batch 6 - China paint-code discovery (BYD Group)

**Research only.** Nothing was imported into any application, no application or Batch 1-5 file was changed, nothing was published. Validation: `batch6/validation_report_batch6.md`.

## Bottom line

1. **Still no verified factory code.** Searching Chinese-language sources (BYD's own site, Autohome, JD, search terms 比亚迪原厂漆号 / 车漆代码 / 油漆配方 / 车身颜色编码 / 原厂颜色代码 / VIN油漆代码查询), VSM, Yuhuahang (御华行) and VIN decoders turned up **no public table of BYD factory paint codes**. Every code in this batch is third-party, so **VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED = 0**; each row is POSSIBLE or CONFLICTED.
2. **The practical gain is discovery.** Two new supplier sources (OEMatch: 167 BYD product titles; CROP: 18 products) plus a re-read of the Batch 2-5 listings produced **1003 candidate-code rows** and a **model/year/colour lookup of 496 rows** (`lookup_model_year_colour.csv`) in which a given model, year and Chinese colour name returns its candidate codes, a status and a code type. 40 code tokens are new to the catalog.
3. **One OEM statement is genuinely useful:** BYD's own service page says its 精诚钣喷 repair network selects three refinish brands - **AkzoNobel (阿克苏诺贝尔), BASF (巴斯夫), Donglai (东来)** - and uses '原厂数据、原厂配方' (OEM data, OEM formulas). This implies that factory formulas are reached through those paint makers' systems (the page does not say how); a formula identifier from such a system is a *paint-system reference* that maps back to BYD data, not necessarily the code printed on a car.
4. **WA2 and HA4 are real, widely listed short codes; B9 and BYD007WA2 were not found anywhere** (details below).

### Numbers

| Measure | Value |
|---|---|
| Candidate-code rows (`discovered_codes.csv`) | **1003** |
| ...linked to a catalog colour record (model + year + Chinese colour name) | 618 rows covering **375** colour records (148 not covered by Batch 5) |
| ...model-level supplier listings (supplier model/year, Chinese name not matched) | 331 |
| ...code-only leads (supplier name, no model/year) | 54 |
| Distinct code tokens | 154 |
| Rows POSSIBLE / CONFLICTED | 713 / 290 |
| Colour records POSSIBLE / CONFLICTED | 275 / 100 |
| VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED | 0 / 0 / 0 |
| New supplier products parsed | 81 distinct (code, name) pairs; 27 matched to BYD colour records; 54 unmatched (code-only) |
| Supplier names matching Denza/Yangwang/Fangchengbao/Linghui colour names but deliberately NOT linked | 9 (suppliers list under 'BYD'; a shared colour name is not evidence for another brand) |

## Code types - OEM code vs international code vs formula identifier

`code_type` classifies a code's **format and provenance class**; it is not a correctness verdict. Every code here is supplier-listed.

| code_type | Rows | What it is | Examples |
|---|---|---|---|
| SUPPLIER_LISTED_OEM_STYLE_CODE | 887 | Short 2-4 character code (e.g. AAP, HB5, UA6, W36C) of the kind BYD factory codes appear to use; suppliers present it as the factory code, nobody cites an OEM source | 00AN, A3, AA1, AAP, AN, B1 |
| SUPPLIER_OR_PAINT_SYSTEM_STYLE_IDENTIFIER | 60 | Long identifiers with a maker prefix (BYHB-00001, BYHA-00002); format differs from the short codes - more likely a supplier/paint-system internal ID | BYHA-00002, BYHB-00001 |
| SUPPLIER_LISTED_LEGACY_HYPHEN_CODE | 40 | Letter-hyphen-number codes (L-27, W-21...) listed by OEMatch/CROP; origin unknown (an older numbering or a supplier convention) | B-02, J-01, L-21, L-27, L-30, O-22 |
| SUPPLIER_LISTED_NUMERIC_STYLE_CODE | 16 | Letter + 3-5 digits (e.g. B7822); format unlike the others - unclassified origin | B7822 |

**Structural observation (not verification).** The short 'OEM-style' codes follow a consistent first-letter-by-colour-family pattern across independent retailers: 灰: 9/12 start with H; 蓝: 7/10 start with L; 黑: 3/6 start with A; 白: 5/6 start with W; 绿: 4/6 start with U - 28 of 40 distinct (name, code) pairs (70%). A convention this regular suggests the retailers draw on one coherent coding system - plausibly BYD's factory codes or a refinish system built on them - but a shared upstream is equally consistent with the pattern, so it **does not verify** any individual code.

**Three kinds of identifier to keep apart in the database:** (1) *OEM/factory code* - printed by the manufacturer on a label or in repair documentation: none confirmed; (2) *international/colour-family codes* sold by touch-up retailers: what this batch mostly found; (3) *paint-system formula IDs* from AkzoNobel/BASF/Donglai/PPG-type systems (formula number or variant) - not found for BYD in any public source; retailer-style identifiers such as BYHB-00001 may belong here.

## The identifiers you asked about

| Identifier | Found? | Finding |
|---|---|---|
| BYD007WA2 | No | Not found in any source (baseline retailers, OEMatch, CROP, web searches for 'BYD007'). Structure is consistent with a paint-system style identifier that concatenates a maker prefix + index + a short code ending in the known retailer code WA2 - this is a HYPOTHESIS about format only, not evidence of what it is. |
| WA2 | Yes - B6S02;S226;S227;S31;S32 | OEM-style 3-char code on retailer lists; same white also listed as W36C (CROP) and WA8, BYHB-00001 (TUPF). Appears with Carross 'W36C, WA2' and OEMatch 'Xue Yu Bai Pearl WA2'. Reads like a BYD factory-style short code, but no OEM document confirms it and a competing code (W36C) exists for the same name. |
| HA4 | Yes - B6S02;S226;S30;S32 | OEM-style 3-char code; listed by Cartouch, TUPF and OEMatch ('Shi Guang Hui Metallic HA4') for 时光灰; Cartouch also lists it for 'Harbour Grey, Boulder Grey' alongside another code - alias-group ambiguity. |
| B9 | No | Searched all baseline candidates, 167 OEMatch BYD titles and 9 CROP products: B9 does not occur. Cannot be classified; request the source (screenshot/URL/vehicle) where it was seen. |
| W36C | Yes - B6S03;S226;S227;S31;S32 | OEM-style 4-char code with a digit pattern different from the 3-letter codes; listed by CROP ('W36C Xue Yu Bai Pearl'), Carross and TUPF. Competes with WA2 for the same colour name. |
| BYHB-00001 | Yes - S226;S32 | Appears only in Touch Up Paint Factory lists, always bundled with W36C;WA2;WA8 for a multi-name white group. The 'BYHB-<digits>' format differs from the OEM-style short codes; it is more likely a supplier/paint-system internal identifier than a factory code, but this is unverified. |

Conclusion: none corresponds to a *confirmed* OEM code. WA2 (雪域白) and HA4 (时光灰) behave like BYD-style factory short codes and are listed by several retailers, but 雪域白 also appears as W36C (CROP) and, in Touch Up Paint Factory's multi-name white group that includes Snow White, WA8 and BYHB-00001, and 时光灰 has a separate matte code HC2 in OEMatch. If you saw `B9` or `BYD007WA2` somewhere (a screenshot, a paint-system lookup, a parts listing), send the source: with it, they can be classified; without it they cannot.

## Conflicts (nothing merged, no code chosen)

`conflicts.csv` has 34 rows: 10 nested and 6 non-nested supplier disagreements (aggregated by colour name and code-set signature; they cover 100 colour records), 12 multi-code alias groups, named conflicts for 雪域白 (W36C vs WA2 vs WA8 vs BYHB-00001) and 亚特兰蒂斯灰 (HB5 vs HB6), a finish-type conflict for 雪域白 (Autohome Q&A says solid; retailers say pearl/metallic), a name-match review item and the carried-over label-location conflict.

**New hypothesis worth testing:** OEMatch gives matte (Mat/Matt) variants their own codes - HB5 (gloss) vs HB6 (matt), HA4 vs HC2, UAM vs UAN, LAT vs LAV - so part of the HB5/HB6-style disagreements may be gloss-vs-matte, not error. Carross lists HB6 for the plain grey, so it stays unresolved. The builder therefore never links a matte supplier code to a non-matte colour record.

## Denza, Yangwang, Fangchengbao, Linghui

| Brand | Catalog models | Rows in `discovered_codes.csv` | What exists |
|---|---|---|---|
| Denza | 19 | 0 | **No code from any source.** OEMatch, CROP, Carross and Touch Up Paint Factory list no Denza model that was reachable (Touch Up Paint Factory returned 403 for its brand index). |
| Yangwang | 7 | 5 | Carross pages for U8 (2023: AAP obsidian black, EY quanta silver matt, UAM Holmes green) and U9 (2024: LYE/CA7 Argyle purple); OEMatch carries AAP/UAM/EY under BYD names. All supplier-only. |
| Fangchengbao | 11 | 9 | Carross Leopard (Bao) 5 (2023-24: HCJ 'Milk Ash Green') and Leopard 8 (2024: BB8 'Snow Silver') model-level rows; the same code HCJ is also on OEMatch ('Duo Nuo Mi Di Shan Mai Lv') and, under a Shark listing, on Touch Up Paint Factory - three retailers with differing names, still POSSIBLE. No Chinese colour name is matched, so these sit as model-level rows. |
| Linghui | 4 | 0 | **No code from any source.** |

## How to use the lookup

`lookup_model_year_colour.csv`: filter by `international_model_name` / `chinese_model_name`, `production_year` and `original_chinese_color_name`. `candidate_codes` lists every supplier code found (separated by ` | `); `confidence_status` is POSSIBLE (one consistent answer, unverified) or CONFLICTED (suppliers disagree - do not choose); `code_ambiguity` shows multi-code alias groups; `row_scope` says whether the row is tied to a catalog colour record or is a model-level supplier row. Treat results as leads: confirm with the vehicle label (location still undocumented for BYD - see Batch 5), a VIN lookup at a BYD service centre, or a refinish system that carries BYD data (AkzoNobel, BASF, Donglai) before mixing paint.

## Sources and what did not work

See `sources.csv` (18 rows). Found and used: BYD China service page (OEM statement), OEMatch listings, CROP listings, Autohome/JD/chejiahao pages (colour names and finish remarks only). Not found / not accessible: VSM and Yuhuahang databases, Glasurit Color Online (licensed), any public BYD colour-code table in Chinese, any DB for Denza/Linghui. Third-party BYD repair-manual mirrors were not used (Batch 5 rationale).

## Limitations

- OEMatch coverage is **not exhaustive**: titles come from a search-suggest endpoint (<=10 per query); 167 BYD titles were collected. CROP's listing exposed 9 colours (pages beyond 3 redirect).
- Matching a supplier's romanised name to a Chinese colour name uses exact pinyin (or exact English gloss) equality; homophones and translations can mislead, and one supplier code is applied to every BYD colour record with that name. Model-year applicability is never confirmed.
- Supplier model-level rows carry the supplier's own year range, unverified.
- Code-type labels describe format only. A well-formed, widely repeated code is still unverified.

## Next steps that could actually verify codes

1. VIN-based colour-code lookup at a BYD service centre for one sample vehicle per priority model/colour (Seal, Dolphin, Seagull, Atto 3, Han, Qin PLUS, Song PLUS, Destroyer 05, e2) - a few dozen lookups would test the supplier codes.
2. Licensed access to a refinish system that carries BYD data (AkzoNobel, BASF/Glasurit, Donglai) - these are the systems BYD's own network names.
3. Owner/body-shop photographs of the physical label, with VIN, model and year visible.
