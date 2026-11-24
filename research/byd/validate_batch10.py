#!/usr/bin/env python3
"""Batch 10 validator. Exit 0 = all checks pass. Writes batch10/validation_report.md and batch10/previous_batches_manifest.txt.
Usage: python3 validate_batch10.py [--base-commit 8ae4f435479939ea17bc444bf77c40e65666f6b5]"""
import csv, os, sys, re, json, subprocess, datetime, collections, tempfile, shutil, hashlib

HERE = os.path.dirname(os.path.abspath(__file__)); U = f"{HERE}/catalog_union"; B10 = f"{HERE}/batch10"; REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = "8ae4f435479939ea17bc444bf77c40e65666f6b5"
if "--base-commit" in sys.argv: BASE = sys.argv[sys.argv.index("--base-commit") + 1]
rd = lambda p: list(csv.DictReader(open(p, encoding="utf-8", newline="")))
res = []
def chk(n, ok, d=""): res.append((n, bool(ok), str(d))); return ok
STATUSES = {"VERIFIED_OEM", "VERIFIED_LABEL", "CORROBORATED", "PAINT_SYSTEM_REFERENCE", "POSSIBLE", "CONFLICTED", "UNVERIFIED"}
REF_RE = re.compile(r"BYH[A-Z]-\d+|BYD\d{2,}[A-Z0-9]*")

SA = rd(f"{B10}/source_audit.csv"); LG = rd(f"{B10}/source_lineage_graph.csv"); CA = rd(f"{B10}/colour_conflict_audit.csv"); MY = rd(f"{B10}/model_year_consistency.csv"); RQ = rd(f"{B10}/evidence_requirements.csv")
st = json.load(open(f"{B10}/stats_batch10.json", encoding="utf-8"))
cols = {c["color_id"]: c for c in rd(f"{U}/factory_colors_all.csv")}; models = {m["model_id"]: m for m in rd(f"{U}/models_all.csv")}; years = {y["model_year_id"]: y for y in rd(f"{U}/model_years_all.csv")}; gens = {g["generation_id"]: g for g in rd(f"{U}/generations_all.csv")}
report = open(f"{B10}/REPORT_batch10.md", encoding="utf-8").read()
FILES = ["REPORT_batch10.md", "source_audit.csv", "source_lineage_graph.csv", "colour_conflict_audit.csv", "model_year_consistency.csv", "evidence_requirements.csv", "owner_request_zh.md", "owner_request_en.md", "dealer_request_zh.md", "dealer_request_en.md", "evidence_photo_checklist.md", "unresolved_questions.md"]
txt = {f: open(f"{B10}/{f}", encoding="utf-8").read() for f in FILES}

