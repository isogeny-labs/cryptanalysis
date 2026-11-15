"""I/O-only actual whole-line omission controls and compression."""
from pathlib import Path
import subprocess,json,lzma,hashlib
p=Path('/workspace/scratch/ct77-next-native-audit-01')
n=Path('/workspace/scratch/ct77-next-native-01')
exe=p/'actual-auditor.bin'
for phase,kind in [('edge','N4_NEXT13_PUBLIC'),('model','N4_NEXT13_MATCHED_MODELS')]:
 for mode in ['compare','omission']:
  raw=n/phase/'native.txt'
  dst=p/(phase+'-'+mode+'-accepted.json')
  if mode=='omission':
   lines=raw.read_bytes().splitlines(keepends=True)
   bad=[x for x in lines if (kind+' ').encode() in x]
   assert len(bad)==1
   raw=p/(phase+'-actual-whole-record-omission.txt')
   raw.write_bytes(b''.join(x for x in lines if (kind+' ').encode() not in x))
   (p/(phase+'-omission-custody.json')).write_text(json.dumps(dict(removed_whole_kind=kind,removed_bytes=len(bad[0]),removed_sha256=hashlib.sha256(bad[0]).hexdigest(),all_other_bytes_unchanged=True),indent=2)+'\n')
  q=subprocess.run([str(exe),'--compare',phase,str(p/(phase+'-all-native-records.json')),str(raw),str(dst)],capture_output=True)
  (p/(phase+'-'+mode+'.txt')).write_bytes(q.stdout+q.stderr)
  (p/(phase+'-'+mode+'.exit')).write_text(str(q.returncode)+'\n')
  print(phase,mode,q.returncode,'output',dst.exists(),flush=True)
  assert q.returncode==(0 if mode=='compare' else 101)
  assert dst.exists()==(mode=='compare')
 for name,raw in [(phase+'-all-native-records.json.xz',p/(phase+'-all-native-records.json')),(phase+'-whole-positive-native.txt.xz',n/phase/'native.txt')]:
  b=raw.read_bytes()
  dst=p/name
  dst.write_bytes(lzma.compress(b))
  assert lzma.decompress(dst.read_bytes())==b
  print(name,dst.stat().st_size,flush=True)
