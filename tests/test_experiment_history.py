"""Point-in-time invariants for the exploratory historical features."""
import importlib.util
from pathlib import Path
import pandas as pd
import numpy as np
from delaylens import review_features as module

def sample():
    return pd.DataFrame({'order_id':['a','b','c','d'], 'seller_id':['s']*4,
        'seller_state':['SP']*4,'customer_state':['RJ']*4,
        'order_approved_at':pd.to_datetime(['2018-01-01','2018-01-02','2018-01-04','2018-01-05']),
        'order_delivered_customer_date':pd.to_datetime(['2018-01-04','2018-01-10','2018-01-12','2018-01-15']),
        'late':[0,1,1,1],'promised_days':[5,5,5,5]})

def test_history_uses_completed_events_strictly_before_approval():
    out=module.history_features(sample())
    assert out.seller_count.tolist()==[0,0,0,1]
    assert out.route_count.tolist()==[0,0,0,1]
    assert out.loc[3,'seller_days']==3
    assert out.loc[3,'seller_late']==0

def test_future_outcomes_cannot_change_earlier_features():
    df=sample(); a=module.history_features(df)
    df.loc[1:,'late']=0
    df.loc[1:,'order_delivered_customer_date']+=pd.Timedelta(days=100)
    b=module.history_features(df)
    cols=['seller_count','seller_days','seller_late','route_count','route_days','route_late','seller_slack','route_slack']
    np.testing.assert_allclose(a[cols],b[cols])

def test_input_row_order_does_not_change_history():
    df=sample()
    a=module.history_features(df).set_index('order_id').sort_index()
    b=module.history_features(df.iloc[::-1]).set_index('order_id').sort_index()
    pd.testing.assert_frame_equal(a,b)

