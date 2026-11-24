# Batch 7 - OEM paint-code deep discovery (BYD Group)

**Research only.** No application file was changed, nothing was imported, nothing was published; Batches 1-6 are unchanged (validated by `git diff` against `f3b8f83c33c7f79b41b3efef053b249917324def`).

## Bottom line

1. **No factory paint code was verified** (VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED = 0). Every record is a retailer-derived candidate (POSSIBLE or CONFLICTED).
2. **The useful result is a method.** The evidence now shows how a factory code can and cannot be obtained, and what a verifiable record must contain (below). In short: **the VIN is only a key; the only OEM-sourced route is the BYD service system's build record, read by a BYD service centre; paint-system formulas (AkzoNobel, BASF, Donglai) are downstream of the OEM code, not a way to find it.**
3. **New OEM evidence, Chinese-market:** four Chinese-language BYD owner's manuals (Seal 2025, Song PLUS EV, Han L EV, Han DM-i) list the vehicle nameplate (整车铭牌, lower right B-pillar) contents - company, brand, country, model, seats, build date, motor and battery data, VIN, maximum mass - with **no paint/colour item**. Together with Batch 5's ATTO 3 manual, the B-pillar nameplate is **not** where a BYD colour code is printed, and none of the manuals I read documents a colour-code label (absence from a manual is not proof that none exists).
4. **New regulatory evidence:** China's vehicle certificate standard GB/T 21085-2020 says the certificate's body-colour field is filled with one of ten colour classes (白灰黄粉红紫绿蓝棕黑) - **a colour family, never a code.** Useful to narrow candidates, useless to pick between WA2 and W36C.
5. **Repeated retailer listings are one source, not many.** DipYourCar's BYD list (92 titles) is the same data as OEMatch's: of 60 codes both list, 57 (95%) carry identical romanised names and abbreviations. Records now carry `independent_lineage_count`; the highest in this batch is 4 and such rows are still only POSSIBLE or CONFLICTED.

## Recommended repeatable method: VIN + model year + original colour -> factory code

The method separates *finding the code* (OEM data) from *turning it into a formula* (paint system), and says what evidence upgrades a catalogue record.

| Step | Action | Output | Evidence class |
|---|---|---|---|
| 0 | Collect VIN, model, model year, market, colour name from invoice/brochure, and the **colour class on the 合格证** (white/grey/...). Look up the model + year + colour name in `batch6/lookup_model_year_colour.csv` (and `batch7/discovered_codes.csv`) | shortlist of candidate codes, status POSSIBLE/CONFLICTED | candidates only |
| 1 | Narrow by colour class and finish (gloss vs matte) | fewer candidates | candidates only |
| 2 | Inspect the car for any printed colour label (location undocumented by BYD - check bonnet area, door frames/sills, boot, service booklet); **photograph it with the VIN plate in the same frame** | label photo | **VERIFIED_LABEL** if code + VIN + model + year are visible |
| 3 | **Ask a BYD service centre to read the factory colour from the build record by VIN** (script in `vin_research.csv`, V16); photograph/screenshot the screen or printout with VIN visible | dealer record | **VERIFIED_OEM** if the record shows VIN + code + colour name (name the shop and date) |
| 4 | Only with a verified OEM code: look it up in the paint system (AkzoNobel colour retrieval takes make + year + colour code; BASF chips are sorted by OEM with the code on the back; check variants (偏差色)); store the formula/variant ID in a **separate** field | formula reference | `FORMULA_SYSTEM_REFERENCE`, never an OEM code |
| 5 | If no code can be obtained: spectrophotometer match (Axalta Acquire or equivalent) or chip match; record the result as a formula match to the car's *current* paint, check respray history | formula for current paint | not a factory code |

