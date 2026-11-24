# Batch 6 validation report

Run: 2026-11-24 05:22 UTC · `research/byd/validate_batch6.py` · base commit `43ec2cdb88ab8dfd1b321b43287e1ebad2887ebd`

**Result: ALL CHECKS PASSED** (29/29)

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | required fields non-empty on every row | PASS | 0 |
| 2 | all 13 requested fields exist as columns | PASS |  |
| 3 | record ids unique | PASS |  |
| 4 | status vocabulary (POSSIBLE/CONFLICTED/UNVERIFIED only; no VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED) | PASS | Counter({'POSSIBLE': 713, 'CONFLICTED': 290}) |
| 5 | no third-party code typed as OEM | PASS | Counter({'SUPPLIER_LISTED_OEM_STYLE_CODE': 887, 'SUPPLIER_OR_PAINT_SYSTEM_STYLE_IDENTIFIER': 60, 'SUPPLIER_LISTED_LEGACY_HYPHEN_CODE': 40, 'SUPPLIER_LISTED_NUMERIC_STYLE_CODE': 16} |
| 6 | every source id registered in sources.csv | PASS | [] |
| 7 | every source id exists in baseline or is B6S* | PASS |  |
| 8 | every row has an https source URL | PASS |  |
| 9 | sources.csv: OEM-verification flag never YES | PASS |  |
| 10 | every code is traceable to a source record (baseline candidate/link or harvested listing) | PASS | [] |
| 11 | model / year / colour relationships valid; Chinese colour name unchanged | PASS | [] |
| 12 | brand matches the catalog brand for linked models | PASS |  |
| 13 | name-equivalence links only attach to BYD-brand colour records (not cross-brand) | PASS |  |
| 14 | no duplicate (colour record, code) rows | PASS |  |
| 15 | one status per colour record | PASS |  |
| 16 | every CONFLICTED colour record has a conflict row (and vice versa) | PASS | 100 |
| 17 | every multi-code POSSIBLE colour is flagged | PASS |  |
| 18 | conflict ids unique | PASS |  |
| 19 | conflicts carry resolution status (no arbitrary choice) | PASS |  |
| 20 | formula identifiers investigated: WA2, HA4, B9, BYD007WA2 | PASS |  |
| 21 | B9 / BYD007WA2 not claimed as found | PASS |  |
| 22 | no identifier marked verified | PASS |  |
| 23 | lookup colour ids exist and match discovered rows | PASS |  |
| 24 | lookup statuses within vocabulary | PASS |  |
| 25 | all required deliverables exist | PASS |  |
| 26 | Batch 5 base commit present | PASS | 43ec2cdb88ab8dfd1b321b43287e1ebad2887ebd |
| 27 | Batches 1-5 files unchanged vs 43ec2cdb (git diff + untracked) | PASS |   |
| 28 | application files untouched (non-research diff vs base) | PASS |  |
| 29 | Batch 5 validator passes on a clean checkout of 43ec2cdb | PASS | PASS  application files untouched (non-research tracked diff vs base) |

## Row counts

- discovered_codes.csv: 1003
- lookup_model_year_colour.csv: 496
- sources.csv: 18
- conflicts.csv: 34
- formula_identifier_investigation.csv: 6

## Scope notes

- Validates internal consistency and traceability to the harvested listings; it cannot prove any supplier code is the factory code.
- Any VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED status would fail validation: no OEM document or exact-vehicle label evidence was found in Batch 6.
