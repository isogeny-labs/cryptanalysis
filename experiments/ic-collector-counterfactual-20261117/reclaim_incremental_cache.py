#!/usr/bin/env python3
"""Clear only this checkout's inactive, regenerable incremental Rust cache."""
import fcntl,hashlib,json,os,shutil,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[1]
cache=ROOT/'suite/target/debug/incremental'
expected=Path('/Volumes/SSD990-2/cryptanalysis-worktrees/ic-rational-current-20261115/suite/target/debug/incremental')
assert cache==expected and cache.resolve()==expected and cache.is_dir() and not cache.is_symlink()
probe=ROOT/'suite/target/debug/examples/ic_affine_pipeline_probe'
probe_hash=hashlib.sha256(probe.read_bytes()).hexdigest()
with (cache.parent/'.cargo-lock').open('r+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    opened=subprocess.run(['lsof','-u',os.environ['USER'],'-Fn'],text=True,capture_output=True,timeout=30)
    assert opened.returncode in [0,1]
    assert not any(line.startswith('n'+str(cache)+'/') for line in opened.stdout.splitlines()),'incremental cache is in use'
    files=[p for p in cache.rglob('*') if p.is_file()]
    assert all(not p.is_symlink() for p in cache.rglob('*'))
    count=len(files); size=sum(p.stat().st_size for p in files)
    assert count>0 and size>0
    shutil.rmtree(cache); cache.mkdir()
    assert hashlib.sha256(probe.read_bytes()).hexdigest()==probe_hash
    out=P/'incremental-cache-cleanup.json'; assert not out.exists()
    out.write_text(json.dumps(dict(status='pass',exact_cache_path=str(cache),regenerable_incremental_files_removed=count,bytes=size,target_lock='exclusive acquired',active_open_files_under_cache=0,existing_identity_probe_unchanged_sha256=probe_hash,scope='Only this checkout incremental compilation cache; source, dependency outputs, executables, raw data and unrelated builds retained.'),indent=2)+'\n')
print('Reclaimed inactive incremental compilation bytes',size,'files',count)
