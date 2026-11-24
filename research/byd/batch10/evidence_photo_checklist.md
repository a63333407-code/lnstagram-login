# Evidence photo checklist and code-identification guide

Use this for a photograph of any factory label on **your own vehicle**, and to judge what a photographed code is. It does **not** say where a BYD colour label is: **no official source confirms a colour-label location for any specific BYD model** (BYD's owner's manuals list the nameplate contents and other labels without a colour item; retailer statements about door frames, B-pillars or the bonnet conflict and are unconfirmed).

## 1. Before you start

- [ ] Park in daylight, car off, parking brake on. Do **not** remove or loosen any trim.
- [ ] Decide what identity link you will offer (none / first 9 VIN characters / your own SHA-256 hash). **Never send a full VIN.**
- [ ] Remove or cover: number plate, VIN (all 17 characters, including on windscreen plate and labels), your name, address, phone, documents, other people.
- [ ] Turn off location tagging on the camera, or strip GPS metadata afterwards.

## 2. The shots (aim for 4-6 photos)

1. **Whole vehicle, side or three-quarter view** - shows colour, finish (gloss/matte) and the model's body shape. Plate covered.
2. **Context shot** - the area where you found the label, wide enough to show it is attached to the vehicle body (door frame, panel, etc.).
3. **Medium shot** - the label with its surroundings (edges, fasteners, adhesive, stamping).
4. **Close-up, label flat on** - every character legible, no glare. **Mask any VIN characters** (a plain piece of paper held in front is fine).
5. **Close-up of the field name next to the code** (e.g. "颜色", "油漆", "Color", "Paint") - the *meaning* of the code matters as much as its value.
6. *(Optional)* Second angle or lighting for a glare-free reading.

Do **not** photograph: other customers' documents, keys, insurance/registration papers, anything showing personal data.

## 3. Record, in this order

1. Write down the characters **exactly as printed** (letters, digits, hyphens, slashes) **before** comparing with any code found online.
2. Note the **field name** next to the code and the **language**.
3. Note the **position** you found it, in your own words.
4. Note model, model year, colour name on the contract, gloss/matte, any respray.
5. Only then compare with candidate codes (optional).

## 4. Is the photographed code an OEM paint code? (guide)

| Question | If yes | If no |
|---|---|---|
| Does a field name meaning **colour/paint** (颜色, 车身颜色, 油漆, 涂装, Color, Paint, Paint code) sit next to the value? | supports "colour code" | the value's meaning is **unknown** - do not call it a paint code |
| Is the value **short** (typically 2-5 alphanumeric characters, possibly with a hyphen)? | consistent with colour codes seen in supplier lists | long strings are probably something else |
| Is it **17 characters**? | it is a VIN - **not** a paint code; mask it | - |
| Is it a **date, month/year, weight, voltage, capacity, pressure or seat count**? | not a paint code | - |
| Is it a **model/type designation, part number, barcode or QR content**? | not a paint code | - |
| Does it look like a **long identifier with a prefix and digits** (e.g. `BYHB-00001` style)? | probably a supplier/paint-system reference: **PAINT_SYSTEM_REFERENCE**, not an OEM code | - |
| Is it printed on a **paint can, touch-up pen or retailer sticker**? | that is a **product/formula label**, not a factory vehicle label | - |

Classification of what you photographed (none of these upgrades a status by itself):

| Result | Meaning |
|---|---|
| LIKELY_OEM_PAINT_CODE | field name means colour/paint, value is short and plausible, label is factory-applied and attached to the vehicle |
| UNCERTAIN | field name unreadable/absent, or label authenticity unclear |
| NOT_A_PAINT_CODE | VIN, date, model/part number, weights, pressures, barcode |
| FORMULA_OR_SYSTEM_ID | looks like a paint-system or supplier identifier |

## 5. What makes a photo usable as VERIFIED_LABEL (all three needed)

1. **Vehicle association** - model, year, colour name, and an identity link (first 9 VIN characters or your own hash; ideally the VIN plate in an unmasked, separate private photo).
2. **Authenticity** - context and medium shots showing a genuine factory-attached label, not a loose sticker, paint-can label or edited image.
3. **Meaning** - the field name shows the value is a colour/paint code.

A photo with only a close-up code, no context and no field name remains a lead.
