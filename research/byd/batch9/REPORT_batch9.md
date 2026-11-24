# Batch 9 - field verification & official dealer evidence (BYD Group)

## **No genuine OEM paint code was verified. No field evidence was obtained.**

No call was made, no service centre was visited, no vehicle label was photographed, no VIN was used, no dealer document exists. VERIFIED_OEM, VERIFIED_LABEL and CORROBORATED remain **0**; both priority cases (T01, T02) are **PENDING**; all 107 conflicted colour records are **unchanged**. This batch prepares the field work and sharpens priorities; it does not manufacture progress.

## 1. What was actually verified (by reading official pages today)

These are access facts, not paint codes. None upgrades any status.

| Fact | Source | Level |
|---|---|---|
| BYD official hotline **950858** (24 h, 365 days), 2,300+ Dynasty/Ocean outlets, store finders, BYD App, 精诚管家 | https://www.byd.com/cn/after-sales-service | fetched and read |
| BYD customer-service phone **400-830-3666** in the Han L EV and Han DM-i owner's manuals | BYD manual PDFs (Batch 7 copies) | line re-checked in local copy |
| Fangchengbao official hotline **950859**; manual-download page exists (JavaScript app, no static PDF list) | https://www.fangchengbao.com/ ; /store.html ; /user-manual | fetched and read |
| Denza footer **950856** beside '©腾势汽车销售服务有限公司'; store finder claims 400+ outlets in 180+ cities (the page configuration also holds Fangchengbao template residue, so the number is unconfirmed) | https://www.tengshiauto.com/ ; /store.html | fetched and read; /support/service-support.html **not reachable** |
| Yangwang footer **950855**; booking-failure text elsewhere names 400-039-6666; manual-download page exists (JavaScript app) | https://www.yangwangauto.com/ ; /user-manual | fetched and read |
| BYD says 精诚钣喷 uses AkzoNobel/BASF/Donglai with '原厂数据、原厂配方' (Batch 6); manuals only inside the app for some models (Batch 8) | BYD pages | read earlier |

Still unknown after reading them: whether any of these service networks can show a factory paint code from a VIN.

## 2. What was only reported verbally

**Nothing.** No call or conversation took place. (`dealer_contact_results.csv`: 25 question rows across 5 channels, every one `NOT_CALLED` / `UNANSWERED`.) Even when a call is made, a verbal answer verifies no paint code; it only informs whether the route exists.

## 3. What remains untested

- Whether BYD service centres can retrieve factory paint information by VIN (Task 1 questions 1-5) - no public confirmation, no call made.
- T01 (Seal 亚特兰蒂斯灰: HB5 vs HB6, matte vs gloss) and T02 (Han EV 雪域白: W36C vs WA2 vs WA8, `BYHB-00001` as formula reference) - both workflows ready, both PENDING.
- Whether the BYD App / 精诚管家 shows body colour or code to the owner.
- BASF Baslac Formula Finder: whether it lists BYD, models/years, inputs accepted.
- Gloss-vs-matte hypothesis (HB5/HB6, HA4/HC2, UAM/UAN, LAT/LAV).

## 4. What requires the user's or a vehicle owner's participation

- **Making the calls** (K01-K03 required, K04-K05 optional): only a person can complete a real call; the script is `call_script_zh.md` (five questions) and needs no VIN.
- **T01 and T02:** a real Seal and a real Han EV, their owner's written consent, and the owner's **own** VIN. I never request or use anyone else's VIN. Full VINs stay out of research files: only a SHA-256 hash and the first 9 characters (Batch 7 privacy method) are stored.
- **Label inspection** with the VIN plate in the same frame.
- **Baslac test:** only the user may read and accept (or decline) the BASF agreement; I will not accept terms, create accounts or log in.

## 5. What cannot be stored because of licensing or privacy

- **BASF formula content** (mixing ratios, toner lists, anything copyable from the Formula Finder): BASF property, usable only with BASF products, not to be passed on or saved without a separate written licence. If the user completes the factual test, only their factual answers and the permission restrictions are recorded; ask BASF/Baslac for written permission before storing even a code shown there.
- Full VINs, owner identities, photos/screenshots of private vehicle records.
- Anything obtained by bypassing a login, paywall, terms or access control.

## Task 1 - hotline workflow

`call_script_zh.md` is a concise Chinese script with exactly the five requested questions (VIN retrieval; build-record content; written OEM code; official record/screenshot/printout; variation by model/year/brand), recording rules, and the rule that unanswered stays UNANSWERED. `dealer_contact_results.csv` holds one row per channel per question (K01 950858, K02 400-830-3666, K03 950859 required; K04 Denza 950856 and K05 Yangwang 950855 optional and flagged unconfirmed).

## Task 2 - T01 and T02 workflows

