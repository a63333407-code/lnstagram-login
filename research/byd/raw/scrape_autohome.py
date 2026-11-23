import re, json, subprocess, sys, time, html, os
DATA = sys.argv[1]
SERIES = {"Seal":6394,"Dolphin":6139,"Seagull":6762,"Yuan Plus":6298,"Han":5499,"Qin Plus":5964,"Song Plus":5761,"Destroyer 05":6337,"e2":5238}
UA = "Mozilla/5.0"
def get(url):
    for i in range(3):
        p = subprocess.run(["curl","-sS","-m","40","-A",UA,url],capture_output=True)
        if p.returncode==0 and len(p.stdout)>5000:
            return p.stdout.decode("gb18030","ignore")
        time.sleep(2)
    return ""
def list_specs(page):
    specs=[]
    for m in re.finditer(r'<dt>([^<]*)</dt><dd>(.*?)</dd>', page, re.S):
        yr = m.group(1)
        for a in re.finditer(r'<a href="/pic/series-s(\d+)/(\d+)\.html[^"]*"[^>]*>\s*([^<]*)<span[^>]*>\(?(\d+)([^<]*)</span>(.*?)</a>', m.group(2), re.S):
            specs.append(dict(year=yr, spec_id=a.group(1), label=html.unescape(a.group(3)).strip(), photos=int(a.group(4)),
                              stopsale=("icon-stopsale" in a.group(6)), color_view=("icon16-rainbow" in a.group(6))))
    return specs
old = json.load(open(DATA+"/autohome_raw.json")) if os.path.exists(DATA+"/autohome_raw.json") else {}
out = {}
for name,sid in SERIES.items():
    cache = {s["spec_id"]:s for s in old.get(name,{}).get("specs",[])}
    seen = {}
    pages = {}
    for tag,url in (("series-t",f"https://car.autohome.com.cn/pic/series-t/{sid}.html"),("series",f"https://car.autohome.com.cn/pic/series/{sid}.html")):
        pg = get(url); time.sleep(0.5)
        pages[tag]=url
        for s in list_specs(pg):
            s["listed_on"]=[tag]
            if s["spec_id"] in seen: seen[s["spec_id"]]["listed_on"].append(tag)
            else: seen[s["spec_id"]]=s
    print(name, sid, "specs:", len(seen), "new:", len([k for k in seen if k not in cache]), file=sys.stderr, flush=True)
    for sp in seen.values():
        if sp["spec_id"] in cache and cache[sp["spec_id"]].get("title"):
            c=cache[sp["spec_id"]]; sp["title"]=c["title"]; sp["url"]=c["url"]; sp["colors"]=c["colors"]; continue
        u = f"https://car.autohome.com.cn/pic/series-s{sp['spec_id']}/{sid}-1.html"
        pg = get(u); time.sleep(0.5)
        t = re.search(r'<title>([^<]*)', pg)
        sp["title"] = t.group(1).strip() if t else None
        sp["url"] = u
        sp["colors"] = [dict(color_id=c.group(1), hex=c.group(2), name_zh=c.group(3).strip(), photos=int(c.group(4)))
            for c in re.finditer(r'<a href="/pic/spec-%s-(\d+)-[^"]*" class="color-cont[^"]*"[^>]*><em style="background-color:(#[0-9A-Fa-f]{3,6});?"></em><em class="carcolor-bg"></em>([^<]*)<span[^>]*>\((\d+)' % sp["spec_id"], pg)]
    out[name] = dict(series_id=sid, series_urls=pages, specs=list(seen.values()))
    json.dump(out, open(DATA+"/autohome_raw2.json","w"), ensure_ascii=False, indent=1)
