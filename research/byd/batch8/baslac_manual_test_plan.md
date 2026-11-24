# Baslac Formula Finder - manual test plan (to be done by the user)

**Status: NOT TESTED.** The tool sits behind a legal click-through ("I agree" / "I disagree") at https://formula-finder.baslac.com/ (and a mirror at https://formula-finder.baslac.com.au/). I read the public disclaimer image but did **not** accept it, submit the form, or create an account; accepting terms is the user's decision.

## What the agreement says (read from the public disclaimer image)

- "baslac" is a registered trademark of BASF Coatings GmbH; the agreement is between the user and BASF.
- The BASF colour mixing formulas **remain BASF property**, are a **company secret**, and are provided for **non-exclusive, non-transferable use**; they are copyright-protected.
- Use is allowed **only with BASF coating products**.
- Formulas may **not be sold, leased or passed to third parties**; **downloading/saving requires a separate written licence**.
- **Integration into third-party software** is not permitted without a written licence.
- BASF disclaims liability for correctness; violations end the right of use and may lead to legal action.

**Consequence for this project:** no formula (mixing ratios, toner lists) from the Formula Finder may be copied, saved or imported into the Paint Code Intelligence database. Whether even the *OEM code / colour name* shown beside a formula may be stored is unclear; ask BASF/Baslac (or your local Baslac distributor, via the "find a dealer" link on https://www.baslac.com/zh-apac/colors) for written permission before storing anything from the tool.

## What the public Baslac pages already tell us

- The Formula Finder is "an online colour-information tool" with a database of 125,000+ (e-finder page) / 140,000+ (colours page) mixing formulas for **all vehicle manufacturers**, updated with new colours **and variants**.
- The chip set (3,000+ chips) is sorted **by OEM**, each chip corresponds to **one standard formula**; deviation variants (偏差色) are darker/finer/coarser than the standard and are shown with their direction.
- Nothing public says whether **BYD** is included, which models/years exist, or which input fields the tool accepts.

## Questions the manual test must answer (record answers only - no formulas)

| # | Question | Where to look | Record |
|---|---|---|---|
| 1 | Is **BYD** in the make list? Any BYD sub-brand (Denza, Yangwang, Fangchengbao)? | make selector | yes/no + list |
| 2 | Which BYD **models** and **year ranges** are offered? | model/year selectors | list (names/years only) |
| 3 | Which **inputs** does the search accept: OEM colour code? colour name? year? VIN? | search form | list of input types |
| 4 | Does the result show an **OEM colour code**, a **colour name**, a **formula/variant number**, or all? Are these separate fields? | result page | field names only |
| 5 | Are **deviation colours / variants** listed separately from the standard formula? How are they labelled? | result page | description only |
| 6 | Is there a **"VIN" search**? (expected: no) | search form | yes/no |
| 7 | Does it separate gloss and matte (e.g. HB5 vs HB6)? | result page | yes/no, example colour name only |
| 8 | Any notice about market/region coverage (China vs export)? | page text | quote |

## Rules while testing

1. Read the agreement yourself before clicking anything; stop if you disagree.
2. **Do not copy, screenshot or save any mixing formula.** Note only the facts in the table above.
3. Use only colours of **your own** vehicle, or generic searches; no other person's VIN.
4. Record the date, the language setting and the URL of the tool you used.
5. Report findings back as text (table above). If the tool lists BYD OEM codes beside colour names, ask BASF/Baslac for permission before any code is stored in this project; until then the information is **PAINT_SYSTEM_REFERENCE at best, never VERIFIED_OEM** (a paint system's own listing is not BYD documentation).

## How results would be classified

| Finding | Classification |
|---|---|
| Baslac lists a BYD colour with a code and name | a **paint-system listing** of an OEM code: PAINT_SYSTEM_REFERENCE (supports plausibility, does not verify the code on a specific vehicle) |
| Baslac formula/variant numbers | PAINT_SYSTEM_REFERENCE (never an OEM code) |
| BYD absent from the make list | recorded as "BYD not covered by Baslac Formula Finder (date)" |
