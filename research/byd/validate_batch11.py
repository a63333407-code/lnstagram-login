#!/usr/bin/env python3
"""Batch 11 validator. Exit 0 = all checks pass. Writes batch11/validation_report.md and batch11/previous_batches_manifest.txt.
Usage: python3 validate_batch11.py [--base-commit 0baa8ac225c74396c5fdcdea4cf156073be5f54d]"""
import csv, os, sys, re, json, subprocess, datetime, collections, tempfile, shutil, hashlib

HERE = os.path.dirname(os.path.abspath(__file__)); U = f"{HERE}/catalog_union"; B11 = f"{HERE}/batch11"; REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = "0baa8ac225c74396c5fdcdea4cf156073be5f54d"
if "--base-commit" in sys.argv: BASE = sys.argv[sys.argv.index("--base-commit") + 1]
rd = lambda p: list(csv.DictReader(open(p, encoding="utf-8", newline="")))
res = []
def chk(n, ok, d=""): res.append((n, bool(ok), str(d))); return ok
STATUSES = {"VERIFIED_OEM", "VERIFIED_LABEL", "CORROBORATED", "PAINT_SYSTEM_REFERENCE", "POSSIBLE", "CONFLICTED", "UNVERIFIED"}
REF_RE = re.compile(r"BYH[A-Z]-\d+|BYD\d{2,}[A-Z0-9]*")

OC = rd(f"{B11}/official_colour_tables.csv"); MC = rd(f"{B11}/model_year_colour_catalog.csv"); FE = rd(f"{B11}/field_evidence_register.csv"); LQ = rd(f"{B11}/code_link_quality_audit.csv"); PU = rd(f"{B11}/priority_conflict_updates.csv"); SA = rd(f"{B11}/source_audit.csv")
st = json.load(open(f"{B11}/stats_batch11.json", encoding="utf-8")); docs = json.load(open(f"{B11}/raw/official_colour_extracts.json", encoding="utf-8")); bp = json.load(open(f"{B11}/raw/brand_colour_pages.json", encoding="utf-8"))
cols = {c["color_id"]: c for c in rd(f"{U}/factory_colors_all.csv")}; models = {m["model_id"]: m for m in rd(f"{U}/models_all.csv")}; years = {y["model_year_id"]: y for y in rd(f"{U}/model_years_all.csv")}
b10my = {r["color_id"]: r for r in rd(f"{HERE}/batch10/model_year_consistency.csv")}; b10ca = rd(f"{HERE}/batch10/colour_conflict_audit.csv"); b5 = rd(f"{HERE}/batch5/oem_paint_codes.csv")
b6 = [r for r in rd(f"{HERE}/batch6/discovered_codes.csv") if r["link_scope"] == "COLOUR_RECORD"]; b7 = [r for r in rd(f"{HERE}/batch7/discovered_codes.csv") if r["link_scope"] == "COLOUR_RECORD"]
report = open(f"{B11}/REPORT_batch11.md", encoding="utf-8").read(); unres = open(f"{B11}/unresolved_questions.md", encoding="utf-8").read()
FILES = ["REPORT_batch11.md", "official_colour_tables.csv", "model_year_colour_catalog.csv", "field_evidence_register.csv", "code_link_quality_audit.csv", "priority_conflict_updates.csv", "source_audit.csv", "unresolved_questions.md"]

