# Batch 11 - field evidence ingestion & model-year colour catalogue (BYD Group)

## **No field evidence was received, so no paint code was verified.** Field evidence received: **0**. VERIFIED_OEM = 0, VERIFIED_LABEL = 0, CORROBORATED = 0.

Intake checks (git history, repository scan, messages) found no label photograph, dealer reply, VIN-linked record or OEM paint document; every verification slot is **PENDING**. This batch (1) collected **official colour names** from BYD-group sources, (2) classified every existing colour/code link, and (3) built a model-year colour catalogue. **An official colour name is not a paint-code verification, no code was copied between models, nothing was promoted and no conflict was closed.**

## Required figures

| # | Measure | Value |
|---|---|---|
| 1 | Official colour tables found | **12 official brochures/spec sheets** with exterior colour names (of 13 fetched; 1 has image-only colour pages) + **11 official Denza/Yangwang/Fangchengbao model pages** with embedded colour names (84 entries) + 16 BYD China model pages whose colours load dynamically (not extracted). Only 1 brochure prints Chinese names (Macau Seal, Traditional script); 1 states finish per colour (UK Seal 6 DM-i: metallic); 3 list 'Metallic paint' as an equipment line; **0 contain a paint code** |
| 2 | Model/year combinations covered | Brochures: Seal (Macau, Australia 2025, UK MY26, South Africa), ATTO 3 (Australia 2026), Dolphin (site 'sc' 2025, Australia dealer 2025), Seal U DM-i (Croatia importer, 2024), plus context models. **Not covered by any official table: Han EV, Qin PLUS, e2, Destroyer 05.** Catalogue model-year pairs whose colour name is attested for the same model by an official source: **34** (the documents state no year, so this shows the name exists for the model, not for that year). Years are stated only in file names/titles for 6 brochures |
| 3 | Name-only code associations | **212 of 709** colour/code links (30%) have no supplier listing for that model; the code was attached by colour name alone (flag `NAME_ONLY_PROPAGATED`). The other 497 are model-listed by a supplier (approximate name matching) - still retailer evidence |
| 4 | Model-year mismatches | **24 links** (15 colour records) where the supplier's own year range excludes the record's model year. Also: 568 links with unknown production period, 709 (all) with no China-market confirmation, 7 with a matte-labelled code on a record of unknown finish |
| 5 | Field evidence actually received | **0** (checks IC01-IC03 in `field_evidence_register.csv`) |
| 6 | Verified OEM / verified label codes | **0 / 0** |
| 7 | Remaining priority conflicts | **4 of 4 OPEN**: 雪域白, 攀岩灰, 亚特兰蒂斯灰, 苍穹蓝 (all competing codes preserved) |
| 8 | Exact next evidence | see 'Next evidence' below |

Colour records audited: **1223** (POSSIBLE 329, CONFLICTED 107, UNVERIFIED 787; unchanged from Batch 10).

## Task 1 - official colour names (`official_colour_tables.csv`)

Official, BYD-hosted documents were downloaded and their text searched; every colour listed was checked against the extracted text (`extract_official_docs_batch11.py`; short excerpts and sha256 in `raw/`). Highlights:

- **Macau Seal brochure (BYD site, 2024-03 metadata)** prints Chinese with English: 北冰藍/Arctic Blue, 極光白/Aurora White, 亞特蘭蒂斯灰/Atlantis Gray, 迷迭灰/Shark Gray, 玄空黑/Cosmos Black, 風卷草綠/Mystic Green. **A Seal's white is 极光白, not 雪域白.**
- Seal in Australia (2025), South Africa (document dated 2024-09) and the UK (MY26) use other English names; UK MY26 is a different palette (Atlantis *Blue*, Obsidian Black, Polar White, Indigo/Lavender Grey, Ruby Red).
- ATTO 3 Australia 2026: Ski White, Harbour Grey, Cosmos Black, Atlantis Grey ('only available on PREMIUM Model'). Dolphin: Ski White, Harbour Grey, Atlantis Grey (+ two-tone) in Australia 2025; Atlantis Grey/Delan Black, Ski White/Urban Grey, Sand White in the 'sc' document.
- **Mapping cautions found while auditing earlier assumptions:** the Cambodia 'Seal 5 DM-i 海豹' brochure is catalogue Seal 05 DM-i (M021), **not Destroyer 05** (the alias table lists 'Seal 5 DM-i' under both); the Cambodia 'Sealion 6 DM-i 海狮' brochure is 海狮06 DM-i (M031), not Song PLUS DM-i. 'Seal U DM-i' (Croatia) maps to Song PLUS DM-i only through the catalogue alias.
- Finish: only the UK Seal 6 DM-i sheet states a finish per colour (metallic). No document states matte for any colour. **No official document contains a paint code.**
- BYD China model pages (16 fetched) load colours with scripts; I did not call the API behind them. Han EV, Qin PLUS, e2 and Destroyer 05 therefore have **no** official colour table here (rows `NOT_FOUND`).

## Task 2 - field evidence ingestion (`field_evidence_register.csv`)

Three intake checks (IC01-IC03) found nothing new. The register defines four evidence types with acceptance checks (label photo; dealer written reply; owner-supplied build record; OEM paint document), the VIN rule (never a full VIN: SHA-256 hash and first 9 characters only), and 20 PENDING target slots (T01-T20 from Batch 8). Nothing was fabricated or marked complete.

## Task 3 and 5 - model-year catalogue and link-quality audit

