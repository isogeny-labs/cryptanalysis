"""Actual compiler/runtime auditor bytes; I/O only."""
from pathlib import Path
import hashlib,json,shutil,sys
out=Path(sys.argv[1]);mode,label,name=sys.argv[2:5]
rows=[]
for line in(out/(label+'-compile.txt')).read_text().splitlines():
 try:row=json.loads(line)
 except json.JSONDecodeError:continue
 if row.get('reason')=='compiler-artifact'and row.get('target',{}).get('name')==name:rows.append(row)
assert len(rows)==1
artifact=rows[0];source=Path(artifact['executable']);copy=out/('actual-compiled-'+label+'.bin')
assert artifact['profile']['opt_level']=='3'and not artifact['profile']['test']
if mode=='compiled':
 shutil.copy2(source,copy);(out/(label+'-actual-path.txt')).write_text(str(source)+'\n')
else:
 assert mode=='runtime'and source.read_bytes()==copy.read_bytes()
 assert(out/(label+'-actual-path.txt')).read_text().strip()==str(source)
 shutil.copy2(source,out/('actual-runtime-'+label+'.bin'))
(out/(label+'-'+mode+'-custody.json')).write_text(json.dumps(dict(actual_Cargo_artifact=artifact,actual_path=str(source),bytes=copy.stat().st_size,sha256=hashlib.sha256(copy.read_bytes()).hexdigest(),mode=mode,whole_compiled_runtime_equal=mode=='runtime'),indent=2)+'\n')
