#!/usr/bin/env python3
"""
Batch 11 helper: record what the downloaded OFFICIAL brochure PDFs say about exterior colours.

Usage: python3 extract_official_docs_batch11.py <dir-with-downloaded-pdfs>
Writes research/byd/batch11/raw/official_colour_extracts.json  (short text excerpts + sha256 + PDF metadata; the PDFs themselves are NOT stored)

Each document entry lists the colour names a human read from the extracted text; this script VERIFIES that every listed name (and Chinese name)
literally occurs in the extracted text of the PDF, and stores the lines that contain them as evidence.  Requires poppler (pdftotext, pdfinfo).
"""
import os, re, sys, json, hashlib, subprocess

SRC = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batch11", "raw"); os.makedirs(OUT, exist_ok=True)

# id, local file stem, url, title as it appears in the URL, host class, market, model as printed, colours [(printed, chinese_or_None)], finish_note, equipment_lines
DOCS = [
 ("D01", "seal_mo", "https://www.byd.com/material/byd-site/mo/product/seal/BYDSEAL-brochure.pdf", "BYDSEAL-brochure.pdf", "BYD official website (Macau path 'mo')", "Macau", "SEAL",
  [("ARCTIC BLUE", "北冰藍"), ("AURORA WHITE", "極光白"), ("ATLANTIS GRAY", "亞特蘭蒂斯灰"), ("SHARK GRAY", "迷迭灰"), ("COSMOS BLACK", "玄空黑"), ("MYSTIC GREEN", "風卷草綠")], "", []),
 ("D02", "seal_au", "https://www.bydautomotive.com.au/brochures/BYD-SEAL-2025.pdf", "BYD-SEAL-2025.pdf", "BYD Australia (importer) website", "Australia", "SEAL",
  [("Atlantis Grey", None), ("Cosmos Black", None), ("Aurora White", None), ("Shark Grey", None)], "", []),
 ("D03", "seal_uk26", "https://prod.byd.com/material/byd-site/byd-uk/specifications/SEAL MY26 UK Leaflet.pdf", "SEAL MY26 UK Leaflet.pdf", "BYD UK website (prod.byd.com)", "United Kingdom", "SEAL",
  [("Atlantis Blue", None), ("Obsidian Black", None), ("Polar White", None), ("Indigo Grey", None), ("Lavender Grey", None), ("Ruby Red", None)], "document lists 'Metallic paint' as an equipment line (not per colour)", ["Metallic paint"]),
 ("D04", "seal_za", "https://www.byd.com/material/byd-site/za/product/seal/BYD SEAL Vehicle Specifications South Africa.pdf", "BYD SEAL Vehicle Specifications South Africa.pdf", "BYD official website (South Africa path 'za')", "South Africa", "SEAL",
  [("Sky Black", None), ("Atlantis Gray", None), ("Aurora White", None), ("North lce Blue", None), ("Rosemary Gray", None), ("Wind Grass Green", None)], "", []),
 ("D05", "seal5_kh", "https://www.byd.com/material/__CN/kh-sealion5/seal5/BYD Seal 5 DM-I 海豹-ENG Final 2026.pdf", "BYD Seal 5 DM-I 海豹-ENG Final 2026.pdf", "BYD official website (Cambodia path 'kh')", "Cambodia", "Seal 5 DM-i (title carries 海豹)",
  [("Snowy White", None), ("Atlantic Grey", None)], "", []),
 ("D06", "sealion6_kh", "https://www.byd.com/material/__CN/kh-sealion5/kh-sealion6dmi/BYD Sealion 6 DM-i 海狮-ENG Final 2026.pdf", "BYD Sealion 6 DM-i 海狮-ENG Final 2026.pdf", "BYD official website (Cambodia path 'kh')", "Cambodia", "Sealion 6 DM-i (title carries 海狮)",
  [("Azure Blue", None), ("Harbour Grey", None), ("Arctic White", None), ("Delan Black", None), ("Stone Grey", None), ("Emperor Red", None)], "", []),
 ("D07", "sealu_hr", "https://autohrvatska.hr/EasyEdit/UserFiles/Catalogs/SEAL U DM-i_Product Information Guide_download_en.pdf", "SEAL U DM-i_Product Information Guide_download_en.pdf", "BYD authorised importer website (Autohrvatska, Croatia)", "Croatia / EU", "SEAL U DM-i",
  [("Delan black", None), ("Time grey", None), ("Snow white", None), ("Tian qing", None), ("Boundless cloud", None)], "document lists 'Metallic paint' as an equipment line for both trims (not per colour)", ["Metallic paint"]),
 ("D08", "dolphin_sc", "https://www.byd.com/material/byd-site/sc/BYD DOLPHIN.pdf", "BYD DOLPHIN.pdf", "BYD official website (path 'sc'; country not named in the document)", "not stated (site path 'sc')", "DOLPHIN",
  [("Atlantis Grey", None), ("Delan Black", None), ("Ski White", None), ("Urban Grey", None), ("Sand White", None)], "", []),
 ("D09", "dolphin_au_dealer", "https://evdealergroup-byd.com.au/brochures/BYD-DOLPHIN-2025.pdf", "BYD-DOLPHIN-2025.pdf", "BYD authorised dealer-group website (evdealergroup-byd.com.au)", "Australia", "DOLPHIN",
  [("Ski White", None), ("Harbour Grey", None), ("Atlantis Grey", None)], "", []),
 ("D10", "atto3_au26", "https://bydautomotive.com.au/brochures/BYD-ATTO-3-2026.pdf", "BYD-ATTO-3-2026.pdf", "BYD Australia (importer) website", "Australia", "ATTO 3",
  [("Ski White", None), ("Harbour Grey", None), ("Cosmos Black", None), ("Atlantis Grey", None)], "", ["Atlantis Grey only available on PREMIUM Model"]),
 ("D11", "seal6dmi_uk", "https://www.byd.com/material/byd-site/byd-uk/specifications/SEAL 6 DM-i-1225-BPS-UK-V2-web.pdf", "SEAL 6 DM-i-1225-BPS-UK-V2-web.pdf", "BYD UK website", "United Kingdom", "SEAL 6 DM-i",
  [("Polar White", None), ("Obsidian Black", None), ("Atlantis Blue", None), ("Sandstone", None)], "document states 'Metallic paint: Polar White; Optional Metallic paint: Obsidian Black; Atlantis Blue; Sandstone' (finish stated per colour: metallic)", ["Metallic paint: Polar White", "Optional Metallic paint: Obsidian Black; Atlantis Blue; Sandstone"]),
 ("D12", "sealion5_uk", "https://www.byd.com/material/byd-site/byd-uk/specifications/BYD SEALION 5 DM-i UK Leaflet-v3.pdf", "BYD SEALION 5 DM-i UK Leaflet-v3.pdf", "BYD UK website", "United Kingdom", "SEALION 5 DM-i",
  [("Atlantis Blue", None), ("Obsidian Black", None), ("Time Grey", None), ("Polar White", None)], "document lists 'Metallic paint' as an equipment line (not per colour)", ["Metallic paint"]),
]


