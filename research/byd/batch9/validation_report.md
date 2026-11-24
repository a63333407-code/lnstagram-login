# Batch 9 validation report

Run: 2026-11-24 06:06 UTC · `research/byd/validate_batch9.py` · base commit `5cd5bd71309c8e1f2e137b49fdfe6b8180348151`

**Result: ALL CHECKS PASSED** (40/40)

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | report states plainly at the top that no genuine OEM paint code was verified and no field evidence was obtained | PASS |  |
| 2 | report separates the five required categories | PASS |  |
| 3 | contact results: 5 channels x 5 questions, identical question set per channel | PASS |  |
| 4 | no call is claimed: every row NOT_CALLED / UNANSWERED with empty date, caller, operator, verbatim, reference | PASS |  |
| 5 | required channels are exactly BYD 950858, 400-830-3666, Fangchengbao 950859 | PASS | {'K01': '950858', 'K02': '400-830-3666', 'K03': '950859'} |
| 6 | every contact number has provenance and an evidence-register entry | PASS |  |
| 7 | verbal answers verify nothing (status_effect says so) | PASS |  |
| 8 | Chinese call script contains the five questions and says no call was made | PASS |  |
| 9 | exactly two cases T01 and T02 with ten steps each | PASS |  |
| 10 | cases PENDING; consent NOT_OBTAINED; all steps NOT_PERFORMED; no outcome, no document | PASS |  |
| 11 | VIN fields empty (hash/prefix to be filled only by the owner's own record); no full VIN anywhere | PASS |  |
| 12 | case data match Batch 8 targets (model, colour, candidate codes, status); status unchanged | PASS |  |
| 13 | T01 is Seal 亚特兰蒂斯灰 and T02 is Han EV 雪域白 | PASS |  |
| 14 | workflow demands owner consent, own VIN only, hash + 9-char prefix, exact reason when not provided | PASS |  |
| 15 | outcome vocabulary covers refusal, no-field, verbal-only, formula-only, owner presence | PASS |  |
| 16 | evidence register: nothing supports a status upgrade | PASS |  |
| 17 | pending field evidence items are NOT_OBTAINED (calls, T01, T02, Baslac test) | PASS |  |
| 18 | licensing restriction recorded (Baslac formulas cannot be stored) | PASS |  |
| 19 | no status other than the seven appears in any Batch 9 table | PASS |  |
| 20 | no VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED assigned to any record | PASS |  |
| 21 | all 39 carried conflict rows appear exactly once (29 scored groups + 10 cross-cutting) | PASS | 29+10 |
| 22 | all 107 conflicted colour records mapped exactly once, with tier of their group | PASS |  |
| 23 | record tiers equal their group's tier; colour names unchanged vs catalog | PASS |  |
| 24 | score equals the documented formula for every group | PASS | [] |
| 25 | tier thresholds consistent (A>=14, B 11-13, C<=10) and priority ids ranked by score | PASS |  |
| 26 | no conflict resolved; none decided by majority vote or site count | PASS |  |
| 27 | each scored group's candidate codes equal the Batch 7 conflict's codes (nothing added, nothing dropped) | PASS |  |
| 28 | privacy/secrets: no VIN-like 17-character strings, no tokens | PASS |  |
| 29 | other brands: Linghui and unreachable Denza page recorded as not found/not reachable; no claim of inspecting inaccessible sources | PASS |  |
| 30 | all deliverables except validation_report.md / manifest exist | PASS |  |
| 31 | Batch 8 base commit present | PASS | 5cd5bd71309c8e1f2e137b49fdfe6b8180348151 |
| 32 | Batches 1-8: all 224 files at 5cd5bd71 present and byte-identical (git blob comparison) | PASS | mismatch=[] missing=[] |
| 33 | no stray new files outside batch9 and its scripts | PASS | [] |
| 34 | application files untouched (non-research diff vs base) | PASS |  |
| 35 | Batch 3 validator (validate_batch3.py) passes on a clean checkout of b39bff8 | PASS | exit 0 |
| 36 | Batch 4 validator (validate_batch4.py) passes on a clean checkout of cb78fcb | PASS | exit 0 |
| 37 | Batch 5 validator (validate_batch5.py) passes on a clean checkout of 43ec2cd | PASS | exit 0 |
| 38 | Batch 6 validator (validate_batch6.py) passes on a clean checkout of f3b8f83 | PASS | exit 0 |
| 39 | Batch 7 validator (validate_batch7.py) passes on a clean checkout of 9c594da | PASS | exit 0 |
| 40 | Batch 8 validator (validate_batch8.py) passes on a clean checkout of 5cd5bd7 | PASS | exit 0 |

## Row counts

- dealer_contact_results.csv: 25
- field_verification_cases.csv: 22
- evidence_register.csv: 13
- conflict_priority.csv: 146

## Notes

- The validator proves that no call, dealer response, VIN, document or code was fabricated: every field-evidence cell is empty and every status is unchanged.
- Previous-batch integrity: every research file of Batches 1-8 at the Batch 8 commit is compared by git blob id with the working tree; per-area digests are in `previous_batches_manifest.txt`.
- Validators for Batches 3-8 were each run on a clean `git worktree` checkout of the commit that completed that batch (the Batch 8 validator in turn re-runs Batches 3-7).
