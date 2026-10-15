import json
import numpy as np
import pandas as pd
import pytest
from delaylens.review import month_cohort,outcomes_asof,make_model,queue,paired_days,training_cohort,NUMERIC,EXTRA,CATEGORICAL
from delaylens.cache import cached_frame,fingerprint,sha
from delaylens.review_features import history_features

def rows():
    return pd.DataFrame({'order_id':['a','b','c'],'order_approved_at':pd.to_datetime(['2018-06-01','2018-06-01','2018-06-01']),
        'order_delivered_customer_date':pd.to_datetime(['2018-06-03','2018-08-10',None]),'late':[0.,1.,np.nan],
        'promised_days':[2.,3.,4.],'seller_id':['s']*3,'seller_state':['SP']*3,'customer_state':['RJ']*3})

def test_no_outcome_filtering_of_evaluation():
    df=rows();df['order_status']=['delivered','shipped','canceled']
    before=month_cohort(df,'2018-06-01')
    df['late']=np.nan;df['order_delivered_customer_date']=pd.NaT;df['order_status']='unavailable'
    assert month_cohort(df,'2018-06-01').order_id.tolist()==before.order_id.tolist()
    censored=outcomes_asof(before,pd.Timestamp('2018-07-01'))
    assert len(censored)==3 and censored.late.notna().sum()==1
    assert queue(censored,[0,1,2],2).selected.sum()==2

def test_training_requires_observed_outcome_before_cutoff():
    train=training_cohort(rows(),'2018-07-01')
    assert train.order_id.tolist()==['a']

def test_unknown_queue_bounds_are_paired_not_independent():
    df=rows()
    daily=paired_days(df,[3,2,1],[1,2,3],1)
    assert daily.difference.sum()==0
    assert daily.worst_unknown_difference.sum()==-1
    assert daily.best_unknown_difference.sum()==0

def test_unknown_delivery_never_enters_history():
    df=rows();df.loc[2,'order_approved_at']=pd.Timestamp('2018-09-01')
    h=history_features(df)
    assert h.loc[2,'seller_count']==2
    assert h.loc[0,'seller_count']==0

def test_cache_checks_code_fingerprint_and_file_content(tmp_path):
    p=tmp_path/'cache.pkl'; calls=[]
    def build():calls.append(1);return pd.DataFrame({'value':[len(calls)]})
    a,state=cached_frame(p,{'v':1},build);assert state=='rebuilt_from_verified_raw'
    a,state=cached_frame(p,{'v':1},build);assert state=='verified_cache'
    p.write_bytes(b'corrupt')
    a,state=cached_frame(p,{'v':1},build);assert len(calls)==2
    a,state=cached_frame(p,{'v':2},build);assert len(calls)==3

def test_raw_hash_change_is_rejected(tmp_path):
    (tmp_path/'x.csv').write_text('x\n1\n');manifest=tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'files':{'x.csv':sha(tmp_path/'x.csv')}}))
    fingerprint(tmp_path,manifest,[])
    (tmp_path/'x.csv').write_text('x\n2\n')
    with pytest.raises(ValueError,match='hash mismatch'):fingerprint(tmp_path,manifest,[])

def test_monotone_coordinate_and_joint_promise_constraints():
    # Synthetic data only: tests implementation, never chooses model settings.
    rng=np.random.default_rng(9);n=500
    x=pd.DataFrame({c:rng.normal(size=n) for c in NUMERIC+EXTRA})
    for c in CATEGORICAL:x[c]='SP'
    y=(x.promised_days+ .5*x.route_slack+rng.normal(size=n)<0).astype(int)
    model=make_model('monotone_enriched_boosting').fit(x,y)
    for cols in [['promised_days'],['seller_slack'],['route_slack'],['promised_days','seller_slack','route_slack']]:
        lower=x.iloc[:30].copy();upper=lower.copy()
        upper[cols]=upper[cols]+1
        assert np.all(model.predict_proba(upper)[:,1]<=model.predict_proba(lower)[:,1]+1e-12)
    params=model.named_steps['model'].get_params()
    assert params['early_stopping'] is False


def test_strict_monotone_calibration_preserves_queue():
    from scipy.special import expit,logit
    df=rows();p=np.array([.2,.4,.6]);cal=expit(1.2*logit(p)-.3)
    a=queue(df,p,2);b=queue(df,cal,2)
    assert a.order_id.tolist()==b.order_id.tolist()
