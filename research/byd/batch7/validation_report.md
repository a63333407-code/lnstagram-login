# Batch 7 validation report

Run: 2026-11-24 05:40 UTC · `research/byd/validate_batch7.py` · base commit `f3b8f83c33c7f79b41b3efef053b249917324def`

**Result: ALL CHECKS PASSED** (31/31)

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | always-required fields non-empty | PASS | 0 |
| 2 | colour-record rows carry model (intl name; Chinese name exactly as catalog - may be NULL for models without one) and catalog ids | PASS |  |
| 3 | colour-record rows with a named model year match the catalog; blank year never invented | PASS |  |
| 4 | record ids unique | PASS |  |
| 5 | all requested field columns exist | PASS |  |
| 6 | status vocabulary: POSSIBLE/CONFLICTED/UNVERIFIED only (no VERIFIED_*/CORROBORATED) | PASS | Counter({'POSSIBLE': 323, 'CONFLICTED': 108}) |
| 7 | no row is above POSSIBLE regardless of lineage count (repetition is not corroboration) | PASS |  |
| 8 | formula-system references kept separate from vehicle paint-code candidates (code_role) | PASS |  |
| 9 | no code typed or roled as OEM | PASS |  |
| 10 | every source id registered in sources.csv | PASS | [] |
| 11 | sources.csv: usable_as_oem_verification never YES | PASS |  |
| 12 | independent_lineage_count correct; OEMatch + DipYourCar count as one lineage | PASS | [] |
| 13 | every code is traceable to a source record (harvested listing, baseline candidate or Batch 6 row) | PASS | [] |
| 14 | colour-record relationships valid; Chinese colour name unchanged; no cross-brand name linking | PASS | [] |
| 15 | delta labels consistent with Batch 6 (NEW_ROW/STATUS_CHANGED/SOURCE_ADDED) | PASS | [] |
| 16 | pipeline reproduces Batch 6 exactly when DipYourCar is excluded (self-check) | PASS | {'batch6_keys': 672, 'reproduced_keys': 672, 'identical': True} |
| 17 | every CONFLICTED colour record in the delta file has a conflict row | PASS |  |
| 18 | conflict ids unique; all OPEN (nothing silently resolved) | PASS |  |
| 19 | lineage, colour-class and label-location conflicts recorded | PASS |  |
| 20 | every source named in conflicts exists | PASS | [] |
| 21 | lineage analysis: OEMatch vs DipYourCar identical-name share >= 60% (same upstream) | PASS | 95% |
| 22 | vin_research: fields present, sources registered, flag vocabulary, nothing marked a confirmed VIN->code route | PASS | 16 |
| 23 | vin_research: VIN-decode, certificate, nameplate, dealer, paint-system methods all covered | PASS |  |
| 24 | vin_research: dealer route marked unverified for BYD | PASS |  |
| 25 | sample plan: models exist, statuses valid, rows sorted by priority | PASS | 63 |
| 26 | evidence template stores no raw VIN (hash + first 9 chars only) | PASS |  |
| 27 | all required deliverables exist | PASS |  |
| 28 | Batch 6 base commit present | PASS | f3b8f83c33c7f79b41b3efef053b249917324def |
| 29 | Batches 1-6 files unchanged vs f3b8f83c (git diff + untracked) | PASS |   |
| 30 | application files untouched (non-research diff vs base) | PASS |  |
| 31 | Batch 6 validator passes on a clean checkout of f3b8f83c | PASS | PASS  Batch 5 validator passes on a clean checkout of 43ec2cdb  PASS  application files untouched (n |

## Row counts

- discovered_codes.csv (changes vs Batch 6): 431
- sources.csv: 39
- vin_research.csv: 16
- conflicts.csv: 39
- source_lineage_analysis.csv: 34
- verification_sample_plan.csv: 63

## Scope notes

- Validates internal consistency, traceability to harvested listings and previous-batch integrity; it cannot prove that any supplier code is the factory code.
- Any VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED status would fail validation: no OEM document, dealer record or exact-vehicle label evidence was obtained in Batch 7.
- The self-check proves the Batch 6 matching pipeline, re-implemented in `build_batch7.py`, reproduces Batch 6 exactly before the new source is added.