**Rules that keep the database honest**
- A supplier code, a repeated supplier code, or a formula ID never becomes OEM-verified. Only an OEM-origin record (dealer system, OEM document) or a label photograph tied to the exact vehicle does.
- `code_role` separates `VEHICLE_PAINT_CODE_CANDIDATE` from `FORMULA_SYSTEM_REFERENCE_CANDIDATE` (e.g. BYHB-00001-style identifiers).
- Evidence submissions use `vin_evidence_template.csv`: **no raw VIN is committed** - store a SHA-256 hash and the first nine characters (WMI+VDS, which identify the model, not the car); keep photos/screenshots in a private store.
- `verification_sample_plan.csv` ranks 63 model/colour targets for the first dealer or label checks (20 are CONFLICTED, so one read settles a dispute). Priority models first: Seal (8), Dolphin (6), Seagull (3), Atto 3 / Yuan PLUS (6), Han (13), Qin PLUS (9), Song PLUS (11), Destroyer 05 (3), e2 (2), Yangwang U9 (1), Yangwang U8 (1).

## What the research found, by area

**A. Professional paint systems** (`vin_research.csv` V09-V12)
- **AkzoNobel:** colour retrieval takes *make, year, colour code and/or colour group* and returns a formula. The OEM code is an input.
- **BASF (Baslac 百事利 / Glasurit):** chips are sorted by OEM, each chip maps to one standard formula, the **OEM code is printed on the chip back**, and deviation variants (偏差色, darker / finer / coarser) are listed in Formula Finder. A variant or formula ID is therefore not the OEM code. Baslac's Formula Finder is reachable only through a terms click-through; I did not accept terms on your behalf, so whether it lists BYD is **untested - a quick manual check is worthwhile**.
- **Axalta:** colour retrieval plus a spectrophotometer that matches the paint actually on the car (no code needed, no factory code returned).
- **Donglai (东来) = Onwings** (Shanghai, STAR-listed 688129; brands onwings/onwaves/fixs): no public colour-retrieval page found.
- **BYD itself** says its 精诚钣喷 service uses AkzoNobel, BASF and Donglai with '原厂数据、原厂配方' - so BYD's repair network works from factory data held in those systems and BYD's own records.

**B. Chinese data ecosystem** (V01, V08, V13, V14)
- **17vin** offers VIN decoding (web/API), EPC-level parts data and a BYD repair-manual index; whether a decode returns colour/code is unknown and needs a test with an owned VIN.
- Generic VIN decoders and vendor guides agree the VIN does not contain the paint code. JD/Chinese retail lists colour names only. No Chinese-language page documents a VIN -> BYD paint-code lookup.

**C. OEM evidence** (V02-V07, V15, V16)
- Eleven BYD owner's manuals reviewed (7 export + 4 Chinese-market; keyword-searched, nameplate sections read): five state the nameplate contents (none include paint) and none of the label inventories I read (Seal 2025 in full) lists a colour-code label. The Seal 2025 manual warns against unnecessary respray 'to prevent mismatched colour'.
- The dealer VIN read-out is the only plausible OEM route and is **unverified for BYD**: no public BYD document describes it. V16 gives the question script to use.

**D. Brand coverage**
- BYD: the DipYourCar harvest adds rows (below). Denza, Yangwang, Fangchengbao, Linghui: **no new code data**; BYD-hosted domestic manuals for these brands were not found (paths not guessed). Yangwang U8/U9 and Fangchengbao Bao 5/8 remain model-level supplier rows from Batch 6; Denza and Linghui have none.

## Discovery results (changes versus Batch 6)

| Measure | Value |
|---|---|
| Rows in `discovered_codes.csv` (only what is new or changed) | **431** (375 linked to catalog colour records, 56 code-only) |
| NEW_ROW / SOURCE_ADDED / SOURCE_ADDED_SAME_LINEAGE / STATUS_CHANGED | 105 / 270 / 42 / 14 |
| Status of these rows POSSIBLE / CONFLICTED | 323 / 108 |
| Colour records with at least one candidate code (all batches, recomputed) | 436 (POSSIBLE 329, CONFLICTED 107) |
| DipYourCar titles / distinct (code, name) pairs / matched to BYD colour records / code-only | 92 / 91 / 35 / 56 |
| Code tokens new to the catalog (from DipYourCar) | 19: CA8, CAJ, EA5, EA7, EAF, EAP, EX, HCH, HDK, HE3, JN, L15C, R14C, S-01, UAK, UAY, UBG, UBM, YC8 |
| Independent-lineage count of delta rows (1 / 2 / 3 / 4) | 295 / 120 / 13 / 3 - **all still POSSIBLE or CONFLICTED** |
| VIN/method rows (`vin_research.csv`) / sources (`sources.csv`) / conflict rows | 16 / 39 / 39 |

