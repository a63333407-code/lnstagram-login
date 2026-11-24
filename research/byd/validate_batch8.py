#!/usr/bin/env python3
"""Batch 8 validator. Exit 0 = all checks pass. Writes batch8/validation_report.md and batch8/previous_batches_manifest.txt.
Usage: python3 validate_batch8.py [--base-commit 9c594da126d3e79fd74f576ebecd3072825ad7a4]"""
import csv, os, sys, re, json, subprocess, datetime, collections, tempfile, shutil, hashlib, glob

HERE = os.path.dirname(os.path.abspath(__file__)); U = f"{HERE}/catalog_union"; B6 = f"{HERE}/batch6"; B7 = f"{HERE}/batch7"; B8 = f"{HERE}/batch8"; REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = "9c594da126d3e79fd74f576ebecd3072825ad7a4"
if "--base-commit" in sys.argv: BASE = sys.argv[sys.argv.index("--base-commit") + 1]
rd = lambda p: list(csv.DictReader(open(p, encoding="utf-8", newline="")))
res = []
def chk(n, ok, d=""): res.append((n, bool(ok), str(d))); return ok
STATUSES = {"VERIFIED_OEM", "VERIFIED_LABEL", "CORROBORATED", "PAINT_SYSTEM_REFERENCE", "POSSIBLE", "CONFLICTED", "UNVERIFIED"}
REF_RE = re.compile(r"BYH[A-Z]-\d+|BYD\d{2,}[A-Z0-9]*")

D = rd(f"{B8}/discovered_codes.csv"); S = rd(f"{B8}/sources.csv"); C = rd(f"{B8}/conflicts.csv"); VR = rd(f"{B8}/verification_results.csv")
st = json.load(open(f"{B8}/stats_batch8.json", encoding="utf-8")); b6 = rd(f"{B6}/discovered_codes.csv"); b7 = rd(f"{B7}/discovered_codes.csv"); b7c = rd(f"{B7}/conflicts.csv"); plan = rd(f"{B7}/verification_sample_plan.csv")
sids = {s["source_id"] for s in S}

# --- Task 5 classification
chk("seven statuses defined (VERIFIED_OEM, VERIFIED_LABEL, CORROBORATED, PAINT_SYSTEM_REFERENCE, POSSIBLE, CONFLICTED, UNVERIFIED)", set(st["statuses_defined"]) == STATUSES)
chk("discovered_codes statuses within the seven; none VERIFIED_* or CORROBORATED", all(r["confidence_status"] in STATUSES and not r["confidence_status"].startswith("VERIFIED") and r["confidence_status"] != "CORROBORATED" for r in D), collections.Counter(r["confidence_status"] for r in D))
chk("every reference row has a BYH?-style identifier and status PAINT_SYSTEM_REFERENCE; typed as reference, never OEM", all(REF_RE.fullmatch(r["paint_code"].upper()) and r["confidence_status"] == "PAINT_SYSTEM_REFERENCE" and r["code_type"] == "PAINT_SYSTEM_REFERENCE_IDENTIFIER" and "not a vehicle paint code" in r["code_role"] for r in D))
allrefs = {("C", r["color_id"], r["paint_code"]) for r in b6 + b7 if r["link_scope"] == "COLOUR_RECORD" and REF_RE.fullmatch(r["paint_code"].upper())}
mrefs = {r["source_record_ids"] + "|" + r["paint_code"] for r in b6 if r["link_scope"] == "MODEL_LEVEL_LISTING" and REF_RE.fullmatch(r["paint_code"].upper())}
got_c = {("C", r["color_id"], r["paint_code"]) for r in D if r["link_scope"] == "COLOUR_RECORD"}
chk("every Batch 6/7 reference-style identifier on colour records is reclassified (none missed, none invented)", got_c == allrefs, f"{len(got_c)} vs {len(allrefs)}")
chk("model-level reference rows count matches Batch 6", sum(1 for r in D if r["link_scope"] == "MODEL_LEVEL_LISTING") == len(mrefs), len(mrefs))
chk("reclassified rows keep their Batch 7 status in a separate column (colour-record statuses not changed)", all(r["batch7_status"] in ("POSSIBLE", "CONFLICTED") for r in D))
chk("required fields non-empty (brand, code, type, source, evidence, status)", all(r[k] for r in D for k in ("brand", "paint_code", "code_type", "source_ids", "source_url", "evidence_description", "confidence_status")))
chk("every source id registered in sources.csv; all URLs https", all(s in sids for r in D for s in r["source_ids"].split(";")) and all(u.startswith("https://") for r in D for u in r["source_url"].split()))
b67 = {r["paint_code"] for r in b6 + b7}
chk("no code appears that is absent from Batch 6/7 (nothing invented)", all(r["paint_code"] in b67 for r in D))
# --- Task 3 targets
req = {"Seal 亚特兰蒂斯灰": any(r["international_model_name"] == "Seal" and r["original_chinese_color_name"] == "亚特兰蒂斯灰" for r in VR),
       "雪域白 x>=4": sum(1 for r in VR if r["original_chinese_color_name"] == "雪域白") >= 4, "Qin PLUS >=2": sum(1 for r in VR if r["priority_group"] == "Qin PLUS") >= 2,
       "Song PLUS >=2": sum(1 for r in VR if r["priority_group"] == "Song PLUS") >= 2, "Atto 3 >=2": sum(1 for r in VR if r["priority_group"].startswith("Atto 3")) >= 2}