`model_year_colour_catalog.csv` has one row for each of the 1,223 colour records with generation, model year, production year (UNKNOWN - the catalogue holds model years only), market, trim scope, finish, colour name, official-document support level, candidate codes **with their support class** and flags. `code_link_quality_audit.csv` classifies all 709 existing colour/code links and keeps their history (`first_seen_batch`, `status_history`) - nothing deleted or re-assigned.

| Primary class | Links |
|---|---|
| MODEL_LISTED_YEAR_MATCH | 102 |
| MODEL_LISTED_YEAR_UNKNOWN | 371 |
| NAME_ONLY_PROPAGATED | 212 |
| MODEL_YEAR_MISMATCH | 24 |

Official-document support for colour records: 98 records carry an official **Chinese** name printed for the same model (Seal brochure and brand pages), 12 rest on an official English name whose Chinese equivalent is inferred. Neither establishes a year, finish or code.

## Task 4 - the four priority conflicts (`priority_conflict_updates.csv`)

Every competing code is preserved with its exact supplier evidence; facts, hypotheses and minimum evidence are separated; nothing is decided by vote.

- **雪域白** (codes BYHB-00001, W36C, WA2, WA8): [FACT] No fetched official document prints the Chinese name 雪域白. Official Seal documents print 極光白 / Aurora White (D01, D02, D04) for the white, so a Seal is not a 雪域白 car and retailer listings of the 'Snow White' code group under SEAL are not evidence for 极光白. [FACT] Official export documents list 'Snow white' for Seal U DM-i (D07, Croatia importer guide, 2024-05 metadata) and 'Snowy White' for Seal 5 DM-i / 海豹 (D05, Cambodia, 2025-07 metadata). The documents give no Chinese name, finish or code.
- **攀岩灰** (codes HA4, HAN): [FACT] Official Australian documents list 'Harbour Grey' for the ATTO 3 (D10, 2026) and for the Dolphin (D09, 2025). Neither prints a Chinese name, finish or code. [FACT] Cartouch (AU) lists 'HARBOUR GREY, BOULDER GREY' with HAN, HA4 for ATTO 3 2023-2025 and 'BOULDER GREY, TIME GREY' with HAN, HA4 for Dolphin 2024; other lineages tie HA4 to 时光灰.
- **亚特兰蒂斯灰** (codes HB5, HB6): [FACT] Official documents print Atlantis Grey/Gray (Chinese 亞特蘭蒂斯灰 on the Macau Seal brochure D01) for Seal (D01, D02, D04), ATTO 3 (D10, 'only available on PREMIUM Model'), Dolphin (D08, D09). None states finish (matte/metallic) or a code. UK documents print 'Atlantis BLUE' (D03, D11, D12) and D05 prints 'Atlantic Grey' - different names, not to be equated. [FACT] Every retailer text with a finish tag labels HB6 matte (¤MAT / MATT / Matt) and HB5 plain metallic (three lineages). HB6 is supported for Seal 2022 only by Carross.
- **苍穹蓝** (codes BYL, F2, L32C, LAN): [FACT] No fetched official document prints 苍穹蓝 / Firmament Blue / Sky Blue. Other official blues (北冰蓝 / Arctic Blue on Seal, Azure Blue on Sealion 6, Atlantis Blue in the UK) are different names. [FACT] 苍穹蓝 appears in the catalogue for e2 (2019-2021) and older models; no priority-model official document covers e2.

## Task 6 - other brands

Official model pages embed Chinese colour names: Denza (17 entries: Z9 GT 2026款, 2nd-gen D9), Yangwang (33: U8, U8L, U7, U9 - several entries are not classifiable as exterior vs interior and are not used), Fangchengbao (34: Bao 5, Bao 8, Tai 3, Tai 7, Formula S). Names only; no codes; live pages without dates. **Brands are not assumed to share paint codes**, and no code was transferred. **Linghui (领汇)** stays separate: no official source establishing its relationship or paint data was found.

A name-level lead (no status change): Fangchengbao's official Bao 5 page names **多诺米蒂山脉绿**; OEMatch's romanisation 'Duo Nuo Mi Di Shan Mai Lv' equals it and carries HCJ, and Carross lists HCJ for Leopard 5 2023-2024 under a different English name. Two retailer lineages and an official Chinese name agree at name level - still retailer evidence only.

## Next evidence needed

1. **A Seal owner's record** (dealer system/printout or label photo, own vehicle, year and finish noted) for 亚特兰蒂斯灰 - decides HB5 vs HB6 and tests the matte hypothesis.
2. **A Han EV / Qin PLUS / Song PLUS / Destroyer 05 owner's record** for 雪域白 (one 2020-22 and one 2023-25 car of one model) - decides W36C vs WA2 vs WA8.
3. **An Atto 3/Yuan PLUS 攀岩灰, a Dolphin 贝贝灰 and a 时光灰 car** - settles HAN vs HA4 and whether Dolphin and Atto 3 share a paint.
4. **An e2 (2019-2021) 苍穹蓝 record**, plus any BYD document pairing Chinese names with export names and stating finish.
5. Desk work still possible: the BYD China model pages' colour tables (if BYD publishes them in a static document), and official Chinese brochures for Han EV, Qin PLUS, e2 and Destroyer 05.

## Limitations

- PDF 'document dates' are metadata creation dates, not publication dates; most documents state no model year.
- Official English names are mapped to Chinese names only where a Chinese name is printed (Macau Seal) or the match is marked INFERRED.
- Supplier model matching is approximate; supplier year ranges are the suppliers' own.
- Colours on live brand pages are current offerings; they do not describe earlier model years.
