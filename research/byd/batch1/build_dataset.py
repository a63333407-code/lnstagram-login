#!/usr/bin/env python3
"""
Builds the BYD research dataset (normalized CSV + JSON + REPORT.md).

Everything here is transcribed from sources listed in SOURCES. Nothing is invented:
unknown values are None (NULL). No paint codes were found in any source, so
paint_codes.csv is intentionally header-only.

Run:  python3 build_dataset.py
"""
import csv, json, os, re
from collections import defaultdict

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- sources
# retrieval: FULL = page/document text read in full for the relevant part
#            SNIPPET = only a search-result summary was seen (needs re-fetch to confirm)
SOURCES = [
 ("S01","Wikipedia - List of BYD Auto vehicles","https://en.wikipedia.org/wiki/List_of_BYD_Auto_vehicles","secondary-encyclopedia","FULL","Model list, body types, intro/facelift/discontinued years. Not an OEM source."),
 ("S02","BYD Australia - BYD SEAL 2025 brochure (PDF)","https://www.bydautomotive.com.au/brochures/BYD-SEAL-2025.pdf","OEM-importer brochure","FULL","Text extracted locally with pdftotext; exterior colour list read. Contains NO paint codes."),
 ("S03","NonPaints / CROP - BYD colour code page","https://www.nonpaints.com/en/color-code/byd","third-party paint retailer","FULL","Reviewed and REJECTED as code source: lists no per-model BYD codes (only generic examples R1A/B23/LZ5 not tied to any model)."),
 ("S04","Autohome - Qin PLUS picture gallery","https://car.autohome.com.cn/pic/series-5964-12359-1.html","secondary-catalog","SNIPPET","Chinese colour names only; no codes; gallery covers more than one variant/year, unresolved."),
 ("S05","Autocar India - BYD Atto 3 colours","https://www.autocarindia.com/cars/byd/atto-3/colours","secondary-media","SNIPPET","Colour names; no codes."),
 ("S06","The Driven - Forest Green option for BYD Atto 3 goes live (Jan 2023)","https://thedriven.io/2023/01/11/forest-green-colour-option-for-byd-atto-3-goes-live/amp","secondary-media","SNIPPET","Australia, Forest Green added Jan 2023."),
 ("S07","Carwow UK - BYD Dolphin colours","https://carwow.co.uk/byd/dolphin/colours","secondary-media","SNIPPET","UK colour/roof combinations; no codes; availability varies by trim."),
 ("S08","Carmudi Philippines - BYD Seagull colours","https://carmudi.com.ph/new-cars/byd/seagull/images","secondary-catalog","SNIPPET","2025 and 2026 PH model-year colours."),
 ("S09","BYD India - Seal page","https://www.byd.com/in/car/seal.html","OEM website","SNIPPET","India Seal colours. Another India source lists only 4 (conflict, see issues)."),
 ("S10","BYD Europe-market Seal brochure (hosted by Autohrvatska)","https://autohrvatska.hr/EasyEdit/UserFiles/seal-0325-bps-en-v7-web.pdf","OEM-importer brochure","SNIPPET","Colour names translated, may not match local brochure. Standard vs optional depends on trim."),
 ("S11","BYD Nepal - Atto 3 page","https://www.byd.com/np/car/atto3","OEM website","SNIPPET","Nepal Atto 3 colours."),
 ("S12","Cars24 - BYD Atto 3 gets a new colour","https://www.cars24.com/news/auto/byd-atto-3-gets-a-new-colour-what-is-new-what-stays-the-same/","secondary-media","SNIPPET","Atlantis Gray added; market not stated in snippet."),
 ("S13","Chipex - BYD paint repair","https://eu.chipex.com/brands/byd","third-party paint retailer","SNIPPET","Only says code is on door-jamb sticker (driver or passenger door); location varies by model. No codes."),
 ("S14","Dailymotion - Seagull Honor Edition 2024 listing","https://www.dailymotion.com/video/x8u7edi","weak-secondary","SNIPPET","Claims Honor Edition added Arctic Blue. Weak source."),
]

