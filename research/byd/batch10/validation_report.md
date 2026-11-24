# Batch 10 validation report

Run: 2026-11-24 06:26 UTC · `research/byd/validate_batch10.py` · base commit `8ae4f435479939ea17bc444bf77c40e65666f6b5`

**Result: ALL CHECKS PASSED** (46/46)

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | report states at the top that no genuine OEM evidence was obtained; 0/0/0 verified counts | PASS |  |
| 2 | report contains the required figures table (items 1-7) and top-20 / evidence / next-batch sections | PASS |  |
| 3 | no record in any Batch 10 table is VERIFIED_OEM, VERIFIED_LABEL or CORROBORATED | PASS |  |
| 4 | every source from Batches 1-9 is present in source_audit (nothing deleted) | PASS | [] |
| 5 | source_audit: every row has a class and a lineage; class vocabulary known | PASS | Counter({'MEDIA_PORTAL_CATALOG': 115, 'ENCYCLOPEDIA': 90, 'MANUFACTURER_CONTROLLED': 30, 'RETAILER_TOUCHUP_PAINT': 14, 'SEARCH_RECORD': 13, 'LICENSED_PAINT_SYSTEM': 11, 'MEDIA_ARTI |
| 6 | only retailer/touch-up sources carry vehicle paint codes; no manufacturer-controlled source carries one | PASS |  |
| 7 | source_audit: original type and first batch preserved; reclassified rows say so | PASS |  |
| 8 | each source_audit row states its status effect (no source can verify alone) | PASS |  |
| 9 | exactly 5 paint-code lineages; OEMatch+DipYourCar are one lineage; Touch Up Paint Factory+Cartouch are one lineage (copies counted once) | PASS | ['L-PC-CARROSS', 'L-PC-COLOURTUBES', 'L-PC-CROP', 'L-PC-OEMATCH-LUNA', 'L-PC-TUPF-CARTOUCH'] |
| 10 | graph has a node for every lineage and no node claims OEM grade | PASS |  |
| 11 | graph edges carry evidence text; merge rule documented | PASS |  |
| 12 | total lineage count in stats equals distinct lineages of non-search, non-placeholder sources | PASS | 27 |
| 13 | priority groups in the requested order: 雪域白, 攀岩灰, 亚特兰蒂斯灰, 苍穹蓝 | PASS |  |
| 14 | every competing code of each priority colour is listed (none dropped, none added) | PASS |  |
| 15 | every code row names its supporting sources (registered) and lineages, independence note and explanation tests | PASS |  |
| 16 | all conflict rows OPEN; no winner chosen; no label/official evidence claimed | PASS |  |
| 17 | single-lineage support is flagged NOT INDEPENDENT | PASS |  |
| 18 | reference identifiers kept separate: BYHB-00001 is PAINT_SYSTEM_REFERENCE, never a vehicle code | PASS |  |
| 19 | model_year_consistency has exactly one row per catalogue colour record (1,223) | PASS | 1223 |
| 20 | model/generation/model-year relationships and Chinese colour names exactly as the catalogue; missing years stay UNKNOWN | PASS | [] |
| 21 | status vocabulary valid; counts match stats; no verified status | PASS |  |
| 22 | different generations/years/markets are never merged: rows keyed per colour record; matte Chinese names flagged MATTE separately | PASS |  |
| 23 | year flags are explained (every flagged row has a reason) and counted | PASS |  |
| 24 | every candidate-bearing record states evidence type, lineages and unresolved questions | PASS |  |
| 25 | required per-record fields present (brand, model, year, Chinese + English/transliterated name, codes, finish, lineage, evidence, status, questions) | PASS |  |
| 26 | evidence_requirements: rules for all seven statuses and exactly 20 ranked colour requirements, the four priority colours first | PASS |  |
| 27 | every colour requirement states minimum evidence and what does not count | PASS |  |
| 28 | CORROBORATED rule requires genuinely independent lineages; verbal/retailer/formula/name matches excluded | PASS |  |
| 29 | owner requests do not ask for a VIN and claim no label location; offer voluntary identity options only | PASS |  |
| 30 | dealer requests: VIN only by the owner, in person, voluntarily; researchers never collect it; no location claims | PASS |  |
| 31 | Chinese and English versions cover the same items (owner and dealer) | PASS |  |
| 32 | checklist covers redaction, GPS stripping, label context shots, VIN-vs-paint-code guide, formula identifier, VERIFIED_LABEL conditions, and states no official location is confirmed | PASS |  |
| 33 | unresolved questions cover the four priority colours, lineages, model-year, real-world evidence, other brands | PASS |  |
| 34 | privacy/secrets: no VIN-like 17-character strings, no tokens | PASS |  |
| 35 | all deliverables except validation_report.md / manifest exist | PASS |  |
| 36 | Batch 9 base commit present | PASS | 8ae4f435479939ea17bc444bf77c40e65666f6b5 |
| 37 | Batches 1-9: all 237 files at 8ae4f435 present and byte-identical (git blob comparison) | PASS | mismatch=[] missing=[] |
| 38 | no stray new files outside batch10 and its scripts | PASS | [] |
| 39 | application files untouched (non-research diff vs base) | PASS |  |
| 40 | Batch 3 validator (validate_batch3.py) passes on a clean checkout of b39bff8 | PASS | exit 0 |
| 41 | Batch 4 validator (validate_batch4.py) passes on a clean checkout of cb78fcb | PASS | exit 0 |
| 42 | Batch 5 validator (validate_batch5.py) passes on a clean checkout of 43ec2cd | PASS | exit 0 |
| 43 | Batch 6 validator (validate_batch6.py) passes on a clean checkout of f3b8f83 | PASS | exit 0 |
| 44 | Batch 7 validator (validate_batch7.py) passes on a clean checkout of 9c594da | PASS | exit 0 |
| 45 | Batch 8 validator (validate_batch8.py) passes on a clean checkout of 5cd5bd7 | PASS | exit 0 |
| 46 | Batch 9 validator (validate_batch9.py) passes on a clean checkout of 8ae4f43 | PASS | exit 0 |

## Row counts

- source_audit.csv: 296
- source_lineage_graph.csv: 64
- colour_conflict_audit.csv: 16
- model_year_consistency.csv: 1223
- evidence_requirements.csv: 27

## Notes

- The validator proves traceability and preservation: every earlier source is still present, every colour record is audited once, every priority-colour code is listed with its sources, and nothing is promoted or resolved.
- Previous-batch integrity: every research file of Batches 1-9 at the Batch 9 commit is compared by git blob id with the working tree; per-area digests are in `previous_batches_manifest.txt`.
- Validators for Batches 3-9 were each run on a clean `git worktree` checkout of the commit that completed that batch.
