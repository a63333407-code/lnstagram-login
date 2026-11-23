# BYD research - Batch 2 progress report (priority models)

Status: research only. **No application files modified. Nothing imported.** Nothing is VERIFIED.
Rebuild all files with `python3 build_batch2.py` (reads `batch1/` and `raw/autohome_specs.json`).

## What changed since batch 1
* **Sourced facts and estimates are now separate.** `model_years.csv` holds only years with a source (179 rows).
  The 180 range-derived years from batch 1 moved to `estimates_model_years.csv` and are labelled ESTIMATE; they are not used anywhere else.
* New evidence base: Autohome picture-gallery pages decoded from GBK, read per exact trim (款型) and model year (年款), 9 series.
* Paint-code candidates from 4 supplier catalogs (one more rejected). All codes are POSSIBLE; none is VERIFIED.

## Priority-model coverage (China market, from sourced records)
| Model | Years with a 款 / source year | Model-year records | ...with >=1 colour | Trims (款型) | Colour records | ...with a POSSIBLE code |
|---|---|---|---|---|---|---|
| Seal | 2022-2025 | 4 | 4 | 24 | 35 | 19 |
| Dolphin | 2021-2026 | 5 | 4 | 22 | 33 | 23 |
| Seagull | 2023-2027 | 6 | 5 | 23 | 35 | 13 |
| Atto 3 / Yuan PLUS | 2022-2026 | 5 | 5 | 27 | 42 | 21 |
| Han | 2020-2027 | 18 | 15 | 70 | 56 | 0 |
| Qin PLUS | 2021-2027 | 10 | 10 | 53 | 48 | 0 |
| Song PLUS | 2020-2025 | 9 | 8 | 39 | 34 | 0 |
| Destroyer 05 | 2022-2025 | 4 | 4 | 21 | 14 | 0 |
| e2 | 2019-2024 | 5 | 5 | 20 | 26 | 0 |
| **Total** | | **66** | **60** | **299** | **323** | **76** |

* 323 colour records for the priority models: 268 are Autohome per-trim photo observations, 18 come from OEM-class sources, the rest from media articles. 84 distinct Chinese colour names.
* Han includes EV, DM-i, DM and DM-p; Qin PLUS and Song PLUS include DM-i and EV. Seal's DM-i versions (海豹DM-i = Seal 07 DM-i) are recorded as a separate model.
* **How to read a colour record:** `GALLERY_OBSERVED` = a photo of that exact model year exists in that colour. Each trim shows only some colours (usually 1-5), so the list per model-year is a **lower bound**, not an official colour list.

## Paint codes
* Candidate rows from suppliers: 141; distinct code tokens: 126 (all POSSIBLE; 0 VERIFIED).
* Colour-to-code links: 119 link rows covering 76 colour records, all POSSIBLE, confidence medium/low only. Models with links: Seal, Dolphin, Yuan PLUS/Atto 3, Seagull.
* **Han, Qin PLUS, Song PLUS, Destroyer 05, e2: no supplier lists them, so no code at all (NOT FOUND).** I deliberately did not copy codes by colour name from other models (e.g. "Time Grey" -> HA4 appears for Atto 3/Dolphin only).
* Rejected: Paint Calculators (`BYD-001..010` sequential IDs with generic names, no source); NonPaints (no per-model codes).
* Nothing found from BYD itself: no OEM label photo, parts-catalog or paint-formula document. Official BYD model pages for the priority models returned no colour lists (see sources S27 note).
* Label location is supported only by retailers (driver door jamb, field 颜色/车身颜色). The one conflicting claim (under the bonnet) is a weak Q&A answer.

## Other fields requested
| Field | Status |
|---|---|
| Exact model name / generation | Done for priority models; generation numbering conflicts recorded in `source_conflicts.csv` |
| Production years | Month/year start and end text from Wikipedia for each priority generation (`production_start_text/end_text`); per-year records only where a source lists the 款 |
| Body style / doors | Doors documented for most priority generations (source per row); one-line body style text; **exterior design descriptions NOT collected** (no source text describes styling beyond body class; Seal 'fastback') |
| Trims | 299 Chinese 款型 names with Autohome spec IDs and photo counts. English trim names only in notes; `trim_name_en` is empty |
| Colours per model year | Chinese names exact; hex swatches from gallery (display colour, not a paint spec) |
| English colour names | **Not documented officially for China-market colours.** Only market names from OEM sites/brochures (Seal AU, Atto 3 Nepal, India/Europe snippets). Supplier-published English names are stored in `supplier_published_en_names` for the 76 linked colours and are NOT official |

## Known gaps (full list in `missing_data.csv`, `unmapped_specs.csv`, `excluded_specs.csv`)
* 13 priority-scope gaps: years with no 款 in the gallery (Dolphin 2022, Qin PLUS 2022, Song PLUS 2022, e2 2022), model-years with no colour photo (Dolphin 2026, Seagull 2026, Han 2027, ...), missing door counts for next-generation rows.
* 5 specs could not be assigned to EV/DM-i (Europe-export and special editions); 2 concept-car specs excluded.
* The Autohome gallery is a Chinese-market view only. Export colours (Australia, UK, India, Europe, Nepal, Philippines) exist only as batch-1 snippet-level records.
* No colour record has OEM-document evidence for China-market model years (BYD China site model pages did not expose colours).
* The two list-page years 'Han DM-i 2020' and 'Song Plus DM-i 2020' look wrong (see conflicts).

## Source reliability summary
OEM-class: BYD Australia Seal brochure (read in full, colour names only), BYD China Dahan EV page, BYD India/Nepal/Europe pages (snippets). Everything else is secondary (Autohome, Wikipedia, media) or retailer catalog. See `sources.csv` (reliability column).

## Suggested next steps (needs your decision)
1. Acquire real code evidence: label photos, BYD parts catalog / paint-formula access, or a licensed refinish database. Without it, codes stay POSSIBLE.
2. Fill export-market colours per year from BYD country sites and brochures (AU, UK, EU, Brazil, TH) for the priority models.
3. Continue to the remaining BYD-group models with the same pipeline (Seal 07/DM-i, Seal 05/06, Sealion, Tang, Song L/Pro, Frigate, Denza, Yangwang, Fangchengbao, Linghui).
4. Decide how to treat gallery-observed colours (lower bound) vs an official list when importing.
