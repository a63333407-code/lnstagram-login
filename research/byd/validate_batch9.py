#!/usr/bin/env python3
"""Batch 9 validator. Exit 0 = all checks pass. Writes batch9/validation_report.md and batch9/previous_batches_manifest.txt.
Usage: python3 validate_batch9.py [--base-commit 5cd5bd71309c8e1f2e137b49fdfe6b8180348151]"""
import csv, os, sys, re, json, subprocess, datetime, collections, tempfile, shutil, hashlib

HERE = os.path.dirname(os.path.abspath(__file__)); U = f"{HERE}/catalog_union"; B7 = f"{HERE}/batch7"; B8 = f"{HERE}/batch8"; B9 = f"{HERE}/batch9"; REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = "5cd5bd71309c8e1f2e137b49fdfe6b8180348151"
if "--base-commit" in sys.argv: BASE = sys.argv[sys.argv.index("--base-commit") + 1]
rd = lambda p: list(csv.DictReader(open(p, encoding="utf-8", newline="")))
res = []
def chk(n, ok, d=""): res.append((n, bool(ok), str(d))); return ok
STATUSES = {"VERIFIED_OEM", "VERIFIED_LABEL", "CORROBORATED", "PAINT_SYSTEM_REFERENCE", "POSSIBLE", "CONFLICTED", "UNVERIFIED"}

DC = rd(f"{B9}/dealer_contact_results.csv"); CA = rd(f"{B9}/field_verification_cases.csv"); ER = rd(f"{B9}/evidence_register.csv"); CP = rd(f"{B9}/conflict_priority.csv")
st = json.load(open(f"{B9}/stats_batch9.json", encoding="utf-8")); b7c = rd(f"{B7}/conflicts.csv"); b8v = rd(f"{B8}/verification_results.csv")
cols = {c["color_id"]: c for c in rd(f"{U}/factory_colors_all.csv")}
report = open(f"{B9}/REPORT_batch9.md", encoding="utf-8").read(); unres = open(f"{B9}/unresolved_questions.md", encoding="utf-8").read(); script = open(f"{B9}/call_script_zh.md", encoding="utf-8").read()
FILES = ["REPORT_batch9.md", "dealer_contact_results.csv", "field_verification_cases.csv", "evidence_register.csv", "conflict_priority.csv", "unresolved_questions.md"]