Changes in statuses: conflict detection now merges sources of one lineage (same-site pairs TUPF S32/S226 and Carross S31/S227, and OEMatch + DipYourCar) before comparing code sets, so a retailer cannot create a 'disagreement' with its own twin; the normaliser also strips 'P.', 'X.', 'S1' abbreviations (this resolves one Batch 6 code-only row, HAZ, to the colour 苍烟色). The build re-runs the Batch 6 pipeline without the new source and asserts it reproduces Batch 6 exactly before adding anything.

## Identifier classes (what is what)

| Class | Meaning | Where seen | Status |
|---|---|---|---|
| OEM / factory paint code | printed or recorded by BYD for the vehicle | nowhere confirmed | none |
| Vehicle paint-code candidate | retailer-listed short code (AAP, HB5, UA6, W36C, L-27...) presented as the factory code | all retailers | POSSIBLE / CONFLICTED |
| Formula-system reference | identifier from a paint system or retailer (BYHB-00001, BYHA-00002; AkzoNobel/BASF formula or variant numbers) | TUPF lists; paint-system documentation | kept in `code_role=FORMULA_SYSTEM_REFERENCE_CANDIDATE`; never merged with vehicle codes |
| Colour class | one of ten Chinese colour words on the 合格证 | GB/T 21085-2020 | regulatory fact, not a code |

## Conflicts preserved

`conflicts.csv` (39 rows): CODE_VS_CODE_SAME_NAME ×2, COLOUR_CLASS_VS_CODE ×1, FINISH_TYPE ×1, GLOSS_VS_MATTE_CODE_PAIR ×1, LABEL_LOCATION ×1, MULTI_CODE_ALIAS_GROUP ×11, NAME_MATCH_REVIEW ×3, RETAILER_LINEAGE ×1, SOURCES_DISAGREE_NESTED ×9, SOURCES_DISAGREE_NOT_NESTED ×9. Highlights: 雪域白 (W36C / WA2 / WA8 / BYHB-00001), 亚特兰蒂斯灰 (HB5 / HB6), matte-vs-gloss code pairs (now from one lineage, so not stronger), 合格证 colour class vs code, label location. All OPEN.

## Limitations

- Nothing here verifies a code. The dealer route is the one most likely to, and it is untested.
- DipYourCar/OEMatch lists are not exhaustive (search endpoint limit); matching is by colour name and pinyin equality; model-year applicability is never confirmed.
- The Baslac Formula Finder, 17vin decoding and the BYD App were not used (terms/credentials/ownership); their BYD coverage is unknown.
- Domestic manuals for Denza, Yangwang, Fangchengbao and Linghui were not found; only BYD-brand manuals were read.
- GB/T 18411-2018's plate content table is behind a paywall.

## Next steps

1. Take the top rows of `verification_sample_plan.csv` to a BYD service centre with the V16 script (and VIN of a car whose owner agrees); log results in `vin_evidence_template.csv`. A handful of reads on conflicted colours (Seal 亚特兰蒂斯灰, 雪域白 on Han/Qin PLUS/Song PLUS, Atto 3 colours) would settle whether the retailer codes are factory codes.
2. Test the Baslac Formula Finder (after reading its disclaimer) and a Donglai distributor for BYD entries; chips with codes on the back are a second, paint-maker-sourced check.
3. Test a 17vin decode with a VIN you own to see which fields come back.
4. Photograph candidate label locations on several BYD cars with the VIN plate in frame.
