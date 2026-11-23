# BYD Catalog Research Dataset — Batch 1 report

Status: research only. Application NOT modified. Nothing imported. Awaiting approval.
Regenerate everything with `python3 build_dataset.py` (counts in `stats.json`).

## Headline numbers
| # | Metric | Value |
|---|---|---|
| 1 | Models discovered | **127** across BYD Group (88 on the BYD brand itself; Denza 19, Yangwang 6, Fangchengbao 10, Linghui 4) |
| 2 | Generation records | **136** (one per source row; only 9 models have 2 documented generations) |
| 3 | Model-year records | **315**, of which only **131** are documented years (intro/facelift), 180 are *derived* from intro→discontinued ranges for legacy models, 4 come from colour sources |
| 4 | Factory colour records | **45** (34 distinct names), attached to only **4 generations + 1 unresolved Qin PLUS set** |
| 5 | Documented paint codes | **0** |
| 6 | Missing / uncertain | see below |
| 7 | Sources | 14 (see `sources.csv`) |

## 6. Missing or uncertain
- **Paint codes: 0 of 45 colour records.** All 46 verification records = NOT FOUND. No source examined contains a BYD OEM code. The NonPaints page was reviewed and rejected (generic examples only, none tied to a model).
- **Colours: 132 of 136 generations (97%) have no colour data.**
- **Model years:** 18 generations have no intro year at all. Per-year production/colour availability is not documented for any model; only anchor years are.
- **Series unassigned:** 22 BYD-brand models have no Dynasty/Ocean assignment (blank in the Wikipedia extract; not guessed).
- **Trims: 0** collected. **Exterior design: NULL** for all. **Doors:** documented for 6 only.
- **Alias collisions in the source** (need editor decision before import, to avoid duplicates):
  `Seal 6 DM-i` (Qin L DM-i vs Seal 06 DM-i); `King` and `Seal 5 DM-i` (Destroyer 05 vs Seal 05 DM-i); `e2` (Dolphin export name vs e2 model).
- **Snippet-only sources:** 11 of 14 sources (all colour sources except the Australian Seal brochure) were seen only as search-result summaries and must be re-fetched before colours are trusted.
- English names for the Qin PLUS colours are my literal translations of the Chinese, not official names.
- Conflict: India Seal colours listed as 5 by BYD India but 4 by another source.

## Scope notes / assumptions to confirm
1. "BYD" was taken as the whole group (BYD, Denza, Yangwang, Fangchengbao, Linghui). The BYD brand alone is 88 models / 97 generations.
2. "Model" = distinct nameplate+powertrain row; Wikipedia's separate EV/DM-i rows are separate models.
3. Commercial vehicles (buses, trucks, vans) and 21 concept cars are excluded.
4. The existing repo is a static Instagram login page with no database, so there is no schema or data to conflict with yet; the import target ("existing application") needs to be identified.