chk("exactly 20 verification targets; priority list covers Seal 亚特兰蒂斯灰, 雪域白, Qin PLUS, Song PLUS, Atto 3", len(VR) == 20 and all(req.values()), req)
pk = {(r["international_model_name"], r["original_chinese_color_name"]): r for r in plan}
bad = [r["target_id"] for r in VR if (r["international_model_name"], r["original_chinese_color_name"]) not in pk or pk[(r["international_model_name"], r["original_chinese_color_name"])]["candidate_codes"] != r["candidate_codes"]
       or pk[(r["international_model_name"], r["original_chinese_color_name"])]["current_status"] != r["current_status"]]
chk("targets exist in the Batch 7 sample plan with identical candidate codes and status", not bad, bad)
chk("targets unique and ranked 1..20", [int(r["priority"]) for r in VR] == list(range(1, 21)) and len({(r["model_id"], r["original_chinese_color_name"]) for r in VR}) == 20)
chk("no verification claimed: all PENDING_FIELD_EVIDENCE, no verified code, no conflict resolved", all(r["verification_status"] == "PENDING_FIELD_EVIDENCE" and not r["verified_code"] and r["resolves_conflict"].startswith("NO") for r in VR))
cid = {r["conflict_id"] for r in C}
chk("every conflict id cited by a target exists in conflicts.csv", all(c in cid for r in VR for c in r["conflict_ids"].split(";") if c))
# --- conflicts preserved
old = {r["conflict_id"]: r for r in b7c}; new = {r["carried_from"]: r for r in C if r["carried_from"]}
chk("all Batch 7 conflicts carried (none dropped)", set(old) == set(new), f"{len(old)} vs {len(new)}")
chk("carried conflicts keep identical values/sources and stay OPEN", all(new[k]["values_in_conflict"] == old[k]["values_in_conflict"] and new[k]["sources_involved"] == old[k]["sources_involved"] and new[k]["batch8_status"].startswith("OPEN") for k in old))
chk("no conflict marked resolved", all("resolved" not in r["batch8_status"].lower() or r["batch8_status"].lower().startswith("open") for r in C) and all(r["resolution"].startswith("OPEN") for r in C))
chk("sources named in conflicts exist", all(s in sids for r in C for s in r["sources_involved"].split(";") if s), sorted({s for r in C for s in r["sources_involved"].split(";") if s} - sids)[:5])
# --- sources and safety
byid = {s["source_id"]: s for s in S}
chk("sources: Baslac terms recorded as NOT accepted; Denza/Yangwang sites recorded as not accessed", "NOT accepted" in byid["B8S01"]["title"] and "NOT ACCESSED" in byid["B8S06"]["access_result"].upper())
chk("sources: nothing marked usable as OEM verification", all(not s["usable_as_oem_verification"].upper().startswith("YES") for s in S))
chk("source ids unique", len(sids) == len(S))
text_files = [f"{B8}/{n}" for n in ("dealer_inquiry_zh.md", "dealer_inquiry_en.md", "baslac_manual_test_plan.md", "REPORT_batch8.md", "discovered_codes.csv", "sources.csv", "conflicts.csv", "verification_results.csv")]
chk("all required deliverables exist", all(os.path.exists(f) for f in text_files))
zh = open(f"{B8}/dealer_inquiry_zh.md", encoding="utf-8").read(); en = open(f"{B8}/dealer_inquiry_en.md", encoding="utf-8").read(); bt = open(f"{B8}/baslac_manual_test_plan.md", encoding="utf-8").read()
chk("Chinese script covers VIN, build record, paint-code field, written confirmation, screenshot, evidence checklist, own-VIN rule", all(k in zh for k in ("车架号", "出厂配置", "色号", "书面", "截图", "取证清单", "只用你自己车辆的 VIN")))
chk("English script covers build record, paint-code field, written confirmation, screenshot, evidence checklist, own-VIN rule", all(k in en for k in ("build record", "Paint-code field", "Written confirmation", "screenshot", "Evidence checklist", "your own vehicle's VIN")))
chk("both scripts carry the same verified hotline numbers (950858, 400-830-3666, 950859) and a VIN-free policy question", all(n in zh and n in en for n in ("950858", "400-830-3666", "950859")) and "3b" in zh and "3b" in en)
chk("hotline numbers appear in sources.csv evidence", all(any(n in s["notes"] for s in S) for n in ("950858", "400-830-3666", "950859")))
chk("Baslac plan: NOT TESTED, terms not accepted, no formula copying, manual test requirement and 8 questions", all(k in bt for k in ("NOT TESTED", "did **not** accept", "Do not copy", "Questions the manual test must answer")) and len(re.findall(r"^\| \d \|", bt, re.M)) == 8)
allbat = "\n".join(open(f, encoding="utf-8").read() for f in text_files if os.path.exists(f))
chk("privacy/secrets: no VIN-like 17-character strings, no tokens", not re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", re.sub(r"https?://\S+", "", allbat)) and "accessToken" not in allbat and "eyJ" not in allbat)
# --- previous batches: blob comparison + manifest
def git(*a, inp=None): return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, input=inp)
okc = git("cat-file", "-e", BASE + "^{commit}").returncode == 0; chk("Batch 7 base commit present", okc, BASE)
if okc:
    tree = [l.split("\t") for l in git("ls-tree", "-r", BASE, "--", "research").stdout.splitlines()]
    entries = [(t[1], t[0].split()[2]) for t in tree]
    work = [e for e in entries if os.path.exists(os.path.join(REPO, e[0]))]
    hashes = git("hash-object", "--stdin-paths", inp="\n".join(os.path.join(REPO, p) for p, _ in work) + "\n").stdout.split()
    mism = [p for (p, sha), h in zip(work, hashes) if sha != h]; missing = [p for p, _ in entries if not os.path.exists(os.path.join(REPO, p))]
    chk(f"Batches 1-7: all {len(entries)} files at {BASE[:8]} present and byte-identical (git blob comparison)", not mism and not missing and len(hashes) == len(work), f"mismatch={mism[:3]} missing={missing[:3]}")
    own = ("research/byd/batch8/", "research/byd/build_batch8.py", "research/byd/build_batch8_report.py", "research/byd/validate_batch8.py")
    un = [x for x in git("ls-files", "--others", "--exclude-standard", "research").stdout.split() if not x.startswith(own)]
    chk("no stray new files outside batch8 and its scripts", not un, un[:3])
    chk("application files untouched (non-research diff vs base)", git("diff", "--name-only", BASE, "--", ".", ":(exclude)research").stdout.strip() == "")
    grp = collections.OrderedDict()
    for p, sha in entries:
        parts = p.split("/"); key = parts[2] if len(parts) > 3 and parts[2] in ("batch1", "batch4", "batch5", "batch6", "batch7", "catalog_union", "raw", "raw_b4") else "batch2-3 top-level files"
        grp.setdefault(key, []).append(f"{p} {sha}")
    lines = [f"# SHA-256 digests of '<path> <git blob id>' lists per area at {BASE} (verified identical to the working tree)"]
    for k, v in grp.items(): lines.append(f"{hashlib.sha256(chr(10).join(sorted(v)).encode()).hexdigest()}  {k}  ({len(v)} files)")
    open(f"{B8}/previous_batches_manifest.txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")
