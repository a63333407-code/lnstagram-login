#!/usr/bin/env python3
"""Batch 7 validator. Exit 0 = all checks pass. Writes batch7/validation_report.md.
Usage: python3 validate_batch7.py [--base-commit f3b8f83c33c7f79b41b3efef053b249917324def]"""
import csv, os, sys, re, json, subprocess, datetime, collections, tempfile, shutil

HERE = os.path.dirname(os.path.abspath(__file__)); U = f"{HERE}/catalog_union"; B6 = f"{HERE}/batch6"; B7 = f"{HERE}/batch7"; REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = "f3b8f83c33c7f79b41b3efef053b249917324def"
if "--base-commit" in sys.argv: BASE = sys.argv[sys.argv.index("--base-commit") + 1]
rd = lambda p: list(csv.DictReader(open(p, encoding="utf-8", newline="")))
res = []
def chk(n, ok, d=""): res.append((n, bool(ok), str(d))); return ok
def tokens(raw): return {t.strip().upper() for t in re.split(r"[;,/]+|\s+\|\s+", raw or "") if t.strip()}

D = rd(f"{B7}/discovered_codes.csv"); S = rd(f"{B7}/sources.csv"); C = rd(f"{B7}/conflicts.csv"); VR = rd(f"{B7}/vin_research.csv"); PL = rd(f"{B7}/verification_sample_plan.csv"); LA = rd(f"{B7}/source_lineage_analysis.csv")
tmpl_header = open(f"{B7}/vin_evidence_template.csv", encoding="utf-8").read().strip().split(",")
st = json.load(open(f"{B7}/stats_batch7.json", encoding="utf-8"))
models = {m["model_id"]: m for m in rd(f"{U}/models_all.csv")}; cols = {c["color_id"]: c for c in rd(f"{U}/factory_colors_all.csv")}; years = {y["model_year_id"]: y for y in rd(f"{U}/model_years_all.csv")}
cands = {c["candidate_id"]: c for c in rd(f"{U}/paint_code_candidates_all.csv")}; b6 = rd(f"{B6}/discovered_codes.csv")
sids = {s["source_id"] for s in S}
dyc = json.load(open(f"{B7}/raw/dipyourcar_byd_products.json", encoding="utf-8")); dyc_text = "\n".join(r["title"].upper() for r in dyc)
LIN = {"S29": "ColourTubes", "S30": "Cartouch", "S31": "Carross", "S227": "Carross", "S32": "TouchUpPaintFactory", "S226": "TouchUpPaintFactory", "B6S02": "L", "B7S02": "L", "B6S03": "CROP"}

# --- required fields (user's list: brand, model, model year, Chinese colour name, paint code, code type, source, evidence, confidence)
always = ["brand", "paint_code", "code_type", "source_ids", "source_url", "evidence_description", "confidence_status", "link_scope", "record_id", "delta"]
chk("always-required fields non-empty", all(r[k] for r in D for k in always), sum(1 for r in D for k in always if not r[k]))
chk("colour-record rows carry model (intl name; Chinese name exactly as catalog - may be NULL for models without one) and catalog ids", all(r["international_model_name"] and r["model_id"] and r["color_id"] and r["chinese_model_name"] == models[r["model_id"]]["name_zh"] for r in D if r["link_scope"] == "COLOUR_RECORD"))
chk("colour-record rows with a named model year match the catalog; blank year never invented", all((years[cols[r["color_id"]]["model_year_id"]]["year"] == r["production_year"]) if cols[r["color_id"]]["model_year_id"] else (r["production_year"] == "") for r in D if r["link_scope"] == "COLOUR_RECORD"))
chk("record ids unique", len({r["record_id"] for r in D}) == len(D))
chk("all requested field columns exist", all(k in D[0] for k in ["brand", "international_model_name", "production_year", "original_chinese_color_name", "paint_code", "code_type", "source_ids", "source_url", "evidence_description", "confidence_status"]))
# --- evidence discipline
chk("status vocabulary: POSSIBLE/CONFLICTED/UNVERIFIED only (no VERIFIED_*/CORROBORATED)", all(r["confidence_status"] in ("POSSIBLE", "CONFLICTED", "UNVERIFIED") for r in D), collections.Counter(r["confidence_status"] for r in D))
chk("no row is above POSSIBLE regardless of lineage count (repetition is not corroboration)", all(r["confidence_status"] in ("POSSIBLE", "CONFLICTED") for r in D) and max(int(r["independent_lineage_count"]) for r in D) >= 1)
chk("formula-system references kept separate from vehicle paint-code candidates (code_role)", all((r["code_role"] == "FORMULA_SYSTEM_REFERENCE_CANDIDATE") == bool(re.fullmatch(r"BYH[A-Z]-\d+|BYD\d{2,}[A-Z0-9]*", r["paint_code"].upper())) for r in D))
chk("no code typed or roled as OEM", all("OEM_VERIFIED" not in r["code_type"] and r["code_role"] in ("VEHICLE_PAINT_CODE_CANDIDATE", "FORMULA_SYSTEM_REFERENCE_CANDIDATE", "UNCLASSIFIED") and r["code_type"].startswith(("SUPPLIER", "UNCLASSIFIED")) for r in D))
chk("every source id registered in sources.csv", all(s in sids for r in D for s in r["source_ids"].split(";")), sorted({s for r in D for s in r["source_ids"].split(";")} - sids))
chk("sources.csv: usable_as_oem_verification never YES", all(not s["usable_as_oem_verification"].upper().startswith("YES") for s in S))
lin_bad = [r["record_id"] for r in D if int(r["independent_lineage_count"]) != len({LIN[s] for s in r["source_ids"].split(";") if s in LIN})]
chk("independent_lineage_count correct; OEMatch + DipYourCar count as one lineage", not lin_bad, lin_bad[:5])
# --- traceability
bad = []
for r in D:
    code = r["paint_code"].upper(); ok = False; ss = r["source_ids"].split(";")
    if "B7S02" in ss: ok |= bool(re.search(r"(^|\s)" + re.escape(code) + r"(\s|\||$)", dyc_text))
    if any(s in ss for s in ("S29", "S30", "S31", "S32", "S226", "S227")): ok |= any(code in tokens(c["code_raw"]) for c in cands.values() if c["source_id"] in ss)
    if "B6S02" in ss or "B6S03" in ss: ok |= any(x["paint_code"].upper() == code for x in b6)
    if not ok: bad.append(r["record_id"])
