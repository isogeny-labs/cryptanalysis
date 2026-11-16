"""Actual Cargo artifact and full binary bytes only; no research arithmetic."""
from pathlib import Path
import json,hashlib,shutil,sys
out=Path(sys.argv[1]);label=sys.argv[2];target=sys.argv[3]
rows=[]
for line in (out/(label+'-compile.txt')).read_text().splitlines():
 try:r=json.loads(line)
 except json.JSONDecodeError:continue
 if r.get('reason')=='compiler-artifact'and r.get('target',{}).get('name')==target and r.get('executable'):rows.append(r)
assert len(rows)==1
r=rows[0];actual=Path(r['executable']);copy=out/(label+'-original-compiled.bin');shutil.copy2(actual,copy)
assert r['profile']['opt_level']=='3'
assert bool(r['profile']['test'])==(label=='chain')
(out/(label+'-compiled-custody.json')).write_text(json.dumps(dict(Cargo_artifact=r,actual_path=str(actual),copy=str(copy),bytes=copy.stat().st_size,sha256=hashlib.sha256(copy.read_bytes()).hexdigest()),indent=2)+'\n')
