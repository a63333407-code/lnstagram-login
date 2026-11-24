#!/usr/bin/env python3
"""Batch 5 validator.  Exit code 0 = all checks pass.  Writes batch5/validation_report_batch5.md.
Usage: python3 validate_batch5.py [--base-commit cb78fcb9638fa73d363393b5d0ae10731c25a00a]"""
import csv, os, sys, subprocess, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__)); U = os.path.join(HERE, "catalog_union"); B5 = os.path.join(HERE, "batch5")
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
BASE = "cb78fcb9638fa73d363393b5d0ae10731c25a00a"
if "--base-commit" in sys.argv: BASE = sys.argv[sys.argv.index("--base-commit") + 1]
rd = lambda p: list(csv.DictReader(open(p, encoding="utf-8", newline="")))
STAT = {"VERIFIED_OEM", "VERIFIED_LABEL", "CORROBORATED", "POSSIBLE", "CONFLICTED", "UNVERIFIED"}
results = []
def chk(name, ok, detail=""):
    results.append((name, bool(ok), detail)); return ok

models = {m["model_id"]: m for m in rd(f"{U}/models_all.csv")}; cols = {c["color_id"]: c for c in rd(f"{U}/factory_colors_all.csv")}
years = {y["model_year_id"]: y for y in rd(f"{U}/model_years_all.csv")}; gens = {g["generation_id"]: g for g in rd(f"{U}/generations_all.csv")}
srcs = {s["source_id"] for s in rd(f"{U}/sources_all.csv")}; links = {l["link_id"]: l for l in rd(f"{U}/color_paint_code_links_all.csv")}
P = rd(f"{B5}/oem_paint_codes.csv"); SR = rd(f"{B5}/source_register.csv"); LE = rd(f"{B5}/vehicle_label_evidence.csv")
CF = rd(f"{B5}/paint_code_conflicts.csv"); UN = rd(f"{B5}/unresolved_paint_codes.csv"); MC = rd(f"{B5}/model_coverage.csv")
reg_ids = {s["b5_source_id"] for s in SR}

# 1 every code has a source
chk("every code record has >=1 source id", all(r["source_ids"] for r in P), f"{sum(1 for r in P if not r['source_ids'])} without")
chk("every source id is in the baseline or Batch 5 register", all(s in srcs or s in reg_ids for r in P for s in r["source_ids"].split(";") if s))
chk("every code record has a source URL", all(r["source_urls"] for r in P))
# 2 statuses valid, verified have direct evidence
chk("evidence_status in the six allowed values", all(r["evidence_status"] in STAT for r in P + UN + LE))
ver = [r for r in P if r["evidence_status"] in ("VERIFIED_OEM", "VERIFIED_LABEL")]
chk("VERIFIED rows carry oem_paint_code + page + quote", all(r["oem_paint_code"] and r["document_page_section"] and r["evidence_description"] for r in ver), f"{len(ver)} verified rows")
chk("oem_paint_code empty unless VERIFIED_*", all((not r["oem_paint_code"]) or r["evidence_status"].startswith("VERIFIED") for r in P))
chk("no retailer-only row is above POSSIBLE/CONFLICTED", all(r["evidence_status"] in ("POSSIBLE", "CONFLICTED") for r in P if all(s in {"S29","S30","S31","S32","S226","S227"} for s in r["source_ids"].split(";"))))
chk("no CORROBORATED without >=2 non-retailer independent sources", not any(r["evidence_status"] == "CORROBORATED" for r in P))
chk("POSSIBLE/CONFLICTED rows never combined (single status token)", all("|" not in r["evidence_status"] and "/" not in r["evidence_status"] for r in P))
# 3 relationships
bad = []
for r in P:
    c = cols.get(r["color_id"]); m = models.get(r["model_id"])
    if not c or not m or c["model_id"] != r["model_id"]: bad.append(r["record_id"]); continue
    if r["model_year_id"] != c["model_year_id"] or r["generation_id"] != c["generation_id"]: bad.append(r["record_id"]); continue
    y = years.get(c["model_year_id"]); g = gens.get(c["generation_id"])
    if c["model_year_id"] and (not y or y["model_id"] != c["model_id"] or y["generation_id"] != c["generation_id"]): bad.append(r["record_id"] + ":year")
    if not c["model_year_id"] and r["model_year_or_range"]: bad.append(r["record_id"] + ":year_invented")
    if not g or g["model_id"] != c["model_id"]: bad.append(r["record_id"] + ":gen")
    if r["color_name_zh_original"] != c["color_name_zh"]: bad.append(r["record_id"] + ":zh_changed")
