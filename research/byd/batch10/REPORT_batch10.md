# Batch 10 - real-world evidence & source quality audit (BYD Group)

## **No genuine OEM evidence was obtained in Batch 10.** VERIFIED_OEM = 0, VERIFIED_LABEL = 0, CORROBORATED = 0.

No label photograph, dealer record, official paint-code statement or owner contribution exists in this project. This batch audits what we have, shows which apparent conflicts have visible explanations in the supplier text, and prepares the evidence kit. **Nothing was promoted, no conflict was closed, no earlier record was deleted.**

## Required figures

| # | Measure | Value |
|---|---|---|
| 1 | Colour records audited (all brands, all batches) | **1223** (`model_year_consistency.csv`) |
| 2 | Source lineages | **27** lineages across **296** audited sources; **5** lineages carry vehicle paint codes (OEMatch+DipYourCar; Touch Up Paint Factory+Cartouch; Carross; Colour Tubes; CROP). None is OEM-grade; mutual independence of the five is **unproven** (they may share an unknown paint-database upstream) |
| 3 | VERIFIED_OEM | **0** |
| 4 | VERIFIED_LABEL | **0** |
| 5 | CORROBORATED | **0** |
| 6 | POSSIBLE / CONFLICTED colour records | **329 / 107** (plus UNVERIFIED 787; PAINT_SYSTEM_REFERENCE: 60 identifier rows, 0 colour records whose only candidates are references) |
| 7 | Unresolved model-year differences | **29 colour records** in **13 model x colour groups** (15 where a supplier's year range excludes the record's model year; 7 with gloss/matte codes but unknown finish; 13 with no model year assigned) plus era differences in 苍穹蓝 (BYL/F2/L32C 2015-2019 vs LAN) |

## What the audit found (and corrects)

1. **Source quality.** 30 sources are manufacturer-controlled (BYD, Fangchengbao, Denza, Yangwang sites, manuals, importer brochures) - **none contains a paint code**. 14 are retailer/touch-up sources (the only places codes appear), 11 are licensed-paint-system or vendor pages (behaviour only), 115 are Autohome-type catalogue pages and 90 encyclopedia pages (colour names/years only). **No independent professional paint database and no authorised-dealer source has been obtained.**
2. **Lineage correction.** Batch 7 counted Touch Up Paint Factory and Cartouch separately. They share 12 codes and carry identical normalised colour names on all 12 (100%); Cartouch states Axalta sourcing. They are now merged as a *likely shared upstream* (heuristic: >=10 shared codes and >=90% identical names). OEMatch and DipYourCar remain merged (95% over 60 codes). Paint-code lineages therefore fall from six to five. No status changed because nothing was above POSSIBLE.
3. **HB5 vs HB6 (亚特兰蒂斯灰) is probably a finish difference, not a disagreement.** Every supplier text with a finish tag labels HB6 *matte* (Carross '¤MAT', Touch Up Paint Factory 'MATT', OEMatch/DipYourCar 'Matt Metallic') and HB5 plain metallic. Batch 7 had framed the matte hypothesis as coming from one lineage; Batch 10 finds the HB6-matte label in three lineages. It is still **not evidence**: the catalogue's Chinese 亚特兰蒂斯灰 records carry no finish information, BYD's importer brochures give none, and Carross supports HB6 only for Seal **2022**.
4. **HA4 vs HAN (攀岩灰) looks like name-lumping.** HA4 is tied to 时光灰 ('TIME GREY', pinyin 'Shi Guang Hui') by two lineages; Cartouch's rows list 'HAN, HA4' together under Harbour/Boulder/Time Grey. HAN is tied to both 贝贝灰 (Dolphin) and 'Boulder/Climbing Grey'. The conflict may be an artefact of multi-name rows - unresolved.
5. **雪域白 codes come partly from a seven-name group.** Touch Up Paint Factory lists W36C/WA2/WA8/BYHB-00001 for a group named Bright/Great/Polar/Snow/Snowfield/Summit/White Pearl, so it does not isolate 雪域白. Carross lists W36C *and* WA2 together for 'SNOW WHITE-MET.' (Qin/Tang 2017-2024); CROP says W36C 'Xue Yu Bai Pearl'; OEMatch/DipYourCar say WA2 'Xue Yu Bai Pearl'. Equating Carross's English 'Snow White' with 雪域白 is an assumption (a search snippet suggests BYD's export material uses 'Aurora White' for 雪域白; I could not verify it - the brochure URL returned 404).
6. **Name propagation.** 212 of 709 colour-record/code links (30%) have **no supplier listing for that model**; the code was attached by colour name alone. Supplier model matching used here is approximate (name prefix).
7. **Denza hotline.** 950856 now appears on two separate Denza page elements (footer customer-service line and a 24-hour rescue line on the service-support page), which strengthens - but does not prove - that it is Denza's official number. This is contact information only.
8. **Linghui (领汇).** Media/portal pages describe it as a BYD sub-brand launched in 2026 with models (e5, e7, e9, M9) reported as derived from Dynasty/Ocean models; no official site, manual or service page was found. Parentage or similar names are **not** evidence of shared paint codes.