# --- honesty
chk("report states at the top that no genuine OEM evidence was obtained; 0/0/0 verified counts", "No genuine OEM evidence was obtained" in "\n".join(report.splitlines()[:4]) and "VERIFIED_OEM = 0" in report)
chk("report contains the required figures table (items 1-7) and top-20 / evidence / next-batch sections", all(k in report for k in ("| 1 | Colour records audited", "| 2 | Source lineages", "| 3 | VERIFIED_OEM", "| 4 | VERIFIED_LABEL", "| 5 | CORROBORATED", "| 6 | POSSIBLE / CONFLICTED", "| 7 | Unresolved model-year differences", "## Top 20 highest-priority unresolved colours", "## Exact evidence needed", "## Next batch")))
chk("no record in any Batch 10 table is VERIFIED_OEM, VERIFIED_LABEL or CORROBORATED", not any(r.get("status", "") in ("VERIFIED_OEM", "VERIFIED_LABEL", "CORROBORATED") for r in MY + CA) and st["verified_oem"] == st["verified_label"] == st["corroborated"] == 0)
# --- source audit: preservation + classification
ids = set()
ids |= {r["source_id"] for r in rd(f"{U}/sources_all.csv")}
ids |= {r["b5_source_id"] for r in rd(f"{HERE}/batch5/source_register.csv")}
for b in (6, 7, 8): ids |= {r["source_id"] for r in rd(f"{HERE}/batch{b}/sources.csv")}
ids |= {r["evidence_id"] for r in rd(f"{HERE}/batch9/evidence_register.csv")}
have = {r["source_key"] for r in SA}
chk("every source from Batches 1-9 is present in source_audit (nothing deleted)", ids <= have, sorted(ids - have)[:5])
chk("source_audit: every row has a class and a lineage; class vocabulary known", all(r["source_class"] and r["lineage_id"] for r in SA) and set(r["source_class"] for r in SA) <= {"MANUFACTURER_CONTROLLED", "RETAILER_TOUCHUP_PAINT", "LICENSED_PAINT_SYSTEM", "MEDIA_PORTAL_CATALOG", "ENCYCLOPEDIA", "MEDIA_ARTICLE", "FORUM_QA", "MARKETPLACE_OR_COPIED_LISTING", "REGULATORY_STANDARD", "DATA_PLATFORM_THIRD_PARTY", "SEARCH_RECORD", "PENDING_PLACEHOLDER", "INDUSTRY_BODY_INDEX", "OTHER"}, collections.Counter(r["source_class"] for r in SA))
chk("only retailer/touch-up sources carry vehicle paint codes; no manufacturer-controlled source carries one", all(r["source_class"] == "RETAILER_TOUCHUP_PAINT" for r in SA if r["contains_vehicle_paint_codes"] == "YES") and not any(r["manufacturer_controlled"] == "YES" and r["contains_vehicle_paint_codes"] == "YES" for r in SA))
chk("source_audit: original type and first batch preserved; reclassified rows say so", all(r["original_type"] and r["first_batch"] for r in SA) and all(r["audit_note"] for r in SA if r["source_class"] in ("FORUM_QA", "MARKETPLACE_OR_COPIED_LISTING")))
chk("each source_audit row states its status effect (no source can verify alone)", all(r["status_effect"] for r in SA))
# --- lineage graph
code_lins = sorted({r["lineage_id"] for r in SA if r["contains_vehicle_paint_codes"] == "YES"})
lin = {r["source_key"]: r["lineage_id"] for r in SA}
chk("exactly 5 paint-code lineages; OEMatch+DipYourCar are one lineage; Touch Up Paint Factory+Cartouch are one lineage (copies counted once)", len(code_lins) == 5 == st["paint_code_lineages"] and lin["B6S02"] == lin["B7S02"] and lin["S32"] == lin["S226"] == lin["S30"] and lin["S31"] == lin["S227"], code_lins)
nodes = {r["id"] for r in LG if r["row_type"] == "NODE"}
chk("graph has a node for every lineage and no node claims OEM grade", {r["lineage_id"] for r in SA} <= nodes and all(r["oem_grade"] == "NO" for r in LG))
chk("graph edges carry evidence text; merge rule documented", all(r["evidence"] for r in LG) and any("heuristic" in r["evidence"] for r in LG if r["row_type"] == "NODE"))
chk("total lineage count in stats equals distinct lineages of non-search, non-placeholder sources", st["lineages_all"] == len({r["lineage_id"] for r in SA if r["source_class"] not in ("SEARCH_RECORD", "PENDING_PLACEHOLDER")}), st["lineages_all"])
# --- priority conflict audit
grp = [r for r in CA if r["row_type"] == "GROUP"]
chk("priority groups in the requested order: 雪域白, 攀岩灰, 亚特兰蒂斯灰, 苍穹蓝", [r["colour_zh"] for r in grp] == ["雪域白", "攀岩灰", "亚特兰蒂斯灰", "苍穹蓝"])
b67 = [r for b in (6, 7) for r in rd(f"{HERE}/batch{b}/discovered_codes.csv") if r["link_scope"] == "COLOUR_RECORD"]
ok = True
for g in grp:
    want = {r["paint_code"] for r in b67 if r["original_chinese_color_name"] == g["colour_zh"]}
    got = {r["code"] for r in CA if r["row_type"] == "CODE" and r["colour_zh"] == g["colour_zh"]}
    ok &= want == got and set(g["competing_codes"].split(" | ")) == want