# ---------------------------------------------------------------- models (from S01)
# (group, series, name, zh, alt_names, body_raw, powertrain, intro, facelift, discontinued, status, note)
# series None = the Wikipedia extract left the series cell blank (NOT guessed).
D,O,L = "Dynasty","Ocean","Legacy"
M = []
def m(*a): M.append(a)
# --- BYD brand, Dynasty
m("BYD",D,"Dahan EV","大汉EV",None,"Full-size sedan","BEV",2026,None,None,"current",None)
m("BYD",D,"Han DM-i","汉DM-i",None,"Full-size sedan","PHEV",2020,2024,None,"current",None)
m("BYD",D,"Han L DM","汉L DM",None,"Full-size sedan","PHEV",2025,None,None,"current",None)
m("BYD",D,"Qin L DM-i","秦L DM-i","Seal 6 DM-i","Mid-size sedan","PHEV",2024,None,None,"current",None)
m("BYD",D,"Qin L EV","秦L EV","Seal 6 EV","Mid-size sedan","BEV",2025,None,None,"current",None)
m("BYD",D,"Qin Max DM-i","秦MAX DM-i",None,"Mid-size sedan","PHEV",2026,None,None,"current",None)
m("BYD",D,"Qin Plus DM-i","秦PLUS DM-i","Qin Plus","Compact sedan","PHEV",2021,2025,None,"current",None)
m("BYD",D,"Qin Plus DM-i (2nd gen)","秦PLUS DM-i",None,"Mid-size sedan","PHEV",2026,None,None,"current","Model code HA3H")
m("BYD",D,"Datang DM","大唐DM",None,"Full-size crossover SUV","PHEV",2026,None,None,"current",None)
m("BYD",D,"Song L DM-i","宋L DM-i",None,"Mid-size crossover SUV","PHEV",2024,None,None,"current",None)
m("BYD",D,"Song L EV","宋L EV",None,"Mid-size crossover SUV","BEV",2023,None,None,"current",None)
m("BYD",D,"Song Ultra DM-i","宋Ultra DM-i",None,"Mid-size crossover SUV","PHEV",2026,None,None,"current",None)
m("BYD",D,"Song Pro","宋Pro DM-i","Song Pro; Sealion 5 DM-i","Compact crossover SUV","PHEV",2019,2024,None,"current",None)
m("BYD",D,"Tang DM-i","唐DM-i","Tang DM-i","Mid-size crossover SUV","PHEV",2018,2024,None,"current",None)
m("BYD",D,"Tang EV (3rd gen)","唐EV",None,"Mid-size crossover SUV","BEV",2026,None,None,"current",None)
m("BYD",D,"Tang L DM","唐L DM","Sealion 8 DM-i; Atto 8","Mid-size crossover SUV","PHEV",2025,None,None,"current",None)
m("BYD",D,"Yuan Plus (1st gen)","元PLUS","Atto 3; Yuan Plus","Compact crossover SUV","BEV",2022,2025,None,"current",None)
m("BYD",D,"Yuan Plus (2nd gen)","元PLUS","Atto 5","Compact crossover SUV","BEV",2026,None,None,"current",None)
m("BYD",D,"Yuan Up (PHEV)",None,"Atto 2 DM-i; Yuan Up DM-i; Yuan Pro DM-i","Subcompact crossover SUV","PHEV",2025,None,None,"current",None)
m("BYD",D,"Xia","夏","M9; eMax 9 DM-i","MPV/minivan","PHEV",2024,None,None,"current",None)
# --- BYD brand, Ocean
m("BYD",O,"Destroyer 05","驱逐舰05","Chazor; King; Seal 5 DM-i","Compact sedan","PHEV",2022,None,None,"current","No longer sold in China")
m("BYD",O,"Seal","海豹","Seal","Mid-size sedan","BEV",2022,None,None,"current","No longer sold in China")
m("BYD",O,"Seal 05 DM-i","海豹05 DM-i","Seal 5 DM-i; King","Compact sedan","PHEV",2025,None,None,"current",None)
m("BYD",O,"Seal 06 DM-i","海豹06 DM-i","Seal 6 DM-i","Mid-size sedan","PHEV",2024,None,None,"current",None)
m("BYD",O,"Seal 06 DM-i (2nd gen)","海豹06 DM-i",None,"Mid-size sedan","PHEV",2026,None,None,"current",None)
m("BYD",O,"Seal 07 DM-i","海豹07 DM-i","Seal 7 DM-i","Full-size sedan","PHEV",2023,2025,None,"current","Previously Seal DM-i")
m("BYD",O,"Seal 07 DM-i (2nd gen)","海豹07 DM-i",None,"Full-size sedan","PHEV",2026,None,None,"current",None)
m("BYD",O,"Seal 08 DM-i","海豹08 DM-i",None,"Full-size sedan","PHEV",2026,None,None,"current",None)
m("BYD",O,"Seal 06 DM-i Touring","海豹06 DM-i旅行版","Seal 6 DM-i Touring","Mid-size wagon","PHEV",2025,None,None,"current",None)
m("BYD",O,"Dolphin","海豚","Dolphin; E2","Compact hatchback","BEV",2021,2025,None,"current",None)
m("BYD",O,"e2","e2","e2","Compact hatchback","BEV",2019,2023,None,"current","Hatchback version of the e3; series 'e (Ocean)'")
m("BYD",O,"Seagull (1st gen)","海鸥","Seagull; Dolphin Mini; Dolphin Surf; Atto 1","City car","BEV",2023,2025,None,"current",None)
m("BYD",O,"Seagull (2nd gen)","海鸥",None,"Supermini","BEV",2026,None,None,"current",None)
m("BYD",O,"Seal 06 GT","海豹06 GT",None,"Mid-size hatchback","BEV",2024,None,None,"current",None)
m("BYD",O,"Sealion 05 DM-i (2nd gen)","海狮05 DM-i",None,"Compact crossover SUV","PHEV",2026,None,None,"current",None)
m("BYD",O,"Sealion 06 DM-i","海狮06 DM-i",None,"Mid-size crossover SUV","PHEV",2025,None,None,"current",None)
m("BYD",O,"Sealion 07 EV","海狮07 EV","Sealion 7","Mid-size crossover SUV","BEV",2024,None,None,"current","No longer sold in China")
m("BYD",O,"Sealion 08 DM-i","海狮08 DM-i",None,"Full-size crossover SUV","PHEV",2026,None,None,"current",None)
m("BYD",O,"Song Plus DM-i","宋PLUS DM-i","Seal U DM-i; Sealion 6 DM-i","Compact crossover SUV","PHEV",2020,2023,None,"current","Ocean Network since 2022 (page footnote); no longer sold in China")
m("BYD",O,"e6","e6","e6","Compact MPV (taxi)","BEV",2021,None,None,"current","Based on Song Max; series 'e (Ocean)'")
# --- BYD brand, series blank in extract
for r in [
 ("Han EV","汉EV","Han","Full-size sedan","BEV",None,None,"current",None),
 ("Han L EV","汉L EV",None,"Full-size sedan","BEV",None,None,"current",None),
 ("Qin Max EV","秦MAX EV",None,"Mid-size sedan","BEV",None,None,"current",None),
 ("Qin Plus EV","秦PLUS EV",None,"Compact sedan","BEV",None,None,"current",None),
 ("Seal 06 EV","海豹06 EV",None,"Mid-size sedan","BEV",2025,2026,"current",None),
 ("Seal 07 EV","海豹07 EV",None,"Full-size sedan","BEV",2026,None,"current",None),
 ("Seal 07 EV (2nd gen)","海豹07 EV",None,"Full-size sedan","BEV",2026,None,"current",None),
 ("Seal 08 EV","海豹08 EV",None,"Full-size sedan","BEV",None,None,"current",None),
 ("Dolphin G DM-i",None,"Dolphin G DM-i","Compact hatchback","PHEV",2026,None,"current",None),
 ("Racco",None,None,"Kei car, rear sliding doors","BEV",2026,None,"current",None),
 ("Datang EV","大唐EV",None,"Full-size crossover SUV","BEV",None,None,"current",None),
 ("Sealion 05 EV","海狮05 EV",None,"Compact crossover SUV","BEV",2025,2026,"current",None),
 ("Sealion 06 EV","海狮06 EV","Song Plus","Mid-size crossover SUV","BEV",None,None,"current",None),
 ("Sealion 08 EV","海狮08 EV",None,"Full-size crossover SUV","BEV",None,None,"current",None),
 ("Song Plus EV","宋PLUS EV","Seal U EV","Compact crossover SUV","BEV",None,None,"current","No longer sold in China"),
 ("Song Ultra EV","宋Ultra EV",None,"Mid-size crossover SUV","BEV",None,None,"current",None),
 ("Tang EV (2022)","唐EV","Tang; Tan; Sealion 8","Mid-size crossover SUV","BEV",2022,None,"current","No longer sold in China"),
 ("Tang L EV","唐L EV",None,"Mid-size crossover SUV","BEV",None,None,"current",None),
 ("Ti 7",None,"Ti 7; Titan 7","Mid-size SUV","PHEV",2026,None,"current","Export rebadge of Fangchengbao Ti7"),
 ("Yuan Up (BEV)","元UP","Atto 2; Yuan Up; Yuan Pro; S1 Pro","Subcompact crossover SUV","BEV",2024,None,"current","Name cell blank in extract; inferred from image caption"),
 ("M6 DM",None,"M6 DM","Three-row compact MPV","PHEV",2026,None,"current","Based on Song Max"),
 ("M6 EV",None,"M6 EV; eMax 7","Three-row compact MPV","BEV",2024,None,"current","Based on e6 and Song Max"),
 ("Mako",None,"Mako","Pickup","PHEV",None,None,"upcoming",None),
 ("Shark 6",None,"Shark 6; Shark","Four-door body-on-frame pickup","PHEV",2024,None,"current",None),
]:
    m("BYD",None,r[0],r[1],r[2],r[3],r[4],r[5],r[6],None,r[7],r[8])
