# Batch 8 - real OEM verification & Chinese data access (BYD Group)

**Research only.** No application file changed, nothing imported or published, Batches 1-7 untouched (blob-by-blob comparison against `9c594da126d3e79fd74f576ebecd3072825ad7a4`; all five earlier validators re-run on clean checkouts of their own commits - see `validation_report.md`).

## Bottom line

1. **No code was verified in this batch (VERIFIED_OEM 0, VERIFIED_LABEL 0, CORROBORATED 0), and none could be.** Verification needs one of three things I cannot do from here: a BYD service-centre read-out for a vehicle whose VIN you own, a photographed label on a real car, or a licence acceptance that only you can give. This batch therefore **prepares that fieldwork so it is cheap to execute and cannot be misclassified**.
2. **The Baslac Formula Finder is gated by a licence that restricts exactly what this project would do.** I read the public disclaimer without accepting it: BASF formulas are BASF property, usable only with BASF coating products, not to be passed on or saved without a separate written licence, and not to be integrated into third-party software. So **no Formula Finder data may be copied into the database** - a manual test may only record whether BYD exists and which inputs the tool takes (`baslac_manual_test_plan.md`).
3. **No Chinese data system is shown to return a BYD factory paint code.** 17vin's published API schema has no colour/paint field; no public BYD EPC, repair-data portal or Chinese paint-system lookup was found. The only plausible OEM route remains a BYD service-centre read of the build record - unverified.
4. **A VIN-free first step now exists:** call BYD's official line (950858, or 400-830-3666 from the manuals) and ask the policy question in `dealer_inquiry_*.md` section 3b. It needs no VIN and tells us whether the route exists at all.

## Task 1 - BASF / Baslac Formula Finder

| Question | Answer | Evidence |
|---|---|---|
| Is BYD listed? | **Unknown - not tested.** Tool is behind a click-through I did not accept | B8S01 |
| BYD models/years available? | Unknown | - |
| Does it accept OEM paint codes? | Not documented publicly. Baslac says its chips are sorted by OEM and each chip maps to one standard formula; vendor tools generally take the OEM code as input (AkzoNobel: make + year + colour code; Glasurit: code printed on chip back) | B8S02, B7S01, B7S04 |
| OEM code vs deviation colour vs formula ID | Three different things: OEM code (input/identifier of the factory colour), deviation colours (`偏差色`, labelled darker/finer/coarser relative to the standard formula), formula/variant numbers (output). Only the first can be an OEM code; the others are PAINT_SYSTEM_REFERENCE | B7S03, B8S02 |
| Legal terms / accounts | **Not accepted, no account created.** Agreement summarised in `baslac_manual_test_plan.md` | B8S01 |
| Manual testing requirement | Yes: the user must read and decide on the agreement, then answer 8 factual questions without copying any formula; ask BASF/Baslac for written permission before storing anything displayed | `baslac_manual_test_plan.md` |
| Note on ownership | Disclaimer text: baslac is a registered trademark of BASF Coatings GmbH; page footer reads '© Surventis 2026' (operator relationship not established) | B8S01, B8S02 |

## Task 2 - BYD dealer VIN lookup

**Finding: unverified.** No public BYD document says that a service centre can retrieve original paint information by VIN, or what it displays. What is documented: BYD's service network (2,300+ outlets) runs 精诚钣喷 with AkzoNobel, BASF and Donglai refinish paints and 'OEM data, OEM formulas' (B6S01, B8S03); official lines are 950858 (B8S03), 400-830-3666 (manuals, B8S09) and, for Fangchengbao, 950859 (B8S05). Whether a screen shows a factory code, a formula number, or only a colour name is exactly what the inquiry is built to find out.

Delivered: `dealer_inquiry_zh.md` and `dealer_inquiry_en.md` - rules (own VIN only), contact channels with sources, a **VIN-free policy question**, an opening line, 15 questions covering the build record (A), paint-code field availability (B), written/screenshot confirmation (C), the shop's paint system (D), repair history (E) and fallbacks (F), a tick-box evidence checklist, and a mapping from evidence to status.

## Task 3 - Verification sample (20 targets)

`verification_results.csv` holds **20 prioritised targets** chosen from Batch 7's `verification_sample_plan.csv`: Seal (3), Han (2), Qin PLUS (3), Song PLUS (4), Atto 3 / Yuan PLUS (4), Dolphin (1), e2 (1), Destroyer 05 (1), Yangwang U9 (1). 16 of 20 are CONFLICTED. Forced picks: Seal 亚特兰蒂斯灰 (T01), 雪域白 on Han EV, Qin PLUS EV/DM-i, Song PLUS EV/DM-i and Destroyer 05 (T02-T06, T19), Atto 3 / Yuan PLUS 滑雪白, 攀岩灰, 探险绿, 跑酷红 (T07-T10). Each row names the hypothesis to test (e.g. HB5 vs HB6 gloss/matte; W36C vs WA2 vs WA8), the evidence required and a backup route. **Every row is `PENDING_FIELD_EVIDENCE`; nothing was resolved.**

