"""Generate narrative tables from saved evidence. NEVER fits or selects a model."""
import json
from pathlib import Path
import pandas as pd
from delaylens.cache import fingerprint,sha
from delaylens.review import RULES,BUDGETS,month_cohort,outcomes_asof,predict_method,queue,summarize
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/review'
def table(df,digits=2):
    def value(x):
        if pd.isna(x):return 'NA'
        if isinstance(x,float):return f'{x:.{digits}f}'
        return str(x)
    return '| '+' | '.join(map(str,df.columns))+' |\n|'+ '|'.join(['---']*len(df.columns))+'|\n'+'\n'.join('| '+' | '.join(value(v) for v in row)+' |' for row in df.itertuples(index=False,name=None))+'\n'
def pct(x):return f'{100*x:.2f}%'
def main():
    decision=json.loads((OUT/'decision.json').read_text());ledger=json.loads((OUT/'RUN_LEDGER.json').read_text())
    raw=pd.read_csv(OUT/'raw_monthly.csv');rb=pd.read_csv(OUT/'raw_monthly_buckets.csv');perf=pd.read_csv(OUT/'monthly_performance.csv');bp=pd.read_csv(OUT/'bucket_performance.csv');stress=pd.read_csv(OUT/'stress_summary.csv')
    # Prespecified early-month rule diagnostics; no model fits, no selection changes.
    cache=ROOT/'data/processed/review.pkl'
    if cache.exists():
        codes=[ROOT/'src/delaylens'/f for f in ['data.py','features.py','schema.py','review_features.py','cache.py']]
        stamp=fingerprint(ROOT/'data/raw',ROOT/'data/source_manifest.json',codes)
        meta=json.loads(cache.with_suffix('.manifest.json').read_text())
        if meta['fingerprint']!=stamp or meta['cache_sha256']!=sha(cache):raise ValueError('Cache verification failed')
        df=pd.read_pickle(cache);early=[];early_buckets=[]
        for start in ['2017-01-01','2017-02-01']:
            cohort=outcomes_asof(month_cohort(df,start),pd.Timestamp('2018-07-01'))
            for method in RULES:
                scores=predict_method(method,None,cohort)
                for k in BUDGETS:
                    q=queue(cohort,scores,k);base={'phase':'early_rule_diagnostic','month':start[:7],'method':method}
                    early.append({**base,**summarize(q,k)})
                    for label,g in q.groupby('bucket'):early_buckets.append({**base,'bucket':label,**summarize(g,k)})
        pd.DataFrame(early).to_csv(OUT/'early_rules.csv',index=False);pd.DataFrame(early_buckets).to_csv(OUT/'early_rule_buckets.csv',index=False)
    if (OUT/'early_rules.csv').exists():perf=pd.concat([perf,pd.read_csv(OUT/'early_rules.csv')],ignore_index=True)
    if (OUT/'early_rule_buckets.csv').exists():bp=pd.concat([bp,pd.read_csv(OUT/'early_rule_buckets.csv')],ignore_index=True)
    perf.to_csv(OUT/'all_monthly_performance.csv',index=False);bp.to_csv(OUT/'all_bucket_performance.csv',index=False)
    # Exact compact tables used by README, report and final delivery.
    status=raw[['month','orders','median_promised_days','unknown_outcomes','delivered','shipped','canceled','unavailable']].copy()
    status['other_status']=raw[['invoiced','processing','created','approved']].sum(axis=1)
    status.columns=['Month','Orders','Median promise','Unknown','Delivered','Shipped','Canceled','Unavailable','Other']
    bucket_table=pd.DataFrame({'Month':raw.month})
    for label in ['<=10','11-20','21-30','>30']:
        b=rb[rb.bucket.eq(label)].set_index('month').reindex(raw.month)
        bucket_table[label+' share / observed late']= [f'{pct(s)} / {pct(l) if pd.notna(l) else "NA"}' for s,l in zip(b.share_of_month,b.observed_late_rate)]
    bucket_table['Invalid share']=raw['share_invalid'].map(pct)
    dev=perf[perf.phase.eq('development')]
    totals=dev.groupby(['method','budget'],as_index=False).agg(confirmed_hits=('confirmed_late_found','sum'),mean_month_hits=('confirmed_late_found','mean'),selected_unknown=('selected_unknown','sum'))
    totals.to_csv(OUT/'development_summary.csv',index=False)
    pivot=totals.pivot(index='method',columns='budget',values='confirmed_hits').reset_index();pivot.columns=['Method','Hits @10','Hits @25','Hits @50']
    primary=dev[dev.budget.eq(50)].pivot(index='month',columns='method',values='confirmed_late_found').reset_index()
    selection=pd.DataFrame(decision['model_decisions'])
    selected_ci=[c for c in decision['comparisons'] if c['rule']==decision['best_simple_rule']]
    ci_table=pd.DataFrame([{'Model':c['model'],'Mean monthly gain':c['difference'],'Months won':c['months_won'],'95% paired CI':f"[{c['difference_ci95'][0]:.2f}, {c['difference_ci95'][1]:.2f}]",'Worst-case simultaneous CI':f"[{c['worst_unknown_difference_simultaneous_ci'][0]:.2f}, {c['worst_unknown_difference_simultaneous_ci'][1]:.2f}]"} for c in selected_ci])
    st=stress[['method','budget','selected','review_share','confirmed_late_found','selected_unknown','lift_known_hits']].copy();st.review_share=st.review_share.map(pct)
    st.columns=['Method','Budget','Reviewed','Review share','Confirmed late hits','Selected unknown','Known-hit lift']
    stress_month=perf[perf.phase.eq('retrospective_stress')][['month','method','budget','confirmed_late_found','selected_unknown','lift_known_hits']]
    # A single out-of-time diagnostic model per month, with explicit unavailable months.
    lift_rows=[]
    for month in raw.month:
        phase='early_rule_diagnostic' if month<'2017-03' else ('development' if month<='2018-05' else 'june_snapshot_diagnostic' if month=='2018-06' else 'retrospective_stress')
        g=perf[perf.month.eq(month)&perf.phase.eq(phase)&perf.budget.eq(50)].set_index('method')
        model='original_features_boosting' if month<='2018-06' else 'frozen_original_ml'
        row={'Month':month,'Short-rule lift':g.loc['short_promise_rule','lift_known_hits'] if 'short_promise_rule' in g.index else float('nan'),'Route-rule lift':g.loc['route_duration_rule','lift_known_hits'] if 'route_duration_rule' in g.index else float('nan'),'Model lift':g.loc[model,'lift_known_hits'] if model in g.index else float('nan'),'Model':model if model in g.index else 'not available'};lift_rows.append(row)
    lift=pd.DataFrame(lift_rows);lift.to_csv(OUT/'monthly_lift_compact.csv',index=False)
    tables={'monthly_status':status,'monthly_buckets':bucket_table,'monthly_lift':lift,'development_totals':pivot,'development_monthly_50':primary,'selection_intervals':ci_table,'stress_summary':st,'stress_monthly':stress_month}
    for name,df2 in tables.items():(OUT/(name+'.md')).write_text(table(df2))
    ml='Yes' if decision['ml_promoted'] else 'No'
    headline='ML did not pass the missing-outcome robustness gate; simple-rule performance varies by period.' if not decision['ml_promoted'] else 'ML passed the development gate; July–August remains retrospective evidence only.'
    summary=f'''# {headline}

Preferred development method: **{decision['selected_method']}**. ML promoted: **{ml}**.
Selection was frozen before June/July/August diagnostics. Both simple rules are
reported; July–August never chooses the preferred method.

## Development totals, confirmed late orders found

{table(pivot)}
## Paired selection evidence against {decision['best_simple_rule']}

{table(ci_table)}
These are mean monthly differences at the primary review budget. The ordinary
intervals describe fixed-score observed-label variation. The final column also
allows unobserved outcomes to favour the rule, with a simultaneous adjustment
for the prespecified model/rule comparisons. It is not a prediction interval for
new months. Passing the ordinary observed-label gate alone does not establish
robustness to missing outcomes.

## Retrospective stress results

{table(st)}
Unknown outcomes stay in every queue. Known-hit lift compares confirmed late hits
to random review over exactly the same full cohort; it is not full-population
recall. Budgets are hypothetical capacities, not a staffing recommendation.
The frozen API artifact is a historical comparator, not the new selected method.
'''
    (OUT/'SUMMARY.md').write_text(summary)
    july=raw[raw.month.eq('2018-07')].iloc[0];aug=raw[raw.month.eq('2018-08')].iloc[0]
    jshort=rb[rb.month.eq('2018-07')&rb.bucket.eq('<=10')].iloc[0];ashort=rb[rb.month.eq('2018-08')&rb.bucket.eq('<=10')].iloc[0]
    diagnostic=f'''## August shift: supported observations and unresolved causes

In raw approved orders, median promised days changed from {july.median_promised_days:.0f}
in July to {aug.median_promised_days:.0f} in August. The share promised within ten
days changed from {pct(jshort.share_of_month)} to {pct(ashort.share_of_month)};
the observed late rate in that bucket changed from {pct(jshort.observed_late_rate)}
to {pct(ashort.observed_late_rate)}. Unknown-outcome shares were
{pct(july.unknown_outcomes/july.orders)} and {pct(aug.unknown_outcomes/aug.orders)}.

Supported: the recorded promise distribution and observed relationship with
lateness changed. The August unknown share does not show a simple increase in
missing outcomes relative to July. This alone does not exclude dataset-end
selection or timestamp errors. Unverified hypotheses: a promise-policy change,
seasonality, operational disruption, and administrative extraction effects.
The source has no policy log, status transition times or verified observation
cutoff. Do not call any one hypothesis the proven cause.

Raw diagnostic cohorts include all orders with a recorded approval in each
month. Model cohorts additionally require valid approval-time inputs and one
seller. Their counts can differ. Bucket rates use observed outcomes; exact
unknown counts and lower/upper late-rate bounds are in raw_monthly_buckets.csv.
'''
    limitations='''## What the data cannot establish

- Missing deliveries are unresolved/unknown, not automatically on-time or late.
  Canceled and unavailable orders have competing outcomes that this delivery
  target cannot resolve. Training still learns from completed deliveries only.
- Final-snapshot price, product, ZIP, geolocation and promise values are assumed
  to have been available unchanged at approval; the dataset cannot prove it.
- All data has been inspected in earlier work. A committed local protocol protects
  this run against changing choices, but is not independent external preregistration.
- Calibration is not fitted in this audit. The original positive-slope sigmoid is
  strictly monotone and cannot improve its queue ranking. It did not make the
  old model's capacity performance better.
- Daily queues are retrospective next-shift prioritisation, not instant online
  action at approval. No intervention was tested. No causal impact or savings.
- Bootstrap intervals hold scores and fitted models fixed. They do not cover new
  regimes, future label completeness or repeated investigation of this dataset.
'''
    (OUT/'DIAGNOSIS.md').write_text('# Monthly data diagnosis\n\n'+diagnostic+'\n'+table(status)+'\n'+table(bucket_table)+'\n'+table(lift)+'\nFull budget/bucket lift contributions: all_bucket_performance.csv. They retain full-day queues, not new quotas within each bucket. Early model values are unavailable, not invented.\n')
    full=summary+'\n'+diagnostic+'\n## Raw monthly counts and status mix\n\n'+table(status)+'\n## Promised-day buckets: share / observed late rate\n\n'+table(bucket_table)+'\n## Monthly rule/model known-hit lift at primary budget\n\n'+table(lift)+'\n## Development monthly confirmed late hits at primary budget\n\n'+table(primary)+'\n## Stress results by month and budget\n\n'+table(stress_month)+'\n'+limitations
    full+='\n## Protocol and run provenance\n\nCommit: `'+ledger['protocol_commit']+'`. Full hashes, start/end times and package versions: `RUN_LEDGER.json`. The experiment was invoked once and completed; no candidate settings were changed after its results.\n'
    (OUT/'FULL_REVIEW.md').write_text(full)
    readme='# DelayLens — '+headline+'\n\nAn AI-assisted research prototype for approval-time delivery-delay prioritisation, using Olist historical data. The purpose is to test whether added ML complexity is justified. It is not a production deployment.\n\n'+summary.split('\n',1)[1]
    readme+='''
## Reproduce or inspect

- Start with `START_HERE.md` and `reports/review/FULL_REVIEW.md`.
- Read the fixed protocol in `experiments/REVIEW_PROTOCOL.md`.
- Python 3.12: `python scripts/rebuild.py` creates an isolated reproduction from
  verified raw files, installs `requirements-lock.txt`, freezes the protocol,
  fits once, and writes evidence. Internet is needed for missing files/packages.
- The supplied notebooks have actual outputs. `python scripts/execute_notebooks.py`
  executes their evidence/API cells without fitting candidates again.
- `python scripts/run_checks.py` records actual test counts and live HTTP checks.
- Original API demonstration: `python -m uvicorn app.main:app --port 8000`.
  It loads the supplied old artifact, not the new preferred research method.

The runtime lock was installed and checked on Python 3.12/Linux; other platforms
are not verified. Full clean-wrapper reproduction is not run again in the
authoring session because that would repeat the fixed experiment. Its underlying
installation, raw rebuild, experiment, report generation, tests and notebook
execution are verified separately and recorded.

## Evidence and limitations

`reports/review/` is authoritative. `reports/legacy/` preserves superseded evidence
and explains the old delivered-only comparisons. Current cohort counts differ
because unresolved outcomes stay in review queues. The API evidence endpoint
retains the original model's matched legacy report and is marked accordingly.

No claim of savings, causal impact, production readiness, fully observed outcomes,
independent confirmation, or universally superior ML. Original code is MIT;
Olist data-derived artifacts/reports retain the source dataset's non-commercial
license conditions. See `DATA_LICENSE.md`.
'''
    (ROOT/'README.md').write_text(readme)
if __name__=='__main__':main()