# --- Linghui
for r in [("e5","领汇e5","Compact sedan","BEV",None,"upcoming","Based on Qin Plus EV"),
          ("e7","领汇e7","Mid-size sedan","BEV",2026,"current",None),
          ("e9","领汇e9","Full-size sedan","BEV",2026,"current","Based on Han EV"),
          ("M9","领汇M9","MPV/minivan","PHEV",2026,"current","Based on Xia")]:
    m("Linghui",None,r[0],r[1],None,r[2],r[3],r[4],None,None,r[5],r[6])
# --- Denza
for r in [
 ("Z9S","腾势Z9S",None,"Full-size 4-door sedan","BEV",2026,None,None,"current",None),
 ("Z9 GT PHEV","腾势Z9 GT插混",None,"Full-size 5-door shooting brake","PHEV",2024,None,None,"current",None),
 ("Z9 GT EV","腾势Z9 GT纯电",None,"Full-size 5-door shooting brake","BEV",None,None,None,"current",None),
 ("Z Coupe","腾势Z硬頂",None,"Coupe","BEV",2026,None,None,"current","Model code EXE"),
 ("Z Spider","腾势Z敞篷",None,"Convertible","BEV",None,None,None,"current",None),
 ("B5",None,None,"Mid-size SUV","PHEV",2025,None,None,"current","Rebadged Fangchengbao Bao 5 for export"),
 ("B8",None,None,"Full-size SUV","PHEV",2025,None,None,"current","Rebadged Fangchengbao Bao 8 for export"),
 ("B3",None,None,"Compact SUV","BEV",2026,None,None,"current","Rebadged Fangchengbao Tai 3 for export"),
 ("N8 PHEV","腾势N8插混",None,"Full-size SUV","PHEV",2026,None,None,"current",None),
 ("N8 EV","腾势N8纯电",None,"Full-size SUV","BEV",2026,None,None,"current",None),
 ("N8L PHEV","腾势N8L插混",None,"Full-size SUV","PHEV",2025,None,None,"current",None),
 ("N8L EV","腾势N8L纯电",None,"Full-size SUV","BEV",2026,None,None,"current",None),
 ("N9","腾势N9",None,"Full-size SUV","PHEV",2024,None,None,"current",None),
 ("D9 DM-i","腾势D9插混",None,"MPV/minivan","PHEV",2022,2026,None,"current",None),
 ("D9 EV","腾势D9纯电",None,"MPV/minivan","BEV",None,None,None,"current",None),
 ("Z9","腾势Z9",None,"Full-size 4-door sedan","BEV/PHEV",2024,None,2026,"discontinued",None),
 ("400/500/EV","腾势400/500/EV",None,"Compact hatchback","BEV",2014,None,2019,"discontinued",None),
 ("X","腾势X",None,"Mid-size crossover SUV","PHEV/BEV",2019,None,2021,"discontinued",None),
 ("N7","腾势N7",None,"Mid-size SUV","BEV",2023,None,2026,"discontinued",None)]:
    m("Denza",None,r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8],r[9])
