# Batch 3 validation report

**RESULT: ALL HARD CHECKS PASSED**

| Check | Result | Detail |
|---|---|---|
| image_id unique | PASS | 47662 rows |
| (spec, photo id) unique | PASS | 47662 unique pairs |
| image -> trim/model/generation/year consistent | PASS | 0 problems, e.g. []; unlinked(model unresolved)=347 |
| image URLs well-formed; spec/series/photo/category/colour ids in the source URL agree with the row | PASS | 0 problems, e.g. []; 47662 photo-page URLs parsed |
| required per-image fields present | PASS | image_url, source_page_url, category, attribution, licence, collected_at |
| each image appears in exactly its category's gallery dataset | PASS | {'exterior': 6014, 'interior_cockpit': 21167, 'interior_seats': 19877, 'official_press': 604} |
| view labels: only exterior images, only CANDIDATE or individually inspected, never VERIFIED | PASS | 0 problems [] |
| colour associations: image, trim, colour facet and factory_colors record consistent | PASS | 0 problems []; 5519 associations; 0 without a factory_colors record |
| swatches: trim/colour FKs and hex format | PASS | 965 swatches, 0 problems |
| logos: brand FK and Wikimedia URL | PASS | 6 logos |
| every trim/spec has a final status | PASS | 317 specs; {'COMPLETED': 314, 'PARTIAL': 3} |
| status counts equal image rows (non-exterior categories) | PASS | 0 mismatches [] |
| no trim left in FAILED_RETRY_REQUIRED (publish gate) | PASS | 0 trims: [] |
| every PARTIAL trim was re-fetched at least once (retry log has its URLs) | PASS | 3 PARTIAL trims; not retried: [] |
| no staged file overwrites an existing dataset file | PASS | collisions: [] |
| previously committed datasets unchanged (git status) | PASS | modified tracked files: [] |
| no test/partial outputs in the staged dataset | PASS |  |
