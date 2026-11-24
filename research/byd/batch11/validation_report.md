# Batch 11 validation report

Run: 2026-11-24 06:48 UTC · `research/byd/validate_batch11.py` · base commit `0baa8ac225c74396c5fdcdea4cf156073be5f54d`

**Result: ALL CHECKS PASSED** (44/44)

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | report states at the top that no field evidence was received and no code verified; 0/0/0 | PASS |  |
| 2 | report contains the eight required figures | PASS |  |
| 3 | no VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED status anywhere in the Batch 11 tables | PASS |  |
| 4 | every official-document colour row is literally present in the recorded PDF extract (name and, where printed, Chinese name) | PASS |  |
| 5 | each official-document colour has an extract excerpt line naming it | PASS |  |
| 6 | brand-page colour rows come from the recorded page extract | PASS |  |
| 7 | no official row contains a paint code; official colour names never marked as code evidence | PASS |  |
| 8 | required fields present: URL, date basis, model, market, year basis, Chinese name basis, finish statement, paint-code flag | PASS |  |
| 9 | Chinese names are 'printed' only for the Macau Seal brochure and official brand pages; others say NOT STATED | PASS |  |
| 10 | finish stated per colour only where the document says so (D11); equipment-line finish not treated as per-colour | PASS |  |
| 11 | Cambodia 'Seal 5 DM-i 海豹' is mapped to Seal 05 DM-i (M021), never to Destroyer 05 (M019); 'Sealion 6' to M031 | PASS |  |
| 12 | priority models without an official table are recorded as NOT_FOUND (Han EV, Qin PLUS, Song PLUS EV, e2, Destroyer 05) | PASS |  |
| 13 | BYD China model pages recorded as dynamic; API not called | PASS |  |
| 14 | official brochure counts: 13 fetched, 12 with exterior names, 1 with Chinese names, 0 with a paint code | PASS |  |
| 15 | model_year_colour_catalog has exactly one row per colour record (1,223); statuses identical to Batch 10 | PASS |  |
| 16 | catalogue rows keep exact model/generation/model-year/colour name; production year stays UNKNOWN; separate fields present | PASS | [] |
| 17 | official_doc_support values valid and consistent with the official table | PASS |  |
| 18 | link audit covers exactly the 709 existing colour/code links (none deleted, none added) | PASS |  |
| 19 | audit history preserved: Batch 5/6/7 statuses recorded exactly as in the earlier files | PASS |  |
| 20 | name_only_flag is YES exactly for NAME_ONLY support; counts match stats (212 / 497) | PASS |  |
| 21 | every link carries year, finish, market and production-period checks and a primary class; mismatch flag matches the year check | PASS |  |
| 22 | link statuses unchanged vs Batch 10 (reference identifiers stay PAINT_SYSTEM_REFERENCE) | PASS |  |
| 23 | codes are not propagated: no code in the catalogue exists that is absent from the Batch 6/7 links of that colour record | PASS |  |
| 24 | field evidence register: three intake checks found nothing; all evidence types and 20 target slots PENDING; nothing received | PASS |  |
| 25 | evidence rules cover label photo, dealer written reply, owner build record, OEM document and forbid full VINs | PASS |  |
| 26 | priority conflict updates: all four colours, each with FACT, HYPOTHESIS, MINIMUM_EVIDENCE, BATCH11_STATUS and catalogue rows | PASS |  |
| 27 | every competing code of Batch 10's audit is preserved (none dropped, none added) | PASS |  |
| 28 | facts cite sources; hypotheses are graded HYPOTHESIS; no majority vote; conflicts stay OPEN | PASS |  |
| 29 | source_audit: new official sources are manufacturer-controlled (or dealer-hosted) with no paint codes; failed URLs flagged HTTP 404/000 and unused | PASS |  |
| 30 | source_audit includes every fetched official document, China page and brand page | PASS |  |
| 31 | privacy/secrets: no VIN-like 17-character strings, no tokens | PASS |  |
| 32 | all deliverables except validation_report.md / manifest exist | PASS |  |
| 33 | Batch 10 base commit present | PASS | 0baa8ac225c74396c5fdcdea4cf156073be5f54d |
| 34 | Batches 1-10: all 255 files at 0baa8ac2 present and byte-identical (git blob comparison) | PASS | mismatch=[] missing=[] |
| 35 | no stray new files outside batch11 and its scripts | PASS | [] |
| 36 | application files untouched (non-research diff vs base) | PASS |  |
| 37 | Batch 3 validator (validate_batch3.py) passes on a clean checkout of b39bff8 | PASS | exit 0 |
| 38 | Batch 4 validator (validate_batch4.py) passes on a clean checkout of cb78fcb | PASS | exit 0 |
| 39 | Batch 5 validator (validate_batch5.py) passes on a clean checkout of 43ec2cd | PASS | exit 0 |
| 40 | Batch 6 validator (validate_batch6.py) passes on a clean checkout of f3b8f83 | PASS | exit 0 |
| 41 | Batch 7 validator (validate_batch7.py) passes on a clean checkout of 9c594da | PASS | exit 0 |
| 42 | Batch 8 validator (validate_batch8.py) passes on a clean checkout of 5cd5bd7 | PASS | exit 0 |
| 43 | Batch 9 validator (validate_batch9.py) passes on a clean checkout of 8ae4f43 | PASS | exit 0 |
| 44 | Batch 10 validator (validate_batch10.py) passes on a clean checkout of 0baa8ac | PASS | exit 0 |

## Row counts

- official_colour_tables.csv: 164
- model_year_colour_catalog.csv: 1223
- field_evidence_register.csv: 27
- code_link_quality_audit.csv: 709
- priority_conflict_updates.csv: 41
- source_audit.csv: 56

## Notes

- Official colour names were checked against short text excerpts recorded from the downloaded PDFs and pages (the documents themselves are not stored).
- Previous-batch integrity: every research file of Batches 1-10 at the Batch 10 commit is compared by git blob id with the working tree; per-area digests are in `previous_batches_manifest.txt`.
- Validators for Batches 3-10 were each run on a clean `git worktree` checkout of the commit that completed that batch.