# --- Yangwang
for r in [("Altior","仰望鼎耀","Full-size luxury sedan",None,None,"upcoming","Model code HU"),
          ("U7 PHEV","仰望U7 PHEV","Full-size luxury sedan","PHEV",2024,"current",None),
          ("U7 EV","仰望U7 EV","Full-size luxury sedan","BEV",2024,"current",None),
          ("U8","仰望U8","Full-size luxury SUV","Range-extended electric",2023,"current",None),
          ("U8L","仰望U8L","Full-size luxury SUV","Range-extended electric",2025,"current","LWB variant of U8"),
          ("U9","仰望U9","Supercar","BEV",2023,"current",None)]:
    m("Yangwang",None,r[0],r[1],None,r[2],r[3],r[4],None,None,r[5],r[6])
# --- Fangchengbao
for r in [("Formula S","方程S",None,"Full-size sedan","BEV",2026,"current",None),
          ("Formula SL","方程SL",None,"Full-size sedan","BEV",None,"upcoming",None),
          ("Formula S GT","方程S GT",None,"Full-size station wagon","BEV",2026,"current",None),
          ("Bao 5","豹5",None,"Mid-size SUV","PHEV",2023,"current","Exported as Denza B5"),
          ("Bao 8","豹8",None,"Full-size SUV","PHEV",2024,"current","Exported as Denza B8"),
          ("Tai 3","鈦3",None,"Compact SUV","BEV",2025,"current","Exported as Denza B3"),
          ("Ti7 (PHEV)","鈦7",None,"Mid-size SUV","PHEV",2025,"current",None),
          ("Ti7 (BEV)","鈦7",None,"Mid-size SUV","BEV",2026,"current",None),
          ("Ti9","鈦9",None,"Full-size SUV","PHEV",2026,"current",None),
          ("Shark","鲨鱼",None,"Four-door body-on-frame pickup","PHEV",2026,"current",None)]:
    m("Fangchengbao",None,r[0],r[1],r[2],r[3],r[4],r[5],None,None,r[6],r[7])
