#!/usr/bin/env python3
"""Batch 6 validator. Exit 0 = all checks pass. Writes batch6/validation_report_batch6.md.
Usage: python3 validate_batch6.py [--base-commit 43ec2cdb88ab8dfd1b321b43287e1ebad2887ebd]"""
import csv, os, sys, re, json, subprocess, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__)); U = os.path.join(HERE, "catalog_union"); B6 = os.path.join(HERE, "batch6"); REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = "43ec2cdb88ab8dfd1b321b43287e1ebad2887ebd"
if "--base-commit" in sys.argv: BASE = sys.argv[sys.argv.index("--base-commit") + 1]
rd = lambda p: list(csv.DictReader(open(p, encoding="utf-8", newline="")))
res = []
def chk(n, ok, d=""): res.append((n, bool(ok), str(d))); return ok
def tokens(raw): return {t.strip().upper() for t in re.split(r"[;,/]+|\s+\|\s+", raw or "") if t.strip()}

D = rd(f"{B6}/discovered_codes.csv"); S = rd(f"{B6}/sources.csv"); C = rd(f"{B6}/conflicts.csv"); L = rd(f"{B6}/lookup_model_year_colour.csv"); FI = rd(f"{B6}/formula_identifier_investigation.csv")
models = {m["model_id"]: m for m in rd(f"{U}/models_all.csv")}; cols = {c["color_id"]: c for c in rd(f"{U}/factory_colors_all.csv")}; years = {y["model_year_id"]: y for y in rd(f"{U}/model_years_all.csv")}
cands = {c["candidate_id"]: c for c in rd(f"{U}/paint_code_candidates_all.csv")}; links = {l["link_id"]: l for l in rd(f"{U}/color_paint_code_links_all.csv")}
sids = {s["source_id"] for s in S}; base_ids = {s["source_id"] for s in rd(f"{U}/sources_all.csv")}
oem = json.load(open(f"{B6}/raw/oematch_byd_products.json", encoding="utf-8")); crop = json.load(open(f"{B6}/raw/crop_byd_products.json", encoding="utf-8"))
oem_text = "\n".join(r["title"].upper() for r in oem); crop_text = "\n".join(r["slug"].upper().replace("-", " ") for r in crop)

REQ = ["brand", "paint_code", "code_type", "source_url", "evidence_description", "confidence_status", "source_ids", "paint_manufacturer_system", "link_scope"]
chk("required fields non-empty on every row", all(r[k] for r in D for k in REQ), sum(1 for r in D for k in REQ if not r[k]))
chk("all 13 requested fields exist as columns", all(k in D[0] for k in ["brand", "chinese_model_name", "international_model_name", "production_year", "trim", "original_chinese_color_name", "english_color_name", "paint_code", "code_type", "paint_manufacturer_system", "source_url", "evidence_description", "confidence_status"]))
chk("record ids unique", len({r["record_id"] for r in D}) == len(D))
chk("status vocabulary (POSSIBLE/CONFLICTED/UNVERIFIED only; no VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED)", all(r["confidence_status"] in ("POSSIBLE", "CONFLICTED", "UNVERIFIED") for r in D), collections.Counter(r["confidence_status"] for r in D))
chk("no third-party code typed as OEM", all("OEM_VERIFIED" not in r["code_type"] and r["code_type"].startswith(("SUPPLIER", "UNCLASSIFIED")) for r in D), collections.Counter(r["code_type"] for r in D))
chk("every source id registered in sources.csv", all(s in sids for r in D for s in r["source_ids"].split(";")), sorted({s for r in D for s in r["source_ids"].split(";")} - sids))
chk("every source id exists in baseline or is B6S*", all(s in base_ids or s.startswith("B6S") for s in sids))
chk("every row has an https source URL", all(all(u.startswith("https://") for u in r["source_url"].split()) for r in D))
chk("sources.csv: OEM-verification flag never YES", all(not s["usable_as_oem_verification"].upper().startswith("YES") for s in S))
# traceability
bad = []
for r in D:
    code = r["paint_code"].upper(); ok = False
    for rec in r["source_record_ids"].split(";"):
        if rec.startswith("P") and rec in cands: ok |= code in tokens(cands[rec]["code_raw"])
        elif rec.startswith("L") and rec in links: ok |= links[rec]["oem_code"].upper() == code
    if "B6S02" in r["source_ids"].split(";"): ok |= bool(re.search(r"(^|[\s])" + re.escape(code) + r"([\s]|$)", oem_text.replace(" | ", " "), re.M))
    if "B6S03" in r["source_ids"].split(";"): ok |= bool(re.search(r"(^|[\s])" + re.escape(code.replace("-", " ")) + r"([\s]|$)", crop_text, re.M))
    if not ok: bad.append(r["record_id"])
