# Batch 5 - BYD Group OEM paint-code verification

**Research only.** No application file was modified, nothing was imported into any application, nothing was published. Batch 1-4 datasets are unchanged (validated by `git diff` against `cb78fcb9638fa73d363393b5d0ae10731c25a00a`).

## Bottom line

**No genuine factory (OEM) paint code could be verified for any BYD Group vehicle.** I found no OEM paint-code document (repair manual, paint-repair procedure, parts/colour table) and no photographed original vehicle label tied to an exact vehicle that shows a colour code. All 139 paint-code entries (51 distinct code tokens) that exist in the catalog still come only from retail touch-up-paint catalogs and therefore remain POSSIBLE (or CONFLICTED where those catalogs disagree). The rules of this batch forbid promoting them, so none were promoted. A smaller verified database is better than a guessed one - and here the verified database is empty; this report says so rather than papering over it.

### Required summary

| Measure | Value |
|---|---|
| Models researched | **137** (BYD 96, Denza 19, Fangchengbao 11, Yangwang 7, Linghui 4) |
| Colour records researched | **1223** (same 1,223 colour records as the Batch 4 catalog) |
| VERIFIED_OEM | **0** |
| VERIFIED_LABEL | **0** |
| CORROBORATED | **0** |
| POSSIBLE | **199** colour records (393 colour-to-code links) |
| CONFLICTED | **28** colour records (53 colour-to-code links) |
| UNVERIFIED (no code evidence of any kind) | **996** colour records |
| Models with no reliable (OEM-grade) paint-code evidence | **137 of 137** - every model |
| ...of which have no code from any source, not even a retailer | **107** models (21 of these also have no colour record at all) |
| Distinct supplier code tokens in play | 51 (the baseline's 139 paint-code entries group these) |

Status counts are per colour record (each colour record has exactly one status; statuses are never combined). A colour record with several candidate codes appears as several rows in `oem_paint_codes.csv`, all carrying the same status.

## What was searched and what it returned

**Priority 1 - OEM documentation.**
- BYD repair / body-repair / paint manuals are dealer-gated. No public BYD paint-code or colour table was found. Search for Axalta, PPG, Glasurit, Standox, Spies Hecker and BASF BYD colour libraries returned nothing (those databases are login-gated and not indexed).
- Third-party portals/mirrors that claim to hold BYD repair manuals were checked only at the access level: `byd.ev-manual.com` is a paid portal whose landing page shows no colour data; the two GitHub mirror repositories returned HTTP 403 (not enabled for this session). They were not pursued: their provenance cannot be verified and they are probably unauthorised copies of restricted documents, so they could never support VERIFIED_OEM anyway. Paywalls were not circumvented.
- I-CAR's OEM Technical Information Matrix is a US index of whether repair information exists; it contains no paint codes and no BYD entry surfaced.
- **Seven official BYD owner's manuals were downloaded from byd.com, converted to text and searched in full (paint code / colour code / body colour / paint colour / nameplate); their vehicle-identification sections were read** (ATTO 3 EU 2024, ATTO 3 Middle East, ATTO 3 2022, ATTO 3 EVO 2026, Dolphin Surf, ATTO 2 Long Range, ETP3). None contains a paint/colour-code table or a colour-code field (keyword search; image-only content was not OCR'd).

**Priority 2 - vehicle labels.** `vehicle_label_evidence.csv` records what the manuals say (9 rows).
- Six manuals place the *vehicle nameplate* at or under the (right) B-pillar - the Middle East ATTO 3 manual says only 'under the B-pillar' - (ETP3: 15 cm below the lock ring on the front right door).
- **The ATTO 3 (2022) manual lists the nameplate's contents** - company, brand, country of manufacture, model, seats, build year/month, motor model and peak power, battery voltage and capacity, VIN, maximum mass - **and no paint/colour item.** So for the ATTO 3 the OEM-documented B-pillar plate does not carry a paint code, which contradicts generic retailer statements (CROP: under bonnet / driver's door / B-pillar; Chipex: door jamb or engine compartment) and leaves the real location of any BYD colour code undocumented. A weak Autohome Q&A answer (baseline S34) says a plate under the bonnet shows 'paintcolor' or 'H/S'; unverified.
- No photograph of an original label tied to an identified vehicle (model, year, VIN) was found, so **VERIFIED_LABEL = 0**. Generic label examples are not accepted as evidence.
- Visual inspection: two nameplate pages (ATTO 3 EU p.205, Dolphin Surf p.187) were rendered and viewed; they show the nameplate location only, no sample plate text.

**Priority 3 - supplier/retailer evidence.** Unchanged from Batch 4: Colour Tubes, Cartouch, Carross and Touch Up Paint Factory. They are retailers, none cites an OEM source, and the same upstream data can sit behind several of them, so agreement between them is **not** treated as corroboration (CORROBORATED = 0). Their codes are stored in `supplier_candidate_code`; `oem_paint_code` is empty for every row. No BYD-issued touch-up part number exists in what I found (retailer pens such as Greendrive/CROP are aftermarket).

## Priority series