# --- legacy BYD (discontinued)
for r in [
 ("e3","e3","Compact sedan","BEV",2019,2022),("e5","e5","Compact sedan","BEV",2015,2020),
 ("F3","F3","Compact sedan (sedan version of F3R)",None,2005,2021),("F3DM","F3DM","Compact sedan","PHEV",2008,2013),
 ("F6","F6","Mid-size sedan",None,2008,2012),("G3","G3","Compact sedan (sedan version of G3R)",None,2009,2014),
 ("G5","G5","Compact sedan",None,2014,2017),("G6","G6","Mid-size sedan",None,2011,2018),
 ("L3 / New F3","L3","Compact sedan",None,2010,2015),("Qin","秦","Compact sedan","ICE/PHEV/BEV",2012,2024),
 ("Qin Pro","秦Pro","Compact sedan","ICE/PHEV/BEV",2018,2021),("Sirui","思锐","Mid-size sedan",None,2013,2014),
 ("Surui","速锐","Compact sedan",None,2012,2019),("S8","S8","Compact sports car",None,2009,2010),
 ("e1","e1","City car (hatchback)","BEV",2019,2020),("F0","F0","City car",None,2008,2015),
 ("Flyer","福莱尔","City car",None,2005,2008),("F3R","F3R","Compact hatchback",None,2005,2014),
 ("G3R","G3R","Compact hatchback",None,2009,2014),("Frigate 07","护卫舰07","Mid-size crossover SUV","PHEV",2022,2025),
 ("S1","S1","Subcompact crossover SUV",None,2015,2016),("S2","S2","Subcompact crossover SUV","BEV",2019,2022),
 ("S6","S6","Mid-size crossover SUV",None,2011,2016),("S7","S7","Mid-size crossover SUV",None,2014,2018),
 ("Sealion 05 DM-i (1st gen)","海狮05 DM-i","Compact crossover SUV","PHEV",2024,2026),
 ("Sealion 07 DM-i","海狮07 DM-i","Mid-size crossover SUV","PHEV",2025,2026),
 ("Song","宋","Compact crossover SUV",None,2015,2022),("Tang","唐","Mid-size crossover SUV",None,2015,2018),
 ("Yuan","元","Compact crossover SUV","ICE/BEV",2016,2024),("D1","D1","Compact MPV (ride-hailing, DiDi)","BEV",2020,2023),
 ("e6 (2009)","e6","Compact MPV/minivan","BEV",2009,2021),("M6 (2010)","M6","Compact MPV/minivan",None,2010,2017),
 ("Song Max","宋MAX","Three-row compact MPV","ICE/PHEV/BEV",2017,2024)]:
    m("BYD",L,r[0],r[1],None,r[2],r[3],r[4],None,r[5],"discontinued",None)