# --- honesty of the report
first = "\n".join(report.splitlines()[:6])
chk("report states plainly at the top that no genuine OEM paint code was verified and no field evidence was obtained", "No genuine OEM paint code was verified" in first and "No field evidence was obtained" in first)
chk("report separates the five required categories", all(k in report for k in ("## 1. What was actually verified", "## 2. What was only reported verbally", "## 3. What remains untested", "## 4. What requires the user's or a vehicle owner's participation", "## 5. What cannot be stored")))
# --- Task 1: contact workflow
chk("contact results: 5 channels x 5 questions, identical question set per channel", len(DC) == 25 and len({r["contact_id"] for r in DC}) == 5 and all(len({r["question_zh"] for r in DC if r["contact_id"] == c}) == 5 for c in {r["contact_id"] for r in DC}))
chk("no call is claimed: every row NOT_CALLED / UNANSWERED with empty date, caller, operator, verbatim, reference", all(r["call_status"] == "NOT_CALLED" and r["answer_category"] == "UNANSWERED" and not any(r[k] for k in ("call_datetime", "caller_role", "operator_name_or_id", "answer_verbatim", "reference_number", "written_follow_up_offered")) for r in DC))
req = {r["contact_id"]: r["phone_number"] for r in DC if r["channel_requirement"] == "REQUIRED"}
chk("required channels are exactly BYD 950858, 400-830-3666, Fangchengbao 950859", set(req.values()) == {"950858", "400-830-3666", "950859"} and len(req) == 3, req)
chk("every contact number has provenance and an evidence-register entry", all(r["number_provenance"] and r["evidence_ref"] in {e["evidence_id"] for e in ER} for r in DC))
chk("verbal answers verify nothing (status_effect says so)", all("verifies no paint code" in r["status_effect"] for r in DC))
chk("Chinese call script contains the five questions and says no call was made", all(k in script for k in ("原厂车漆色号", "出厂/生产档案", "书面形式", "截图或打印", "车型、生产年份或品牌")) and "未拨打" in script and "UNANSWERED" in script)
# --- Task 2: cases
c = [r for r in CA if r["row_type"] == "CASE"]; s = [r for r in CA if r["row_type"] == "STEP"]
chk("exactly two cases T01 and T02 with ten steps each", sorted(r["target_id"] for r in c) == ["T01", "T02"] and collections.Counter(r["target_id"] for r in s) == {"T01": 10, "T02": 10})
chk("cases PENDING; consent NOT_OBTAINED; all steps NOT_PERFORMED; no outcome, no document", all(r["case_status"] == "PENDING" and r["owner_consent"] == "NOT_OBTAINED" and not r["outcome_code"] and not r["evidence_file_ref_private"] and not r["evidence_type"] for r in c) and all(r["step_status"] == "NOT_PERFORMED" for r in s))
chk("VIN fields empty (hash/prefix to be filled only by the owner's own record); no full VIN anywhere", all(not r["vin_sha256_hex"] and not r["vin_wmi_vds_first_9"] for r in c))
v = {r["target_id"]: r for r in b8v}
chk("case data match Batch 8 targets (model, colour, candidate codes, status); status unchanged", all(r["candidate_codes"] == v[r["target_id"]]["candidate_codes"] and r["colour_zh"] == v[r["target_id"]]["original_chinese_color_name"] and r["catalog_status"] == v[r["target_id"]]["current_status"] == "CONFLICTED" and r["resulting_status"].startswith("(unchanged)") for r in c))
chk("T01 is Seal 亚特兰蒂斯灰 and T02 is Han EV 雪域白", any(r["target_id"] == "T01" and r["model"] == "Seal" and r["colour_zh"] == "亚特兰蒂斯灰" for r in c) and any(r["target_id"] == "T02" and r["model"] == "Han EV" and r["colour_zh"] == "雪域白" for r in c))
chk("workflow demands owner consent, own VIN only, hash + 9-char prefix, exact reason when not provided", all(k in " ".join(r["step_description"] for r in s) for k in ("written consent", "own", "SHA-256", "first 9", "exact reason")))
chk("outcome vocabulary covers refusal, no-field, verbal-only, formula-only, owner presence", all(k in c[0]["allowed_outcomes"] for k in ("DOC_CODE_PROVIDED", "VERBAL_ONLY", "REFUSED_POLICY", "SYSTEM_HAS_NO_FIELD", "DOC_FORMULA_NUMBER_ONLY", "REQUIRES_OWNER_PRESENCE")))
# --- Task 3: classification discipline
chk("evidence register: nothing supports a status upgrade", all(r["supports_status_upgrade"] == "NO" for r in ER))
chk("pending field evidence items are NOT_OBTAINED (calls, T01, T02, Baslac test)", {r["evidence_id"] for r in ER if r["verification_level"] == "NOT_OBTAINED"} == {"EP01", "EP02", "EP03", "EP04"})
chk("licensing restriction recorded (Baslac formulas cannot be stored)", any(r["category"] == "LICENSING_RESTRICTION" and "CANNOT be stored" in r["classification_effect"] for r in ER))
chk("no status other than the seven appears in any Batch 9 table", all(set(re.findall(r"\b(VERIFIED_[A-Z]+|CORROBORATED|PAINT_SYSTEM_REFERENCE|POSSIBLE|CONFLICTED|UNVERIFIED)\b", " ".join(r.values()))) <= STATUSES for r in CP + ER))
chk("no VERIFIED_OEM / VERIFIED_LABEL / CORROBORATED assigned to any record", not any(r.get("colour_status", "") in ("VERIFIED_OEM", "VERIFIED_LABEL", "CORROBORATED") or r.get("tier") in ("VERIFIED_OEM",) for r in CP) and st["verified_total"] == 0)
# --- Task 5: priority table
ids7 = [r["conflict_id"] for r in b7c]; grp = [r for r in CP if r["row_type"] == "GROUP"]; cross = [r for r in CP if r["row_type"] == "CROSS_CUTTING"]; rec = [r for r in CP if r["row_type"] == "COLOUR_RECORD"]
chk("all 39 carried conflict rows appear exactly once (29 scored groups + 10 cross-cutting)", sorted(r["conflict_id"] for r in grp + cross) == sorted(ids7) and len(grp) == 29 and len(cross) == 10, f"{len(grp)}+{len(cross)}")
b7_cids = {c_ for r in b7c if r["conflict_type"].startswith("SOURCES_DISAGREE") for c_ in r["color_id"].split(";") if c_}
chk("all 107 conflicted colour records mapped exactly once, with tier of their group", {r["color_id"] for r in rec} == b7_cids and len(rec) == 107 == len(b7_cids) and all(r["tier"] in ("A", "B", "C") for r in rec))
gt = {r["conflict_id"]: r["tier"] for r in grp}
chk("record tiers equal their group's tier; colour names unchanged vs catalog", all(gt[r["conflict_id"]] == r["tier"] and cols[r["color_id"]]["color_name_zh"] == r["colour_zh"] for r in rec))
bad = [r["priority_id"] for r in grp if int(r["score"]) != 2 * int(r["popularity_proxy"]) + int(r["competition"]) + int(r["matte_gloss"]) + int(r["route_plausibility"]) + int(r["genuine_disagreement"]) + int(r["size"])]
chk("score equals the documented formula for every group", not bad, bad[:5])
chk("tier thresholds consistent (A>=14, B 11-13, C<=10) and priority ids ranked by score", all((r["tier"] == "A") == (int(r["score"]) >= 14) and (r["tier"] == "B") == (11 <= int(r["score"]) < 14) for r in grp) and [int(r["score"]) for r in sorted(grp, key=lambda r: r["priority_id"])] == sorted((int(r["score"]) for r in grp), reverse=True))
chk("no conflict resolved; none decided by majority vote or site count", all(r["status_effect"].lower().startswith("none") for r in CP) and all("majority" not in r["rationale"].lower() for r in CP))
def _codes(r7):
    if r7["conflict_type"].startswith("SOURCES_DISAGREE"): return {x for v in json.loads(r7["values_in_conflict"]).values() for x in v}
    return {x.strip() for x in r7["values_in_conflict"].split("/") if x.strip()}
