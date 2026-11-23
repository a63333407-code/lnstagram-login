# Batch 3 image verification report

## What is and is not verified
* **Vehicle linkage (trim / year / generation / model):** every image comes from the gallery of one exact Autohome 款型 (spec id). The spec id, series id and photo id embedded in each source-page URL were checked against the row (47662 URLs parsed; see validation report). Autohome's own labelling of that spec is the only evidence; no editor reviewed it.
* **Colour association:** 5519 images are linked to a colour because they appear in that trim's colour-filtered gallery (URL contains the colour facet id). It is Autohome's colour label; I did not machine-check photo colour against the swatch. Colours with no gallery for the exact trim have **no** image (no substitute or generic image is used).
* **View labels (front / rear / left / right / 3-4):** **nothing is VERIFIED** (no human editor). Status counts: {"UNKNOWN_NO_SEQUENCE_CONTEXT": 495, "CANDIDATE": 5109, "MODEL_REVIEWED_NOT_EDITOR_VERIFIED": 15, "UNKNOWN_NON_STANDARD_GALLERY_SIZE": 375, "REVIEWED_GALLERY_IRREGULAR_NO_LABEL": 20}.
  * `CANDIDATE`: label taken from the position in a 7/8-photo colour gallery. Autohome's usual order is front-left 3/4, front, front-right 3/4, left side, rear-left 3/4, rear, rear-right 3/4, right side (8-photo galleries only). In my sample **16 of 19** non-empty galleries followed this order and **3 did not** (dealer-showroom shoots). These labels are therefore a prior, not a fact.
  * `MODEL_REVIEWED_NOT_EDITOR_VERIFIED`: images I looked at individually (one full 8-photo gallery at 480x360; the position-4 image of 7 further galleries, nose pointing left = left side). A model reviewed them, not a human editor.
  * `REVIEWED_GALLERY_IRREGULAR_NO_LABEL`: galleries I found to deviate; no label assigned.
  * `UNKNOWN_*`: no basis (plain exterior list, or gallery size is not 7/8).
* **Left/right rule used:** nose pointing left in the image = car's left (driver) side visible.
* **Interior images:** only two source categories exist (中控方向盘, 车厢座椅). Dashboard vs steering wheel vs centre console, and front vs rear seats, are **not distinguished**. Interior colour names/swatches are recorded per trim but photos are not linked to interior colours.
* **Official press images:** Autohome category 官图 (53). Provenance is by category label only; per-image credit is not provided. They are not classified as exterior/interior.
* **Resolution:** thumbnails only (400x300 / 480x360). Full-size URLs were not harvested.
* **Swatch HEX:** supplied by Autohome's colour facet; not sampled from photos and not a paint specification.
* **Rights:** no image licence is cleared (see image_sources.csv). Do not publish or hot-link without permission.
* **Collection timestamps:** the main harvest recorded a run-level window only (2026-11-23T16:07:53Z to 2026-11-23T16:33:34Z); per-image time exists only for images re-fetched in retry rounds.

## Live URL spot check (seeded random sample, run after the build)

| URL type | sampled | resolved OK (HTTP 200 + expected content type) | rate-limited, not verified live | failed |
|---|---|---|---|---|
| image_url | 100 | 100 | 0 | 0 |
| source_page_url | 40 | 40 | 0 | 0 |
| color_gallery_photo_page_url | 10 | 10 | 0 | 0 |
| logo_url | 6 | 5 | 1 | 0 |

Detail per URL: `url_spot_check.csv`. A 429 means the host throttled this machine; the URL itself was returned by the MediaWiki API (see brand_logos.csv) but could not be re-fetched live in this run.