# generation grouping: row name -> (model_key, generation_label)
GEN = {
 "Qin Plus DM-i":("Qin Plus DM-i","1st gen (implied by 2nd-gen row)"),
 "Qin Plus DM-i (2nd gen)":("Qin Plus DM-i","2nd gen"),
 "Yuan Plus (1st gen)":("Yuan Plus","1st gen"),"Yuan Plus (2nd gen)":("Yuan Plus","2nd gen"),
 "Seagull (1st gen)":("Seagull","1st gen"),"Seagull (2nd gen)":("Seagull","2nd gen"),
 "Seal 06 DM-i":("Seal 06 DM-i","1st gen (implied by 2nd-gen row)"),"Seal 06 DM-i (2nd gen)":("Seal 06 DM-i","2nd gen"),
 "Seal 07 DM-i":("Seal 07 DM-i","1st gen (implied by 2nd-gen row)"),"Seal 07 DM-i (2nd gen)":("Seal 07 DM-i","2nd gen"),
 "Seal 07 EV":("Seal 07 EV","1st gen (implied by 2nd-gen row)"),"Seal 07 EV (2nd gen)":("Seal 07 EV","2nd gen"),
 "Sealion 05 DM-i (1st gen)":("Sealion 05 DM-i","1st gen"),"Sealion 05 DM-i (2nd gen)":("Sealion 05 DM-i","2nd gen"),
 "Tang EV (2022)":("Tang EV","source label: 2022"),"Tang EV (3rd gen)":("Tang EV","3rd gen"),
 "e6 (2009)":("e6","source label: 2009"),"e6":("e6","source label: 2021 row"),
}
# --------------------------------------------------------------- derive tables
def body_type(raw):
    s = raw.lower()
    for kw,bt in [("pickup","Pickup"),("supercar","Supercar"),("sports car","Sports car"),("convertible","Convertible"),
                  ("coupe","Coupe"),("shooting brake","Wagon / shooting brake"),("wagon","Wagon / shooting brake"),
                  ("mpv","MPV"),("suv","SUV / crossover"),("hatchback","Hatchback"),
                  ("city car","City car / kei"),("supermini","City car / kei"),("kei","City car / kei"),("sedan","Sedan")]:
        if kw in s: return bt
    return None
def doors(raw):
    mm = re.search(r"(\d)-door", raw, re.I)
    if mm: return int(mm.group(1))
    if re.search(r"four-door", raw, re.I): return 4
    return None
def size_class(raw):
    mm = re.match(r"(Subcompact|Compact|Mid-size|Full-size|Three-row compact|Supermini)", raw)
    return mm.group(1) if mm else None
def key_of(name):
    return GEN.get(name, (name, None))

brands = [("B1","BYD Group (parent)",None),("B2","BYD","B1"),("B3","Denza","B1"),("B4","Yangwang","B1"),
          ("B5","Fangchengbao","B1"),("B6","Linghui","B1")]
brand_id = {"BYD":"B2","Denza":"B3","Yangwang":"B4","Fangchengbao":"B5","Linghui":"B6"}

body_ids, bt_rows = {}, []
models, model_ids = [], {}
gens = []
for (grp,ser,name,zh,alt,body,pt,intro,fl,disc,status,note) in M:
    mk, glabel = key_of(name)
    mkey = (grp,mk,pt if mk==name else pt)  # powertrain is part of identity: same key + same powertrain
    # models are unique by (brand, model_key); powertrain-specific rows carry it in the name already
    mid_key = (grp, mk)
    bt = body_type(body)
    if bt and bt not in body_ids:
        body_ids[bt] = f"BT{len(body_ids)+1:02d}"; bt_rows.append((body_ids[bt],bt))
    if mid_key not in model_ids:
        model_ids[mid_key] = f"M{len(model_ids)+1:03d}"
        models.append(dict(model_id=model_ids[mid_key],brand_id=brand_id[grp],series=ser,model_key=mk,
                           name_zh=zh,alt_names=alt,powertrain=pt,source_id="S01"))
    else:
        mo = next(x for x in models if x["model_id"]==model_ids[mid_key])
        for f,v in (("name_zh",zh),("alt_names",alt),("series",ser)):
            if mo[f] is None and v: mo[f]=v
    gens.append(dict(generation_id=f"G{len(gens)+1:03d}",model_id=model_ids[mid_key],source_row_name=name,
        generation_label=glabel,status=status,intro_year=intro,facelift_year=fl,discontinued_year=disc,
        body_type_id=body_ids.get(bt),body_raw=body,size_class=size_class(body),doors=doors(body),
        exterior_design=None,note=note,source_id="S01"))
gen_by_name = {g["source_row_name"]:g for g in gens}

# model years -------------------------------------------------------------
my, my_idx = [], {}
def add_my(g, year, basis, src):
    k=(g["generation_id"],year)
    if k in my_idx: return my_idx[k]
    my_idx[k]=f"Y{len(my)+1:04d}"
    my.append(dict(model_year_id=my_idx[k],generation_id=g["generation_id"],year=year,year_basis=basis,source_id=src))
    return my_idx[k]