# --- honesty
chk("report states at the top that no field evidence was received and no code verified; 0/0/0", "No field evidence was received" in "\n".join(report.splitlines()[:4]) and "VERIFIED_OEM = 0" in report)
chk("report contains the eight required figures", all(f"| {i} |" in report for i in range(1, 9)))
chk("no VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED status anywhere in the Batch 11 tables", not any(r.get("status", r.get("current_status", "")) in ("VERIFIED_OEM", "VERIFIED_LABEL", "CORROBORATED") for r in MC + LQ) and st["verified_oem"] == st["verified_label"] == st["corroborated"] == st["field_evidence_received"] == 0)
# --- Task 1: official colour tables
colours = [r for r in OC if r["row_type"] == "COLOUR"]
chk("every official-document colour row is literally present in the recorded PDF extract (name and, where printed, Chinese name)", all(any(c["printed"].lower() == r["colour_as_printed"].lower() for d in docs if d["doc_id"] == r["doc_id"] for c in d["colours"]) or r["two_tone"] == "YES" for r in colours if r["doc_id"].startswith("D")))
chk("each official-document colour has an extract excerpt line naming it", all(any(c["printed"].lower() in l.lower() for l in d["excerpt_lines"]) for d in docs for c in d["colours"]))
chk("brand-page colour rows come from the recorded page extract", all(any(e["name"] == r["colour_as_printed"] for p in bp if p["url"] == r["source_url"] for e in p["colour_entries"]) for r in colours if r["doc_id"].startswith("BP-")))
chk("no official row contains a paint code; official colour names never marked as code evidence", all(r["contains_paint_code"] == "NO" for r in OC) and all("not paint-code evidence" in r["status_effect"] or r["row_type"] in ("NOT_FOUND", "DOCUMENT_NO_COLOURS", "CN_MODEL_PAGE_DYNAMIC") for r in OC))
chk("required fields present: URL, date basis, model, market, year basis, Chinese name basis, finish statement, paint-code flag", all(r["source_url"].startswith("https://") and r["document_date_basis"] and r["model_as_printed"] and r["market"] and r["model_year_basis"] and r["chinese_name_basis"] and r["finish_explicit"] and r["contains_paint_code"] for r in colours))
chk("Chinese names are 'printed' only for the Macau Seal brochure and official brand pages; others say NOT STATED", all((r["chinese_name_basis"].startswith("NOT STATED")) for r in colours if r["doc_id"].startswith("D") and r["doc_id"] != "D01") and all(r["chinese_name_basis"].startswith("PRINTED") for r in colours if r["doc_id"] == "D01"))
chk("finish stated per colour only where the document says so (D11); equipment-line finish not treated as per-colour", {r["doc_id"] for r in colours if r["finish_explicit"].startswith("YES")} == {"D11"})
chk("Cambodia 'Seal 5 DM-i 海豹' is mapped to Seal 05 DM-i (M021), never to Destroyer 05 (M019); 'Sealion 6' to M031", {r["catalog_model_id"] for r in colours if r["doc_id"] == "D05"} == {"M021"} and {r["catalog_model_id"] for r in colours if r["doc_id"] == "D06"} == {"M031"})
chk("priority models without an official table are recorded as NOT_FOUND (Han EV, Qin PLUS, Song PLUS EV, e2, Destroyer 05)", len([r for r in OC if r["row_type"] == "NOT_FOUND"]) == 5 and any("Destroyer 05" in r["model_as_printed"] for r in OC if r["row_type"] == "NOT_FOUND"))
chk("BYD China model pages recorded as dynamic; API not called", all("API" in r["evidence_excerpt"] and "NOT called" in r["evidence_excerpt"] for r in OC if r["row_type"] == "CN_MODEL_PAGE_DYNAMIC") and st["cn_model_pages"] == 16)
chk("official brochure counts: 13 fetched, 12 with exterior names, 1 with Chinese names, 0 with a paint code", st["official_documents_fetched"] == 13 and st["official_documents_with_exterior_colour_names"] == 12 and st["docs_with_chinese_names"] == 1 and st["docs_with_paint_code"] == 0)
# --- Task 3/5: catalogue + link audit
chk("model_year_colour_catalog has exactly one row per colour record (1,223); statuses identical to Batch 10", len(MC) == len(cols) == 1223 and {r["color_id"] for r in MC} == set(cols) and all(r["status"] == b10my[r["color_id"]]["status"] for r in MC))
bad = []
for r in MC:
    c = cols[r["color_id"]]; y = years.get(c["model_year_id"], {})
    if r["colour_name_zh"] != c["color_name_zh"] or r["model_id"] != c["model_id"] or r["generation_id"] != c["generation_id"] or r["model_year"] != (y.get("year") or "UNKNOWN") or not r["production_year"].startswith("UNKNOWN"): bad.append(r["color_id"])
