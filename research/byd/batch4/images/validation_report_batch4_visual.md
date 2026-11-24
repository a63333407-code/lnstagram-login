# Batch 4 visual validation report

**RESULT: ALL HARD CHECKS PASSED**

| Check | Result | Detail |
|---|---|---|
| image_id unique within batch 4 and disjoint from batch 3 | PASS | 156401 rows |
| (spec, photo id) unique and disjoint from batch 3 | PASS | 156401 pairs |
| swatch_id unique and disjoint from batch 3 | PASS | 2956 swatches |
| image -> trim/model/generation/year consistent (union catalog) | PASS | 0 problems, e.g. []; unlinked(model unresolved)=2832 |
| image URLs well-formed; spec/series/photo/category/colour ids in the source URL agree with the row | PASS | 0 problems, e.g. [] |
| required per-image fields present | PASS | url, source page, category, attribution, licence, collected_at |
| each image appears in exactly its category's gallery dataset | PASS | {'exterior': 20794, 'interior_cockpit': 66255, 'interior_seats': 67412, 'official_press': 1940} |
| view labels: exterior only; CANDIDATE or individually inspected; never VERIFIED | PASS | 0 problems [] |
| colour associations consistent with trim, facet and factory_colors | PASS | 0 problems []; 18537 associations; 0 without a factory_colors record |
| swatches: trim/colour FKs and hex format | PASS | 2956 swatches, 0 problems |
| every trim/spec has a final status | PASS | 1088 specs; {'COMPLETED': 1080, 'PARTIAL': 8} |
| status counts equal image rows (non-exterior categories) | PASS | 0 mismatches [] |
| no trim left in FAILED_RETRY_REQUIRED (publish gate) | PASS | 0 trims: [] |
| no unexplained or unresolved failed request remains | PASS | {'NOT_A_FAILURE_CATEGORY_EMPTY': 1075, 'GENUINE_MAIN_RUN_FAILURE_RECOVERED_BY_RETRY': 2, 'GENUINE_NETWORK_FAILURE_RECOVERED': 29} |
| every PARTIAL trim was re-fetched at least once | PASS | 8 PARTIAL trims; not retried: [] |
| no invented image URLs: every image URL, photo-page URL and gallery URL appears in a harvested record | PASS | 156401 images; not harvested: 0 image urls, 0 page urls, 0 list urls |
| previously committed datasets (batches 1-3) unchanged (git status) | PASS | modified tracked non-script files: [] |
| no test/partial outputs in staging | PASS |  |
