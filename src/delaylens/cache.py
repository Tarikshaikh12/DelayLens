"""Content-addressed raw/code/cache verification. Stale data is never trusted."""
import hashlib,json
from pathlib import Path
import pandas as pd

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def fingerprint(raw,manifest,code_files):
    expected=json.loads(Path(manifest).read_text())['files']
    observed={name:sha(Path(raw)/name) for name in expected}
    if observed!=expected: raise ValueError('Raw data hash mismatch: restore pinned source files.')
    return {'raw':observed,'code':{Path(p).name:sha(p) for p in code_files}}

def cached_frame(path,stamp,builder,force=False):
    path=Path(path); meta=path.with_suffix('.manifest.json')
    if not force and path.exists() and meta.exists():
        old=json.loads(meta.read_text())
        if old.get('fingerprint')==stamp and old.get('cache_sha256')==sha(path):
            return pd.read_pickle(path), 'verified_cache'
    frame=builder();path.parent.mkdir(parents=True,exist_ok=True);frame.to_pickle(path)
    meta.write_text(json.dumps({'fingerprint':stamp,'cache_sha256':sha(path)},indent=2)+'\n')
    return frame,'rebuilt_from_verified_raw'