## Priority conflict audit (`colour_conflict_audit.csv`)

| Colour | Competing codes | Supporting lineages (per code) | What explains it? | Status |
|---|---|---|---|---|
| 雪域白 | BYHB-00001, W36C, WA2, WA8 | BYHB-00001: 1; W36C: 3; WA2: 3; WA8: 1 | see assessment in the CSV (finish / year / name-lumping candidates; none proven) | **OPEN** |
| 攀岩灰 | HA4, HAN | HA4: 2; HAN: 2 | see assessment in the CSV (finish / year / name-lumping candidates; none proven) | **OPEN** |
| 亚特兰蒂斯灰 | HB5, HB6 | HB5: 4; HB6: 3 | see assessment in the CSV (finish / year / name-lumping candidates; none proven) | **OPEN** |
| 苍穹蓝 | BYL, F2, L32C, LAN | BYL: 2; F2: 2; L32C: 1; LAN: 2 | see assessment in the CSV (finish / year / name-lumping candidates; none proven) | **OPEN** |

- **雪域白**: Competing codes W36C, WA2, WA8 and BYHB-00001. W36C is named for 'Xue Yu Bai Pearl' by CROP and for 'SNOW WHITE-MET.' by Carross (which lists W36C and WA2 together for Qin/Tang 2017-2024); WA2 is named for 'Xue Yu Bai Pearl' by OEMatch/DipYourCar (one lineage). TUPF lists all four for a SEVEN-name white group (Bright/Great/Polar/Snow/Snowfield/Summit/White Pearl), so it does not isolate 雪域白. BYHB-00001 is a reference-style identifier. No listing assigns W36C vs WA2 to different years, models or markets; Carross lists both for the same rows. Finish, year, market or trim therefore do NOT demonstrably explain the difference; two codes may also belong to one colour. OPEN.
- **攀岩灰**: Competing HAN and HA4(+HAN). HA4 is tied to 时光灰/'TIME GREY' by two lineages (OEMatch/DipYourCar pinyin 'Shi Guang Hui'; TUPF 'TIME GREY'); Cartouch lists 'HAN, HA4' together on rows naming Harbour/Boulder/Time Grey, i.e. a name-lumped row. HAN is tied to 'Bei Bei Hui' (贝贝灰, OEMatch/DYC) AND to 'Boulder Grey / Climbing Grey' (TUPF), so one code spans two Chinese names. Plausible reading: 攀岩灰 = HAN and HA4 belongs to 时光灰 - but name-lumping, not a label, is all that supports it. OPEN.
- **亚特兰蒂斯灰**: HB5 vs HB6. Every supplier text that carries a finish tag labels HB6 as MATT (Carross '¤MAT', TUPF 'ATLANTIS GREY MATT', OEMatch/DipYourCar 'Matt Metallic') and HB5 as plain metallic (CROP, OEMatch, TUPF). Finish therefore probably explains the difference, but the catalogue's Chinese 亚特兰蒂斯灰 records carry no finish evidence, and BYD's importer brochures give no finish wording. Whether a given Seal is HB5 or HB6 depends on its finish: UNKNOWN. Cartouch lists HB5, HB6 and H84C together for ATTO 3 2025 (name-lumped). OPEN.
- **苍穹蓝**: Codes by era in Carross: BYL 2016-2017, F2/L32C 2015-2019 (Yuan EV 'FIRMAMENT BLUE-MET.'); TUPF e2: BYL;F2 for 'SKY BLUE, FIRMAMENT BLUE'; LAN (TUPF: 'AZUL SKY, CERULEAN BLUE, DOME BLUE, SKY BLUE' - 'Dome Blue' suggests 穹顶蓝, a different colour; OEMatch/DipYourCar pinyin 'Cang Qiong Lan' LAN); L-27 (OEMatch/DYC 'Cangqiong Blue Metallic' - an English name that was not linked to a catalogue colour record, so it is not counted among the competing codes above). Model year/generation may explain F2/L32C/BYL (2015-2019) versus LAN/L-27, but no supplier ties a code to a catalogue year inside 2019-2021 (e2). OPEN.

