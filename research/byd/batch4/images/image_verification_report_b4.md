# Batch 4 image verification report

## What is and is not verified
* **Vehicle linkage (trim / year / generation / model):** every image comes from the gallery of one exact Autohome trim (spec id). The spec id, series id and photo id inside each source-page URL were checked against the row for all 156,401 images (validation report). Autohome's labelling is the only evidence; no editor reviewed it. Trims whose EV/DM-i variant could not be resolved keep their images as `UNLINKED_MODEL_UNRESOLVED` (2,832 images).
* **No invented URLs:** every image URL, photo-page URL and gallery URL in the tables appears in a harvested record (checked against raw_b4/autohome_images.jsonl.gz and the retry records).
* **Colour association:** 18,537 images are linked to a colour because they appear in that trim's colour-filtered gallery (the URL carries the colour facet id). It is Autohome's colour label; photo colour vs swatch was not machine-checked. A colour with no gallery for the exact trim has no image (no substitute is used).
* **View labels:** **nothing is VERIFIED** (no human editor). Status counts: {"UNKNOWN_NO_SEQUENCE_CONTEXT": 1890, "UNKNOWN_NON_STANDARD_GALLERY_SIZE": 4147, "REVIEWED_GALLERY_IRREGULAR_NO_LABEL": 28, "CANDIDATE": 14713, "MODEL_REVIEWED_NOT_EDITOR_VERIFIED": 16}.
  * `CANDIDATE`: label from the position in a 7/8-photo colour gallery. In my visual review of 32 galleries from 32 different series, **28 followed the standard order and 4 did not** (all dealer-showroom shoots). With batch 3 (16 of 19) that is 44 of 51 galleries (86%), so a candidate label can be wrong about one time in seven.
  * `MODEL_REVIEWED_NOT_EDITOR_VERIFIED`: the 16 images I looked at individually at 400x300 (position 4 = left side, position 8 = right side in 8 galleries; nose direction checked in each). A model reviewed them, not a human editor.
  * `REVIEWED_GALLERY_IRREGULAR_NO_LABEL`: galleries I found to deviate; no label assigned.  `UNKNOWN_*`: no basis (plain exterior list, or a gallery size other than 7/8).
* **Left/right rule:** nose pointing left in the image = car's left (driver) side visible.
* **Interior images:** only two source categories exist (中控方向盘, 车厢座椅); dashboard vs steering wheel vs centre console and front vs rear seats are not distinguished. Interior colours are recorded as names/swatches per trim; photos are not linked to interior colours.
* **Official press images:** Autohome category 官图 (53); provenance by category label only, not classified as exterior/interior.
* **Resolution:** thumbnails only (400x300 / 480x360). No full-size image was downloaded or its URL harvested (batch 4 scope).
* **Swatch HEX:** supplied by Autohome's colour facet; not sampled from photos and not a paint specification.
* **Rights:** no image licence is cleared (same terms as batch 3). Do not publish or hot-link without permission.
* **Collection timestamps:** run-level window (2026-11-24T02:02:39Z to 2026-11-24T03:44:23Z); per-image time only for images re-fetched in retry rounds.

## Live URL spot check (seeded random sample, run after the build)

| URL type | sampled | resolved OK (HTTP 200 + expected content type) | rate-limited, not verified live | failed |
|---|---|---|---|---|
| image_url | 100 | 100 | 0 | 0 |
| source_page_url | 40 | 40 | 0 | 0 |
| color_gallery_photo_page_url | 10 | 10 | 0 | 0 |

Detail per URL: `url_spot_check_b4.csv`.