for g in gens:
    if g["intro_year"]: add_my(g,g["intro_year"],"intro_year_documented","S01")
    if g["facelift_year"]: add_my(g,g["facelift_year"],"facelift_year_documented","S01")
    if g["discontinued_year"] and g["intro_year"]:
        for y in range(g["intro_year"]+1, g["discontinued_year"]+1):
            add_my(g,y,"derived_from_intro_to_discontinued_range","S01")

# factory colours ---------------------------------------------------------
colors=[]
def add_color(gen_name, year, market, names, src, retrieval, note=None, role="body", model_ref=None):
    g = gen_by_name.get(gen_name)
    myid = add_my(g,year,"color_source_year","%s"%src) if (g and year) else None
    for n in names:
        zh = None
        if isinstance(n,tuple): n,zh=n
        colors.append(dict(color_id=f"C{len(colors)+1:03d}",generation_id=g["generation_id"] if g else None,
            model_year_id=myid,model_ref_text=model_ref,market=market,color_name_en=n,color_name_zh=zh,
            color_role=role,source_id=src,retrieval=retrieval,note=note))
add_color("Seal",2025,"Australia",["Atlantis Grey","Aurora White","Cosmos Black","Shark Grey"],"S02","FULL",
          "Brochure 'Exterior colour' list. Per-variant availability not extracted. No paint codes in brochure.")
add_color("Seal",None,"India",["Arctic Blue","Aurora White","Atlantis Grey","Cosmos Black","Shark Grey"],"S09","SNIPPET",
          "Another India source lists only 4 colours (no Shark Grey): conflict unresolved.")
add_color("Seal",None,"Europe (importer brochure, translated names)",["Atlantis Grey","Space Black","Polar White","Ice Blue","Indigo Grey"],"S10","SNIPPET",
          "Names may differ from local brochure; standard/optional depends on trim.")
add_color("Yuan Plus (1st gen)",None,"Nepal",["Surf Blue","Ski White","Harbour Grey","Cosmos Black"],"S11","SNIPPET","Marketed as Atto 3.")
add_color("Yuan Plus (1st gen)",None,"India (publisher-inferred)",["Atlantis Gray"],"S12","SNIPPET","Reported as added (replacing Surf Blue); market and date need confirmation.")
add_color("Yuan Plus (1st gen)",2023,"Australia",["Forest Green"],"S06","SNIPPET","Reported live Jan 2023. 2022 launch colour names not retrieved.")
add_color("Dolphin",None,"United Kingdom",["Amethyst Purple","Coral Pink","Jet Black","Skiing White","Surfing Blue"],"S07","SNIPPET",
          "Body colours as listed; availability varies by trim.")
add_color("Dolphin",None,"United Kingdom",["Urban Grey","Atlantis Grey"],"S07","SNIPPET",
          "Listed as second tone in two-tone combos (e.g. 'Coral pink / Urban grey'); role inferred, unconfirmed.",role="secondary/roof (unconfirmed)")
for y in (2025,2026):
    add_color("Seagull (1st gen)",y,"Philippines",["Apricity White","Delan Black","Sprout Green"],"S08","SNIPPET",
              "Model-year label as shown by catalog; 2026 may be a later generation in other markets.")
add_color("Seagull (1st gen)",2024,None,["Arctic Blue"],"S14","SNIPPET","Honor Edition addition; weak source; market not stated.")
add_color(None,None,"China",[("Snowy White","雪域白"),("Time Grey","时光灰"),("Ice Amber Cyan","冰珀青"),("White Glaze Cyan","白釉青"),
    ("Galaxy Beige","星河米"),("Weiyang Grey","未央灰"),("Pine Smoke Green","松烟绿"),("Chidi Red","赤帝红"),
    ("Xuankong Black","玄空黑"),("Ink Jade Blue","墨玉蓝"),("Ink Bamboo Cyan","墨竹青")],"S04","SNIPPET",
    "Chinese names from Autohome gallery for Qin PLUS (series 5964). English names are my literal translations, NOT official. Variant (DM-i/EV) and year per colour unresolved.",
    model_ref="Qin PLUS (variant/year unresolved)")

# paint codes: none found (header-only file) -------------------------------
paint_codes=[]
# verification records: one NOT FOUND per colour record (paint code search outcome)
ver=[]
for c in colors:
    ver.append(dict(verification_id=f"V{len(ver)+1:03d}",subject_type="factory_color",subject_id=c["color_id"],
        status="NOT FOUND",evidence="No paint code appears in the cited source; no reliable code found elsewhere.",
        source_id=c["source_id"],editor_approved=False,reviewed_on=None))