b7map = {r["conflict_id"]: r for r in b7c}
chk("each scored group's candidate codes equal the Batch 7 conflict's codes (nothing added, nothing dropped)", all(set(r["candidate_codes"].split(" | ")) == _codes(b7map[r["conflict_id"]]) for r in grp))
# --- Task 6 / privacy
allt = "\n".join(open(f"{B9}/{f}", encoding="utf-8").read() for f in FILES + ["call_script_zh.md"])
chk("privacy/secrets: no VIN-like 17-character strings, no tokens", not re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", re.sub(r"https?://\S+", "", allt)) and "accessToken" not in allt and "eyJ" not in allt)
chk("other brands: Linghui and unreachable Denza page recorded as not found/not reachable; no claim of inspecting inaccessible sources", "Linghui" in unres and "NOT FOUND" in unres and "not reachable" in unres and "NOT ACCESSED" in " ".join(r["verification_level"] for r in ER if r["evidence_id"] == "EV04"))
chk("all deliverables except validation_report.md / manifest exist", all(os.path.exists(f"{B9}/{f}") for f in FILES))
# --- previous batches
def git(*a, inp=None): return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, input=inp)
okc = git("cat-file", "-e", BASE + "^{commit}").returncode == 0; chk("Batch 8 base commit present", okc, BASE)
if okc:
    tree = [l.split("\t") for l in git("ls-tree", "-r", BASE, "--", "research").stdout.splitlines()]; entries = [(t[1], t[0].split()[2]) for t in tree]
    work = [e for e in entries if os.path.exists(os.path.join(REPO, e[0]))]
    hashes = git("hash-object", "--stdin-paths", inp="\n".join(os.path.join(REPO, p) for p, _ in work) + "\n").stdout.split()
    mism = [p for (p, sha), h in zip(work, hashes) if sha != h]; missing = [p for p, _ in entries if not os.path.exists(os.path.join(REPO, p))]
    chk(f"Batches 1-8: all {len(entries)} files at {BASE[:8]} present and byte-identical (git blob comparison)", not mism and not missing and len(hashes) == len(work), f"mismatch={mism[:3]} missing={missing[:3]}")
    own = ("research/byd/batch9/", "research/byd/build_batch9.py", "research/byd/build_batch9_report.py", "research/byd/validate_batch9.py")
    un = [x for x in git("ls-files", "--others", "--exclude-standard", "research").stdout.split() if not x.startswith(own)]
    chk("no stray new files outside batch9 and its scripts", not un, un[:3])
    chk("application files untouched (non-research diff vs base)", git("diff", "--name-only", BASE, "--", ".", ":(exclude)research").stdout.strip() == "")
    grpd = collections.OrderedDict()
    for p, sha in entries:
        parts = p.split("/"); key = parts[2] if len(parts) > 3 and parts[2] in ("batch1", "batch4", "batch5", "batch6", "batch7", "batch8", "catalog_union", "raw", "raw_b4") else "batch2-3 top-level files"
        grpd.setdefault(key, []).append(f"{p} {sha}")
    lines = [f"# SHA-256 digests of sorted '<path> <git blob id>' lists per area at {BASE} (each verified identical to the working tree; {len(entries)} files)"]
    for k, vv in grpd.items(): lines.append(f"{hashlib.sha256(chr(10).join(sorted(vv)).encode()).hexdigest()}  {k}  ({len(vv)} files)")
    open(f"{B9}/previous_batches_manifest.txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")