chk("every code is traceable to a source record (harvested listing, baseline candidate or Batch 6 row)", not bad, bad[:5])
bad = []
for r in D:
    if r["link_scope"] == "COLOUR_RECORD":
        c = cols.get(r["color_id"])
        if not c or c["model_id"] != r["model_id"] or c["color_name_zh"] != r["original_chinese_color_name"] or models[r["model_id"]]["name_zh"] != r["chinese_model_name"]: bad.append(r["record_id"])
        elif models[r["model_id"]]["brand_id"] != "B2": bad.append(r["record_id"] + ":cross_brand")
chk("colour-record relationships valid; Chinese colour name unchanged; no cross-brand name linking", not bad, bad[:5])
# --- delta correctness
b6k = {}
for x in b6:
    if x["link_scope"] == "COLOUR_RECORD": b6k[(x["color_id"], x["paint_code"])] = x["confidence_status"]
dbad = []
for r in D:
    if r["link_scope"] != "COLOUR_RECORD": continue
    k = (r["color_id"], r["paint_code"])
    if r["delta"] == "NEW_ROW" and k in b6k: dbad.append(r["record_id"])
    if r["delta"] == "STATUS_CHANGED" and (k not in b6k or b6k[k] == r["confidence_status"] or r["batch6_status"] != b6k[k]): dbad.append(r["record_id"])
    if r["delta"] == "SOURCE_ADDED" and (k not in b6k or r["batch6_status"] != b6k[k]): dbad.append(r["record_id"])
