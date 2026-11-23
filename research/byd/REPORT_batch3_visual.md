# BYD visual catalog - Batch 3 report (priority models)

Status: research only. **No application files modified. Nothing imported.** No image files are stored (URLs and metadata only).
Batch 1 and batch 2 datasets are unchanged (verified with `git status` inside the validation gate).
Rebuild: `python3 build_batch3_visual.py` (reads `raw/`, writes to a staging folder, publishes only if `validate_batch3.py` passes), then `python3 raw/spot_check_urls.py`.

## Harvest result
| Item | Result |
|---|---|
| Trims (exact 款型) harvested | **317** (all concept-car specs excluded) |
| Final status | **COMPLETED 314 / PARTIAL 3 / NO_IMAGES_AVAILABLE 0 / FAILED_RETRY_REQUIRED 0** (`trim_harvest_status.csv`) |
| Images (unique per trim + photo) | **47,662** (all 480x360 thumbnails) |
| - exterior | 6,014 |
| - interior cockpit (dashboard / steering wheel / centre console area) | 21,167 |
| - seats / cabin | 19,877 |
| - official press (官图) | 604 (on 57 of 317 trims) |
| Linked to an exact trim, year, generation, model | 47,315; **347 unlinked** (5 specs whose EV/DM-i variant could not be resolved, kept with `UNLINKED_MODEL_UNRESOLVED`) |
| Images linked to a factory colour | 5,519 (from colour-filtered galleries of the same trim; 286 trims have colour galleries) |
| Colour swatches | 726 exterior (per trim) + 239 interior options (25 distinct interior names, 181 trims) |
| Brand logos | 6 (BYD group, BYD, Denza, Yangwang, Fangchengbao, Linghui) with licence metadata |
| Dimensions | 16 rows from Wikipedia infoboxes (per generation; variants/markets kept as stated) |
| Models with images | 15 model records in 9 series; **114 BYD-group models not yet researched** (`image_coverage_by_model.csv`) |

### How completeness was judged
Autohome states the photo total for every category on each trim page. A trim is COMPLETED only if the harvested count equals Autohome's own total for all four categories and for every colour-filtered gallery.
* **A redirect is never a success.** When a category has no photos Autohome answers HTTP 302 to the trim landing page. 278 category lists were like this; each was requested again and confirmed (`raw/empty_category_checks.jsonl`, HTTP code and UTC time) and is reported as *confirmed empty*, not as harvested, and not as a failure.
* **Genuine failures were retried.** The retry pass re-fetched every list whose count disagreed with the stated total, with full pagination, up to 4 rounds (`raw/retry_log_N.jsonl`). 2 requests failed with a network error (connection reset) and succeeded on a later attempt.
* **3 PARTIAL trims** remain after 4 retry rounds. Each returns HTTP 200 but the page shows no photo list even though Autohome's colour facet claims photos: Song PLUS 2021 EV 旗舰型 (spec 45550, 赤帝红: 7 stated, 0 served), Yuan PLUS 2022 510KM 旗舰型 (spec 52183, 冲浪蓝: 7 stated, 0 served), Yuan PLUS 2022 510KM 旗舰型PLUS (spec 55070, 滑雪白: 14 stated, 7 served). This is a source inconsistency, not a harvest fault; the other categories of these trims are complete.

## Quality rules and what they mean for the data
1. **Exact generation/year.** Images come only from the gallery of one exact trim (spec id). The spec id, series id and photo id inside each source-page URL were checked against the row for all 47,662 images.
2. **No generic substitutes.** A colour with no gallery for the exact trim has no image (`missing_images_report.csv` lists 64 text-only colour records).
3. **View labels (front / rear / left / right / 3-4) are NOT verified.** 5,109 exterior images carry a `CANDIDATE` label taken from their position in a 7/8-photo colour gallery. In my sample 16 of 19 galleries followed that order and 3 did not (dealer-showroom shoots), so a candidate label can be wrong. 15 images I looked at individually are `MODEL_REVIEWED_NOT_EDITOR_VERIFIED` (a model, not a human editor); 20 are in galleries I found irregular (no label); 870 have no basis (`UNKNOWN_*`). **Zero images are VERIFIED.** Left = car's left (driver) side, read from nose direction.
4. **Interior images are not subdivided.** The source has only two categories (中控方向盘, 车厢座椅). Dashboard vs steering wheel vs centre console, and front vs rear seats, cannot be separated from the data. Interior colour names/swatches exist per trim, but photos are not linked to interior colours (interior-colour galleries were not harvested).
5. **Official press images** = Autohome category 官图, presented as manufacturer-supplied; no per-image credit exists and they are not classified as exterior/interior.
6. **HEX values** are Autohome's own facet swatches (source-supplied, not sampled from photos, not paint specifications).
7. **Rights: nothing is cleared.** Autohome photos (several show 汽车之家 plates) are presumed all-rights-reserved; Denza's logo is fair-use on English Wikipedia only; all logos are trademarks. Do not publish or hot-link without permission (`image_sources.csv`, `brand_logos.csv`).
8. **Timestamps.** The main harvest recorded a run-level window (2026-11-23T16:07:53Z to 16:33:34Z), not a time per image; retry-round images and all HTTP checks have exact UTC times.

## Validation (`validation_report_batch3.md`: all hard checks passed)
Unique ids; image -> trim / model / generation / year consistent; URL ids agree; every image in exactly its category dataset; view-label rules; colour associations consistent with `factory_colors`; swatch and logo foreign keys; all 317 trims have a final status and the status counts equal the image rows; no trim in FAILED_RETRY_REQUIRED; every PARTIAL trim was retried; no earlier dataset modified; no test/partial output published.
**Live spot check** (`url_spot_check.csv`): 100/100 sampled image URLs, 40/40 photo pages, 10/10 colour-gallery pages and 5/6 logos resolved correctly; the 6th (Linghui logo) was throttled (HTTP 429) by Wikimedia from this machine and is reported as *not verified live*.

## Files
| File | Content |
|---|---|
| `vehicle_images.csv` | master: one row per image with URL, source page URL, vehicle/generation/year/trim ids, category, view label + status, colour association + evidence URLs, attribution, licence, collection time |
| `exterior_images.csv` / `interior_images.csv` / `seat_images.csv` / `official_press_images.csv` | gallery datasets keyed by `image_id` |
| `vehicle_color_images.csv`, `color_swatches.csv` | image-to-colour links and swatches (exterior + interior) |
| `brand_logos.csv`, `vehicle_dimensions.csv`, `vehicle_identification.csv` | identification data (identification is one row per trim) |
| `image_sources.csv` | sources, rights holder, licence status |
| `trim_harvest_status.csv` | final status per trim with expected vs harvested counts |
| `missing_images_report.csv`, `failed_requests_report.csv`, `image_verification_report.md`, `validation_report_batch3.md`, `url_spot_check.csv` | reports |
| `raw/` | harvest and retry logs, expected counts, scripts (`harvest_images.py`, `retry_failures.py`, `confirm_empty_categories.py`, ...) |

## Not done in this batch
* Full-size images (each photo page exposes a larger version) and interior-colour-filtered galleries.
* Wikimedia Commons / official BYD press kits as additional, licence-clean image sources.
* The remaining 114 BYD-group models (Seal 05/06/07, Sealion, Tang, Song L/Pro, Denza, Yangwang, Fangchengbao, Linghui, ...).
* Any human review of view labels.