| # | Series | Catalog model | Colour records | With any supplier code | POSSIBLE | CONFLICTED | UNVERIFIED | OEM-verified |
|---|---|---|---|---|---|---|---|---|
| 1 | Seal | M020 Seal | 35 | 19 | 8 | 11 | 16 | 0 |
| 2 | Dolphin | M026 Dolphin | 33 | 23 | 20 | 3 | 10 | 0 |
| 3 | Seagull | M028 Seagull | 35 | 13 | 13 | 0 | 22 | 0 |
| 4 | Atto 3 / Yuan PLUS | M016 Yuan Plus | 42 | 21 | 8 | 13 | 21 | 0 |
| 5 | Han | M002 Han DM-i | 19 | 4 | 4 | 0 | 15 | 0 |
| 5 | Han | M036 Han EV | 31 | 10 | 10 | 0 | 21 | 0 |
| 5 | Han | M128 Han DM | 3 | 2 | 2 | 0 | 1 | 0 |
| 5 | Han | M129 Han DM-p | 3 | 0 | 0 | 0 | 3 | 0 |
| 6 | Qin PLUS | M007 Qin Plus DM-i | 32 | 10 | 10 | 0 | 22 | 0 |
| 6 | Qin PLUS | M039 Qin Plus EV | 16 | 8 | 8 | 0 | 8 | 0 |
| 7 | Song PLUS | M034 Song Plus DM-i | 16 | 11 | 11 | 0 | 5 | 0 |
| 7 | Song PLUS | M049 Song Plus EV | 18 | 10 | 10 | 0 | 8 | 0 |
| 7 | Song PLUS | M133 Song Plus (ICE) | 4 | 0 | 0 | 0 | 4 | 0 |
| 8 | Destroyer 05 | M019 Destroyer 05 | 14 | 8 | 8 | 0 | 6 | 0 |
| 9 | e2 | M027 e2 | 26 | 4 | 4 | 0 | 22 | 0 |

Note: Han L, Qin L, Song L and the Dynasty/Ocean DM-i and EV variants outside the list above are in the remaining-model pass (`model_coverage.csv`); Song PLUS (M047 Sealion 06 EV alias) is not counted under rank 7 because its alias relationship is ambiguous.

## Conflicts (nothing merged silently)

`paint_code_conflicts.csv` has 133 rows: 28 colour records where suppliers list different code sets (status CONFLICTED; 26 nested - one supplier lists a subset of another's codes, which may be an incomplete listing rather than a contradiction - and 2 not nested), 86 multi-code alias groups where all suppliers agree on the same several codes (status POSSIBLE with an ambiguity flag), 17 codes matched to more than one Chinese colour name (informational), and 2 label-location/nameplate-content conflicts between OEM manuals and retailer guidance. Examples include Yuan PLUS 攀岩灰 (HAN vs HA4/HAN) and 滑雪白 (WAC vs W46C/WAC), and Seal 亚特兰蒂斯灰 (HB5 vs HB6).

## Coverage by brand

| Brand | Models | Colour records | Models with any supplier code |
|---|---|---|---|
| BYD | 96 | 988 | 28 |
| Denza | 19 | 120 | 0 |
| Fangchengbao | 11 | 71 | 0 |
| Yangwang | 7 | 38 | 2 |
| Linghui | 4 | 6 | 0 |

Denza, Fangchengbao and Linghui have no supplier code listings at all; the colour names exist (from Autohome galleries) but no code evidence of any kind has been found.

## Limitations

- The retailer codes may well be correct, but nothing obtained here can show it. A code is NOT an OEM code merely because several shops print it.
- Supplier matching is by colour name, not by VIN; listings are model-level or name-only, so model-year applicability is unconfirmed for every row. 31 of the 1223 colour records have no model year assigned in the Batch 4 baseline; their year fields are left empty, never filled in.
- Only seven owner's manuals were read, and they describe the nameplate, not a colour code. Owner's manuals for the other models and Chinese-market manuals were not reviewed in this batch.
- Search-engine snippets were used for retailer location guidance (CROP, Chipex); those pages were not read in full.

## What would actually verify codes

1. BYD dealer/body-repair paint documentation, obtained through a licensed route (e.g. BYD repair-information portal, or a refinish-system vendor's licensed BYD library), for the exact model-year and market.
2. Photographs of original vehicle labels with the VIN, model and year visible, from owners/body shops, with permission. Where the colour code is physically printed on BYD vehicles first needs to be established (the ATTO 3 B-pillar nameplate is documented as not carrying it).
3. A VIN-based dealer lookup for sample vehicles per model-year (one per series would already establish whether supplier codes are right).

## Files

All in `research/byd/batch5/`: `oem_paint_codes.csv` (code-level records; supplier codes separate from OEM codes), `vehicle_label_evidence.csv`, `source_register.csv`, `paint_code_conflicts.csv`, `unresolved_paint_codes.csv`, `model_coverage.csv`, `validation_report_batch5.md`, plus `stats_batch5.json`. Reproducible with `research/byd/build_batch5.py`, `build_batch5_report.py`, `validate_batch5.py`.