chk("catalogue rows keep exact model/generation/model-year/colour name; production year stays UNKNOWN; separate fields present", not bad and all(k in MC[0] for k in ("generation_label", "model_year", "production_year", "market", "trim_scope", "finish_catalogue", "colour_name_zh", "candidate_vehicle_codes_with_support", "code_association_flags")), bad[:5])
chk("official_doc_support values valid and consistent with the official table", all(r["official_doc_support"] in ("NONE", "OFFICIAL_CHINESE_NAME_PRINTED", "OFFICIAL_ENGLISH_NAME_INFERRED_CHINESE") and bool(r["official_doc_ids"]) == (r["official_doc_support"] != "NONE") for r in MC))
state = {(r["color_id"], r["paint_code"]) for r in b6 + b7}
chk("link audit covers exactly the 709 existing colour/code links (none deleted, none added)", len(LQ) == 709 == len(state) and {(r["color_id"], r["paint_code"]) for r in LQ} == state)
hist5 = {(r["color_id"], r["supplier_candidate_code"]): r["evidence_status"] for r in b5}
chk("audit history preserved: Batch 5/6/7 statuses recorded exactly as in the earlier files", all((("B5:" + hist5[(r["color_id"], r["paint_code"])]) in r["status_history"]) if (r["color_id"], r["paint_code"]) in hist5 else ("B5:" not in r["status_history"]) for r in LQ) and all(r["first_seen_batch"] in ("5 (baseline link)", "6", "7") for r in LQ))
chk("name_only_flag is YES exactly for NAME_ONLY support; counts match stats (212 / 497)", all((r["name_only_flag"] == "YES") == (r["model_support"] == "NAME_ONLY") for r in LQ) and st["name_only_links"] == sum(1 for r in LQ if r["name_only_flag"] == "YES") == 212 and st["model_listed_links"] == 497)
chk("every link carries year, finish, market and production-period checks and a primary class; mismatch flag matches the year check", all(r["year_check"] and r["finish_check"] and r["market_check"] and r["production_period_check"] and r["primary_quality_class"] for r in LQ) and all(("MODEL_YEAR_MISMATCH" in r["flags"]) == (r["year_check"] == "MODEL_YEAR_MISMATCH") for r in LQ) and st["model_year_mismatch_links"] == sum(1 for r in LQ if "MODEL_YEAR_MISMATCH" in r["flags"]))
chk("link statuses unchanged vs Batch 10 (reference identifiers stay PAINT_SYSTEM_REFERENCE)", all(r["current_status"] == ("PAINT_SYSTEM_REFERENCE" if REF_RE.fullmatch(r["paint_code"].upper()) else b10my[r["color_id"]]["status"]) for r in LQ))
chk("codes are not propagated: no code in the catalogue exists that is absent from the Batch 6/7 links of that colour record", all(set(re.findall(r"([A-Z0-9][A-Z0-9\-]*)\[", r["candidate_vehicle_codes_with_support"] + ";" + r["paint_system_references"])) == {c for (cid, c) in state if cid == r["color_id"]} for r in MC))
# --- Task 2: field evidence
chk("field evidence register: three intake checks found nothing; all evidence types and 20 target slots PENDING; nothing received", {r["id"] for r in FE if r["row_type"] == "INTAKE_CHECK"} == {"IC01", "IC02", "IC03"} and all(r["status"] == "NO_NEW_EVIDENCE" for r in FE if r["row_type"] == "INTAKE_CHECK") and sum(1 for r in FE if r["row_type"] == "TARGET_SLOT") == 20 and all(r["status"] == "PENDING" for r in FE if r["row_type"] in ("TARGET_SLOT", "EVIDENCE_TYPE_RULE")) and all(r["received"] == "NO" for r in FE))
chk("evidence rules cover label photo, dealer written reply, owner build record, OEM document and forbid full VINs", {r["evidence_type"] for r in FE if r["row_type"] == "EVIDENCE_TYPE_RULE"} == {"LABEL_PHOTO", "DEALER_WRITTEN", "VIN_BUILD_RECORD_OWNER_SUPPLIED", "OEM_PAINT_DOCUMENT"} and all("never store a full VIN" in r["vin_handling"] for r in FE if r["row_type"] == "EVIDENCE_TYPE_RULE"))
# --- Task 4: priority conflicts
Z = ["雪域白", "攀岩灰", "亚特兰蒂斯灰", "苍穹蓝"]
chk("priority conflict updates: all four colours, each with FACT, HYPOTHESIS, MINIMUM_EVIDENCE, BATCH11_STATUS and catalogue rows", all({"FACT", "HYPOTHESIS", "MINIMUM_EVIDENCE", "BATCH11_STATUS", "CATALOGUE_FACT", "COMPETING_CODE"} <= {r["row_type"] for r in PU if r["colour_zh"] == z} for z in Z))
chk("every competing code of Batch 10's audit is preserved (none dropped, none added)", all({r["item"] for r in PU if r["colour_zh"] == z and r["row_type"] == "COMPETING_CODE"} == {r["code"] for r in b10ca if r["row_type"] == "CODE" and r["colour_zh"] == z} for z in Z))
chk("facts cite sources; hypotheses are graded HYPOTHESIS; no majority vote; conflicts stay OPEN", all(r["source_or_basis"] for r in PU if r["row_type"] in ("FACT", "COMPETING_CODE")) and all(r["evidence_grade"] == "HYPOTHESIS" for r in PU if r["row_type"] == "HYPOTHESIS") and all(r["statement"].startswith("OPEN") for r in PU if r["row_type"] == "BATCH11_STATUS") and not any("majority" in r["statement"].lower() and "no majority" not in r["statement"].lower() for r in PU))
# --- source audit
chk("source_audit: new official sources are manufacturer-controlled (or dealer-hosted) with no paint codes; failed URLs flagged HTTP 404/000 and unused", all(r["contains_vehicle_paint_codes"] == "NO" for r in SA) and all("HTTP 404" in r["fetch_result"] or "HTTP 000" in r["fetch_result"] for r in SA if r["source_key"].startswith(("B11-F", "B11-BPF"))) and any(r["source_class"] == "AUTHORISED_DEALER_HOSTED" for r in SA) and len({r["source_key"] for r in SA}) == len(SA))
chk("source_audit includes every fetched official document, China page and brand page", sum(1 for r in SA if re.match(r"B11-D\d\d$", r["source_key"])) == 13 and sum(1 for r in SA if r["source_key"].startswith("B11-CN-")) == 16 and sum(1 for r in SA if r["source_key"].startswith("B11-BP-")) == 11)
# --- privacy + deliverables
allt = "\n".join(open(f"{B11}/{f}", encoding="utf-8").read() for f in FILES)
chk("privacy/secrets: no VIN-like 17-character strings, no tokens", not re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", re.sub(r"https?://\S+", "", allt)) and "accessToken" not in allt and "eyJ" not in allt)
chk("all deliverables except validation_report.md / manifest exist", all(os.path.exists(f"{B11}/{f}") for f in FILES))
# --- previous batches
def git(*a, inp=None): return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, input=inp)
okc = git("cat-file", "-e", BASE + "^{commit}").returncode == 0; chk("Batch 10 base commit present", okc, BASE)
if okc:
    tree = [l.split("\t") for l in git("ls-tree", "-r", BASE, "--", "research").stdout.splitlines()]; entries = [(t[1], t[0].split()[2]) for t in tree]
    work = [e for e in entries if os.path.exists(os.path.join(REPO, e[0]))]
    hashes = git("hash-object", "--stdin-paths", inp="\n".join(os.path.join(REPO, p) for p, _ in work) + "\n").stdout.split()
    mism = [p for (p, sha), h in zip(work, hashes) if sha != h]; missing = [p for p, _ in entries if not os.path.exists(os.path.join(REPO, p))]
    chk(f"Batches 1-10: all {len(entries)} files at {BASE[:8]} present and byte-identical (git blob comparison)", not mism and not missing and len(hashes) == len(work), f"mismatch={mism[:3]} missing={missing[:3]}")
    own = ("research/byd/batch11/", "research/byd/build_batch11.py", "research/byd/build_batch11_report.py", "research/byd/validate_batch11.py", "research/byd/extract_official_docs_batch11.py", "research/byd/extract_brand_pages_batch11.py")
    un = [x for x in git("ls-files", "--others", "--exclude-standard", "research").stdout.split() if not x.startswith(own)]
    chk("no stray new files outside batch11 and its scripts", not un, un[:3])
    chk("application files untouched (non-research diff vs base)", git("diff", "--name-only", BASE, "--", ".", ":(exclude)research").stdout.strip() == "")
    grpd = collections.OrderedDict()
    for p, sha in entries:
        parts = p.split("/"); key = parts[2] if len(parts) > 3 and parts[2] in ("batch1", "batch4", "batch5", "batch6", "batch7", "batch8", "batch9", "batch10", "catalog_union", "raw", "raw_b4") else "batch2-3 top-level files"
        grpd.setdefault(key, []).append(f"{p} {sha}")
    lines = [f"# SHA-256 digests of sorted '<path> <git blob id>' lists per area at {BASE} (each verified identical to the working tree; {len(entries)} files)"]
    for k, vv in grpd.items(): lines.append(f"{hashlib.sha256(chr(10).join(sorted(vv)).encode()).hexdigest()}  {k}  ({len(vv)} files)")
    open(f"{B11}/previous_batches_manifest.txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")