RUN = [("b39bff8", "validate_batch3.py", "Batch 3"), ("cb78fcb", "validate_batch4.py", "Batch 4"), ("43ec2cd", "validate_batch5.py", "Batch 5"), ("f3b8f83", "validate_batch6.py", "Batch 6"), ("9c594da", "validate_batch7.py", "Batch 7"), ("5cd5bd7", "validate_batch8.py", "Batch 8")]
tmp = tempfile.mkdtemp(prefix="b9_wt_")
try:
    for commit, script_, label in RUN:
        d = f"{tmp}/{commit}"; g = git("worktree", "add", "--detach", d, commit)
        r = subprocess.run([sys.executable, "-I", f"{d}/research/byd/{script_}"], capture_output=True, text=True, cwd=d, timeout=1800) if g.returncode == 0 else None
        chk(f"{label} validator ({script_}) passes on a clean checkout of {commit}", r is not None and r.returncode == 0, "" if r is None else f"exit {r.returncode}")
        git("worktree", "remove", "--force", d)
finally:
    shutil.rmtree(tmp, ignore_errors=True); git("worktree", "prune")

ok = all(r[1] for r in res); passed = sum(1 for r in res if r[1])
md = ["# Batch 9 validation report", "", f"Run: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · `research/byd/validate_batch9.py` · base commit `{BASE}`", "",
      f"**Result: {'ALL CHECKS PASSED' if ok else 'FAILURES PRESENT'}** ({passed}/{len(res)})", "", "| # | Check | Result | Detail |", "|---|---|---|---|"]
for i, (n, o, dt) in enumerate(res, 1): md.append(f"| {i} | {n} | {'PASS' if o else 'FAIL'} | {dt.replace('|', '/')[:180]} |")
md += ["", "## Row counts", ""] + [f"- {n}: {len(vv)}" for n, vv in (("dealer_contact_results.csv", DC), ("field_verification_cases.csv", CA), ("evidence_register.csv", ER), ("conflict_priority.csv", CP))]
md += ["", "## Notes", "", "- The validator proves that no call, dealer response, VIN, document or code was fabricated: every field-evidence cell is empty and every status is unchanged.",
       "- Previous-batch integrity: every research file of Batches 1-8 at the Batch 8 commit is compared by git blob id with the working tree; per-area digests are in `previous_batches_manifest.txt`.",
       "- Validators for Batches 3-8 were each run on a clean `git worktree` checkout of the commit that completed that batch (the Batch 8 validator in turn re-runs Batches 3-7)."]
open(f"{B9}/validation_report.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(f"{'PASS' if o else 'FAIL'}  {n}  {dt[:110]}" for n, o, dt in res)); sys.exit(0 if ok else 1)