def norm(s): return re.sub(r"\s+", " ", s).strip().lower()


out = []
for did, stem, url, title, host, market, model, colours, finish, equip in DOCS:
    pdf = os.path.join(SRC, stem + ".pdf")
    data = open(pdf, "rb").read()
    txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
    info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    meta = {k: v.strip() for k, v in (l.split(":", 1) for l in info.splitlines() if ":" in l) if k in ("CreationDate", "ModDate", "Pages", "Title")}
    flat = norm(txt)
    missing = [c for c, zh in colours if norm(c) not in flat] + [zh for c, zh in colours if zh and zh not in txt] + [e for e in equip if norm(e) not in flat]
    if missing: raise SystemExit(f"{did}: strings not found in extracted text: {missing}")
    keys = [c for c, _ in colours] + [zh for _, zh in colours if zh] + equip
    lines = []
    for ln in txt.splitlines():
        if any(norm(k) in norm(ln) for k in keys):
            s = re.sub(r"\s{3,}", " | ", ln.strip())
            if s not in lines: lines.append(s[:220])
    out.append(dict(doc_id=did, url=url, title_in_url=title, host_class=host, market=market, model_as_printed=model, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), pdf_metadata=meta,
                    colours=[dict(printed=c, chinese=zh) for c, zh in colours], finish_note=finish, equipment_lines=equip, excerpt_lines=lines[:14], retrieved="2026-11-24"))
# a document whose colour pages are images only
han = os.path.join(SRC, "han_fr.pdf")
data = open(han, "rb").read(); txt = subprocess.run(["pdftotext", "-layout", han, "-"], capture_output=True, text=True).stdout
info = subprocess.run(["pdfinfo", han], capture_output=True, text=True).stdout
out.append(dict(doc_id="D13", url="https://www.byd.com/material/byd-site/fr/product/han/BYD%20HAN.pdf", title_in_url="BYD HAN.pdf", host_class="BYD official website (France path 'fr')", market="France", model_as_printed="HAN", sha256=hashlib.sha256(data).hexdigest(),
                bytes=len(data), pdf_metadata={k: v.strip() for k, v in (l.split(":", 1) for l in info.splitlines() if ":" in l) if k in ("CreationDate", "ModDate", "Pages")}, colours=[], finish_note="", equipment_lines=[],
                excerpt_lines=[], no_colour_text=(not re.search(r"\b(white|black|grey|gray|blue|green|red|blanc|noir|gris|bleu|vert|rouge)\b", txt, re.I)), retrieved="2026-11-24"))
json.dump(out, open(os.path.join(OUT, "official_colour_extracts.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("documents", len(out), "colour entries", sum(len(d["colours"]) for d in out), "han no colour text:", out[-1]["no_colour_text"])