chk("every code is traceable to a source record (baseline candidate/link or harvested listing)", not bad, bad[:5])
# relationships
bad = []
for r in D:
    if r["link_scope"] == "COLOUR_RECORD":
        c = cols.get(r["color_id"])
        if not c or c["model_id"] != r["model_id"] or (c["model_year_id"] and years[c["model_year_id"]]["year"] != r["production_year"]) or (not c["model_year_id"] and r["production_year"]) or c["color_name_zh"] != r["original_chinese_color_name"]: bad.append(r["record_id"])
        elif models[r["model_id"]]["name_zh"] != r["chinese_model_name"]: bad.append(r["record_id"] + ":model")
    elif r["link_scope"] == "MODEL_LEVEL_LISTING" and r["model_id"] and r["model_id"] not in models: bad.append(r["record_id"])
chk("model / year / colour relationships valid; Chinese colour name unchanged", not bad, bad[:5])
chk("brand matches the catalog brand for linked models", all(r["brand"] == {"B2": "BYD", "B3": "Denza", "B4": "Yangwang", "B5": "Fangchengbao", "B6": "Linghui"}[models[r["model_id"]]["brand_id"]] for r in D if r["model_id"] in models))
chk("name-equivalence links only attach to BYD-brand colour records (not cross-brand)", all(models[r["model_id"]]["brand_id"] == "B2" or "B6S" not in r["source_ids"] for r in D if r["link_scope"] == "COLOUR_RECORD"))
k = collections.Counter((r["color_id"], r["paint_code"]) for r in D if r["link_scope"] == "COLOUR_RECORD"); chk("no duplicate (colour record, code) rows", max(k.values()) == 1)
st = collections.defaultdict(set)
for r in D:
    if r["link_scope"] == "COLOUR_RECORD": st[r["color_id"]].add(r["confidence_status"])
chk("one status per colour record", all(len(v) == 1 for v in st.values()))
# conflicts: nothing silently merged
conf_cids = {c for r in C if r["conflict_type"].startswith("SOURCES_DISAGREE") for c in r["color_id"].split(";")}
chk("every CONFLICTED colour record has a conflict row (and vice versa)", conf_cids == {cid for cid, v in st.items() if v == {"CONFLICTED"}}, len(conf_cids))
alias_cids = {c for r in C if r["conflict_type"] == "MULTI_CODE_ALIAS_GROUP" for c in r["color_id"].split(";")}
multi = collections.defaultdict(set)
for r in D:
    if r["link_scope"] == "COLOUR_RECORD": multi[r["color_id"]].add(r["paint_code"])