## Top 20 highest-priority unresolved colours

| Rank | Colour | Competing / candidate codes | Current state |
|---|---|---|---|
| 1 | 雪域白 | W36C vs WA2 vs WA8 | 63 conflicted / 63 candidate colour records; Batch 9 score 16 tier A |
| 2 | 攀岩灰 | HA4 vs HAN | 4 conflicted / 4 candidate colour records; Batch 9 score 14 tier A |
| 3 | 亚特兰蒂斯灰 | HB5 vs HB6 | 4 conflicted / 25 candidate colour records; Batch 9 score 14 tier A |
| 4 | 苍穹蓝 | BYL vs F2 vs L32C vs LAN | 7 conflicted / 10 candidate colour records; Batch 9 score 14 tier A |
| 5 | 贝贝灰 | HAN | 3 conflicted / 5 candidate colour records; Batch 9 score 14 tier A |
| 6 | 玄空黑 | 00AN vs AA1 | 3 conflicted / 26 candidate colour records; Batch 9 score 13 tier B |
| 7 | 滑雪白 | W46C vs WAC | 4 conflicted / 4 candidate colour records; Batch 9 score 12 tier B |
| 8 | 探险绿 | LAG vs UA6 | 3 conflicted / 3 candidate colour records; Batch 9 score 12 tier B |
| 9 | 跑酷红 | LAQ vs RA5 | 1 conflicted / 1 candidate colour records; Batch 9 score 12 tier B |
| 10 | 风卷草绿 | LAD vs UY | 2 conflicted / 4 candidate colour records; Batch 9 score 11 tier B |
| 11 | 德兰黑 | B1 vs B7822 vs DBU | 0 conflicted / 7 candidate colour records; Batch 9 score 11 tier B |
| 12 | 暮山紫 | C9 vs CA5 | 0 conflicted / 1 candidate colour records; Batch 9 score 11 tier B |
| 13 | 马赛灰 | BMS vs H16C vs H3 | 7 conflicted / 7 candidate colour records; Batch 9 score 9 tier C |
| 14 | 巧克力棕 | BCZ vs Z10C vs Z2 | 2 conflicted / 4 candidate colour records; Batch 9 score 9 tier C |
| 15 | 阿盖尔紫 | CA7 vs LYE | 1 conflicted / 1 candidate colour records; Batch 9 score 7 tier C |
| 16 | 山脉灰 | BYM vs DN | 0 conflicted / 10 candidate colour records; Batch 9 score 7 tier C |
| 17 | 活力橙 | BCP vs XB | 0 conflicted / 2 candidate colour records; Batch 9 score 6 tier C |
| 18 | 时光灰 | HA4 | 0 conflicted / 43 candidate colour records; Batch 9 score 0 tier C |
| 19 | 苍烟色 | HAZ | 0 conflicted / 14 candidate colour records; Batch 9 score 0 tier C |
| 20 | 冲浪蓝 | LAP | 0 conflicted / 5 candidate colour records; Batch 9 score 0 tier C |

