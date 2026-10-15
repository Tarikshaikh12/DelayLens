"""Record the actual runtime and lock consistency without assuming installation."""
import importlib.metadata,json,platform
from pathlib import Path
from delaylens.cache import sha
ROOT=Path(__file__).resolve().parents[1]
def main():
    expected={}
    for line in (ROOT/'requirements-lock.txt').read_text().splitlines():
        if '==' in line and not line.startswith('#'):
            name,version=line.split('==');expected[name]=version
    actual={name:importlib.metadata.version(name) for name in expected}
    mismatch={n:{'expected':v,'actual':actual[n]} for n,v in expected.items() if actual[n]!=v}
    if mismatch:raise RuntimeError(f'Lock version mismatch: {mismatch}')
    out=ROOT/'reports/review';out.mkdir(parents=True,exist_ok=True)
    result={'python':platform.python_version(),'platform':platform.platform(),'requirements_lock_sha256':sha(ROOT/'requirements-lock.txt'),'exact_locked_packages':actual,'mismatches':mismatch,'source_files_verified':len(json.loads((ROOT/'data/source_manifest.json').read_text())['files'])}
    (out/'runtime_lock_check.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Installed versions exactly match',len(expected),'locked packages')
if __name__=='__main__':main()