chk("delta labels consistent with Batch 6 (NEW_ROW/STATUS_CHANGED/SOURCE_ADDED)", not dbad, dbad[:5])
chk("pipeline reproduces Batch 6 exactly when DipYourCar is excluded (self-check)", st["self_check"]["identical"] and st["self_check"]["batch6_keys"] == st["self_check"]["reproduced_keys"], st["self_check"])
# --- conflicts
conf = {c for r in C if r["conflict_type"].startswith("SOURCES_DISAGREE") for c in r["color_id"].split(";")}
chk("every CONFLICTED colour record in the delta file has a conflict row", {r["color_id"] for r in D if r["link_scope"] == "COLOUR_RECORD" and r["confidence_status"] == "CONFLICTED"} <= conf)
chk("conflict ids unique; all OPEN (nothing silently resolved)", len({r["conflict_id"] for r in C}) == len(C) and all(r["resolution"].startswith("OPEN") for r in C))
chk("lineage, colour-class and label-location conflicts recorded", {"RETAILER_LINEAGE", "COLOUR_CLASS_VS_CODE", "LABEL_LOCATION"} <= {r["conflict_type"] for r in C})
chk("every source named in conflicts exists", all(s in sids for r in C for s in re.split(r"[;,]\s*", r["sources_involved"]) if s and not s[0].isspace()), sorted({s for r in C for s in r["sources_involved"].split(";") if s} - sids)[:5])
oem_dyc = next(r for r in LA if (r["source_a"], r["source_b"]) == ("B6S02", "B7S02"))
chk("lineage analysis: OEMatch vs DipYourCar identical-name share >= 60% (same upstream)", int(oem_dyc["shared_codes"]) > 0 and int(oem_dyc["shared_codes_with_identical_normalised_name"]) / int(oem_dyc["shared_codes"]) >= 0.6, oem_dyc["identical_name_share"])
# --- VIN research
chk("vin_research: fields present, sources registered, flag vocabulary, nothing marked a confirmed VIN->code route", all(r["method_id"] and r["finding"] and r["verification_level"] and r["role_in_recommended_method"] and all(s in sids for s in r["source_ids"].split(";")) and not r["yields_factory_paint_code"].upper().startswith("YES") for r in VR), len(VR))
chk("vin_research: VIN-decode, certificate, nameplate, dealer, paint-system methods all covered", all(any(k in r["method"] for r in VR) for k in ("Decode the VIN", "certificate", "nameplate", "service centre", "AkzoNobel", "Baslac", "Axalta", "17vin")))
chk("vin_research: dealer route marked unverified for BYD", any("UNVERIFIED" in r["yields_factory_paint_code"].upper() for r in VR if "service centre" in r["method"]))
# --- sample plan and template
pl_bad = [r["model_id"] for r in PL if r["model_id"] not in models or r["current_status"] not in ("POSSIBLE", "CONFLICTED")]
chk("sample plan: models exist, statuses valid, rows sorted by priority", not pl_bad and [int(r["priority_rank"]) for r in PL] == sorted(int(r["priority_rank"]) for r in PL), len(PL))
chk("evidence template stores no raw VIN (hash + first 9 chars only)", not any(re.fullmatch(r"vin|vin_full|vin_number", h.strip().lower()) for h in tmpl_header) and "vin_sha256_hex" in tmpl_header)
chk("all required deliverables exist", all(os.path.exists(f"{B7}/{f}") for f in ("REPORT_batch7.md", "discovered_codes.csv", "sources.csv", "vin_research.csv", "conflicts.csv")))
# --- previous batches
def git(*a): return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True)
okc = git("cat-file", "-e", BASE + "^{commit}").returncode == 0; chk("Batch 6 base commit present", okc, BASE)
if okc:
    ex = [":(exclude)research/byd/batch7", ":(exclude)research/byd/build_batch7.py", ":(exclude)research/byd/validate_batch7.py", ":(exclude)research/byd/build_batch7_report.py"]
    d = git("diff", "--name-status", BASE, "--", "research", *ex).stdout.strip()
    un = [x for x in git("ls-files", "--others", "--exclude-standard", "research").stdout.split() if not x.startswith("research/byd/batch7/") and x not in ("research/byd/build_batch7.py", "research/byd/validate_batch7.py", "research/byd/build_batch7_report.py")]
    chk("Batches 1-6 files unchanged vs " + BASE[:8] + " (git diff + untracked)", d == "" and not un, d + " " + " ".join(un))
    chk("application files untouched (non-research diff vs base)", git("diff", "--name-only", BASE, "--", ".", ":(exclude)research").stdout.strip() == "")
wt = tempfile.mkdtemp(prefix="b7_wt_")
try:
    g = git("worktree", "add", "--detach", wt + "/co", BASE)
    r6 = subprocess.run([sys.executable, "-I", wt + "/co/research/byd/validate_batch6.py"], capture_output=True, text=True, cwd=wt + "/co") if g.returncode == 0 else None
    chk("Batch 6 validator passes on a clean checkout of " + BASE[:8], r6 is not None and r6.returncode == 0, "" if r6 is None else (r6.stdout.strip().splitlines()[-1][:100] if r6.stdout.strip() else r6.stderr[-100:]))
finally:
    git("worktree", "remove", "--force", wt + "/co"); shutil.rmtree(wt, ignore_errors=True); git("worktree", "prune")

ok = all(r[1] for r in res); passed = sum(1 for r in res if r[1])
md = ["# Batch 7 validation report", "", f"Run: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · `research/byd/validate_batch7.py` · base commit `{BASE}`", "",
      f"**Result: {'ALL CHECKS PASSED' if ok else 'FAILURES PRESENT'}** ({passed}/{len(res)})", "", "| # | Check | Result | Detail |", "|---|---|---|---|"]
for i, (n, o, dt) in enumerate(res, 1): md.append(f"| {i} | {n} | {'PASS' if o else 'FAIL'} | {dt.replace('|', '/')[:180]} |")
md += ["", "## Row counts", ""] + [f"- {n}: {len(v)}" for n, v in (("discovered_codes.csv (changes vs Batch 6)", D), ("sources.csv", S), ("vin_research.csv", VR), ("conflicts.csv", C), ("source_lineage_analysis.csv", LA), ("verification_sample_plan.csv", PL))]
md += ["", "## Scope notes", "", "- Validates internal consistency, traceability to harvested listings and previous-batch integrity; it cannot prove that any supplier code is the factory code.",
       "- Any VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED status would fail validation: no OEM document, dealer record or exact-vehicle label evidence was obtained in Batch 7.",
       "- The self-check proves the Batch 6 matching pipeline, re-implemented in `build_batch7.py`, reproduces Batch 6 exactly before the new source is added."]
open(f"{B7}/validation_report.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(f"{'PASS' if o else 'FAIL'}  {n}  {dt[:110]}" for n, o, dt in res)); sys.exit(0 if ok else 1)
