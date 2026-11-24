# BYD authorised service centre - factory paint information inquiry (English)

> **Nature**: a research template, **not a BYD-approved procedure**. No public BYD document says whether a service centre can retrieve original paint information by VIN, so the purpose of this script is to **test that**. "Yes", "no" and "colour name only" are all useful results - record whichever you get.

## 0. Ground rules

1. **Use only your own vehicle's VIN, or one the owner has permitted in writing.** Never use another person's VIN; do not publish a full VIN. The evidence template (`batch7/vin_evidence_template.csv`) stores only a SHA-256 hash and the first 9 characters.
2. The service centre may decline to show internal systems. Ask politely; do not pressure staff.
3. Do not photograph other customers' data or unrelated screens.
4. Only **documentary** evidence (screen, printout, stamped statement) can become VERIFIED_OEM. A verbal answer is recorded as "staff statement" and **never** upgrades a status.

## 1. Official contact channels (taken from official BYD pages; re-check before use)

| Channel | Detail | Source |
|---|---|---|
| BYD customer-service hotline | **950858** (service page: 365 days, 24 h) | https://www.byd.com/cn/after-sales-service |
| BYD customer-service phone | **400-830-3666** | front matter of the Han L EV and Han DM-i owner's manuals |
| Fangchengbao hotline | **950859** | https://www.fangchengbao.com/ (site configuration) |
| Dynasty / Ocean store finders | 2,300+ after-sales outlets | https://www.byd.com/cn/dynasty-home/find-store ; https://www.byd.com/cn/ocean-home/find-store |
| BYD App / 精诚管家 | booking and online service (whether it shows body colour/code is **unknown**) | https://www.byd.com/cn/after-sales-service |
| Denza, Yangwang | official sites are linked from byd.com's footer (not reachable from the research environment; hotlines **not verified**) | https://www.tengshiauto.com/ ; https://www.yangwangauto.com/ |

## 2. What to prepare

- Model, model year, powertrain
- **Colour name** on the sales contract / invoice (e.g. 亚特兰蒂斯灰, 雪域白)
- **Body-colour class** on the vehicle certificate (合格证) / registration: one of white/grey/yellow/pink/red/purple/green/blue/brown/black (GB/T 21085-2020)
- Any respray/bodywork history
- A phone for photos; a pen for names/dates

## 3. Opening line (phone or in person)

> Hello, I would like to **confirm the original factory paint information** for my car, for future touch-up and my records. It is a [brand/model/year] whose contract colour is "[colour name]". Can your service system look up the **factory body colour** from the **VIN**?

## 3b. Policy question that needs NO VIN (call 950858 or 400-830-3666 first)

> I have a general question, **not about a specific car**: can BYD authorised service centres, given an owner's VIN, look up and tell the owner the car's **original factory body colour / colour code**? If so, can the centre give a **written statement or a system screenshot**? Does the **owner have to attend in person**, and with what documents? Is it the same for each brand (Dynasty / Ocean / Denza / Yangwang / Fangchengbao)?

Record: operator name/ID, date, their words, whether a written channel was offered. This step needs **no VIN** and answers directly whether the route exists.

## 4. Question list (ask in order, record every answer)

**A. Factory build record**
1. Can the system pull up this vehicle's factory configuration / vehicle file by VIN?
2. Does the record show only the colour **name**, or also a colour **code**?
3. Is the displayed colour name identical to my contract's? (ask them to read it out verbatim)

**B. Paint-code field availability**
4. Is there a field such as paint / coating / colour code? What is it called?
5. Does that field hold the **factory colour code** or a **refinish formula number** (e.g. from the body-shop paint system)? Are they the same number?
6. Does the code have **variants** (standard vs deviation formulas)?
7. Does it distinguish **gloss vs matte**?

**C. Written confirmation / screenshot**
8. May I **photograph or screenshot** the screen, with **VIN and colour/code visible together**?
9. If not, can they **print** it, or give a **stamped written statement**?
10. If only verbal, can they **write it down and sign / add an employee ID**?

**D. Body-shop paint system**
11. BYD's website says its 精诚钣喷 service uses AkzoNobel, BASF and Donglai refinish paints with "OEM data, OEM formulas": **which one does this shop actually use?**
12. Is mixing based on the **factory code** or on **spectrophotometer matching**? Is the mixing sheet for this car kept?

**E. Repair history**
13. Does the system show any **respray / bodywork** on this car? (A resprayed car may not carry the factory colour.)

**F. If they cannot provide it**
14. Which department should I contact (after-sales / parts / technical support / manufacturer hotline)?
15. Why can't it be provided (permissions, policy, field does not exist)? - **the reason itself is a result to record.**

## 5. Evidence checklist (tick on site)

- [ ] Service centre name, city, network (Dynasty/Ocean/Denza/Yangwang/Fangchengbao)
- [ ] Responder's role (front desk / adviser / body-shop technician / parts), date and time
- [ ] Screen or printout showing **VIN + colour name + code** together (photo/screenshot, stored privately)
- [ ] The code **exactly as shown** (letters, digits, hyphens)
- [ ] Gloss or matte; variants if any
- [ ] Nature of the field: factory colour code / formula number / unclear
- [ ] Respray or bodywork history
- [ ] If a colour label exists on the car: location + photo with the **VIN plate in the same frame**
- [ ] Reason, if they refused or could not provide it

## 6. Recording the result (`batch8/verification_results.csv`)

| Evidence obtained | Record as |
|---|---|
| Dealer system / printout shows **VIN + colour name + code** (photo, screenshot or stamped statement) | **VERIFIED_OEM** (name the centre and date) |
| Photo of a colour-code label with the **VIN plate in frame**, model/year identifiable | **VERIFIED_LABEL** |
| Verbal answer only | stays POSSIBLE/CONFLICTED; note "staff statement"; **no upgrade** |
| The number shown is a refinish formula number | **PAINT_SYSTEM_REFERENCE** (not a factory code) |
| Only a colour name, no code | record "system has no code field" (a valid outcome - it tells us whether this route works) |
| Several sources repeat one code | still not CORROBORATED unless they are **independent OEM-grade** sources |

## 7. Do not

- Use another person's VIN or ask staff for other customers' data.
- Accept legal terms you do not understand, or bypass any paywall/login.
- Treat a resprayed car as evidence of the factory colour (ask question 13 first).
- Copy paint formulas (e.g. from BASF's Formula Finder) into the research database (see `baslac_manual_test_plan.md`).
