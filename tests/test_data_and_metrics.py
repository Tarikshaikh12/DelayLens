import pandas as pd
import numpy as np
import pytest
from delaylens.data import build_dataset, temporal_split
from delaylens.features import feature_frame, FEATURES
from delaylens.schema import OrderInput
from delaylens.evaluation import capacity_metrics

def test_feature_contract_and_id_invariance(order):
    first = feature_frame([OrderInput(**order)])
    order['order_id']='DIFFERENT-ID'
    pd.testing.assert_frame_equal(first,feature_frame([OrderInput(**order)]))
    assert list(first.columns)==FEATURES
    assert first.promised_days.iloc[0]==10
    assert first.approval_hours.iloc[0]==1
    assert not any('delivered' in c or c.endswith('_id') for c in FEATURES)

def test_label_maturity_and_disjoint_windows():
    rows=[]
    for period in ['2017-06-01','2018-03-10','2018-05-10','2018-07-10']:
        for label in [0,1]:
            rows.append({'order_id':f'{period}-{label}','order_approved_at':pd.Timestamp(period),
                         'order_delivered_customer_date':pd.Timestamp(period)+pd.Timedelta(days=10),'late':label})
    rows.append({'order_id':'unmatured','order_approved_at':pd.Timestamp('2017-12-20'),
                 'order_delivered_customer_date':pd.Timestamp('2018-03-10'),'late':1})
    parts,report=temporal_split(pd.DataFrame(rows))
    assert report['train']['excluded_unmatured']==1
    assert 'unmatured' not in parts['train'].order_id.tolist()
    assert set(parts['train'].order_id).isdisjoint(parts['test'].order_id)

def test_daily_budget_resets_and_ties_are_stable():
    data=pd.DataFrame({'order_id':['B','A','D','C'], 'order_approved_at':pd.to_datetime(['2018-07-01']*2+['2018-07-02']*2),'late':[0,1,0,1]})
    result=capacity_metrics(data,np.ones(4),budget=1)
    assert result['selected']==2
    assert result['late_found']==2
    assert result['precision']==1
    assert result['random_expected_late_found']==1

def test_join_keeps_one_row_per_order_and_calendar_day_label(tmp_path):
    orders=[]
    for i,delivery in enumerate(['2018-07-20 18:00:00','2018-07-21 00:00:00']):
        orders.append(dict(order_id=f'o{i}',customer_id=f'c{i}',order_status='delivered',order_purchase_timestamp='2018-07-01 10:00:00',order_approved_at='2018-07-01 11:00:00',order_estimated_delivery_date='2018-07-20 00:00:00',order_delivered_customer_date=delivery))
    pd.DataFrame(orders).to_csv(tmp_path/'olist_orders_dataset.csv',index=False)
    pd.DataFrame([dict(order_id=f'o{i}',order_item_id=j,product_id='p',seller_id='s',price=10,freight_value=2) for i in range(2) for j in [1,2]]).to_csv(tmp_path/'olist_order_items_dataset.csv',index=False)
    pd.DataFrame([dict(customer_id=f'c{i}',customer_state='SP') for i in range(2)]).to_csv(tmp_path/'olist_customers_dataset.csv',index=False)
    pd.DataFrame([dict(seller_id='s',seller_state='RJ')]).to_csv(tmp_path/'olist_sellers_dataset.csv',index=False)
    pd.DataFrame([dict(product_id='p',product_category_name='cat',product_weight_g=100,product_length_cm=10,product_height_cm=10,product_width_cm=10)]).to_csv(tmp_path/'olist_products_dataset.csv',index=False)
    pd.DataFrame([dict(product_category_name='cat',product_category_name_english='test')]).to_csv(tmp_path/'product_category_name_translation.csv',index=False)
    frame, requests, audit=build_dataset(tmp_path)
    assert len(frame)==2
    assert frame.late.tolist()==[0,1]
    assert frame.item_count.tolist()==[2,2]
    assert frame.total_price_brl.tolist()==[20,20]
    assert frame.total_weight_g.tolist()==[200,200]
    assert audit['eligible_orders']==2
