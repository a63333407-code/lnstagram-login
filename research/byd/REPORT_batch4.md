# BYD research - Batch 4 final report (remaining BYD-group models)

**Status: the Batch 4 image harvest is finished (all 1,088 trims have a final status) and every validator passes.**
Nothing was imported into any application, no application file was modified, and the catalog is **not published**. Batches 1-3 are unchanged (verified with `git status` inside both validators).
Rebuild order: `build_batch4.py` -> `build_batch4_visual.py` -> `raw_b4/spot_check_urls_b4.py` -> `build_batch4_reports.py`.

## Headline numbers
| Item | Result |
|---|---|
| Autohome series inventoried (4 brand pages) | 119 (95 harvested, 9 done in batch 3, 9 concept/show cars and 6 commercial series documented as excluded) |
| Catalog models after batch 4 (BYD group) | **137** (BYD 96, Denza 19, Fangchengbao 11, Linghui 4, Yangwang 7); 8 models were discovered from Autohome and are absent from the Wikipedia list |
| Model research status | COMPLETE_FOR_AVAILABLE_SOURCES 116 / PARTIAL 9 / NO_SOURCE_DATA_FOUND 12 |
| Autohome trims (specs) read | 1,094 -> **1,070 mapped to a model**, 18 unmapped (explained), 6 excluded (concept cars) |
| New sourced model-year rows | 208 (plus 69 existing batch-2 rows enriched); merged catalog: 387 model-year rows, all SOURCED, **no estimates** |
| Generations after batch 4 | 155 (17 new, including 'generation unspecified' buckets) |
| Trims in merged catalog | 1,382 |
| Factory colour records (batch 4) | 881 (251 distinct Chinese names; per-trim observations: 2,324) |
| Dimension rows / generation facts (Wikipedia infoboxes) | 149 / 133 |
| Paint-code candidates (retailer catalogs) | 212 new rows -> 13 new code tokens; 139 codes in the merged catalog, **all POSSIBLE / RETAILER_CATALOG_UNVERIFIED** |
| Colour-to-code links (merged) | 446; 227 colour records linked; **confirmed OEM codes: 0** |
| Images (batch 4) | **156,401**: exterior 20,794, interior/cockpit 66,255, seats 67,412, official press 1,940 |
| Image linkage | 153,569 linked to an exact trim/year/generation/model; 2,832 unlinked (the 18 unmapped trims); 18,537 linked to a factory colour |
| Trim harvest status | **COMPLETED 1,080 / PARTIAL 8 / NO_IMAGES_AVAILABLE 0 / FAILED_RETRY_REQUIRED 0** |
| Swatches | 2,324 exterior (per trim) + 632 interior |
| Live URL spot check | 150 of 150 sampled URLs resolved (HTTP 200 + expected type) |

## Coverage by brand
| Brand | Models | Complete for available sources | Partial | No source data found | Trims | Colour records | Images (b3+b4) |
|---|---|---|---|---|---|---|---|
| BYD | 96 | 83 | 6 | 7 | 1188 | 988 | 159013 |
| Denza | 19 | 16 | 0 | 3 | 102 | 120 | 21772 |
| Fangchengbao | 11 | 10 | 1 | 0 | 63 | 71 | 14463 |
| Linghui | 4 | 2 | 0 | 2 | 7 | 6 | 798 |
| Yangwang | 7 | 5 | 2 | 0 | 22 | 38 | 4838 |

**Reading 'complete for available sources':** the model has at least one trim, one colour record and one image from the sources reached. It does **not** mean every field is documented: see missing-data report (`missing_data_b4.csv`, 122 model-level gaps; the global gaps are listed once per model).

### Models marked PARTIAL (9)
| Brand | Model | Trims | Colour records | Missing |
|---|---|---|---|---|
| BYD | Yuan Up (PHEV) | 1 | 0 | exterior colours |
| BYD | Racco | 1 | 0 | exterior colours |
| BYD | Shark 6 | 2 | 0 | exterior colours |
| Yangwang | Altior | 2 | 0 | exterior colours |
| BYD | F3DM | 2 | 0 | doors ; exterior colours |
| BYD | S8 | 3 | 0 | exterior colours |
| BYD | Flyer | 3 | 0 | exterior colours |
| Yangwang | U9 Xtreme | 1 | 0 | doors ; dimensions ; exterior colours |
| Fangchengbao | Ti6 | 1 | 0 | doors ; dimensions ; exterior colours |

These have trims and images but no colour photos on any trim (placeholder, show-car or Europe-only Autohome entries with a few photos).