chk("every competing code of each priority colour is listed (none dropped, none added)", ok)
codes_rows = [r for r in CA if r["row_type"] == "CODE"]
chk("every code row names its supporting sources (registered) and lineages, independence note and explanation tests", all(r["supporting_sources"] and all(s in have for s in r["supporting_sources"].split(";")) and r["lineage_independence"] and r["explanation_tests"] for r in codes_rows))
chk("all conflict rows OPEN; no winner chosen; no label/official evidence claimed", all(r["resolution_status"] == "OPEN" for r in CA) and all(r["official_or_label_evidence"].startswith("NONE FOUND") for r in codes_rows) and not any("winner" in " ".join(r.values()).lower() or "majority" in r.get("assessment", "").lower() for r in CA))
chk("single-lineage support is flagged NOT INDEPENDENT", all(r["lineage_independence"] == "NOT INDEPENDENT" for r in codes_rows if int(r["n_lineages"]) <= 1))
chk("reference identifiers kept separate: BYHB-00001 is PAINT_SYSTEM_REFERENCE, never a vehicle code", all((r["code_class"] == "PAINT_SYSTEM_REFERENCE") == bool(REF_RE.fullmatch(r["code"])) and (r["status"] == "PAINT_SYSTEM_REFERENCE") == bool(REF_RE.fullmatch(r["code"])) for r in codes_rows))
# --- model-year consistency over all colour records
chk("model_year_consistency has exactly one row per catalogue colour record (1,223)", len(MY) == len(cols) == 1223 and {r["color_id"] for r in MY} == set(cols), len(MY))
bad = []
for r in MY:
    c = cols[r["color_id"]]; y = years.get(c["model_year_id"], {})
    if r["colour_name_zh"] != c["color_name_zh"] or r["model_id"] != c["model_id"] or r["generation_id"] != c["generation_id"] or r["model_year_id"] != c["model_year_id"]: bad.append(r["color_id"])
    elif r["model_year"] != (y.get("year") or "UNKNOWN"): bad.append(r["color_id"] + ":year")
    elif c["model_year_id"] and (y.get("model_id") != c["model_id"]): bad.append(r["color_id"] + ":my_model")