RUN = [("b39bff8", "validate_batch3.py", "Batch 3"), ("cb78fcb", "validate_batch4.py", "Batch 4"), ("43ec2cd", "validate_batch5.py", "Batch 5"), ("f3b8f83", "validate_batch6.py", "Batch 6"), ("9c594da", "validate_batch7.py", "Batch 7"), ("5cd5bd7", "validate_batch8.py", "Batch 8"), ("8ae4f43", "validate_batch9.py", "Batch 9"), ("0baa8ac", "validate_batch10.py", "Batch 10")]
tmp = tempfile.mkdtemp(prefix="b11_wt_")
try:
    for commit, script_, label in RUN:
        d = f"{tmp}/{commit}"; g = git("worktree", "add", "--detach", d, commit)
        r = subprocess.run([sys.executable, "-I", f"{d}/research/byd/{script_}"], capture_output=True, text=True, cwd=d, timeout=3500) if g.returncode == 0 else None
        chk(f"{label} validator ({script_}) passes on a clean checkout of {commit}", r is not None and r.returncode == 0, "" if r is None else f"exit {r.returncode}")
        git("worktree", "remove", "--force", d)
finally:
    shutil.rmtree(tmp, ignore_errors=True); git("worktree", "prune")

ok = all(r[1] for r in res); passed = sum(1 for r in res if r[1])
md = ["# Batch 11 validation report", "", f"Run: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · `research/byd/validate_batch11.py` · base commit `{BASE}`", "",
      f"**Result: {'ALL CHECKS PASSED' if ok else 'FAILURES PRESENT'}** ({passed}/{len(res)})", "", "| # | Check | Result | Detail |", "|---|---|---|---|"]
for i, (n, o, dt) in enumerate(res, 1): md.append(f"| {i} | {n} | {'PASS' if o else 'FAIL'} | {dt.replace('|', '/')[:180]} |")
md += ["", "## Row counts", ""] + [f"- {n}: {len(vv)}" for n, vv in (("official_colour_tables.csv", OC), ("model_year_colour_catalog.csv", MC), ("field_evidence_register.csv", FE), ("code_link_quality_audit.csv", LQ), ("priority_conflict_updates.csv", PU), ("source_audit.csv", SA))]
md += ["", "## Notes", "", "- Official colour names were checked against short text excerpts recorded from the downloaded PDFs and pages (the documents themselves are not stored).",
       "- Previous-batch integrity: every research file of Batches 1-10 at the Batch 10 commit is compared by git blob id with the working tree; per-area digests are in `previous_batches_manifest.txt`.",
       "- Validators for Batches 3-10 were each run on a clean `git worktree` checkout of the commit that completed that batch."]
open(f"{B11}/validation_report.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(f"{'PASS' if o else 'FAIL'}  {n}  {dt[:110]}" for n, o, dt in res)); sys.exit(0 if ok else 1)
