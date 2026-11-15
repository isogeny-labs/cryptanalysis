"""I/O-only Cargo executable path and whole-byte custody, no research arithmetic."""
from pathlib import Path
import hashlib,json,re,shutil,sys
out=Path(sys.argv[1]);label=sys.argv[2];mode=sys.argv[3]
rows=[]
for line in(out/(label+'-compile.txt')).read_text().splitlines():
 try:row=json.loads(line)
 except json.JSONDecodeError:continue
 if row.get('reason')=='compiler-artifact'and row.get('executable'):rows.append(row)
assert len(rows)==1
artifact=rows[0];source=Path(artifact['executable']);copy=out/(label+'-original-compiled-test.bin')
if mode=='compiled':shutil.copy2(source,copy)
else:
 assert mode=='runtime'
 paths=re.findall(r'Running unittests .*?\(([^)]+)\)',(out/(label+'-native.txt')).read_text())
 assert paths==[str(source)] and source.read_bytes()==copy.read_bytes()
 shutil.copy2(source,out/(label+'-actual-runtime-test.bin'))
value=dict(actual_Cargo_artifact=artifact,actual_path=str(source),bytes=copy.stat().st_size,sha256=hashlib.sha256(copy.read_bytes()).hexdigest(),mode=mode,compiled_runtime_equal=mode=='runtime')
(out/(label+'-'+mode+'-binary.json')).write_text(json.dumps(value,indent=2)+'\n')
