import copy
import json
import hashlib
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import create_app, Predictor
from delaylens.features import feature_frame
from delaylens.schema import OrderInput

ROOT = Path(__file__).resolve().parents[1]

def test_readiness_and_dashboard(client):
    assert client.get('/health').json()['status'] == 'alive'
    assert client.get('/ready').status_code == 200
    assert 'DelayLens' in client.get('/').text
    assert client.get('/openapi.json').json()['paths']['/predict']

def test_api_matches_offline_model(client, order):
    predictor = Predictor(ROOT/'artifacts')
    offline = predictor.model.predict_proba(feature_frame([OrderInput(**order)]))[0,1]
    r = client.post('/predict', json=order)
    assert r.status_code == 200
    assert r.json()['delay_probability'] == pytest.approx(offline, abs=1e-12)
    assert r.json()['release_status'] == 'research_only'

@pytest.mark.parametrize('field,value', [
    ('total_price_brl',-2),('freight_brl',-1),('item_count',1.5),('item_count',True),
    ('item_count',0),('customer_state','XX'),('order_id','<script>'),
    ('approved_at','2017-01-01T00:00:00'),('promised_date','2017-01-01'),
    ('approved_at','2018-07-12T11:00:00Z'),('total_weight_g',0)])
def test_invalid_inputs_rejected(client, order, field, value):
    order[field] = value
    assert client.post('/predict', json=order).status_code == 422

def test_future_information_rejected(client, order):
    order['order_delivered_customer_date'] = '2018-07-30'
    assert client.post('/predict', json=order).status_code == 422

def test_nan_rejected_without_server_crash(client, order):
    raw = json.dumps(order).replace('130', 'NaN', 1)
    assert client.post('/predict', content=raw, headers={'Content-Type':'application/json'}).status_code == 422

def test_batch_ranking_and_budget(client, order):
    a,b = copy.deepcopy(order),copy.deepcopy(order)
    a['order_id'],b['order_id']='Z-ORDER','A-ORDER'
    result = client.post('/predict/batch',json={'orders':[a,b], 'investigation_budget':1}).json()
    assert [r['order_id'] for r in result['orders']] == ['A-ORDER','Z-ORDER']
    assert [r['selected_for_review'] for r in result['orders']] == [True,False]
    assert result['selected'] == 1

def test_duplicate_and_empty_batches_rejected(client, order):
    assert client.post('/predict/batch',json={'orders':[order,order]}).status_code == 422
    assert client.post('/predict/batch',json={'orders':[]}).status_code == 422

def test_unknown_category_and_missing_measurements(client, order):
    order.update(primary_category='new_category',total_weight_g=None,total_volume_cm3=None)
    r = client.post('/predict',json=order)
    assert r.status_code == 200
    assert len(r.json()['warnings']) >= 2
    assert 0 <= r.json()['delay_probability'] <= 1

def test_missing_model_fails_closed(tmp_path, order):
    with TestClient(create_app(tmp_path)) as client:
        assert client.get('/health').status_code == 200
        assert client.get('/ready').status_code == 503
        assert client.post('/predict',json=order).status_code == 503

def test_corrupt_model_rejected(tmp_path):
    (tmp_path/'metadata.json').write_bytes((ROOT/'artifacts/metadata.json').read_bytes())
    (tmp_path/'model.joblib').write_bytes(b'not the model')
    with pytest.raises(ValueError,match='checksum'):
        Predictor(tmp_path)

def test_large_request_rejected(client):
    assert client.post('/predict',content=b'a'*1_000_001).status_code == 413

def test_report_matches_model(client):
    report = client.get('/evaluation').json()
    assert report['model_version'] == client.get('/model').json()['model_version']
    assert report['release_gate']['status'] == 'research_only'

def test_post_body_preserved_and_second_request_is_independent(client,order):
    for ident in ['FIRST','SECOND']:
        payload={**order,'order_id':ident}
        r=client.post('/predict',content=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        assert r.status_code==200
        assert r.json()['order_id']==ident

def test_chunked_body_limit_without_content_length(client,order):
    raw=json.dumps(order).encode()
    def chunks():
        yield raw[:15];yield raw[15:]
    r=client.post('/predict',content=chunks(),headers={'Content-Type':'application/json'})
    assert r.status_code==200
    def too_big():
        yield b' '*600_000;yield b' '*400_001
    assert client.post('/predict',content=too_big(),headers={'Content-Type':'application/json'}).status_code==413

def test_exact_limit_is_parsed_not_rejected(client,order):
    raw=json.dumps(order).encode();raw+=b' '*(1_000_000-len(raw))
    assert client.post('/predict',content=raw,headers={'Content-Type':'application/json'}).status_code==200

def test_revised_research_evidence_is_distinct_from_frozen_model(client):
    response=client.get('/research/evaluation')
    assert response.status_code==200
    data=response.json()
    assert data['decision']['stress_used_for_selection'] is False
    assert data['production_ready'] is False
    assert {'short_promise_rule','route_duration_rule','frozen_original_ml'} <= {r['method'] for r in data['stress']}