chk("every multi-code POSSIBLE colour is flagged", {c for c, v in multi.items() if len(v) > 1 and st[c] == {"POSSIBLE"}} <= alias_cids)
chk("conflict ids unique", len({r["conflict_id"] for r in C}) == len(C))
chk("conflicts carry resolution status (no arbitrary choice)", all(r["resolution"].startswith("OPEN") for r in C))
chk("formula identifiers investigated: WA2, HA4, B9, BYD007WA2", {"WA2", "HA4", "B9", "BYD007WA2"} <= {r["identifier"] for r in FI})
chk("B9 / BYD007WA2 not claimed as found", all(r["oem_status"].startswith("NOT_FOUND") for r in FI if r["identifier"] in ("B9", "BYD007WA2") and int(r["occurrences_in_baseline_listings"]) + int(r["occurrences_in_discovered_codes"]) == 0))
chk("no identifier marked verified", all("VERIFIED_OEM" not in r["oem_status"] or "never" in r["oem_status"] for r in FI))
chk("lookup colour ids exist and match discovered rows", all(c in cols for r in L for c in r["color_ids"].split(";") if c) and sum(1 for r in L if r["row_scope"] == "COLOUR_RECORD") > 0)
chk("lookup statuses within vocabulary", all(set(r["confidence_status"].split("/")) <= {"POSSIBLE", "CONFLICTED", "UNVERIFIED"} for r in L))
chk("all required deliverables exist", all(os.path.exists(f"{B6}/{f}") for f in ("REPORT_batch6.md", "discovered_codes.csv", "sources.csv", "conflicts.csv")))
# previous batches unchanged
def git(*a): return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True)
okc = git("cat-file", "-e", BASE + "^{commit}").returncode == 0; chk("Batch 5 base commit present", okc, BASE)
if okc:
    ex = [":(exclude)research/byd/batch6", ":(exclude)research/byd/build_batch6.py", ":(exclude)research/byd/validate_batch6.py", ":(exclude)research/byd/build_batch6_report.py"]
    d = git("diff", "--name-status", BASE, "--", "research", *ex).stdout.strip()
    un = [x for x in git("ls-files", "--others", "--exclude-standard", "research").stdout.split() if not x.startswith("research/byd/batch6/") and x not in ("research/byd/build_batch6.py", "research/byd/validate_batch6.py", "research/byd/build_batch6_report.py")]
    chk("Batches 1-5 files unchanged vs " + BASE[:8] + " (git diff + untracked)", d == "" and not un, d + " " + " ".join(un))
    chk("application files untouched (non-research diff vs base)", git("diff", "--name-only", BASE, "--", ".", ":(exclude)research").stdout.strip() == "")
import tempfile, shutil
wt = tempfile.mkdtemp(prefix="b6_wt_")
try:   # re-run the Batch 5 validator on a clean checkout of the Batch 5 commit (its own files, nothing of Batch 6)
    g = git("worktree", "add", "--detach", wt + "/co", BASE)
    r5 = subprocess.run([sys.executable, "-I", wt + "/co/research/byd/validate_batch5.py"], capture_output=True, text=True, cwd=wt + "/co") if g.returncode == 0 else None
    chk("Batch 5 validator passes on a clean checkout of " + BASE[:8], r5 is not None and r5.returncode == 0, "" if r5 is None else (r5.stdout.strip().splitlines()[-1][:100] if r5.stdout.strip() else r5.stderr[-100:]))
finally:
    git("worktree", "remove", "--force", wt + "/co"); shutil.rmtree(wt, ignore_errors=True); git("worktree", "prune")

ok = all(r[1] for r in res); passed = sum(1 for r in res if r[1])
md = ["# Batch 6 validation report", "", f"Run: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · `research/byd/validate_batch6.py` · base commit `{BASE}`", "",
      f"**Result: {'ALL CHECKS PASSED' if ok else 'FAILURES PRESENT'}** ({passed}/{len(res)})", "", "| # | Check | Result | Detail |", "|---|---|---|---|"]
for i, (n, o, dt) in enumerate(res, 1): md.append(f"| {i} | {n} | {'PASS' if o else 'FAIL'} | {dt.replace('|', '/')[:180]} |")
md += ["", "## Row counts", ""] + [f"- {n}: {len(v)}" for n, v in (("discovered_codes.csv", D), ("lookup_model_year_colour.csv", L), ("sources.csv", S), ("conflicts.csv", C), ("formula_identifier_investigation.csv", FI))]
md += ["", "## Scope notes", "", "- Validates internal consistency and traceability to the harvested listings; it cannot prove any supplier code is the factory code.",
       "- Any VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED status would fail validation: no OEM document or exact-vehicle label evidence was found in Batch 6."]
open(f"{B6}/validation_report_batch6.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(f"{'PASS' if o else 'FAIL'}  {n}  {dt[:110]}" for n, o, dt in res)); sys.exit(0 if ok else 1)