## Unresolved cases (explicit, never forced)
### 12 models without an Autohome series (you asked about 11; the brand-aware fix exposed Linghui e5 as a twelfth)
| Model | Reason | Evidence |
|---|---|---|
| Datang DM | PHEV variant not listed on Autohome | Autohome series 大唐 (8102) lists 8 trims and every label is 纯电 (EV); Wikipedia list: Datang DM = PHEV 2026 (article BYD Datang). |
| Dolphin G DM-i | upcoming / not on Autohome | Wikipedia list: Dolphin G DM-i 2026 (article BYD Dolphin G, Europe unveiling May 2026); no 海豚G series on the Autohome BYD brand page. |
| Ti 7 | export rebadge of a mapped model | Wikipedia redirect 'BYD Ti 7' -> 'Fangchengbao Ti7'; list note 'Export rebadge of Fangchengbao Ti7'. The Chinese-market vehicle is Autohome series 钛7 (8171), mapped to Ti7 (PHEV)/(BEV). |
| M6 DM | export-market model not on Autohome | Wikipedia list: M6 DM 2026, three-row MPV based on Song Max. Autohome series 比亚迪M6 (798) is the 2010 M6 (mapped to 'M6 (2010)'); no later M6 series on the BYD brand page. |
| M6 EV | export-market model not on Autohome | Wikipedia list: M6 EV 2024 (eMax 7), based on e6 and Song Max. Autohome 比亚迪M6 (798) is the 2010 M6; Autohome 比亚迪e6 (831) is mapped to e6. |
| Mako | upcoming / not on Autohome | Wikipedia list status 'Upcoming'. Autohome has an unnamed 混动皮卡 (hybrid pickup, series 7075, 3 photos): it is not assumed to be the Mako. |
| e5 | upcoming / name collision with the old BYD e5 | Wikipedia list: Linghui e5 upcoming, based on Qin Plus EV (redirect 'Linghui e5' -> 'BYD Qin#Linghui e5'). Autohome 比亚迪e5 (4073) is the 2015-2020 BYD e5, mapped to the BYD-brand row (same model_key, different brand). |
| e9 | different Autohome vehicle under the same name | Autohome 比亚迪e9 (5955) lists 2021-2025 BYD-brand e9 trims, catalogued separately as 'e9 (BYD brand, 2021)'. Wikipedia: Linghui e9 (2026) is a later model (redirect 'Linghui e9' -> 'BYD Han#BYD e9 (2021) / Linghui e9 (2026)'); no 20 |
| B5 | export name of a mapped model | List note: rebadged Fangchengbao Bao 5 for export; Wikipedia redirect 'Fangchengbao Bao 5' -> 'Denza B5'. Autohome lists the Chinese-market 豹5 (7177), mapped to 'Bao 5'. |
| B8 | export name of a mapped model | List note: rebadged Fangchengbao Bao 8 for export; Wikipedia redirect 'Fangchengbao Bao 8' -> 'Denza B8'. Autohome 豹8 (7353) is mapped to 'Bao 8'. |
| B3 | export name of a mapped model | List note: rebadged Fangchengbao Tai 3 for export. Autohome 钛3 (7356) is mapped to 'Tai 3'. |
| S1 | no separate Autohome series | Wikipedia redirect 'BYD S1' -> 'BYD Yuan#BYD S1'; list row S1 (2015-2016). The Autohome BYD brand page has S2, S6, S7 and S8 but no S1 series. |

Each also has an Autohome absence check (brand page URL and fetch time) and a resolution path in `models_without_autohome_mapping_b4.csv`.

