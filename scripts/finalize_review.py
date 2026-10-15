"""Attach issue register and verification from real outputs; no model execution."""
import json
from pathlib import Path
import pandas as pd
from render_review import table
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/review'
def main():
    v=json.loads((OUT/'verification.json').read_text());n=json.loads((OUT/'notebook_execution.json').read_text());d=json.loads((OUT/'decision.json').read_text())
    ledger=json.loads((OUT/'RUN_LEDGER.json').read_text());legacy=json.loads((OUT/'legacy_sensitivity.json').read_text())
    intervals=json.loads((OUT/'stress_intervals.json').read_text())
    stress_ci=pd.DataFrame([{'Candidate':r['candidate'],'Rule':r['rule'],'Budget':r['budget'],'Difference':r['difference'],'Paired 95% CI':f"[{r['difference_ci95'][0]:.2f}, {r['difference_ci95'][1]:.2f}]",'Active days':r['days']} for r in intervals]);(OUT/'stress_intervals.md').write_text(table(stress_ci))
    issues=[
      (1,'fixed','Regime-dependent weak baseline','raw_monthly.csv, all_monthly_performance.csv, decision.json','Both rules are compared throughout; route_duration_rule is preferred using development only. Neither rule is universally best.'),
      (2,'fixed','Outcome-filtered June','review.month_cohort, outcomes_asof; monthly_performance.csv','All eligible June rows stay in queues. Availability masks labels, not rows; full-snapshot outcomes are separately reported.'),
      (3,'fixed','Small winning margin treated as sufficient','decision.json; development_paired_days.csv','Requires month consistency, paired simultaneous intervals and conservative missing-outcome bounds. No model passes the full gate.'),
      (4,'partly fixed','Unexplained August shift','raw_monthly.csv; raw_monthly_buckets.csv; DIAGNOSIS.md','The recorded distribution shift is measured. Policy, seasonal and administrative causes cannot be identified from this snapshot.'),
      (5,'fixed','Strong simple rule absent from stress test','stress_summary.csv; stress_intervals.json','Both rules were evaluated once in the stress audit; neither result changes development selection.'),
      (6,'fixed','Single-March AP selection mismatched to queue goal','REVIEW_PROTOCOL.md; review.execute; development_summary.csv','Canonical selection uses mean monthly paired capacity differences. Old AP selection is preserved only as a labelled frozen-model historical comparator.'),
      (7,'fixed','Calibration confused with capacity gain','test_strict_monotone_calibration_preserves_queue; WALKTHROUGH.md','No new calibration is fitted; original positive-slope sigmoid preserves ranking. No queue benefit claimed.'),
      (8,'fixed','Missing paired original-ML uncertainty','stress_intervals.json; legacy_sensitivity.json','Whole-day paired intervals cover both rules and all budgets. Original delivered-only audit also reproduced. Fixed scores only; not future-regime uncertainty.'),
      (9,'fixed','Stale processed cache','cache.py; cache_verification.json; test_cache_checks_code_fingerprint_and_file_content','Verifies pinned raw bytes, preparation code and cache checksum. Canonical experiment rebuilt from raw.'),
      (10,'partly fixed','Delivered-only cohort and censoring','data.py; cohort_audit.json; raw_audit.json','Unknown outcomes now stay in prediction queues. Training still uses completed events; final status lacks transition times, and unrecorded outcomes cannot be recovered.'),
      (11,'fixed','Unjustified review capacity','development_summary.csv; stress_summary.csv','All prescribed budgets reported with actual review shares. They remain capacity scenarios, not a business staffing recommendation.'),
      (12,'fixed','Body handling, notebook outputs and count inconsistencies','app/middleware.py; verification.json; pytest.xml; notebook_execution.json',f"{v['passed']} tests pass; live POST and chunked oversize verified. {sum(x['executed_code_cells'] for x in n)} cells executed with stored outputs via IPython. Separate Jupyter kernel/Colab/browser rendering remain unverified.")]
    issue_df=pd.DataFrame(issues,columns=['Issue','Status','Problem','Evidence','Remaining uncertainty / resolution'])
    issue_df.to_csv(OUT/'issue_register.csv',index=False)
    (ROOT/'ISSUE_REGISTER.md').write_text('# Independent-review issue register\n\n'+table(issue_df))
    verification=f"""# Actual verification

- Pytest: {v['passed']} passed, {v['failures']} failed, {v['errors']} errors, {v['skipped']} skipped. Source: pytest.xml and verification.json.
- Live uvicorn JSON POST preservation: {v['live_http_post_preserved']}.
- Live chunked oversized POST rejected: {v['live_chunked_oversize_413']}.
- Executed notebooks: {len(n)}; executed code cells: {sum(x['executed_code_cells'] for x in n)}; error outputs: {sum(x['error_outputs'] for x in n)}.
- Fresh dependency installation and compatibility check succeeded; locked reinstall dry-run required no changes. Runtime lock evidence: runtime_lock_check.json; authoring installation evidence: environment.json when included.
- Dashboard DOM behaviour check passed using actual API responses. No visual browser rendering claim.
- Notebook syntax/format checks passed. Real cells executed with IPython in-process.
- Ordinary Jupyter kernel attempt failed due environment network-interface discovery denial. That failure was not presented as a successful Jupyter/Colab session.
- One experiment invocation completed under protocol commit `{ledger['protocol_commit']}`. No tuning or experimental re-runs followed its scores.

## Not run or not verifiable

- The full fresh-checkout rebuild wrapper was not invoked a second time; doing so would repeat the experiment. Its component installation, raw rebuild, fit, reporting, tests and notebook execution ran separately.
- Docker build/runtime and remote GitHub Actions were not run here. GitHub upload remains blocked by the previously observed integration permission error.
- Windows/macOS dependency compatibility, live Colab upload/proxy and rendered browser appearance were not verified.
- Exact extraction cutoff, outcome collection completeness, status transition dates, historical field revisions and the causal reason for August's shift are unavailable.
- Out-of-time model lift before the preregistered development start is unavailable, explicitly marked NA. Both simple rules have descriptive early-month results.
- No new independent cohort, deployment, intervention experiment, savings estimate or production readiness validation.
"""
    (OUT/'VERIFICATION.md').write_text(verification)
    (ROOT/'reports/VERIFICATION.md').write_text(verification)
    full=OUT/'FULL_REVIEW.md';s=full.read_text();s+='\n## Issue register\n\n'+table(issue_df)+'\n## Paired retrospective uncertainty\n\n'+table(stress_ci)+'\n'+verification
    (OUT/'FULL_REVIEW.md').write_text(s)
    md=ROOT/'README.md';s=md.read_text();s+=f"\n## Verification\n\n{v['passed']} tests passed; {len(n)} notebooks contain {sum(x['executed_code_cells'] for x in n)} executed code cells with stored outputs. Live POST and chunked oversize checks passed. Notebook execution used IPython in-process because separate Jupyter kernel startup was blocked. See `reports/review/VERIFICATION.md`.\n";md.write_text(s)
    questions=[
     ('What problem does DelayLens solve?','It studies which orders to review within a fixed daily limit, not whether an intervention saves money.'),
     ('When is a prediction made?','At approval. Historical statistics use only deliveries completed strictly earlier. Snapshot field availability remains an assumption.'),
     ('Why not remove undelivered orders?','That selects the evaluation population using a future outcome. Unknown outcomes must remain in the queue and use review capacity.'),
     ('How is the target defined?','A valid delivery calendar date after the promised date is late. Same-day delivery is on time; absent or impossible delivery timestamps are unknown.'),
     ('How was the method selected?','Using prespecified rolling months and mean paired confirmed late-hit differences at the primary budget, with consistency and uncertainty gates.'),
     ('Did the monotone model improve anything?','It improved observed development hits, but did not pass the conservative missing-outcome promotion gate. Those are different claims.'),
     ('What does a monotone constraint mean?','With other features fixed, a longer promise or more slack cannot increase predicted lateness. This is a modelling assumption, not a causal finding.'),
     ('Why is July–August not a clean test?','Its results had already informed earlier discussions. It is retrospective stress evidence and never selects a method in this run.'),
     ('Can calibration improve the daily queue?','A strictly increasing calibration transform preserves ranking, so it cannot change which orders are selected apart from implementation-level ties.'),
     ('What would you need before adoption?','Prospective data, reliable unknown-outcome resolution, versioned inputs, an operational feature service and evidence that the review action improves outcomes.')]
    (ROOT/'docs/INTERVIEW.md').write_text('# Interview questions and short answers\n\n'+'\n\n'.join(f'**{i}. {q}**\n\n{a}' for i,(q,a) in enumerate(questions,1)))
    claims='''# Honest public claims

You can say:
- I built an AI-assisted, reproducible research prototype and can explain its code and decisions.
- I compared fixed ML candidates with simple rules using chronological evaluation and paired uncertainty.
- I retained unresolved outcomes in evaluation queues and reported their effect on the conclusion.
- The monotone model led on observed development outcomes, but failed the conservative missing-outcome promotion gate.
- The preferred development rule and short-promise rule behaved differently across periods.
- The project includes a tested API demonstration and executed evidence notebooks. It has not been deployed to production.

Do not say:
- The model is universally better, production-ready, independently confirmed, or free of all possible leakage.
- The project saved money, prevented delays, or produced measured business impact.
- A local git commit is external preregistration or GitHub publication.
- Unresolved/canceled orders are proven on-time, or that August's cause has been established.
- You independently wrote every component without assistance, or understand decisions you cannot explain.
'''
    (ROOT/'docs/PUBLIC_CLAIMS.md').write_text(claims)
if __name__=='__main__':main()
