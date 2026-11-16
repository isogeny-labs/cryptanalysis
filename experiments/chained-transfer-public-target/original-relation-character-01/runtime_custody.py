"""Complete compiler/runtime/prepared-copy and whole accepted-input I/O custody."""
from pathlib import Path
import hashlib,json,shutil,sys
pkg,build,out=map(Path,sys.argv[1:4]);assert(build/'original.exit').read_text().strip()=='0'
for p in sorted((build/'actual-source').rglob('*')):
 if p.is_file():assert p.read_bytes()==(pkg/p.relative_to(build/'actual-source')).read_bytes()
images={}
for label in ['producer','auditor','control']:
 assert(build/(label+'-compile.exit')).read_text().strip()=='0'
 row=json.loads((build/(label+'-compiled-custody.json')).read_text());p=Path(row['actual_path']);body=p.read_bytes()
 assert body==Path(row['copy']).read_bytes()and len(body)==row['bytes']and hashlib.sha256(body).hexdigest()==row['sha256']
 target=out/('actual-before-'+label+'.bin')
 if target.exists():assert target.read_bytes()==body
 else:shutil.copy2(p,target)
 (out/(label+'-actual-path.txt')).write_text(str(p)+'\n');images[label]=row
assert json.loads((build/'engine-reused.json').read_text())['actual_reuse']is True
for row in json.loads((build/'engine-prepared.json').read_text())['files']:assert Path(row['actual_path']).read_bytes()==Path(row['copy']).read_bytes()
trace=Path('/workspace/scratch/ct101-original-relation-kernel-native-01/whole60-passive-trace.json');rank=Path('/workspace/scratch/ct102-original-relation-rank-native-01/whole60-independent-verdict.json')
v=json.loads(rank.read_text());assert v['whole_calls']==60 and v['complete_matrix_certificates']==360 and v['whole_trace_sha256']==hashlib.sha256(trace.read_bytes()).hexdigest()
(out/'whole-input-custody.json').write_text(json.dumps({str(p):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in [trace,rank]},indent=2)+'\n')
(out/'runtime-custody.json').write_text(json.dumps(dict(images=images,actual_full_original_field_prepared_bytes_equal=True),indent=2)+'\n')
