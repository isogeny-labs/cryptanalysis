#!/usr/bin/env python3
"""Materialize exact tracked record evidence omitted by sparse checkout.

Only missing index paths are restored; existing worktree data and staged store
pointer deletions are untouched. This is checkout preparation, not measurement.
"""
import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'));needed=set()
for path in (ROOT/'benchmarks/records').glob('*.json'):
 paths=[]
 def strings(x):
  if isinstance(x,str):paths.append(x)
  elif isinstance(x,dict):
   for v in x.values():strings(v)
  elif isinstance(x,list):
   for v in x:strings(v)
 strings(json.loads(path.read_text()))
 for p in paths:
  if p in tracked and not (ROOT/p).exists():needed.add(p)
  q=Path(p)
  if not q.is_absolute():
   for parent in [q.parent,*q.parents]:
    m=str(parent/'.artifacts.json')
    if m in tracked and not (ROOT/m).exists():needed.add(m)
if needed:subprocess.run(['git','restore','--worktree','--ignore-skip-worktree-bits','--',*sorted(needed)],cwd=ROOT,check=True)
print('Hydrated',len(needed),'missing tracked record evidence paths')