`field_verification_cases.csv` has two CASE rows (C-T01, C-T02) and ten STEP rows each (consent; record identity without VIN; hash + 9-character prefix; VIN-free policy call; service-centre questions; request written confirmation; store/transcribe; **exact reason if not provided**; optional label photo; classify). Allowed outcomes are enumerated (`DOC_CODE_PROVIDED`, `DOC_NAME_ONLY`, `DOC_FORMULA_NUMBER_ONLY`, `VERBAL_ONLY`, `REFUSED_POLICY`, `SYSTEM_HAS_NO_FIELD`, `REQUIRES_OWNER_PRESENCE`, `REQUIRES_OTHER_DEPARTMENT`, `NOT_ATTEMPTED`) with their status effect. All steps `NOT_PERFORMED`; consent `NOT_OBTAINED`.

## Task 3 - evidence classification

Seven statuses unchanged. A dealer's verbal answer, an unofficial chat, a retailer listing, a formula number or a colour-name match never reaches VERIFIED_OEM. VERIFIED_OEM requires a document from a BYD service system/OEM source showing VIN + code + colour name; VERIFIED_LABEL requires a photographed label with the VIN plate in frame; a refinish formula number is PAINT_SYSTEM_REFERENCE. No record was upgraded.

## Task 4 - BASF/Baslac boundary

Reviewed `batch8/baslac_manual_test_plan.md`; unchanged. No terms accepted, no account, no formula copied, nothing scraped, nothing stored. Status of the factual test: **not performed by the user** (EP04).

## Task 5 - conflict prioritisation

`conflict_priority.csv` maps all **107 conflicted colour records** to their conflict group and scores **29 colour-level groups** (9 tier A, 14 tier B, 6 tier C); the other 10 of the 39 carried conflict rows are cross-cutting (lineage, certificate colour class, label location, finish type, name-match review, matte pairs, named conflicts) and are listed unscored. Records by tier: A 79, B 15, C 13.

**Score** = 2 × popularity proxy + competition + matte/gloss + route plausibility + genuine disagreement + size. *Popularity proxy* (3 vs 1) is membership in your priority series (Seal, Dolphin, Seagull, Atto 3/Yuan PLUS, Han, Qin PLUS, Song PLUS, Destroyer 05, e2) because the repository holds no sales data. *Competition* counts distinct **vehicle** codes (formula-style identifiers excluded). *Matte/gloss* = involvement of a code in an OEMatch/DipYourCar gloss-vs-matte pair (one lineage - a hypothesis, not evidence). *Route plausibility* = 3 on-sale BYD-brand model reachable through the Dynasty/Ocean network, 2 older BYD model, 1 separate brand network. *Genuine disagreement* = 2 if lineages' code sets are not nested, 1 if nested, 0 for alias groups. *Size* = colour records affected (max 3). **No conflict is resolved, by majority vote or otherwise, and sites sharing one upstream are never counted as extra evidence.**

Tier A (highest value for a first field check):

| Rank | Colour | Models | Records | Codes | Score |
|---|---|---|---|---|---|
| P01 | 雪域白 | Han DM-i; Qin Plus DM-i; Song Pro; Tang DM-i; Tang | 42 | BYHB-00001, W36C, WA2, WA8 | 16 |
| P02 | 雪域白 | Seal 06 DM-i; Seal 06 DM-i Touring; Sealion 05 DM- | 21 | W36C, WA2 | 15 |
| P03 | (no Chinese name) | Yuan Plus | 1 | H84C, HA4, HAN, HB5, HB6 | 15 |
| P04 | 攀岩灰 | Yuan Plus | 4 | HA4, HAN | 14 |
| P05 | 亚特兰蒂斯灰 | Seal | 4 | HB5, HB6 | 14 |
| P06 | 苍穹蓝 | e2 | 4 | BYL, F2, LAN | 14 |
| P07 | 贝贝灰 | Dolphin | 3 | HA4, HAN | 14 |
| P08 | (no Chinese name) | Seal | 1 | HB5, HB6 | 14 |
| P09 | (no Chinese name) | Yuan Plus | 1 | H84C, HB5, HB6 | 14 |

T01/T02 remain the right first cases: 雪域白 (P01, P02) covers 63 colour records across Han, Qin PLUS, Song PLUS and others, and 亚特兰蒂斯灰 (P05) is the clearest gloss-vs-matte test.

## Task 6 - other BYD Group brands

Official sites for Denza, Yangwang and Fangchengbao loaded (hotlines in section 1). **No owner-manual PDF, authorised service documentation, genuine label or manufacturer-controlled parts/service system was found for any of them**; Yangwang and Fangchengbao manual pages are JavaScript apps with no static list (and I did not call their undocumented APIs); Denza shows no manual link and one service page was unreachable; **Linghui (领汇): no official source found**. Nothing inaccessible is claimed as inspected.

## Suggested next step (Batch 10)

1. Make the K01/K02 calls (5 minutes, no VIN) and record the answers in `dealer_contact_results.csv`.
2. If the answer is 'yes, in writing', run T01 and T02 with an owner's own VIN; ingest results; only then revisit tier-A conflicts.
3. If the answer is 'no', the factory-code route through dealers is closed and the project should rely on label photographs and licensed paint-system chip/code checks, with every result labelled PAINT_SYSTEM_REFERENCE at best.
