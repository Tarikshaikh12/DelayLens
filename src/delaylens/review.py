"""Single preregistered rolling-origin audit. No search and no stress-driven selection."""
import argparse, hashlib, importlib.metadata, json, math, subprocess
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from threadpoolctl import threadpool_limits
from .cache import fingerprint, cached_frame, sha
from .data import build_dataset
from .features import NUMERIC, CATEGORICAL, FEATURES
from .review_features import history_features, add_distance
ROOT=Path(__file__).resolve().parents[2]
METHODS=['short_promise_rule','route_duration_rule','original_features_boosting','enriched_boosting','monotone_enriched_boosting']
RULES=METHODS[:2]; MODELS=METHODS[2:]; BUDGETS=[10,25,50]
EXTRA=['distance_km','seller_count','seller_days','seller_late','route_count','route_days','route_late','seller_slack','route_slack']
SELECTION_TIME=pd.Timestamp('2018-07-01')


def write_json(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')


def bucket(days):
    return pd.cut(days,[-.001,10,20,30,np.inf],labels=['<=10','11-20','21-30','>30']).astype('string').fillna('invalid')


def raw_diagnostics(raw,out):
    o=pd.read_csv(raw/'olist_orders_dataset.csv')
    for c in ['order_approved_at','order_estimated_delivery_date','order_delivered_customer_date']:
        o[c]=pd.to_datetime(o[c],errors='coerce')
    o['month']=o.order_approved_at.dt.strftime('%Y-%m')
    o['promised_days']=(o.order_estimated_delivery_date.dt.normalize()-o.order_approved_at.dt.normalize()).dt.days
    valid=o.order_delivered_customer_date.ge(o.order_approved_at)
    o['late']=(o.order_delivered_customer_date.dt.normalize()>o.order_estimated_delivery_date.dt.normalize()).astype(float).where(valid)
    o['bucket']=bucket(o.promised_days)
    monthly=[];buckets=[]
    statuses=['delivered','shipped','canceled','unavailable','invoiced','processing','created','approved']
    for month,g in o.loc[o.month.between('2017-01','2018-08')].groupby('month'):
        row={'month':month,'orders':len(g),'median_promised_days':float(g.promised_days.median()),'observed_outcomes':int(g.late.notna().sum()),'unknown_outcomes':int(g.late.isna().sum()),'observed_late_rate':float(g.late.mean())}
        for status in statuses:
            row[status]=int(g.order_status.eq(status).sum()); row[status+'_share']=row[status]/len(g)
        for label in ['<=10','11-20','21-30','>30','invalid']:
            b=g.loc[g.bucket.eq(label)]; known=int(b.late.notna().sum()); hits=int(b.late.fillna(0).sum());unknown=len(b)-known
            row['share_'+label]=len(b)/len(g)
            buckets.append({'month':month,'bucket':label,'orders':len(b),'share_of_month':len(b)/len(g),'observed_outcomes':known,'unknown_outcomes':unknown,'confirmed_late':hits,'observed_late_rate':hits/known if known else np.nan,'late_rate_lower':hits/len(b) if len(b) else np.nan,'late_rate_upper':(hits+unknown)/len(b) if len(b) else np.nan})
        monthly.append(row)
    pd.DataFrame(monthly).to_csv(out/'raw_monthly.csv',index=False)
    pd.DataFrame(buckets).to_csv(out/'raw_monthly_buckets.csv',index=False)
    audit={'raw_orders':len(o),'missing_approval':int(o.order_approved_at.isna().sum()),'delivery_before_approval':int(o.order_delivered_customer_date.lt(o.order_approved_at).sum()),'status_delivered_without_timestamp':int((o.order_status.eq('delivered')&o.order_delivered_customer_date.isna()).sum()),'status_not_delivered_with_timestamp':int((~o.order_status.eq('delivered')&o.order_delivered_customer_date.notna()).sum()),'extraction_cutoff_known':False,'max_recorded_delivery':str(o.order_delivered_customer_date.max()),'max_recorded_purchase':str(pd.to_datetime(o.order_purchase_timestamp).max())}
    write_json(out/'raw_audit.json',audit)


def prepare(root=ROOT,force=False):
    out=root/'reports/review';out.mkdir(parents=True,exist_ok=True)
    codes=[root/'src/delaylens'/f for f in ['data.py','features.py','schema.py','review_features.py','cache.py']]
    stamp=fingerprint(root/'data/raw',root/'data/source_manifest.json',codes)
    def builder():
        df,_,audit=build_dataset(root/'data/raw');write_json(out/'cohort_audit.json',audit)
        return history_features(add_distance(df,root/'data/raw'))
    df,state=cached_frame(root/'data/processed/review.pkl',stamp,builder,force)
    write_json(out/'cache_verification.json',{'state':state,'fingerprint':stamp,'cache_sha256':sha(root/'data/processed/review.pkl')})
    return df


def month_cohort(df,start):
    """Eligibility depends only on approval dates; unknown outcomes stay in the queue."""
    start=pd.Timestamp(start)
    return df.loc[df.order_approved_at.ge(start)&df.order_approved_at.lt(start+pd.offsets.MonthBegin(1))].copy()


def training_cohort(df,start):
    start=pd.Timestamp(start)
    return df.loc[df.order_approved_at.ge(start-pd.Timedelta(days=180))&df.order_approved_at.lt(start)&df.order_delivered_customer_date.lt(start)&df.late.notna()].copy()


def outcomes_asof(df,cutoff=None):
    result=df.copy()
    if cutoff is not None: result['late']=result.late.where(result.order_delivered_customer_date.lt(cutoff))
    return result


def make_model(name):
    nums=list(NUMERIC)+(EXTRA if name!='original_features_boosting' else [])
    constraints=[-1 if name=='monotone_enriched_boosting' and n in ['promised_days','seller_slack','route_slack'] else 0 for n in nums]+[0]*len(CATEGORICAL)
    pre=ColumnTransformer([('num',SimpleImputer(strategy='median',keep_empty_features=True),nums),('cat',OrdinalEncoder(handle_unknown='use_encoded_value',unknown_value=-1),CATEGORICAL)])
    model=HistGradientBoostingClassifier(max_iter=180,learning_rate=.06,max_leaf_nodes=15,min_samples_leaf=35,l2_regularization=5,early_stopping=False,random_state=42,categorical_features=[False]*len(nums)+[True]*len(CATEGORICAL),monotonic_cst=constraints)
    return Pipeline([('preprocess',pre),('model',model)])


def predict_method(name,train,test):
    if name=='short_promise_rule': return -test.promised_days.to_numpy()
    if name=='route_duration_rule': return -test.route_slack.to_numpy()
    if train.late.nunique()<2: raise ValueError('Training lacks two observed classes; do not silently change protocol.')
    estimator=make_model(name).fit(train,train.late)
    return estimator.predict_proba(test)[:,1]


def queue(df,score,k):
    q=df[['order_id','order_approved_at','late','promised_days']].copy()
    q['day']=q.order_approved_at.dt.strftime('%Y-%m-%d');q['month']=q.day.str[:7];q['bucket']=bucket(q.promised_days)
    q['score']=np.asarray(score)
    q=q.sort_values(['day','score','order_id'],ascending=[True,False,True])
    q['selected']=q.groupby('day').cumcount()<k
    q['known_hit']=q.late.fillna(0)*q.selected
    q['unknown_selected']=q.late.isna()*q.selected
    sizes=q.groupby('day').order_id.transform('size')
    q['random_confirmed_contribution']=np.minimum(k,sizes)/sizes*q.late.fillna(0)
    return q


def summarize(q,k):
    selected=int(q.selected.sum());hits=int(q.known_hit.sum());unknown=int(q.unknown_selected.sum());expected=float(q.random_confirmed_contribution.sum())
    return {'budget':k,'orders':len(q),'known_outcomes':int(q.late.notna().sum()),'unknown_outcomes':int(q.late.isna().sum()),'confirmed_late_orders':int(q.late.fillna(0).sum()),'selected':selected,'review_share':selected/len(q) if len(q) else np.nan,'confirmed_late_found':hits,'selected_unknown':unknown,'precision_lower':hits/selected if selected else np.nan,'precision_upper':(hits+unknown)/selected if selected else np.nan,'random_expected_confirmed_hits':expected,'lift_known_hits':hits/expected if expected else np.nan}


def paired_days(df,candidate,rule,k):
    a=queue(df,candidate,k).set_index('order_id'); b=queue(df,rule,k).set_index('order_id').reindex(a.index)
    diff=a.selected.astype(int)-b.selected.astype(int)
    known=diff*a.late.fillna(0)
    worst=known+np.where(a.late.isna(),np.minimum(diff,0),0)
    best=known+np.where(a.late.isna(),np.maximum(diff,0),0)
    return pd.DataFrame({'day':a.day,'month':a.month,'difference':known,'worst_unknown_difference':worst,'best_unknown_difference':best}).groupby(['month','day'],as_index=False).sum()


def bootstrap(daily,monthly=True,repetitions=4000):
    rng=np.random.default_rng(20261014);columns=['difference','worst_unknown_difference','best_unknown_difference']
    groups=[g[columns].to_numpy() for _,g in daily.groupby('month')] if monthly else [daily[columns].to_numpy()]
    draws=np.zeros((repetitions,3))
    for a in groups:
        # Whole days are paired; each month retains its original number of days.
        draws+=a[rng.integers(0,len(a),(repetitions,len(a)))].sum(axis=1)/len(groups)
    point=daily.groupby('month')[columns].sum().mean().to_numpy() if monthly else daily[columns].sum().to_numpy()
    result={'replicates':repetitions,'unit':'mean monthly late hits' if monthly else 'total late hits','days':len(daily)}
    for i,col in enumerate(columns):
        result[col]=float(point[i]);result[col+'_ci95']=[float(v) for v in np.quantile(draws[:,i],[.025,.975])]
        result[col+'_simultaneous_ci']=[float(v) for v in np.quantile(draws[:,i],[.05/12,1-.05/12])]
    return result


def collect(df,scores,phase,rows,bucket_rows,daily_rows):
    for method,score in scores.items():
        for k in BUDGETS:
            q=queue(df,score,k)
            for month,g in q.groupby('month'):
                rows.append({'phase':phase,'month':month,'method':method,**summarize(g,k)})
                for label,b in g.groupby('bucket'):
                    bucket_rows.append({'phase':phase,'month':month,'method':method,'bucket':label,**summarize(b,k)})
            daily=q.groupby(['month','day'],as_index=False).agg(confirmed_late_found=('known_hit','sum'),selected_unknown=('unknown_selected','sum'),selected=('selected','sum'),random_expected_confirmed_hits=('random_confirmed_contribution','sum'))
            daily['phase']=phase;daily['method']=method;daily['budget']=k;daily_rows.append(daily)


def execute(root=ROOT):
    out=root/'reports/review';out.mkdir(parents=True,exist_ok=True)
    protocol=root/'experiments/REVIEW_PROTOCOL.md'
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    committed=subprocess.check_output(['git','show',f'{commit}:experiments/REVIEW_PROTOCOL.md'],cwd=root)
    if committed!=protocol.read_bytes():raise ValueError('Protocol must be committed unchanged before fitting.')
    critical=['experiments/REVIEW_PROTOCOL.md','src/delaylens/review.py','src/delaylens/review_features.py','src/delaylens/data.py','src/delaylens/features.py','src/delaylens/schema.py','src/delaylens/cache.py']
    for name in critical:
        if subprocess.check_output(['git','show',f'{commit}:{name}'],cwd=root)!=(root/name).read_bytes():raise ValueError(f'Uncommitted experiment code: {name}')
    ledger=out/'RUN_LEDGER.json'
    record={'status':'started','start_utc':datetime.now(timezone.utc).isoformat(),'protocol_commit':commit,'protocol_sha256':sha(protocol),'code_sha256':{n:sha(root/n) for n in critical},'packages':{n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','scikit-learn','joblib']}}
    # Exclusive creation prevents silently overwriting an earlier experiment.
    with ledger.open('x') as f:json.dump(record,f,indent=2)
    df=prepare(root,force=True)
    raw_diagnostics(root/'data/raw',out)
    monthly=[];buckets=[];days=[];saved=[];training=[]
    for start in pd.date_range('2017-03-01','2018-05-01',freq='MS'):
        train=training_cohort(df,start);test=outcomes_asof(month_cohort(df,start),SELECTION_TIME)
        scores={name:predict_method(name,train,test) for name in METHODS}
        training.append({'month':str(start)[:7],'training_orders':len(train),'training_late':int(train.late.sum()),'evaluation_orders':len(test),'unknown_outcomes_asof_selection':int(test.late.isna().sum())})
        collect(test,scores,'development',monthly,buckets,days);saved.append((test,scores))
        print('Completed development month',str(start)[:7],flush=True)
    table=pd.DataFrame(monthly)
    primary=table.loc[table.budget.eq(50)].groupby('method').confirmed_late_found.mean()
    best_rule=max(RULES,key=lambda n:primary[n]);comparisons=[];eligibility=[];pair_records=[]
    for model in MODELS:
        gate=True;wins=0
        for rule in RULES:
            daily=pd.concat([paired_days(test,scores[model],scores[rule],50) for test,scores in saved],ignore_index=True)
            ci=bootstrap(daily)
            wins_here=int(daily.groupby('month').difference.sum().gt(0).sum())
            comparisons.append({'model':model,'rule':rule,'months_won':wins_here,**ci})
            daily['candidate']=model;daily['rule']=rule;pair_records.append(daily)
            gate=gate and ci['difference_simultaneous_ci'][0]>0 and ci['worst_unknown_difference_simultaneous_ci'][0]>0
            if rule==best_rule:wins=wins_here
        eligible=bool(gate and wins>=10)
        eligibility.append({'model':model,'mean_monthly_paired_difference':float(primary[model]-primary[best_rule]),'months_won_vs_best_rule':wins,'eligible':eligible})
    eligible=[r for r in eligibility if r['eligible']]
    selected=max(eligible,key=lambda r:r['mean_monthly_paired_difference'])['model'] if eligible else best_rule
    decision={'best_simple_rule':best_rule,'selected_method':selected,'ml_promoted':bool(eligible),'primary_budget':50,'development_months':15,'model_decisions':eligibility,'comparisons':comparisons,'stress_used_for_selection':False,'independent_confirmation':False}
    write_json(out/'decision.json',decision)  # Selection frozen before June/stress predictions.
    pd.DataFrame(training).to_csv(out/'training_windows.csv',index=False)
    pd.concat(pair_records).to_csv(out/'development_paired_days.csv',index=False)
    june=month_cohort(df,'2018-06-01');train=training_cohort(df,'2018-06-01')
    diagnostic_names=list(dict.fromkeys(RULES+['original_features_boosting',selected]))
    june_scores={n:predict_method(n,train,june) for n in diagnostic_names}
    collect(outcomes_asof(june,SELECTION_TIME),june_scores,'june_censored_asof_july',monthly,buckets,days)
    collect(june,june_scores,'june_snapshot_diagnostic',monthly,buckets,days)
    # Only selected method and preregistered comparators in stress evaluation.
    stress=df.loc[df.order_approved_at.ge('2018-07-01')&df.order_approved_at.lt('2018-09-01')].copy()
    train=training_cohort(df,'2018-07-01');names=list(dict.fromkeys(RULES+[selected]))
    scores={n:predict_method(n,train,stress) for n in names}
    metadata=json.loads((root/'artifacts/metadata.json').read_text())
    if sha(root/'artifacts/model.joblib')!=metadata['artifact_sha256']:raise ValueError('Original artifact hash mismatch')
    original=joblib.load(root/'artifacts/model.joblib')
    scores['frozen_original_ml']=original.predict_proba(stress[FEATURES])[:,1]
    collect(stress,scores,'retrospective_stress',monthly,buckets,days)
    stress_rows=[];stress_ci=[]
    for method,score in scores.items():
        for k in BUDGETS:stress_rows.append({'method':method,**summarize(queue(stress,score,k),k)})
    for candidate in list(dict.fromkeys(['frozen_original_ml',selected])):
        for rule in RULES:
            if candidate==rule:continue
            for k in BUDGETS:
                d=paired_days(stress,scores[candidate],scores[rule],k)
                stress_ci.append({'candidate':candidate,'rule':rule,'budget':k,**bootstrap(d,monthly=False)})
    # Clearly labelled legacy sensitivity, not the new primary cohort.
    legacy=stress.loc[stress.order_status.eq('delivered')&stress.late.notna()]
    mask=stress.index.isin(legacy.index)
    legacy_rows=[]
    for rule in RULES:
        a=scores['frozen_original_ml'][mask];b=scores[rule][mask]
        legacy_rows.append({'scope':'legacy_delivered_only','rule':rule,'original':summarize(queue(legacy,a,50),50),'baseline':summarize(queue(legacy,b,50),50),'paired':bootstrap(paired_days(legacy,a,b,50),monthly=False)})
    write_json(out/'legacy_sensitivity.json',legacy_rows)
    write_json(out/'stress_intervals.json',stress_ci)
    pd.DataFrame(stress_rows).to_csv(out/'stress_summary.csv',index=False)
    pd.DataFrame(monthly).to_csv(out/'monthly_performance.csv',index=False)
    pd.DataFrame(buckets).to_csv(out/'bucket_performance.csv',index=False)
    pd.concat(days).to_csv(out/'daily_performance.csv',index=False)
    pd.DataFrame([{'month':m,'model_lift':None,'reason':'No preregistered out-of-time model before March 2017'} for m in ['2017-01','2017-02']]).to_csv(out/'unavailable_model_months.csv',index=False)
    record['status']='completed';record['end_utc']=datetime.now(timezone.utc).isoformat();record['selected_method']=selected
    write_json(ledger,record)
    print('Decision:',selected,'ML promoted:',bool(eligible),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--diagnostics-only',action='store_true');args=parser.parse_args()
    with threadpool_limits(limits=2):
        if args.diagnostics_only:
            out=ROOT/'reports/review';out.mkdir(parents=True,exist_ok=True)
            fingerprint(ROOT/'data/raw',ROOT/'data/source_manifest.json',[])
            raw_diagnostics(ROOT/'data/raw',out)
        else:execute()

if __name__=='__main__':main()