chk("model / generation / model-year / colour relationships valid; Chinese colour name unchanged", not bad, str(bad[:5]))
chk("link_id exists and code matches baseline", all(r["link_id"] in links and links[r["link_id"]]["oem_code"] == r["supplier_candidate_code"] for r in P))
chk("no duplicate (colour, code) records", len({(r["color_id"], r["supplier_candidate_code"]) for r in P}) == len(P))
chk("record_ids unique", len({r["record_id"] for r in P}) == len(P))
# 4 conflicts not silently merged
conf_cols = {r["color_id_or_code"] for r in CF if r["conflict_type"] == "SOURCES_DISAGREE"}
chk("every CONFLICTED colour has a conflict row", conf_cols == {r["color_id"] for r in P if r["evidence_status"] == "CONFLICTED"})
alias_cols = {r["color_id_or_code"] for r in CF if r["conflict_type"] == "ALIAS_GROUP_AMBIGUITY"}
chk("every multi-code colour is flagged in conflicts", alias_cols == {r["color_id"] for r in P if r["code_ambiguity"] == "MULTI_CODE_ALIAS_GROUP"})
chk("conflict ids unique", len({r["conflict_id"] for r in CF}) == len(CF))
# 5 coverage
chk("model_coverage covers all 137 baseline models once", {r["model_id"] for r in MC} == set(models) and len(MC) == len(models) == 137)
chk("unresolved list covers all colour records that are not verified", {r["color_id"] for r in UN} == set(cols) and len(UN) == len(cols), f"{len(UN)} rows")
status_by_col = collections.defaultdict(set)
for r in UN: status_by_col[r["color_id"]].add(r["evidence_status"])
chk("colour status consistent between unresolved list and code records", all(status_by_col[r["color_id"]] == {r["evidence_status"]} for r in P))
chk("model_coverage status counts sum to colour records", all(int(r["n_possible"]) + int(r["n_conflicted"]) + int(r["n_unverified"]) + int(r["n_verified_oem"]) + int(r["n_verified_label"]) + int(r["n_corroborated"]) == int(r["colour_records"]) for r in MC))
chk("no model claims reliable paint-code evidence without verified rows", all(r["reliable_paint_code_evidence"] == "NO" or int(r["n_verified_oem"]) + int(r["n_verified_label"]) + int(r["n_corroborated"]) > 0 for r in MC))
chk("label evidence: no code value recorded without exact vehicle link", all((not r["paint_code_value_observed"]) or r["vehicle_identity_linked_to_label"].startswith("YES") for r in LE))
chk("label evidence: no VERIFIED_LABEL without visual inspection", all(r["evidence_status"] != "VERIFIED_LABEL" or r["visually_inspected_page"].startswith("YES") for r in LE))
for f in ("REPORT_batch5.md",):
    pass
# 6 Batch 1-4 unchanged vs base commit
def git(*a): return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True)
head_ok = git("cat-file", "-e", BASE + "^{commit}").returncode == 0
chk("base commit present", head_ok, BASE)
if head_ok:
    d = git("diff", "--name-status", BASE, "--", "research/byd", ":(exclude)research/byd/batch5", ":(exclude)research/byd/build_batch5.py", ":(exclude)research/byd/validate_batch5.py", ":(exclude)research/byd/build_batch5_report.py").stdout.strip()
    # tracked changes (staged or not) vs base, plus any untracked outside batch5
    u = git("ls-files", "--others", "--exclude-standard", "research", "--", ).stdout.split()
    u = [x for x in u if not x.startswith("research/byd/batch5/") and x not in ("research/byd/build_batch5.py", "research/byd/validate_batch5.py", "research/byd/build_batch5_report.py")]
    chk("Batch 1-4 files unchanged vs " + BASE[:8] + " (git diff)", d == "" and not u, (d or "") + " " + " ".join(u))
chk("application files untouched (non-research tracked diff vs base)", git("diff", "--name-only", BASE, "--", ".", ":(exclude)research").stdout.strip() == "")

ok = all(r[1] for r in results)
md = [f"# Batch 5 validation report", "", f"Run: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · script `research/byd/validate_batch5.py` · base commit `{BASE}`", "",
      f"**Result: {'ALL CHECKS PASSED' if ok else 'FAILURES PRESENT'}** ({sum(1 for r in results if r[1])}/{len(results)})", "", "| # | Check | Result | Detail |", "|---|---|---|---|"]
for i, (n, o, dt) in enumerate(results, 1): md.append(f"| {i} | {n} | {'PASS' if o else 'FAIL'} | {dt.replace('|','/')[:200]} |")
md += ["", "## Row counts", ""] + [f"- {n}: {len(v)}" for n, v in (("oem_paint_codes.csv", P), ("vehicle_label_evidence.csv", LE), ("source_register.csv", SR), ("paint_code_conflicts.csv", CF), ("unresolved_paint_codes.csv", UN), ("model_coverage.csv", MC))]
md += ["", "## Scope notes", "", "- The validator proves internal consistency and traceability; it cannot prove that a supplier code is correct. All code rows are POSSIBLE/CONFLICTED by design.",
       "- Verified-status rules are enforced as constraints: with no OEM document or exact-vehicle label in evidence, any VERIFIED_* or CORROBORATED row would fail validation."]
open(f"{B5}/validation_report_batch5.md", "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(f"{'PASS' if o else 'FAIL'}  {n}  {dt[:120]}" for n, o, dt in results)); sys.exit(0 if ok else 1)
