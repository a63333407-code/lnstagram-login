# Batch 8 validation report

Run: 2026-11-24 05:57 UTC · `research/byd/validate_batch8.py` · base commit `9c594da126d3e79fd74f576ebecd3072825ad7a4`

**Result: ALL CHECKS PASSED** (37/37)

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | seven statuses defined (VERIFIED_OEM, VERIFIED_LABEL, CORROBORATED, PAINT_SYSTEM_REFERENCE, POSSIBLE, CONFLICTED, UNVERIFIED) | PASS |  |
| 2 | discovered_codes statuses within the seven; none VERIFIED_* or CORROBORATED | PASS | Counter({'PAINT_SYSTEM_REFERENCE': 60}) |
| 3 | every reference row has a BYH?-style identifier and status PAINT_SYSTEM_REFERENCE; typed as reference, never OEM | PASS |  |
| 4 | every Batch 6/7 reference-style identifier on colour records is reclassified (none missed, none invented) | PASS | 44 vs 44 |
| 5 | model-level reference rows count matches Batch 6 | PASS | 16 |
| 6 | reclassified rows keep their Batch 7 status in a separate column (colour-record statuses not changed) | PASS |  |
| 7 | required fields non-empty (brand, code, type, source, evidence, status) | PASS |  |
| 8 | every source id registered in sources.csv; all URLs https | PASS |  |
| 9 | no code appears that is absent from Batch 6/7 (nothing invented) | PASS |  |
| 10 | exactly 20 verification targets; priority list covers Seal 亚特兰蒂斯灰, 雪域白, Qin PLUS, Song PLUS, Atto 3 | PASS | {'Seal 亚特兰蒂斯灰': True, '雪域白 x>=4': True, 'Qin PLUS >=2': True, 'Song PLUS >=2': True, 'Atto 3 >=2': True} |
| 11 | targets exist in the Batch 7 sample plan with identical candidate codes and status | PASS | [] |
| 12 | targets unique and ranked 1..20 | PASS |  |
| 13 | no verification claimed: all PENDING_FIELD_EVIDENCE, no verified code, no conflict resolved | PASS |  |
| 14 | every conflict id cited by a target exists in conflicts.csv | PASS |  |
| 15 | all Batch 7 conflicts carried (none dropped) | PASS | 39 vs 39 |
| 16 | carried conflicts keep identical values/sources and stay OPEN | PASS |  |
| 17 | no conflict marked resolved | PASS |  |
| 18 | sources named in conflicts exist | PASS | [] |
| 19 | sources: Baslac terms recorded as NOT accepted; Denza/Yangwang sites recorded as not accessed | PASS |  |
| 20 | sources: nothing marked usable as OEM verification | PASS |  |
| 21 | source ids unique | PASS |  |
| 22 | all required deliverables exist | PASS |  |
| 23 | Chinese script covers VIN, build record, paint-code field, written confirmation, screenshot, evidence checklist, own-VIN rule | PASS |  |
| 24 | English script covers build record, paint-code field, written confirmation, screenshot, evidence checklist, own-VIN rule | PASS |  |
| 25 | both scripts carry the same verified hotline numbers (950858, 400-830-3666, 950859) and a VIN-free policy question | PASS |  |
| 26 | hotline numbers appear in sources.csv evidence | PASS |  |
| 27 | Baslac plan: NOT TESTED, terms not accepted, no formula copying, manual test requirement and 8 questions | PASS |  |
| 28 | privacy/secrets: no VIN-like 17-character strings, no tokens | PASS |  |
| 29 | Batch 7 base commit present | PASS | 9c594da126d3e79fd74f576ebecd3072825ad7a4 |
| 30 | Batches 1-7: all 210 files at 9c594da1 present and byte-identical (git blob comparison) | PASS | mismatch=[] missing=[] |
| 31 | no stray new files outside batch8 and its scripts | PASS | [] |
| 32 | application files untouched (non-research diff vs base) | PASS |  |
| 33 | Batch 3 validator (validate_batch3.py) passes on a clean checkout of b39bff8 | PASS | exit 0 |
| 34 | Batch 4 validator (validate_batch4.py) passes on a clean checkout of cb78fcb | PASS | exit 0 |
| 35 | Batch 5 validator (validate_batch5.py) passes on a clean checkout of 43ec2cd | PASS | exit 0 |
| 36 | Batch 6 validator (validate_batch6.py) passes on a clean checkout of f3b8f83 | PASS | exit 0 |
| 37 | Batch 7 validator (validate_batch7.py) passes on a clean checkout of 9c594da | PASS | exit 0 |

## Row counts

- discovered_codes.csv (paint-system-reference rows): 60
- sources.csv: 48
- conflicts.csv: 39
- verification_results.csv: 20

## Notes

- Previous-batch integrity is proved by comparing every research file's git blob id at the Batch 7 commit with the working tree; per-area digests are in `previous_batches_manifest.txt`.
- Each earlier validator (Batches 3-7) was run on a clean `git worktree` checkout of the commit that completed that batch.
- Nothing here verifies a paint code: all verification rows are pending field evidence.
