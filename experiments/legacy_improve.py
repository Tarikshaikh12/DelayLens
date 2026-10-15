# ARCHIVED, SUPERSEDED IMPLEMENTATION: do not use for new evaluation.
# Preserved solely to audit historical results; canonical entry is delaylens.review.
"""Fixed exploratory follow-up. Run: PYTHONPATH=src python experiments/improve.py"""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.metrics import average_precision_score
from threadpoolctl import threadpool_limits
from delaylens.features import NUMERIC, CATEGORICAL
from delaylens.data import build_dataset
from delaylens.evaluation import capacity_metrics, queue_table
ROOT=Path(__file__).resolve().parents[1]
EXTRA=['distance_km','seller_count','seller_days','seller_late','route_count','route_days','route_late','seller_slack','route_slack']

def history_features(df):
    """Update statistics only when a past delivery strictly precedes approval."""
    df=df.copy().reset_index(drop=True)
    deliveries=df.sort_values(['order_delivered_customer_date','order_id']).index.to_numpy()
    durations=(df.order_delivered_customer_date.dt.normalize()-df.order_approved_at.dt.normalize()).dt.days.to_numpy()
    rows=df.to_dict('records'); seller={}; route={}; cursor=0
    global_n=global_days=global_late=0
    out=np.zeros((len(df),6))
    for i in df.sort_values(['order_approved_at','order_id']).index:
        r=rows[i]
        while cursor<len(deliveries) and rows[deliveries[cursor]]['order_delivered_customer_date']<r['order_approved_at']:
            j=deliveries[cursor]; past=rows[j]
            for table,key in [(seller,past['seller_id']),(route,(past['seller_state'],past['customer_state']))]:
                n,d,late=table.get(key,(0,0.,0.))
                table[key]=(n+1,d+durations[j],late+past['late'])
            global_n+=1; global_days+=durations[j]; global_late+=past['late']; cursor+=1
        prior_days=global_days/global_n if global_n else 12.
        prior_late=global_late/global_n if global_n else .08
        values=[]
        for table,key in [(seller,r['seller_id']),(route,(r['seller_state'],r['customer_state']))]:
            n,d,late=table.get(key,(0,0.,0.))
            values += [n,(d+20*prior_days)/(n+20),(late+20*prior_late)/(n+20)]
        out[i]=values
    df[['seller_count','seller_days','seller_late','route_count','route_days','route_late']]=out
    df['seller_slack']=df.promised_days-df.seller_days
    df['route_slack']=df.promised_days-df.route_days
    df['duration_days']=durations
    return df

def add_distance(df,raw):
    geo=pd.read_csv(raw/'olist_geolocation_dataset.csv')
    valid=geo.geolocation_lat.between(-90,90)&geo.geolocation_lng.between(-180,180)
    centers=geo.loc[valid].groupby('geolocation_zip_code_prefix')[['geolocation_lat','geolocation_lng']].median()
    orders=pd.read_csv(raw/'olist_orders_dataset.csv',usecols=['order_id','customer_id'])
    customers=pd.read_csv(raw/'olist_customers_dataset.csv',usecols=['customer_id','customer_zip_code_prefix'])
    sellers=pd.read_csv(raw/'olist_sellers_dataset.csv',usecols=['seller_id','seller_zip_code_prefix'])
    x=df.merge(orders,on='order_id',validate='one_to_one').merge(customers,on='customer_id',validate='many_to_one').merge(sellers,on='seller_id',validate='many_to_one')
    coords=[np.radians(x[f'{who}_zip_code_prefix'].map(centers[c]).to_numpy()) for who in ['customer','seller'] for c in ['geolocation_lat','geolocation_lng']]
    a,b,c,d=coords
    h=np.sin((c-a)/2)**2+np.cos(a)*np.cos(c)*np.sin((d-b)/2)**2
    x['distance_km']=6371*2*np.arcsin(np.sqrt(np.clip(h,0,1)))
    return x

def estimator(enriched=True,regression=False):
    nums=list(NUMERIC)+(EXTRA if enriched else [])
    if regression: nums=[n for n in nums if n not in ['promised_days','seller_slack','route_slack']]
    pre=ColumnTransformer([('num',SimpleImputer(strategy='median'),nums),('cat',OrdinalEncoder(handle_unknown='use_encoded_value',unknown_value=-1),CATEGORICAL)])
    cls=HistGradientBoostingRegressor if regression else HistGradientBoostingClassifier
    model=cls(max_iter=180,learning_rate=.06,max_leaf_nodes=15,min_samples_leaf=35,l2_regularization=5,early_stopping=False,random_state=42,categorical_features=[False]*len(nums)+[True]*len(CATEGORICAL))
    return Pipeline([('preprocess',pre),('model',model)])