chk("model/generation/model-year relationships and Chinese colour names exactly as the catalogue; missing years stay UNKNOWN", not bad, bad[:5])
chk("status vocabulary valid; counts match stats; no verified status", all(r["status"] in STATUSES for r in MY) and dict(collections.Counter(r["status"] for r in MY)) == st["status"] and not any(r["status"].startswith("VERIFIED") for r in MY))
chk("different generations/years/markets are never merged: rows keyed per colour record; matte Chinese names flagged MATTE separately", all(r["finish_from_catalogue"] == ("MATTE" if r["colour_name_zh"].startswith("哑光") else "UNKNOWN") for r in MY))
chk("year flags are explained (every flagged row has a reason) and counted", all((r["unresolved_year_difference"] == "YES") == bool(r["unresolved_year_reasons"]) for r in MY) and st["year_flag_rows"] == sum(1 for r in MY if r["unresolved_year_difference"] == "YES"))
chk("every candidate-bearing record states evidence type, lineages and unresolved questions", all(r["evidence_type"] and r["unresolved_questions"] for r in MY) and all(r["evidence_type"] == "NONE" for r in MY if r["status"] == "UNVERIFIED"))
chk("required per-record fields present (brand, model, year, Chinese + English/transliterated name, codes, finish, lineage, evidence, status, questions)", all(k in MY[0] for k in ("brand", "model", "model_year", "colour_name_zh", "english_name_unofficial", "pinyin_translit", "candidate_vehicle_codes", "finish_from_catalogue", "source_lineages", "evidence_type", "status", "unresolved_questions", "market")))
# --- evidence requirements
rules = [r for r in RQ if r["row_type"] == "STATUS_RULE"]; cr = [r for r in RQ if r["row_type"] == "COLOUR_REQUIREMENT"]
chk("evidence_requirements: rules for all seven statuses and exactly 20 ranked colour requirements, the four priority colours first", {r["target"] for r in rules} == STATUSES and len(cr) == 20 and [r["colour_zh"] for r in cr[:4]] == ["雪域白", "攀岩灰", "亚特兰蒂斯灰", "苍穹蓝"])
chk("every colour requirement states minimum evidence and what does not count", all(r["minimum_evidence"] and r["does_not_count"] for r in cr))
chk("CORROBORATED rule requires genuinely independent lineages; verbal/retailer/formula/name matches excluded", any("independent" in r["minimum_evidence"] and "one upstream" in r["does_not_count"] for r in rules if r["target"] == "CORROBORATED") and any("Verbal" in r["does_not_count"] and "formula" in r["does_not_count"] for r in rules if r["target"] == "VERIFIED_OEM"))
# --- evidence kit
loc = ("B柱", "B-pillar", "door jamb", "门框", "发动机舱", "bonnet", "glovebox", "手套箱")
oz, oe, dz, de, ck = txt["owner_request_zh.md"], txt["owner_request_en.md"], txt["dealer_request_zh.md"], txt["dealer_request_en.md"], txt["evidence_photo_checklist.md"]
chk("owner requests do not ask for a VIN and claim no label location; offer voluntary identity options only", "不要求您提供车架号" in oz and "does **not ask for your VIN**" in oe and not any(k in oz + oe for k in loc) and "前 9 位" in oz and "first 9 characters" in oe)
chk("dealer requests: VIN only by the owner, in person, voluntarily; researchers never collect it; no location claims", "仅在车主本人自愿同意时" in dz and "only if the vehicle owner voluntarily agrees" in de and "in person" in de and "不会收集、保存或公开完整车架号" in dz and not any(k in dz + de for k in loc))
chk("Chinese and English versions cover the same items (owner and dealer)", oz.count("## ") == oe.count("## ") and dz.count("## ") == de.count("## ") and oz.count("\n- ") + oz.count("\n1.") > 0)
chk("checklist covers redaction, GPS stripping, label context shots, VIN-vs-paint-code guide, formula identifier, VERIFIED_LABEL conditions, and states no official location is confirmed", all(k in ck for k in ("GPS", "17 characters", "BYHB-00001", "Vehicle association", "Authenticity", "Meaning")) and "no official source confirms a colour-label location" in ck)
chk("unresolved questions cover the four priority colours, lineages, model-year, real-world evidence, other brands", all(k in txt["unresolved_questions.md"] for k in ("雪域白", "攀岩灰", "亚特兰蒂斯灰", "苍穹蓝", "## B. Lineages", "## C. Model-year", "## D. Real-world evidence", "## E. Other brands")))
allt = "\n".join(txt.values()) + "\n".join(open(f"{B10}/{f}", encoding="utf-8").read() for f in ("source_audit.csv", "source_lineage_graph.csv", "colour_conflict_audit.csv", "model_year_consistency.csv", "evidence_requirements.csv"))
chk("privacy/secrets: no VIN-like 17-character strings, no tokens", not re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", re.sub(r"https?://\S+", "", allt)) and "accessToken" not in allt and "eyJ" not in allt)
chk("all deliverables except validation_report.md / manifest exist", all(os.path.exists(f"{B10}/{f}") for f in FILES))
# --- previous batches
def git(*a, inp=None): return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, input=inp)
okc = git("cat-file", "-e", BASE + "^{commit}").returncode == 0; chk("Batch 9 base commit present", okc, BASE)
if okc:
    tree = [l.split("\t") for l in git("ls-tree", "-r", BASE, "--", "research").stdout.splitlines()]; entries = [(t[1], t[0].split()[2]) for t in tree]
    work = [e for e in entries if os.path.exists(os.path.join(REPO, e[0]))]
    hashes = git("hash-object", "--stdin-paths", inp="\n".join(os.path.join(REPO, p) for p, _ in work) + "\n").stdout.split()
    mism = [p for (p, sha), h in zip(work, hashes) if sha != h]; missing = [p for p, _ in entries if not os.path.exists(os.path.join(REPO, p))]
    chk(f"Batches 1-9: all {len(entries)} files at {BASE[:8]} present and byte-identical (git blob comparison)", not mism and not missing and len(hashes) == len(work), f"mismatch={mism[:3]} missing={missing[:3]}")
    own = ("research/byd/batch10/", "research/byd/build_batch10.py", "research/byd/build_batch10_report.py", "research/byd/validate_batch10.py")
    un = [x for x in git("ls-files", "--others", "--exclude-standard", "research").stdout.split() if not x.startswith(own)]
    chk("no stray new files outside batch10 and its scripts", not un, un[:3])
    chk("application files untouched (non-research diff vs base)", git("diff", "--name-only", BASE, "--", ".", ":(exclude)research").stdout.strip() == "")
    grpd = collections.OrderedDict()
    for p, sha in entries:
        parts = p.split("/"); key = parts[2] if len(parts) > 3 and parts[2] in ("batch1", "batch4", "batch5", "batch6", "batch7", "batch8", "batch9", "catalog_union", "raw", "raw_b4") else "batch2-3 top-level files"
        grpd.setdefault(key, []).append(f"{p} {sha}")
    lines = [f"# SHA-256 digests of sorted '<path> <git blob id>' lists per area at {BASE} (each verified identical to the working tree; {len(entries)} files)"]
    for k, vv in grpd.items(): lines.append(f"{hashlib.sha256(chr(10).join(sorted(vv)).encode()).hexdigest()}  {k}  ({len(vv)} files)")
    open(f"{B10}/previous_batches_manifest.txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")