# --- previous validators on clean checkouts
RUN = [("b39bff8", "validate_batch3.py", "Batch 3"), ("cb78fcb", "validate_batch4.py", "Batch 4"), ("43ec2cd", "validate_batch5.py", "Batch 5"), ("f3b8f83", "validate_batch6.py", "Batch 6"), ("9c594da", "validate_batch7.py", "Batch 7")]
tmp = tempfile.mkdtemp(prefix="b8_wt_")
try:
    for commit, script, label in RUN:
        d = f"{tmp}/{commit}"; g = git("worktree", "add", "--detach", d, commit)
        r = subprocess.run([sys.executable, "-I", f"{d}/research/byd/{script}"], capture_output=True, text=True, cwd=d, timeout=900) if g.returncode == 0 else None
        chk(f"{label} validator ({script}) passes on a clean checkout of {commit}", r is not None and r.returncode == 0, "" if r is None else f"exit {r.returncode}")
        git("worktree", "remove", "--force", d)
finally:
    shutil.rmtree(tmp, ignore_errors=True); git("worktree", "prune")

ok = all(r[1] for r in res); passed = sum(1 for r in res if r[1])
md = ["# Batch 8 validation report", "", f"Run: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · `research/byd/validate_batch8.py` · base commit `{BASE}`", "",
      f"**Result: {'ALL CHECKS PASSED' if ok else 'FAILURES PRESENT'}** ({passed}/{len(res)})", "", "| # | Check | Result | Detail |", "|---|---|---|---|"]
for i, (n, o, dt) in enumerate(res, 1): md.append(f"| {i} | {n} | {'PASS' if o else 'FAIL'} | {dt.replace('|', '/')[:180]} |")
md += ["", "## Row counts", ""] + [f"- {n}: {len(v)}" for n, v in (("discovered_codes.csv (paint-system-reference rows)", D), ("sources.csv", S), ("conflicts.csv", C), ("verification_results.csv", VR))]
md += ["", "## Notes", "", "- Previous-batch integrity is proved by comparing every research file's git blob id at the Batch 7 commit with the working tree; per-area digests are in `previous_batches_manifest.txt`.",
       "- Each earlier validator (Batches 3-7) was run on a clean `git worktree` checkout of the commit that completed that batch.",
       "- Nothing here verifies a paint code: all verification rows are pending field evidence."]
open(f"{B8}/validation_report.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(f"{'PASS' if o else 'FAIL'}  {n}  {dt[:110]}" for n, o, dt in res)); sys.exit(0 if ok else 1)
