"""Actual Cargo auditor executable and full-byte custody; no research arithmetic."""
from pathlib import Path
import hashlib,json,shutil,sys
out=Path(sys.argv[1]);mode=sys.argv[2]
rows=[]
for line in (out/'auditor-compile.txt').read_text().splitlines():
 try: row=json.loads(line)
 except json.JSONDecodeError: continue
 if row.get('reason')=='compiler-artifact' and row.get('target',{}).get('name')=='audit-paired-fourth': rows.append(row)
assert len(rows)==1
artifact=rows[0];source=Path(artifact['executable']);copy=out/'actual-compiled-auditor.bin'
assert artifact['profile']['opt_level']=='3' and not artifact['profile']['test']
if mode=='compiled':
 shutil.copy2(source,copy);(out/'auditor-actual-path.txt').write_text(str(source)+'\n')
else:
 assert mode=='runtime' and source.read_bytes()==copy.read_bytes()
 assert (out/'auditor-actual-path.txt').read_text().strip()==str(source)
 shutil.copy2(source,out/'actual-runtime-auditor.bin')
(out/('auditor-'+mode+'-custody.json')).write_text(json.dumps(dict(actual_Cargo_artifact=artifact,actual_path=str(source),bytes=copy.stat().st_size,sha256=hashlib.sha256(copy.read_bytes()).hexdigest(),mode=mode,whole_compiled_runtime_equal=mode=='runtime'),indent=2)+'\n')