Ranking: the four colours you named first, then Batch 9 conflict score, number of conflicted records and core-model coverage. Popularity is a proxy (your priority series); no sales data exists in the repository.

## Exact evidence needed to resolve each major conflict

| Colour | Needed |
|---|---|
| 雪域白 | (a) VIN-linked dealer record or label photo for Han EV, Qin PLUS (EV and DM-i), Song PLUS, Destroyer 05 - at minimum one 2020-2021 and one 2023-2025 vehicle of one model, to test whether W36C/WA2 split by year; (b) whether WA8 exists on any BYD vehicle; (c) paint-maker documentation stating what BYHB-00001 is |
| 攀岩灰 | A dealer record or label photo from one Atto 3 / Yuan PLUS in 攀岩灰 (HAN vs HA4) and one Dolphin in 贝贝灰 (HAN?), plus one 时光灰 car (HA4?) to settle the name-lumping |
| 亚特兰蒂斯灰 | Dealer record or label photo from one Seal in 亚特兰蒂斯灰, WITH the car's finish noted (gloss vs matte) and the year; ideally two cars (one each finish, if both exist) - an owner or BYD document stating whether a matte Atlantis Grey exists in China |
| 苍穹蓝 | Dealer record or label photo from an e2 (2019-2021) in 苍穹蓝; plus any BYD document naming the colour's code era; separately clarify 穹顶蓝 vs 苍穹蓝 for the LAN listings |

Rows 5-20 and the rules for every status are in `evidence_requirements.csv`. In every case a single vehicle resolves only its own model-year; a split by year, model, finish or market needs at least one vehicle per band. A dealer record or label photo may support VERIFIED_OEM/VERIFIED_LABEL for that vehicle only, and the conflict is then *reviewed*, not auto-closed.

## Evidence kit (real-world workflow)

`owner_request_zh/en.md` (label photograph request - no VIN, no assumed location, voluntary identity link: first 9 characters or the owner's own hash); `dealer_request_zh/en.md` (written VIN-based confirmation - VIN supplied only by the owner, in person, never collected by the researchers); `evidence_photo_checklist.md` (shots, redaction, GPS stripping, what makes a photo VERIFIED_LABEL-grade, and a guide to tell an OEM paint code from a VIN, date, part number or formula/system identifier). **No label location is claimed for any model.**

## Other brands

Official sources re-checked: Denza service-support page now readable (rescue hotline 950856; no paint information); Yangwang and Fangchengbao manual pages remain JavaScript apps with no static PDF list (their undocumented APIs were not called); no owner-manual PDF, authorised documentation or genuine label found for Denza, Yangwang, Fangchengbao or Linghui. Nothing inaccessible is claimed as inspected.

## Next batch

1. **Field evidence is the only way forward** - Batch 11 should ingest whatever the user or owners provide: call answers (Batch 9 script), label photographs and dealer records (this kit), the Baslac factual answers. Without them, further desk research will only add retailer copies.
2. If a Seal or Han EV owner can take part, start with 亚特兰蒂斯灰 (finish decides HB5 vs HB6) and 雪域白 (W36C vs WA2).
3. Desk work worth doing meanwhile: obtain BYD's official colour-name tables per model-year (Chinese configurators/brochures) to fix finish and year availability; this would shrink the model-year question without any paint code.

## Limitations

- Lineage merging is heuristic and deliberately conservative (it can only reduce the independent count).
- Supplier model matching is approximate; supplier year ranges are the suppliers' own and unverified.
- No photograph, dealer record or official paint statement was obtained; the label search (B10S03) found none.