ver.append(dict(verification_id=f"V{len(ver)+1:03d}",subject_type="source",subject_id="S03",status="NOT FOUND",
    evidence="Page lists no BYD per-model codes; only generic examples (R1A, B23, LZ5) not tied to any model. Not recorded as codes.",
    source_id="S03",editor_approved=False,reviewed_on=None))

# --------------------------------------------------------------- write
def w(name, rows, cols):
    with open(os.path.join(OUT,name),"w",newline="",encoding="utf-8") as f:
        wr=csv.DictWriter(f,fieldnames=cols); wr.writeheader()
        for r in rows: wr.writerow(r)
w("brands.csv",[dict(brand_id=a,name=b,parent_brand_id=c) for a,b,c in brands],["brand_id","name","parent_brand_id"])
w("models.csv",models,["model_id","brand_id","series","model_key","name_zh","alt_names","powertrain","source_id"])
w("generations.csv",gens,["generation_id","model_id","source_row_name","generation_label","status","intro_year","facelift_year","discontinued_year","body_type_id","body_raw","size_class","doors","exterior_design","note","source_id"])
w("model_years.csv",my,["model_year_id","generation_id","year","year_basis","source_id"])
w("trims.csv",[],["trim_id","model_year_id","trim_name","source_id"])
w("body_types.csv",[dict(body_type_id=a,name=b) for a,b in bt_rows],["body_type_id","name"])
w("factory_colors.csv",colors,["color_id","generation_id","model_year_id","model_ref_text","market","color_name_en","color_name_zh","color_role","source_id","retrieval","note"])
w("paint_codes.csv",paint_codes,["paint_code_id","color_id","oem_code","alt_code","source_id"])
w("sources.csv",[dict(source_id=s[0],title=s[1],url=s[2],source_type=s[3],retrieval=s[4],notes=s[5]) for s in SOURCES],["source_id","title","url","source_type","retrieval","notes"])
w("verification_records.csv",ver,["verification_id","subject_type","subject_id","status","evidence","source_id","editor_approved","reviewed_on"])

# --------------------------------------------------------------- stats / issues
by_brand=defaultdict(lambda:[0,0])
for mo in models: by_brand[mo["brand_id"]][0]+=1
mid_brand={mo["model_id"]:mo["brand_id"] for mo in models}
for g in gens: by_brand[mid_brand[g["model_id"]]][1]+=1
bname={a:b for a,b,c in brands}

alias=defaultdict(set)
for mo in models:
    for a in (mo["alt_names"] or "").split(";"):
        a=a.strip()
        if a: alias[a.lower()].add(mo["model_key"])
alias_conf={k:sorted(v) for k,v in alias.items() if len(v)>1}

n_no_year=sum(1 for g in gens if not g["intro_year"])
doc_years=sum(1 for r in my if r["year_basis"].endswith("documented"))
derived_years=sum(1 for r in my if r["year_basis"].startswith("derived"))
color_src_years=sum(1 for r in my if r["year_basis"]=="color_source_year")
distinct_names=len({c["color_name_en"].lower() for c in colors})
gens_with_colors=len({c["generation_id"] for c in colors if c["generation_id"]})
unassigned_series=sum(1 for mo in models if mo["series"] is None and mo["brand_id"]=="B2")
stats=dict(
 models=len(models), generation_rows=len(gens),
 models_byd_brand_only=by_brand["B2"][0], gens_byd_brand_only=by_brand["B2"][1],
 model_year_records=len(my), my_documented=doc_years, my_derived=derived_years, my_color_source=color_src_years,
 color_records=len(colors), distinct_color_names=distinct_names, generations_with_any_color=gens_with_colors,
 paint_codes=len(paint_codes), verification_not_found=sum(1 for v in ver if v["status"]=="NOT FOUND"),
 gens_without_intro_year=n_no_year, series_unassigned_models=unassigned_series,
 body_types=len(bt_rows), doors_documented=sum(1 for g in gens if g["doors"]),
 alias_conflicts=alias_conf, by_brand={bname[k]:v for k,v in by_brand.items()},
 sources=len(SOURCES))
with open(os.path.join(OUT,"stats.json"),"w") as f: json.dump(stats,f,indent=2,ensure_ascii=False)
print(json.dumps(stats,indent=2,ensure_ascii=False))
