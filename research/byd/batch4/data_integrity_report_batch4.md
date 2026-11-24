# Batch 4 merged-catalog integrity report

**RESULT: ALL CHECKS PASSED**

| Check | Result | Detail |
|---|---|---|
| primary keys unique in every merged table | PASS | 137 models, 155 generations, 387 model-years, 1382 trims, 1223 colours |
| generation -> model FK | PASS |  |
| model-year -> generation/model FK and (generation, year) unique | PASS |  |
| trim -> model-year/generation/model consistent | PASS | 1382 trims |
| one trim per Autohome spec id | PASS |  |
| colour -> model/generation/model-year consistent | PASS | 1223 colours, 0 problems [] |
| every colour has a source id that exists | PASS |  |
| link -> colour/code FKs | PASS | 446 links |
| no VERIFIED anywhere (codes, links, verification records) | PASS | verification statuses: {'POSSIBLE': 542, 'NOT FOUND': 1066} |
| all model-year rows are SOURCED (no estimates in the merged table) | PASS | estimates stay in batch-2 estimates_model_years.csv only |
| every model has a catalog row | PASS | 137 rows |
| every model with an Autohome mapping has images or documented gap | PASS |  |
| every model without trims is explained in missing_data_b4.csv | PASS |  |
| every harvested trim has a final status | PASS | {'COMPLETED': 1080, 'PARTIAL': 8} |
| no duplicate (brand, model_key); cross-brand key collisions are only the documented one | PASS | cross-brand collisions: {'e5': ['B2', 'B6']} (BYD e5 vs Linghui e5: all lookups are brand-aware) |
| every dimension row equals a parsed Wikipedia infobox and cites its page | PASS | 165 dimension rows, 0 untraceable [] |
| every documented door count has a source id | PASS | 132 generations with doors, 0 without source |
| batch-4 door counts come from a Wikipedia infobox body_style | PASS | 133 fact rows |
| confirmed OEM paint-code table is empty and no paint code has an OEM tier | PASS | 139 codes, all RETAILER_CATALOG_UNVERIFIED/POSSIBLE; confirmed OEM codes: 0 |
| link confidence audit: no 'high'; audited confidence never above original | PASS | {('medium', 'low'): 48, ('low', 'low'): 346, ('medium', 'medium'): 52} |
| all 309 Chinese colour names have a reviewed glossary entry labelled unofficial | PASS | 309 entries; kinds partly transliterated (pinyin) - weakest: 28; literal: 242; two-tone (literal): 16; proper name / place name: 23 |
| no gloss is stored as an official English name | PASS | official flag only on OEM-source market names |
| every unmapped trim has a reason, candidates, evidence and a resolution path | PASS | 18 unmapped trims |
| every model without an Autohome series has a reason, evidence and absence check | PASS | 12 models |
| batch 1-3 datasets unchanged (git status) | PASS | modified tracked non-script files: [] |
