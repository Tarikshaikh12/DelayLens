"""One-command raw-data reproduction in an isolated checkout, exactly once there.
Run: python scripts/rebuild.py
The delivered evidence is never overwritten. Requires Python 3.12, git and internet
for missing packages/raw data. Does not need uv. A new reproduction is not tuning.
"""
import argparse,datetime,os,shutil,subprocess,sys,venv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    if sys.version_info[:2]!=(3,12):raise SystemExit('Use Python 3.12 for the verified lock.')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    dest=ROOT/'.reproductions'/stamp;dest.mkdir(parents=True)
    exclude={'.git','.venv','.venv-review','.venv-rebuild','.reproductions','__pycache__','.pytest_cache','node_modules','delaylens.egg-info'}
    for path in ROOT.iterdir():
        if path.name in exclude:continue
        if path.is_dir():shutil.copytree(path,dest/path.name,ignore=shutil.ignore_patterns(*exclude,'*.pyc'))
        else:shutil.copy2(path,dest/path.name)
    shutil.rmtree(dest/'data/processed',ignore_errors=True)
    shutil.rmtree(dest/'reports/review',ignore_errors=True)
    for cmd in [['git','init','-b','main'],['git','add','.'],['git','-c','user.name=DelayLens Reproduction','-c','user.email=reproduction@example.invalid','commit','-m','Freeze supplied protocol and code before independent reproduction']]:
        subprocess.run(cmd,cwd=dest,check=True)
    env=dest/'.venv-rebuild';venv.EnvBuilder(with_pip=True).create(env)
    python=env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    for args in [['-m','pip','install','-r','requirements-lock.txt'],['-m','pip','check'],['scripts/download_data.py'],['scripts/record_environment.py'],['-m','delaylens.review'],['scripts/render_review.py'],['scripts/run_checks.py'],['scripts/execute_notebooks.py','--in-process'],['scripts/finalize_review.py']]:
        subprocess.run([str(python),*args],cwd=dest,check=True)
    print('Reproduction saved:',dest)
if __name__=='__main__':main()