### 18 unmapped trims
| Series | Year | Trim label | Candidate rows | Evidence |
|---|---|---|---|---|
| BYD:汉L | 2025 | 黑神话悟空特别版 | Han L EV; Han L DM | Autohome 汉L lists EV, DM-i and DM-p trims; the special edition label states no powertrain. |
| BYD:唐L | 2025 | 黑神话悟空特别版 | Tang L EV; Tang L DM | Autohome 唐L lists EV and DM trims; the special edition label states no powertrain. |
| BYD:比亚迪C6 | 2014 | 基本型 | none (no catalogue row) | Autohome 比亚迪C6 (3376): one 2014 trim '基本型' with 3 photos and no matching row in the Wikipedia list; probably a show car but no source says so. |
| Denza:腾势Z | 2026 | 赛道版 | Z Coupe; Z Spider | Autohome 腾势Z (8107) lists 硬顶版 (hard-top), 敞篷版 (convertible) and 赛道版 (track edition). Wikipedia 'Denza Z' states coupe and convertible only; the track edition's body style is not stated. |
| Denza:腾势Z9GT | 2026 | 易三方闪充尊荣型 | Z9 GT PHEV; Z9 GT EV | The 2024 trims were mapped by the cited range rule (630 = EV, 1100 = PHEV). These 2026 labels carry no range figure or powertrain token (闪充 = flash charging only) and both rows can exist in 2026 (list: Z9 GT PHEV 2024; Z9 GT EV in |
| Denza:腾势Z9GT | 2026 | 易三方闪充旗舰型 | Z9 GT PHEV; Z9 GT EV | The 2024 trims were mapped by the cited range rule (630 = EV, 1100 = PHEV). These 2026 labels carry no range figure or powertrain token (闪充 = flash charging only) and both rows can exist in 2026 (list: Z9 GT PHEV 2024; Z9 GT EV in |
| Denza:腾势Z9GT | 2026 | 闪充尊荣型 | Z9 GT PHEV; Z9 GT EV | The 2024 trims were mapped by the cited range rule (630 = EV, 1100 = PHEV). These 2026 labels carry no range figure or powertrain token (闪充 = flash charging only) and both rows can exist in 2026 (list: Z9 GT PHEV 2024; Z9 GT EV in |
| Denza:腾势Z9GT | 2026 | 闪充旗舰型 | Z9 GT PHEV; Z9 GT EV | The 2024 trims were mapped by the cited range rule (630 = EV, 1100 = PHEV). These 2026 labels carry no range figure or powertrain token (闪充 = flash charging only) and both rows can exist in 2026 (list: Z9 GT PHEV 2024; Z9 GT EV in |
| Denza:腾势Z9GT | 2026 | 易三方闪充尊越型 | Z9 GT PHEV; Z9 GT EV | The 2024 trims were mapped by the cited range rule (630 = EV, 1100 = PHEV). These 2026 labels carry no range figure or powertrain token (闪充 = flash charging only) and both rows can exist in 2026 (list: Z9 GT PHEV 2024; Z9 GT EV in |
| Denza:腾势Z9GT | 2026 | 易三方闪充性能型 | Z9 GT PHEV; Z9 GT EV | The 2024 trims were mapped by the cited range rule (630 = EV, 1100 = PHEV). These 2026 labels carry no range figure or powertrain token (闪充 = flash charging only) and both rows can exist in 2026 (list: Z9 GT PHEV 2024; Z9 GT EV in |
| Denza:腾势Z9GT | 2026 | 特别版 | Z9 GT PHEV; Z9 GT EV | The 2024 trims were mapped by the cited range rule (630 = EV, 1100 = PHEV). These 2026 labels carry no range figure or powertrain token (闪充 = flash charging only) and both rows can exist in 2026 (list: Z9 GT PHEV 2024; Z9 GT EV in |
| Denza:腾势Z9GT | 2026 | Chopard萧邦联名版 | Z9 GT PHEV; Z9 GT EV | The 2024 trims were mapped by the cited range rule (630 = EV, 1100 = PHEV). These 2026 labels carry no range figure or powertrain token (闪充 = flash charging only) and both rows can exist in 2026 (list: Z9 GT PHEV 2024; Z9 GT EV in |
| Denza:腾势Z9GT | 2025 | 中国香港车展版 | Z9 GT PHEV; Z9 GT EV | Auto-show edition (2025): the label states no powertrain. The 2024 trims were mapped by the cited range rule (630 = EV, 1100 = PHEV). These 2026 labels carry no range figure or powertrain token (闪充 = flash charging only) and both  |
| Denza:腾势D9 | 2025 | 中国香港车展版 | D9 DM-i; D9 EV | Auto-show edition (2025): the label states no powertrain. Both D9 powertrains were sold 2022-2026 (Autohome lists DM-i and EV trims for most years). This label has no powertrain token. |
| Denza:腾势D9 | 2023 | PREMIER 创始版 | D9 DM-i; D9 EV | Both D9 powertrains were sold 2022-2026 (Autohome lists DM-i and EV trims for most years). This label has no powertrain token. |
| Denza:腾势D9 | 2024 | PIONEER 四座创领版 | D9 DM-i; D9 EV | Both D9 powertrains were sold 2022-2026 (Autohome lists DM-i and EV trims for most years). This label has no powertrain token. |
| Fangchengbao:钛7 | 2026 | 315KM 两驱Max版 | Ti7 (PHEV); Ti7 (BEV) | Ti7 PHEV is documented from 2025 and Ti7 BEV from 2026; both exist in 2026. The '315KM'/'300KM' figures are not tied to a powertrain by any source read, so no inference is made. |
| Fangchengbao:钛7 | 2026 | 300KM 四驱Ultra版 | Ti7 (PHEV); Ti7 (BEV) | Ti7 PHEV is documented from 2025 and Ti7 BEV from 2026; both exist in 2026. The '315KM'/'300KM' figures are not tied to a powertrain by any source read, so no inference is made. |

Autohome's per-spec parameter table (which would state EV/PHEV) is deliberately obfuscated (injected `hs_kw..._baikeee` spans), so it was not used. Their images are kept as `UNLINKED_MODEL_UNRESOLVED`.

### Generation assignment
Trims by how their model was chosen: label_token_or_cited_rule: 274; single_row_series_default: 789; unique_row_by_documented_intro_year: 7. By how their generation was chosen: single_generation_row: 971; inferred_from_documented_intro_year: 52; unresolved_before_first_documented_generation: 7; unresolved_generation_boundary_year: 12; unresolved_documented_generations_overlap: 13; unresolved_label_states_第二代: 15.
'Unresolved' means the trim sits in a '[generation unspecified]' bucket instead of being guessed: boundary years, years before the first documented generation, trims whose label states 第二代 (second generation), and Sealion 05 DM-i where Wikipedia's generation dates overlap.
43 source conflicts are recorded in `source_conflicts_b4.csv` (for example Autohome lists e7/M9 trims in 2025 while the Wikipedia list gives 2026; Autohome marks several 'current' list models as discontinued).

## Duplicate names and aliases
`alias_collisions_b4.csv` has 61 rows: export/alt name shared by several model rows: 4; same Chinese name on several model rows: 1; identical normalized model name: 1; export rebadge pair (Wikipedia list note): 7; Wikipedia redirect (name is an alias of another article): 27; one Autohome series covers several model rows: 21. Cross-brand model-key collisions: only **e5** (BYD e5 vs Linghui e5), handled with brand-aware lookups; no duplicate (brand, model_key).

## Paint codes (item 6 audit)
* All 139 codes come from four retailer catalogs (Colour Tubes, Cartouch, Carross, Touch Up Paint Factory); none cites an OEM source. Tier: `RETAILER_CATALOG_UNVERIFIED`, status POSSIBLE. **No code is VERIFIED; `confirmed_oem_paint_codes.csv` is empty.**
* Repetition across retailers does not raise confidence: a link can be `medium` only when a retailer lists that model with a year range containing the model year and at most two names. Audit of all 446 links (original -> audited): medium -> low: 48; low -> low: 346; medium -> medium: 52. The audit only downgrades (48 links fell from medium to low).
* Links require a model match, a year match where the retailer gives years, and an exact normalized match with a literal translation of the Chinese name. Multi-name alias groups (e.g. seven 'white' aliases) are always low.
* Rejected sources (batch 2): Paint Calculators and NonPaints. Official BYD code documentation was not found.

## Chinese colour translations (item 5)
All 309 Chinese colour names were reviewed. Every entry is labelled `REVIEWED_UNOFFICIAL_RESEARCHER_TRANSLATION` (never an official name, never stored in an 'official' field): {'partly transliterated (pinyin) - weakest': 28, 'literal': 242, 'two-tone (literal)': 16, 'proper name / place name': 23}. 12 carry ambiguity notes; 35 are echoed by an independent retailer English name (corroborates the translation only, not the paint code). Five translations were corrected in review (润玉白, 琴海蓝, 极汐绿, 赤帝红, 玄武黑).

## Images
* **Harvest:** 2026-11-24T02:02:39Z to 2026-11-24T03:44:23Z. First pass read 1,088 trims; **a parser gap was found and fixed**: older galleries use `<a class="carpic-img" href=...>` and the first parser missed their photos (429 lists disagreed with Autohome's own totals). All 429 were re-fetched with the fixed parser; 417 matched, 12 still disagree after four rounds (source inconsistencies, below).
* **Redirects:** 1,075 category lists answered HTTP 302 (no photos). Each was re-requested and recorded as *confirmed empty*; a redirect is never counted as a harvest and never as a failure.
* **Failed requests:** NOT_A_FAILURE_CATEGORY_EMPTY: 1,075; GENUINE_MAIN_RUN_FAILURE_RECOVERED_BY_RETRY: 2; GENUINE_NETWORK_FAILURE_RECOVERED: 29; no unresolved failure. See `failed_requests_report_b4.csv`.
* **PARTIAL trims (8), all source inconsistencies after four retries:**
| Series | Year | Trim | Issue |
|---|---|---|---|
| BYD:宋MAX | 2017 | 1.5T 自动智联尊贵型 7座 | colour gallery 钻石蓝: facet says 21, harvested 0 / colour gallery 水晶白: facet says 10, harvested 8 |
| BYD:元 | 2017 | 1.5L 手动酷炫时尚型 | colour gallery 白黑酷: facet says 9, harvested 8 |
| BYD:比亚迪e6 | 2017 | 400 精英版 | colour gallery 白色: facet says 8, harvested 7 |
| BYD:宋MAX | 2017 | 试装版 | colour gallery 钻石蓝: facet says 9, harvested 30 |
| BYD:宋新能源 | 2018 | 宋EV400 智联进享型 | colour gallery 活力橙黑: facet says 12, harvested 11 |
| BYD:海狮05 DM-i | 2025 | DM-i 智驾版 75KM尊贵型 | exterior: the landing page states no total for this category, but the list serves photos (32 on page 1; 32 harvested by paginating to exhaustion); completeness cannot be verified independently / cockpit: the landing page states no |
| BYD:海狮07 DM-i | 2025 | 150 领航版 | colour gallery 苍烟色: facet says 9, harvested 8 |
| Fangchengbao:方程S | 2026 | 900KM云辇A后驱版 | cockpit: expected 115, harvested 179 (last retry: ok) / seats: expected 113, harvested 185 (last retry: ok) |
* **View labels: no image is VERIFIED.** UNKNOWN_NO_SEQUENCE_CONTEXT: 1,890; UNKNOWN_NON_STANDARD_GALLERY_SIZE: 4,147; REVIEWED_GALLERY_IRREGULAR_NO_LABEL: 28; CANDIDATE: 14,713; MODEL_REVIEWED_NOT_EDITOR_VERIFIED: 16. CANDIDATE labels come from photo position in 7/8-photo colour galleries; in my visual review of 32 galleries from different series, 28 matched the standard order and 4 did not (all dealer-showroom shoots). With batch 3 that is 44 of 51 (86%). 16 images were individually inspected at 400x300 (`MODEL_REVIEWED_NOT_EDITOR_VERIFIED`; a model, not a human editor).
* **Interior:** only two source categories (cockpit area, seats/cabin); dashboard/wheel/console and front/rear seats are not separated; photos are not linked to interior colours.
* **Resolution and rights:** 480x360 thumbnails only; no full-size image was downloaded (batch-4 scope). No image licence is cleared; Autohome photos are presumed all-rights-reserved.
* **No invented URLs:** every image, photo-page and gallery URL appears in a harvested record (validator check).

## Source quality
Batch-4 sources by reliability: secondary: 83; secondary (exact-trim photographic evidence): 95; retailer (secondary): 2. OEM-class sources: none new (BYD's China model pages exposed no colour lists). Everything is Autohome photo evidence (exact-trim, but not an official availability list), Wikipedia infoboxes (secondary) and retailer catalogs. Colour lists are **lower bounds**: each trim shows only some colours.

## Validation (all hard checks passed)
* `batch4/images/validation_report_batch4_visual.md`: image/trim/generation/year/colour relationships, URL ids, view-label rules, statuses, URL provenance, no unresolved failures, batches 1-3 unchanged.
* `batch4/data_integrity_report_batch4.md` (merged catalog): 25 checks passed: key uniqueness, FKs, trim/generation/model-year consistency, no VERIFIED anywhere, all years SOURCED, dimensions traceable to an infobox, door counts sourced, brand-aware model keys, confirmed-OEM table empty, link audit, glossary labelling, evidence on every unmapped case.
* `batch4/validation_report_batch4_data.md`: ids unique and disjoint from batches 1-3, none of the 1,094 specs lost (trims + unmapped + excluded), trim/colour consistency, sourced years only, no VERIFIED status, glossary coverage.

## Limitations and remaining blockers
1. **No OEM-verified paint code exists** for any model; verification needs label photos, a BYD parts/paint-formula source or a licensed refinish database.
2. **No official English colour names** for China-market colours; glosses are unofficial.
3. **Images are not cleared for any use**, are thumbnails only, and view labels are candidates (about one in seven wrong in sampled galleries).
4. **18 trims and 12 models** remain unmapped/without a series (above) until a source resolves them.
5. **Exterior design** descriptions are not available beyond body class; doors/dimensions exist only where a Wikipedia infobox states them.
6. The catalog reflects Autohome's Chinese-market gallery view; export-market colours and trims are mostly absent.
7. Not published, not imported, as instructed.
