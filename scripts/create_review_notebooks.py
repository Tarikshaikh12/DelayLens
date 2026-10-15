"""Create four evidence-reading notebooks; fitting is reserved for the one-shot CLI."""
import json
from pathlib import Path
import nbformat as nbf
ROOT=Path(__file__).resolve().parents[1]
SETUP='''import sys, os, json, subprocess, tempfile, zipfile
from pathlib import Path
from IPython.display import display, Markdown
try:
    import google.colab
    IN_COLAB = True
except ImportError:
    IN_COLAB = False
ROOT = next((p for p in [Path.cwd(), Path.cwd().parent, Path('/content/delaylens')] if (p/'experiments/REVIEW_PROTOCOL.md').exists()), None)
if ROOT is None and IN_COLAB:
    from google.colab import files
    uploads = files.upload()
    archive = next(name for name in uploads if name.endswith('.zip'))
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            parts = Path(name).parts
            if not parts or parts[0] != 'delaylens' or '..' in parts or Path(name).is_absolute():
                raise ValueError('Unexpected archive member')
        z.extractall('/content')
    ROOT = Path('/content/delaylens')
if ROOT is None: raise RuntimeError('Open this notebook inside the extracted DelayLens project.')
os.chdir(ROOT)
PYTHON = sys.executable
if IN_COLAB:
    env = Path('/content/delaylens-review-env')
    if not (env/'bin/python').exists():
        subprocess.run([sys.executable,'-m','venv',str(env)],check=True)
    PYTHON = str(env/'bin/python')
    subprocess.run([PYTHON,'-m','pip','install','-r','requirements-lock.txt'],cwd=ROOT,check=True)
def run_python(source):
    result = subprocess.run([PYTHON,'-c',source],cwd=ROOT,text=True,capture_output=True)
    print(result.stdout)
    if result.returncode:
        print(result.stderr)
        result.check_returncode()
print('Ready. This notebook reads real saved evidence; it does not refit candidates.')
'''
def save(name,title,blocks):
    nb=nbf.v4.new_notebook();nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}}
    nb.cells=[nbf.v4.new_markdown_cell(title+'\n\nUpload the complete project ZIP if using Colab. Use Python 3.12 for the verified dependency lock. Run all cells. The original dashboard model is a frozen historical demonstration, not the preferred research method.'),nbf.v4.new_code_cell(SETUP)]
    for typ,source in blocks:nb.cells.append(nbf.v4.new_markdown_cell(source) if typ=='md' else nbf.v4.new_code_cell(source))
    nbf.write(nb,ROOT/'notebooks'/name)
save('00_Run_in_Colab.ipynb','# DelayLens: run the reviewed project',[
 ('md','## Read the evidence first\nThe research decision and the historical API model have different roles. No production, causal-impact or savings claim is made.'),
 ('code',"display(Markdown((ROOT/'reports/review/SUMMARY.md').read_text()))"),
 ('md','## Exercise the API\nThis sends a real JSON request through the FastAPI application. It uses an invented example, not a customer record.'),
 ('code',"run_python(\"from fastapi.testclient import TestClient\\nfrom app.main import create_app\\nimport json\\nwith TestClient(create_app()) as client:\\n    r=client.post('/predict',json=json.load(open('examples/single_order.json')))\\n    r.raise_for_status()\\n    print(json.dumps(r.json(),indent=2))\")"),
 ('md','## Optional browser dashboard\nThe Colab browser proxy requires a live signed-in Colab runtime. It was not verified by the authoring runtime. It is temporary hosting, not production deployment.'),
 ('code',"OPEN_DASHBOARD = False\nif OPEN_DASHBOARD:\n    import time\n    server = subprocess.Popen([PYTHON,'-m','uvicorn','app.main:app','--host','0.0.0.0','--port','8765'],cwd=ROOT)\n    if IN_COLAB:\n        from google.colab import output\n        output.serve_kernel_port_as_window(8765)\n    else:\n        print('http://127.0.0.1:8765')\nelse:\n    print('Optional dashboard server not started. API request above was executed.')"),
 ('md','## Rebuild from raw data\nRun `python scripts/rebuild.py` from the project folder using Python 3.12. It creates a new isolated checkout, installs the lock, downloads/verifies raw data, commits the fixed protocol, runs it once, then produces reports and checks. Do not alter settings to chase July–August results. The supplied results remain intact.')])