RUN = [("b39bff8", "validate_batch3.py", "Batch 3"), ("cb78fcb", "validate_batch4.py", "Batch 4"), ("43ec2cd", "validate_batch5.py", "Batch 5"), ("f3b8f83", "validate_batch6.py", "Batch 6"), ("9c594da", "validate_batch7.py", "Batch 7"), ("5cd5bd7", "validate_batch8.py", "Batch 8"), ("8ae4f43", "validate_batch9.py", "Batch 9")]
tmp = tempfile.mkdtemp(prefix="b10_wt_")
try:
    for commit, script_, label in RUN:
        d = f"{tmp}/{commit}"; g = git("worktree", "add", "--detach", d, commit)
        r = subprocess.run([sys.executable, "-I", f"{d}/research/byd/{script_}"], capture_output=True, text=True, cwd=d, timeout=3000) if g.returncode == 0 else None
        chk(f"{label} validator ({script_}) passes on a clean checkout of {commit}", r is not None and r.returncode == 0, "" if r is None else f"exit {r.returncode}")
        git("worktree", "remove", "--force", d)
finally:
    shutil.rmtree(tmp, ignore_errors=True); git("worktree", "prune")

ok = all(r[1] for r in res); passed = sum(1 for r in res if r[1])
md = ["# Batch 10 validation report", "", f"Run: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · `research/byd/validate_batch10.py` · base commit `{BASE}`", "",
      f"**Result: {'ALL CHECKS PASSED' if ok else 'FAILURES PRESENT'}** ({passed}/{len(res)})", "", "| # | Check | Result | Detail |", "|---|---|---|---|"]
for i, (n, o, dt) in enumerate(res, 1): md.append(f"| {i} | {n} | {'PASS' if o else 'FAIL'} | {dt.replace('|', '/')[:180]} |")
md += ["", "## Row counts", ""] + [f"- {n}: {len(vv)}" for n, vv in (("source_audit.csv", SA), ("source_lineage_graph.csv", LG), ("colour_conflict_audit.csv", CA), ("model_year_consistency.csv", MY), ("evidence_requirements.csv", RQ))]
md += ["", "## Notes", "", "- The validator proves traceability and preservation: every earlier source is still present, every colour record is audited once, every priority-colour code is listed with its sources, and nothing is promoted or resolved.",
       "- Previous-batch integrity: every research file of Batches 1-9 at the Batch 9 commit is compared by git blob id with the working tree; per-area digests are in `previous_batches_manifest.txt`.",
       "- Validators for Batches 3-9 were each run on a clean `git worktree` checkout of the commit that completed that batch."]
open(f"{B10}/validation_report.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(f"{'PASS' if o else 'FAIL'}  {n}  {dt[:110]}" for n, o, dt in res)); sys.exit(0 if ok else 1)
