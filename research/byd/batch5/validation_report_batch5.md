# Batch 5 validation report

Run: 2026-11-24 04:19 UTC · script `research/byd/validate_batch5.py` · base commit `cb78fcb9638fa73d363393b5d0ae10731c25a00a`

**Result: ALL CHECKS PASSED** (26/26)

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | every code record has >=1 source id | PASS | 0 without |
| 2 | every source id is in the baseline or Batch 5 register | PASS |  |
| 3 | every code record has a source URL | PASS |  |
| 4 | evidence_status in the six allowed values | PASS |  |
| 5 | VERIFIED rows carry oem_paint_code + page + quote | PASS | 0 verified rows |
| 6 | oem_paint_code empty unless VERIFIED_* | PASS |  |
| 7 | no retailer-only row is above POSSIBLE/CONFLICTED | PASS |  |
| 8 | no CORROBORATED without >=2 non-retailer independent sources | PASS |  |
| 9 | POSSIBLE/CONFLICTED rows never combined (single status token) | PASS |  |
| 10 | model / generation / model-year / colour relationships valid; Chinese colour name unchanged | PASS | [] |
| 11 | link_id exists and code matches baseline | PASS |  |
| 12 | no duplicate (colour, code) records | PASS |  |
| 13 | record_ids unique | PASS |  |
| 14 | every CONFLICTED colour has a conflict row | PASS |  |
| 15 | every multi-code colour is flagged in conflicts | PASS |  |
| 16 | conflict ids unique | PASS |  |
| 17 | model_coverage covers all 137 baseline models once | PASS |  |
| 18 | unresolved list covers all colour records that are not verified | PASS | 1223 rows |
| 19 | colour status consistent between unresolved list and code records | PASS |  |
| 20 | model_coverage status counts sum to colour records | PASS |  |
| 21 | no model claims reliable paint-code evidence without verified rows | PASS |  |
| 22 | label evidence: no code value recorded without exact vehicle link | PASS |  |
| 23 | label evidence: no VERIFIED_LABEL without visual inspection | PASS |  |
| 24 | base commit present | PASS | cb78fcb9638fa73d363393b5d0ae10731c25a00a |
| 25 | Batch 1-4 files unchanged vs cb78fcb9 (git diff) | PASS |   |
| 26 | application files untouched (non-research tracked diff vs base) | PASS |  |

## Row counts

- oem_paint_codes.csv: 446
- vehicle_label_evidence.csv: 9
- source_register.csv: 23
- paint_code_conflicts.csv: 133
- unresolved_paint_codes.csv: 1223
- model_coverage.csv: 137

## Scope notes

- The validator proves internal consistency and traceability; it cannot prove that a supplier code is correct. All code rows are POSSIBLE/CONFLICTED by design.
- Verified-status rules are enforced as constraints: with no OEM document or exact-vehicle label in evidence, any VERIFIED_* or CORROBORATED row would fail validation.