save('01_Understand_the_ML.ipynb','# Understand cohorts, missing outcomes, and regime changes',[
 ('md','## Approval-time cohort\nRows enter the queue using input eligibility, never eventual status or delivery. A missing or impossible delivery is unknown. It still consumes a review slot if selected. Known-hit lift is not full-population effectiveness.'),
 ('code',"print((ROOT/'reports/review/cohort_audit.json').read_text())\nprint((ROOT/'reports/review/raw_audit.json').read_text())"),
 ('md','## Raw monthly evidence\nThese rows include all raw orders with approval in each month. The prediction cohort is smaller because of input eligibility. Status is descriptive, not an input.'),
 ('code',"run_python(\"import pandas as pd\\nx=pd.read_csv('reports/review/raw_monthly.csv')\\nprint(x[['month','orders','median_promised_days','unknown_outcomes','delivered','shipped','canceled','unavailable']].to_string(index=False))\")"),
 ('md','## Missing-outcome bounds\nLower precision = confirmed late selected / all selected. Upper precision also counts selected unknowns as late. Neither bound is an estimate of savings. The missing outcomes may be non-random.'),
 ('code',"run_python(\"import pandas as pd\\nx=pd.read_csv('reports/review/stress_summary.csv')\\nprint(x[['method','budget','selected','confirmed_late_found','selected_unknown','precision_lower','precision_upper']].to_string(index=False))\")")])
save('02_Use_the_API.ipynb','# API requests, limits and the frozen demonstration model',[
 ('md','## Valid request\nThe API retains the original fitted artifact so its existing probability contract stays explicit. The new evaluation does not silently replace it.'),
 ('code',"run_python(\"import json\\nfrom fastapi.testclient import TestClient\\nfrom app.main import create_app\\nwith TestClient(create_app()) as c:\\n    order=json.load(open('examples/single_order.json'))\\n    r=c.post('/predict',json=order)\\n    assert r.status_code==200\\n    print(r.json())\\n    order['order_delivered_customer_date']='2018-07-31'\\n    bad=c.post('/predict',json=order)\\n    assert bad.status_code==422\\n    print('Future field rejected:',bad.status_code)\\n    large=c.post('/predict',content=b'x'*1000001)\\n    assert large.status_code==413\\n    print('Oversized body rejected:',large.status_code)\")"),
 ('md','## Actual verification evidence\nThe saved test report includes a separate live uvicorn request and a chunked oversized request over loopback. Test counts come from pytest XML.'),
 ('code',"print((ROOT/'reports/review/verification.json').read_text())")])
save('03_Improvement_Experiment.ipynb','# Review the committed, single-run experiment',[
 ('md','## Read what was fixed before execution'),
 ('code',"display(Markdown((ROOT/'experiments/REVIEW_PROTOCOL.md').read_text()))"),
 ('md','## Provenance\nThe commit and hashes record the exact protocol and critical code used. A local timestamp is not independent third-party preregistration.'),
 ('code',"print((ROOT/'reports/review/RUN_LEDGER.json').read_text())"),
 ('md','## Decision and paired uncertainty\nA small lead does not suffice. Promotion requires the preregistered month-win and uncertainty gates, including conservative missing-outcome bounds.'),
 ('code',"print((ROOT/'reports/review/decision.json').read_text())"),
 ('md','## Monthly comparisons'),
 ('code',"run_python(\"import pandas as pd\\nx=pd.read_csv('reports/review/monthly_performance.csv')\\nx=x[(x.phase=='development') & (x.budget==50)]\\nprint(x.pivot(index='month',columns='method',values='confirmed_late_found').to_string())\")")])
print('Created four reviewed notebooks')
