"""Run real pytest checks, preserve the machine-readable count, and test live HTTP."""
import importlib.metadata,json,os,socket,subprocess,sys,time,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/review';OUT.mkdir(exist_ok=True,parents=True)
def main():
    result=subprocess.run([sys.executable,'-m','pytest','-q','--junitxml='+str(OUT/'pytest.xml')],cwd=ROOT,text=True,capture_output=True)
    (OUT/'pytest.txt').write_text(result.stdout+result.stderr)
    print(result.stdout);result.check_returncode()
    tree=ET.parse(OUT/'pytest.xml');suites=tree.getroot().iter('testsuite')
    counts={k:0 for k in ['tests','failures','errors','skipped']}
    for suite in suites:
        for k in counts:counts[k]+=int(suite.attrib.get(k,0))
    # Real uvicorn POST over loopback, not only an in-process TestClient.
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    log=(OUT/'live_http.log').open('w')
    proc=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    try:
        for attempt in range(100):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/ready',timeout=2) as r:assert r.status==200
                break
            except Exception:
                if proc.poll() is not None:raise RuntimeError('Uvicorn exited; inspect live_http.log')
                time.sleep(.1)
        else:raise RuntimeError('Live server not ready')
        payload=json.loads((ROOT/'examples/single_order.json').read_text())
        for ident in ['LIVE-ONE','LIVE-TWO']:
            payload['order_id']=ident
            req=urllib.request.Request(f'http://127.0.0.1:{port}/predict',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=10) as r:
                assert json.load(r)['order_id']==ident
        import http.client
        conn=http.client.HTTPConnection('127.0.0.1',port,timeout=10)
        conn.request('POST','/predict',body=iter([b' '*600_000,b' '*400_001]),headers={'Content-Type':'application/json'},encode_chunked=True)
        assert conn.getresponse().status==413;conn.close()
        counts['live_http_post_preserved']=True;counts['live_chunked_oversize_413']=True
    finally:proc.terminate();proc.wait(timeout=10);log.close()
    counts['passed']=counts['tests']-counts['failures']-counts['errors']-counts['skipped']
    counts['packages']={p:importlib.metadata.version(p) for p in ['pytest','fastapi','starlette','httpx','numpy','pandas','scipy','scikit-learn','joblib']}
    (OUT/'verification.json').write_text(json.dumps(counts,indent=2)+'\n')
if __name__=='__main__':main()