def scores_for(name,train,test):
    if name=='short_promise_rule': return -test.promised_days.to_numpy()
    if name=='route_duration_rule': return -test.route_slack.to_numpy()
    reg=name=='duration_regression'
    model=estimator(name!='original_features_boosting',reg)
    model.fit(train,train.duration_days if reg else train.late)
    return model.predict(test)-test.promised_days.to_numpy() if reg else model.predict_proba(test)[:,1]

def paired_ci(test,scores):
    def hits(q): return q.assign(hit=q.late*q.selected).groupby('day').hit.sum()
    delta=(hits(queue_table(test,scores))-hits(queue_table(test,-test.promised_days.to_numpy()))).to_numpy()
    rng=np.random.default_rng(42)
    draws=[rng.choice(delta,len(delta),replace=True).sum() for _ in range(2000)]
    return {'late_found_difference':int(delta.sum()),'paired_day_bootstrap_95_percent':[float(x) for x in np.quantile(draws,[.025,.975])],'replicates':2000}

def main():
    out=ROOT/'reports/improvement'; out.mkdir(exist_ok=True)
    processed=ROOT/'data/processed/orders.csv'
    if processed.exists(): df=pd.read_csv(processed,parse_dates=['order_approved_at','order_delivered_customer_date'])
    else: df,_,_=build_dataset(ROOT/'data/raw')
    df=history_features(add_distance(df,ROOT/'data/raw'))
    methods=['short_promise_rule','route_duration_rule','original_features_boosting','enriched_boosting','duration_regression']
    results=[]
    for start in pd.date_range('2018-01-01','2018-06-01',freq='MS'):
        end=start+pd.offsets.MonthBegin(1)
        train=df.loc[df.order_approved_at.ge(start-pd.Timedelta(days=180))&df.order_approved_at.lt(start)&df.order_delivered_customer_date.lt(start)]
        test=df.loc[df.order_approved_at.ge(start)&df.order_approved_at.lt(end)&df.order_delivered_customer_date.lt('2018-07-01')]
        for name in methods:
            score=scores_for(name,train,test)
            row={'month':str(start.date())[:7],'method':name,'training_orders':len(train),'evaluation_orders':len(test),'excluded_unmatured':int((df.order_approved_at.ge(start)&df.order_approved_at.lt(end)&df.order_delivered_customer_date.ge('2018-07-01')).sum()),'late_orders':int(test.late.sum()),'average_precision':float(average_precision_score(test.late,score)),**capacity_metrics(test,score)}
            results.append(row)
            print(row['month'],name,'found',row['late_found'],'/',row['late_orders'],flush=True)
    table=pd.DataFrame(results); table.to_csv(out/'rolling_results.csv',index=False)
    totals=table.groupby('method').late_found.sum().sort_values(ascending=False)
    winner=max(methods,key=lambda n:int(totals[n]))
    (out/'selection.json').write_text(json.dumps({'winner':winner,'development_late_found':totals.to_dict(),'protocol_sha256':hashlib.sha256((ROOT/'experiments/PROTOCOL.md').read_bytes()).hexdigest()},indent=2))
    start=pd.Timestamp('2018-07-01')
    train=df.loc[df.order_approved_at.ge(start-pd.Timedelta(days=180))&df.order_approved_at.lt(start)&df.order_delivered_customer_date.lt(start)]
    test=df.loc[df.order_approved_at.ge(start)&df.order_approved_at.lt('2018-09-01')]
    score=scores_for(winner,train,test)
    report={'status':'exploratory_not_independent_confirmation','winner':winner,'orders':len(test),'late_orders':int(test.late.sum()),'winner_capacity':capacity_metrics(test,score),'rule_capacity':capacity_metrics(test,-test.promised_days.to_numpy()),'comparison':paired_ci(test,score),'monthly':{}}
    for month,g in test.assign(experiment_score=score).groupby(test.order_approved_at.dt.strftime('%Y-%m')):
        report['monthly'][month]={'winner':capacity_metrics(g,g.experiment_score),'rule':capacity_metrics(g,-g.promised_days.to_numpy())}
    (out/'retrospective_check.json').write_text(json.dumps(report,indent=2)+'\n')
    # Post-hoc descriptive diagnostic only: it does not feed model selection.
    diagnostic=[]
    for month,g in df.loc[df.order_approved_at.ge('2018-01-01') & df.order_approved_at.lt('2018-09-01')].groupby(df.order_approved_at.dt.strftime('%Y-%m')):
        short=g.loc[g.promised_days<=10]
        diagnostic.append({'month':month,'orders':len(g),'late_rate':g.late.mean(),
            'median_promised_days':g.promised_days.median(),'short_promise_orders':len(short),
            'short_promise_late_rate':short.late.mean(),
            'late_median_promised_days':g.loc[g.late.eq(1),'promised_days'].median()})
    pd.DataFrame(diagnostic).to_csv(out/'monthly_shift.csv',index=False)
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    raise SystemExit('Superseded experiment. Run python -m delaylens.review in a fresh committed reproduction.')

    with threadpool_limits(limits=2): main()