## Task 4 - Chinese domestic data sources

| Source type | What was found | Access |
|---|---|---|
| BYD authorised service network | 2,300+ outlets (Dynasty/Ocean); store finders; hotline 950858; BYD App; 精诚管家 (B8S03) | public pages; paint-by-VIN capability unverified |
| BYD manuals | Domestic index covers 王朝, 海洋, 其他车型; **some manuals only in the 王朝/海洋 App after owner authentication** (B8S04) | public + owner-authenticated |
| Fangchengbao | official site, hotline 950859, manual page exists but is a JavaScript app; no PDF located (B8S05) | partly public |
| Denza, Yangwang | official sites linked from byd.com; **connection reset here - not accessed** (B8S06) | unknown |
| Linghui (领汇) | **no source found** (B8S08) | - |
| OEM parts catalogue (EPC) | none public; BYD page offers only a genuine-part anti-counterfeit check (B8S08) | not found |
| Chinese repair-data platforms | 17vin: VIN decode + EPC-level parts API; **documented schema has no colour field** (B8S07); BYD repair manuals reported to be dealer/workshop-account only (unverified resale-source claim, not used) | login/paid |
| Licensed paint databases | Baslac Formula Finder (click-through licence), Glasurit Colour Online (login), AkzoNobel colour retrieval (licensed software), Axalta colour retrieval (licensed), Donglai/Onwings (no public page) | authorised access required |

No URL was invented: every address above was taken from a fetched page or from BYD's own links; unreachable ones are marked as such.

## Task 5 - Evidence classification (seven statuses)

| Status | Meaning | Count in this batch |
|---|---|---|
| VERIFIED_OEM | dealer/OEM document shows VIN + code + colour name | 0 |
| VERIFIED_LABEL | photographed label, VIN plate in frame, model/year identifiable | 0 |
| CORROBORATED | independent OEM-grade sources agree | 0 |
| PAINT_SYSTEM_REFERENCE | formula/variant or supplier-system identifier (e.g. BYHB-00001, BYHA-00002); never an OEM code | **60 rows** (44 on colour records, 16 model-level) |
| POSSIBLE | supplier-listed vehicle-code candidate | 329 colour records |
| CONFLICTED | sources disagree | 107 colour records |
| UNVERIFIED | no code evidence | 787 of 1223 colour records |

The two reference identifiers (`BYHA-00002`, `BYHB-00001`) are reclassified in `discovered_codes.csv`; the colour records' own statuses are **not changed**. A check of whether any conflict exists *only* because of a reference identifier found **0** such colour records - every one of the 107 conflicted colour records still has a genuine disagreement between vehicle-code candidates.

## Final report

**1. What genuine OEM evidence was found?** No paint-code evidence. OEM-origin facts about the access landscape: BYD's own pages state the service network, hotlines, store finders, app-only manuals and the use of AkzoNobel/BASF/Donglai with factory data; Chinese-market manuals (Batch 7) show the nameplate carries no colour; GB/T 21085 limits the certificate to a colour class.

**2. Which systems can retrieve BYD paint information?** None is confirmed. Candidates, in order of plausibility: the BYD service system's vehicle build record (unverified); paint-system software with BYD data keyed by OEM code (AkzoNobel, BASF, Axalta, Donglai - code -> formula only); not 17vin (no colour field in its published schema).

**3. Which sources require authorised access?** BYD service/DMS records; owner-authenticated 王朝/海洋 App manuals; BYD repair manuals (dealer/workshop accounts); Baslac Formula Finder (click-through licence, BASF-product-only use); Glasurit Colour Online (login); AkzoNobel/Axalta colour retrieval (licensed shop software); 17vin (account, paid API).

**4. Which conflicts were resolved?** **None.** 39 Batch 7 conflict rows are carried unchanged and OPEN; no genuine evidence was obtained.

**5. Which codes remain unverified?** All of them: 329 POSSIBLE and 107 CONFLICTED colour records, 787 colour records with no candidate at all, and the 60 paint-system-reference rows.

**6. Best practical step for Batch 9: a field-evidence batch, starting with two no-cost actions.** (a) Phone BYD's official line with the VIN-free policy question (dealer scripts, section 3b) and record the answer - it settles whether the dealer route exists. (b) Have someone who owns a BYD (with their own VIN) run **T01 (Seal 亚特兰蒂斯灰) and T02 (Han EV 雪域白)** at a service centre using the script and checklist; ingest the result with `vin_evidence_template.csv`. If you can test Baslac Formula Finder yourself, add the 8 facts from the test plan. Batch 9 should then ingest those records, apply the status rules, and only then touch the conflicts.

## Limitations

- No field evidence of any kind was obtained; every verification row is pending.
- Denza/Yangwang sites and `/sell.html` on Fangchengbao failed with connection resets from this environment, so those pages were not read.
- 17vin's conclusion rests on the published API schema, not on real responses.
- Hotline numbers come from official BYD pages/manuals but should be re-checked before calling.
